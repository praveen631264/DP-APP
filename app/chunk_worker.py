import logging
from app.celery_worker import celery
from app.database import Database
from app.ai_models import get_embeddings

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='process_chunk_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_chunk_task(self, chunk_id: str):
    """
    Asynchronous task to process a single document chunk.
    This task generates a vector embedding for the chunk's text.
    """
    db: Database = self.db
    logger.info(f"[CHUNK_TASK_START] Processing chunk ID: {chunk_id}")

    try:
        chunk = db.get_chunk(chunk_id)
        if not chunk:
            logger.error(f"Chunk with ID {chunk_id} not found. Aborting task.")
            return

        chunk_text = chunk.get('text')
        if not chunk_text:
            logger.warning(f"Chunk {chunk_id} has no text. Skipping embedding.")
            db.document_chunks.update_one({'_id': chunk['_id']}, {'$set': {'status': 'Skipped'}})
            return

        # 1. Generate Embedding
        embeddings_model = get_embeddings()
        embedding = embeddings_model.embed_query(chunk_text)

        # 2. Update the chunk in the database with the new embedding
        db.update_chunk_embedding(chunk_id, embedding)

        logger.info(f"[CHUNK_TASK_SUCCESS] Successfully processed chunk ID: {chunk_id}")
        return {"status": "success", "chunk_id": chunk_id}

    except Exception as e:
        logger.error(f"[CHUNK_TASK_FAILURE] An unexpected error occurred while processing chunk ID {chunk_id}: {e}", exc_info=True)
        # Update chunk status to 'Error' to prevent the playbook from getting stuck
        if 'db' in self and hasattr(self.db, 'document_chunks'):
            self.db.document_chunks.update_one({'_id': chunk_id}, {'$set': {'status': 'Error'}})
        raise
