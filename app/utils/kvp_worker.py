import logging
from app.celery_worker import celery
from app.ai_models import get_llm
from app.utils.doc_utils import extract_kvps
from app.db import get_db

logger = logging.getLogger(__name__)

DEFAULT_EXTRACTION_PROMPT = """You are an expert document analysis AI. Your task is to analyze the user's document text and extract important information as Key-Value Pairs (KVPs).

Identify and extract key information from the document as a JSON object. The keys should be in snake_case format.
Focus on extracting details like invoice numbers, dates, names, addresses, total amounts, and any other significant data points."""

@celery.task(bind=True, name='extract_kvp_task')
def extract_kvp_task(self, doc_id: str, category: str, text: str):
    """
    Celery task to extract Key-Value Pairs from a document's text.
    It uses a custom prompt from a category's playbook if one exists.
    """
    logger.info(f"Starting KVP extraction for doc_id: {doc_id} in category: '{category}'")
    db = get_db()

    try:
        # 1. Find the playbook for the given category
        playbook = db.categories.find_one({"name": category})

        # 2. Determine which prompt to use
        extraction_prompt = DEFAULT_EXTRACTION_PROMPT
        if playbook and playbook.get('extraction_prompt'):
            extraction_prompt = playbook['extraction_prompt']
            logger.info(f"Found custom extraction prompt for category '{category}'.")
        else:
            logger.info(f"Using default extraction prompt for category '{category}'.")

        # 3. Get the LLM and run the extraction
        llm = get_llm()
        kvps = extract_kvps(text, extraction_prompt, llm)

        # 4. Update the document in the database with the extracted KVPs
        db.update_document(doc_id, {"kvp": kvps})
        logger.info(f"Successfully extracted and saved {len(kvps)} KVPs for doc_id: {doc_id}")

        # This task is part of a chain, so it doesn't need to update the final status.
        # The orchestration task will handle that.
        return {"doc_id": doc_id, "status": "kvp_extracted"}

    except Exception as e:
        error_message = f"Failed to extract KVPs for doc_id {doc_id}: {e}"
        logger.error(error_message, exc_info=True)
        db.update_document(doc_id, {"status": "FAILED", "status_message": error_message})
        # Re-raise the exception to stop the Celery chain
        raise