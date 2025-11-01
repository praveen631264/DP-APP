import logging
from app.celery_worker import celery
from app.blueprints.stream import publish_status_update
from app.utils.doc_utils import extract_text, split_text_into_chunks, route_to_category
from app.models import Document, DocumentChunk, Category
from app.ai_models import get_llm
from bson import ObjectId
from celery import chain
from mongoengine.connection import get_db
import gridfs

logger = logging.getLogger(__name__)

@celery.task(name='extract_text_task')
def extract_text_task(doc_id: str):
    """Extracts text from a document's file and saves it to the document."""
    logger.info(f"Starting text extraction for document {doc_id}.")
    doc = Document.objects(id=doc_id).first()
    if not doc:
        logger.error(f"Cannot extract text: Document {doc_id} not found.")
        return

    try:
        publish_status_update(doc_id, "Processing", "Step 1/5: Extracting text...")
        
        db = get_db()
        fs = gridfs.GridFS(db)
        
        file_content = fs.get(doc.file.grid_id).read()

        text = extract_text(file_content, doc.content_type)
        doc.text = text
        doc.save()
        logger.info(f"Successfully extracted and saved text for document {doc_id}.")
        return doc_id
    except Exception as e:
        logger.error(f"Error in extract_text_task for doc {doc_id}: {e}", exc_info=True)
        doc.status = "Failed"
        doc.status_message = f"Error during text extraction: {e}"
        doc.save()
        raise

@celery.task(name='route_to_category_task')
def route_to_category_task(doc_id: str):
    """Routes a document to a category, falling back to 'Default'."""
    if not doc_id:
        return
    logger.info(f"Starting category routing for document {doc_id}.")
    doc = Document.objects(id=doc_id).first()
    if not doc or not doc.text:
        logger.error(f"Cannot route category: Document {doc_id} or its text not found.")
        return

    try:
        publish_status_update(doc_id, "Processing", "Step 2/5: Categorizing document...")
        llm = get_llm()
        
        # Fetch all categories except 'Default'
        categories = Category.objects(name__ne="Default")
        category_names = [cat.name for cat in categories]

        # Attempt to find a specific category match
        matched_category = route_to_category(doc.text, category_names, llm)

        # If no specific category is matched, assign it to the 'Default' category
        if not matched_category:
            final_category = "Default"
            logger.info(f"No specific category matched for doc {doc_id}. Assigning to 'Default'.")
        else:
            final_category = matched_category
            logger.info(f"Document {doc_id} routed to specific category: '{final_category}'.")

        doc.category_name = final_category
        doc.save()
        return doc_id
    except Exception as e:
        logger.error(f"Error in route_to_category_task for doc {doc_id}: {e}", exc_info=True)
        doc.status = "Failed"
        doc.status_message = f"Error during categorization: {e}"
        doc.save()
        raise

@celery.task(name='chunk_and_embed_task')
def chunk_and_embed_task(doc_id: str):
    """Chunks the document text and dispatches embedding and playbook tasks."""
    if not doc_id: return
    logger.info(f"Starting chunking and embedding for document {doc_id}.")
    doc = Document.objects(id=doc_id).first()
    if not doc or not doc.text:
        logger.error(f"Cannot chunk/embed: Document {doc_id} or its text not found.")
        return

    try:
        publish_status_update(doc_id, "Processing", "Step 3/5: Chunking & Embedding...")
        text_chunks = split_text_into_chunks(doc.text)
        
        chunks_to_create = [
            DocumentChunk(
                doc_id=doc.id, 
                chunk_index=i, 
                text=chunk_text, 
                status='PENDING'
            ) for i, chunk_text in enumerate(text_chunks)
        ]
        
        if chunks_to_create:
            DocumentChunk.objects.insert(chunks_to_create)
            logger.info(f"Created {len(chunks_to_create)} chunks for document {doc_id}.")
        else:
            logger.warning(f"No chunks were created for document {doc_id}.")

        from app.batch_chunk_worker import batch_process_chunks_task
        from app.playbook_worker import execute_playbook_task
        
        processing_chain = chain(batch_process_chunks_task.s(doc_id), execute_playbook_task.s(doc_id))
        async_result = processing_chain.apply_async()
        
        doc.processing_chain_id = async_result.id
        doc.save()
        
        logger.info(f"Chunking and embedding task chain dispatched for document {doc_id}.")
    except Exception as e:
        logger.error(f"Error in chunk_and_embed_task for doc {doc_id}: {e}", exc_info=True)
        doc.status = "Failed"
        doc.status_message = f"Error during chunking/embedding: {e}"
        doc.save()
        raise
