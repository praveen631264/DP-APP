import logging
from app.celery_worker import celery
from app.database import Database
from app.ai_models import get_llm, get_embeddings
from app.utils.doc_utils import summarize_text_for_embedding
from bson import ObjectId

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='create_summary_embedding_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def create_summary_embedding_task(self, doc_id: str):
    """
    High-priority task for the "fast path".
    It generates a summary of the document's text and creates a single
    embedding for it, allowing for rapid, high-level search.
    """
    db: Database = self.db
    logger.info(f"[SUMMARY_TASK_START] Starting summary embedding for doc ID: {doc_id}")

    try:
        doc = db.get_document(doc_id)
        if not doc or not doc.get('text'):
            logger.warning(f"Document {doc_id} or its text not found. Skipping summary task.")
            return

        # Check for force stop signal
        if doc.get('status') == 'Force Stopped':
            logger.warning(f"Force stop signal received for document {doc_id}. Aborting summary task.")
            return

        # 1. Generate dense summary
        llm = get_llm()
        summary = summarize_text_for_embedding(doc['text'], llm)
        if not summary:
            logger.error(f"Failed to generate summary for doc {doc_id}.")
            return # Fail gracefully

        # 2. Generate embedding for the summary
        embeddings_model = get_embeddings()
        summary_embedding = embeddings_model.embed_query(summary)

        # 3. Update the main document with the summary and its embedding
        db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'summary': summary, 'summary_embedding': summary_embedding}})
        logger.info(f"[SUMMARY_TASK_SUCCESS] Successfully created and stored summary embedding for doc ID: {doc_id}")

    except Exception as e:
        logger.error(f"[SUMMARY_TASK_FAILURE] Error during summary embedding for doc {doc_id}: {e}", exc_info=True)
        raise