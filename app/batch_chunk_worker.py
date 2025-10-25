import logging
from app.celery_worker import celery
from app.database import Database
from app.ai_models import get_embeddings
from bson import ObjectId

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='batch_process_chunks_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def batch_process_chunks_task(self, doc_id: str):
    """
    Asynchronous task to process ALL chunks for a document in a single batch.
    This is more efficient than creating one task per chunk.
    """
    db: Database = self.db
    logger.info(f"[BATCH_CHUNK_START] Processing all chunks for document ID: {doc_id}")

    try:
        # Check for force stop signal at the beginning
        doc = db.get_document(doc_id)
        if doc and doc.get('status') == 'Force Stopped':
            logger.warning(f"Force stop signal received for document {doc_id}. Aborting batch chunk processing.")
            return

        chunks = db.get_chunks_for_document(doc_id)
        pending_chunks = [c for c in chunks if c.get('status') == 'PENDING']

        if not pending_chunks:
            logger.info(f"No pending chunks to process for document {doc_id}. Task complete.")
            return

        logger.info(f"Found {len(pending_chunks)} chunks to embed for document {doc_id}.")
        
        embeddings_model = get_embeddings()
        
        # Get all text from chunks to embed them in a single batch call
        texts_to_embed = [chunk['text'] for chunk in pending_chunks]
        embeddings = embeddings_model.embed_documents(texts_to_embed)

        # Prepare updates for a single bulk write operation for maximum efficiency
        updates = [(str(chunk['_id']), embeddings[i]) for i, chunk in enumerate(pending_chunks)]
        modified_count = db.bulk_update_chunk_embeddings(updates)
        logger.info(f"Bulk updated {modified_count} chunks in the database.")

        # On success, update the parent document's status
        db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Chunks Processed', 'status_message': 'Embeddings generated successfully.'}})
        logger.info(f"[BATCH_CHUNK_SUCCESS] Successfully processed {len(pending_chunks)} chunks for document ID: {doc_id}")
        return {"status": "success", "doc_id": doc_id, "processed_chunks": len(pending_chunks)}
    except Exception as e:
        logger.error(f"[BATCH_CHUNK_FAILURE] Error during batch processing for doc {doc_id}: {e}", exc_info=True)
        db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Error', 'status_message': 'Failed to generate embeddings.'}})
        raise