import logging
from celery import Celery
from flask import current_app, Flask
from app.utils.doc_utils import extract_text_with_positions, get_kvps_and_category_with_positions
from app.ai_models import get_llm, get_embeddings
from app.database import Database

# Initialize Celery
celery = Celery(__name__)
logger = logging.getLogger(__name__)

def make_celery(app: Flask) -> Celery:
    """
    Factory to create and configure a Celery instance that is integrated
    with the Flask application context.
    """
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"]
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
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
    db: Database = self.db

    try:
        logger.info(f"[TASK_START] Processing document ID: {doc_id}")
        doc = db.get_document(doc_id)
        if not doc:
            logger.error(f"Document with ID {doc_id} not found. Aborting task.")
            return

        file_content = db.get_file_content(doc.get('file_id'))
        if not file_content:
            db.update_document_status(doc_id, "Error", {}, None, "File content not found in storage.", None)
            logger.error(f"File content for doc ID {doc_id} not found. Aborting.")
            return

        # 1. Extract Text and Word-level Positional Data
        logger.info(f"Step 1/4: Extracting text and positions from '{doc['filename']}'.")
        text, word_map = extract_text_with_positions(file_content, doc['content_type'])
        if not text:
            db.update_document_status(doc_id, "Error", {}, None, "Failed to extract text.", None)
            logger.warning(f"Could not extract text from '{doc['filename']}'.")
            return

        # 2. Extract Key-Value Pairs, Category, and map Bounding Boxes
        logger.info(f"Step 2/4: Extracting KVPs and category for '{doc['filename']}'.")
        all_categories = db.get_all_categories()
        kvps, category_name, explanation = get_kvps_and_category_with_positions(text, word_map, all_categories)

        # 3. Generate Embeddings
        logger.info(f"Step 3/4: Generating embeddings for '{doc['filename']}'.")
        embeddings_model = get_embeddings()
        embedding = embeddings_model.embed_query(text)
        
        # 4. Update the document in the database with all the new information
        logger.info(f"Step 4/4: Saving all extracted data for '{doc['filename']}'.")
        db.update_document_status(
            doc_id=doc_id,
            status="Processed",
            kvps=kvps,
            category=category_name,
            text=text,
            embedding=embedding,
            word_map=word_map,
            explanation=explanation
        )

        logger.info(f"[TASK_SUCCESS] Successfully processed document ID: {doc_id}")

    except Exception as e:
        logger.error(f"[TASK_FAILURE] An unexpected error occurred while processing document ID {doc_id}: {e}", exc_info=True)
        db.update_document_status(doc_id, "Error", {}, None, "An unexpected error occurred during processing.", None)
        raise

    return {"status": "success", "doc_id": doc_id}
