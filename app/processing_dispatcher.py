import logging
from app.celery_worker import celery
from app.blueprints.stream import publish_status_update
from app.utils.doc_utils import extract_text, split_text_into_chunks, route_to_category
from app.database import MongoDatabase
from app.ai_models import get_llm
from bson import ObjectId
from celery import chain

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='extract_text_task')
def extract_text_task(self, doc_id: str):
    """Extracts text from a document and saves it to the database."""
    db: MongoDatabase = self.db
    doc = db.get_document(doc_id)
    if not doc:
        logger.error(f"Document {doc_id} not found.")
        return

    publish_status_update(doc_id, "Processing", "Step 1/5: Extracting text.")
    file_content = db.get_file_content(doc.get('file_id'))
    text = extract_text(file_content, doc['content_type'])
    db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'text': text}})
    logger.info(f"Text extracted for document {doc_id}.")
    return doc_id

@celery.task(bind=True, name='route_to_category_task')
def route_to_category_task(self, doc_id: str):
    """Routes a document to a category and saves it to the database."""
    db: MongoDatabase = self.db
    doc = db.get_document(doc_id)
    if not doc or not doc.get('text'):
        logger.error(f"Document {doc_id} or its text not found.")
        return

    publish_status_update(doc_id, "Processing", "Step 2/5: Categorizing document.")
    llm = get_llm()
    all_categories = db.get_all_categories()
    category = route_to_category(doc['text'], all_categories, llm)
    db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'category': category}})
    logger.info(f"Document {doc_id} routed to category: '{category}'.")
    return doc_id

@celery.task(bind=True, name='chunk_and_embed_task')
def chunk_and_embed_task(self, doc_id: str):
    """Chunks the document text and dispatches embedding and playbook tasks."""
    db: MongoDatabase = self.db
    doc = db.get_document(doc_id)
    if not doc or not doc.get('text'):
        logger.error(f"Document {doc_id} or its text not found.")
        return

    publish_status_update(doc_id, "Processing", "Step 3/5: Chunking and embedding.")
    text_chunks = split_text_into_chunks(doc['text'])
    chunks_to_create = [{'doc_id': ObjectId(doc_id), 'chunk_index': i, 'text': chunk_text, 'status': 'PENDING'} for i, chunk_text in enumerate(text_chunks)]
    db.create_document_chunks(chunks_to_create)

    from app.batch_chunk_worker import batch_process_chunks_task
    from app.playbook_worker import execute_playbook_task
    processing_chain = chain(batch_process_chunks_task.s(doc_id), execute_playbook_task.s(doc_id))
    async_result = processing_chain.apply_async()
    db.update_document_processing_chain_id(doc_id, async_result.id)
    logger.info(f"Chunking and embedding tasks dispatched for document {doc_id}.")
    return doc_id
