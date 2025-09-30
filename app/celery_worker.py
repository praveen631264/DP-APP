import logging
from celery import Celery
from flask import Flask
from app.utils.doc_utils import get_doc_text, get_kvps_and_category
from langchain.embeddings import HuggingFaceEmbeddings

celery = Celery(__name__)
logger = logging.getLogger(__name__)

# Global variable for the embeddings model
embeddings_model = None

def make_celery(app):
    """
    Factory to create and configure a Celery instance that is integrated
    with the Flask application context.
    """
    global embeddings_model

    celery.conf.update(app.config)

    # Eagerly load the embeddings model when the app is created
    if embeddings_model is None:
        model_name = app.config.get("EMBEDDINGS_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"Loading embeddings model: {model_name}")
        embeddings_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'} 
        )
        logger.info("Embeddings model loaded successfully.")

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

@celery.task(name='process_document_task')
def process_document_task(doc_id):
    """
    Asynchronous task to process a document: extract text, generate embeddings, and get KVPs.
    """
    from flask import current_app
    db = current_app.db

    doc = db.get_document(doc_id)
    if not doc:
        logger.error(f"[Celery Task] Error: Document with ID {doc_id} not found.")
        return

    file_content = db.get_file_content(doc.get('file_id'))
    if not file_content:
        logger.error(f"[Celery Task] Error: File content for doc ID {doc_id} not found in GridFS.")
        db.update_document_status(doc_id, "Processing Failed", {}, None, None, None)
        return

    logger.info(f"[Celery Task] Processing document: {doc['filename']}")

    # 1. Extract text
    text = get_doc_text(file_content, doc['content_type'])
    if not text:
        logger.warning(f"[Celery Task] Warning: Could not extract text from {doc['filename']}")
        db.update_document_status(doc_id, "Processing Failed", {}, None, "", None)
        return

    # 2. Generate vector embedding for the text
    try:
        global embeddings_model
        if embeddings_model is None:
             # This is a fallback in case the model wasn't loaded during app creation
            model_name = current_app.config.get("EMBEDDINGS_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
            embeddings_model = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': 'cpu'})
        
        embedding = embeddings_model.embed_query(text)
    except Exception as e:
        logger.error(f"[Celery Task] Error generating embedding for {doc['filename']}: {e}", exc_info=True)
        db.update_document_status(doc_id, "Processing Failed", {}, None, text, None)
        return

    # 3. Use AI to extract KVPs and categorize
    try:
        kvps, category = get_kvps_and_category(text)
    except Exception as e:
        logger.error(f"[Celery Task] Error during AI processing for {doc['filename']}: {e}", exc_info=True)
        db.update_document_status(doc_id, "Processing Failed", {}, None, text, embedding)
        return

    # 4. Save all results to MongoDB
    db.update_document_status(doc_id, "Processed", kvps, category, text, embedding)
    
    logger.info(f"[Celery Task] Successfully processed and saved document: {doc['filename']}")

    return {"status": "success", "doc_id": doc_id}
