import logging
from celery import Celery
from flask import current_app, Flask
from app.utils.doc_utils import extract_text, extract_kvps_and_category
from app.ai_models import get_llm, get_embeddings
from app.database import DocumentDB

# Initialize Celery
celery = Celery(__name__)
logger = logging.getLogger(__name__)

def make_celery(app: Flask) -> Celery:
    """
    Factory to create and configure a Celery instance that is integrated
    with the Flask application context.
    """
    # Update Celery configuration from Flask app config
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"]
    )

    # Subclass Celery Task to automatically push a Flask app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                # Make the database client available to the task
                self.db = current_app.db
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    logger.info("Celery instance configured.")
    return celery

@celery.task(bind=True, name='process_document_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_document_task(self, doc_id: str):
    """
    Asynchronous task to process a single document. This task is the core of the document analysis pipeline.
    It uses automatic retry for robustness.
    """
    db: DocumentDB = self.db

    try:
        logger.info(f"[TASK_START] Processing document ID: {doc_id}")
        doc = db.get_document(doc_id)
        if not doc:
            logger.error(f"Document with ID {doc_id} not found. Aborting task.")
            return

        file_content = db.get_file_content(doc.get('file_id'))
        if not file_content:
            db.update_document_status(doc_id, "Error", "File content not found in storage.")
            logger.error(f"File content for doc ID {doc_id} not found. Aborting.")
            return

        # 1. Extract Text from document
        logger.info(f"Step 1/4: Extracting text from '{doc['filename']}'.")
        text = extract_text(file_content, doc['content_type'])
        if not text:
            db.update_document_status(doc_id, "Error", "Failed to extract text from document.")
            logger.warning(f"Could not extract text from '{doc['filename']}'.")
            return
        db.update_document_text(doc_id, text)

        # 2. Use AI to Extract Key-Value Pairs and Category
        logger.info(f"Step 2/4: Extracting KVPs and category for '{doc['filename']}'.")
        llm = get_llm()
        all_categories = db.get_all_categories()
        kvps, category_name, explanation = extract_kvps_and_category(text, all_categories, llm)

        # 3. Generate Embeddings for the extracted text
        logger.info(f"Step 3/4: Generating embeddings for '{doc['filename']}'.")
        embeddings_model = get_embeddings()
        embedding = embeddings_model.embed_query(text)
        
        # 4. Update the document in the database with all the new information
        logger.info(f"Step 4/4: Saving all extracted data for '{doc['filename']}'.")
        db.update_document_after_processing(
            doc_id=doc_id,
            kvps=kvps,
            category_name=category_name,
            explanation=explanation,
            embedding=embedding
        )

        logger.info(f"[TASK_SUCCESS] Successfully processed document ID: {doc_id}")

    except Exception as e:
        logger.error(f"[TASK_FAILURE] An unexpected error occurred while processing document ID {doc_id}: {e}", exc_info=True)
        # Mark the document as failed, so it can be reprocessed manually
        db.update_document_status(doc_id, "Error", "An unexpected error occurred during processing.")
        # The task will be retried automatically by Celery.
        raise

    return {"status": "success", "doc_id": doc_id}
