
import logging
from langchain.tools import tool
from flask import current_app
from app.processing_dispatcher import (
    extract_text_task,
    route_to_category_task,
    chunk_and_embed_task,
)
from app.playbook_worker import execute_playbook_task
from celery import chain
from bson import ObjectId

logger = logging.getLogger(__name__)

@tool
def get_document_details(doc_id: str) -> dict:
    """
    Returns the full details of a document, including its current status.
    Use this to understand the current state of a document before deciding on an action.
    """
    db = current_app.db
    return db.get_document(doc_id)

@tool
def dispatch_full_processing_pipeline(doc_id: str) -> str:
    """
    Dispatches the full, end-to-end document processing pipeline for a new document.
    This is a chain of text extraction, categorization, chunking, embedding, and playbook execution.
    """
    logger.info(f"ORCHESTRATOR TOOL: dispatch_full_processing_pipeline called for doc_id: {doc_id}")
    # BOMB FIX: Added the missing execute_playbook_task to complete the pipeline.
    full_chain = chain(
        extract_text_task.s(doc_id),
        route_to_category_task.s(),
        chunk_and_embed_task.s(),
        execute_playbook_task.s() # Assumes the doc_id is passed through the chain results.
    )
    full_chain.apply_async()
    return f"Full processing pipeline has been dispatched for document {doc_id}."

@tool
def dispatch_playbook_execution(doc_id: str) -> str:
    """
    Dispatches only the playbook execution task for a document. Use this when the document
    has already been processed but you want to re-run the playbook.
    """
    logger.info(f"ORCHESTRATOR TOOL: dispatch_playbook_execution called for doc_id: {doc_id}")
    execute_playbook_task.delay(doc_id=doc_id)
    return f"Playbook execution has been dispatched for document {doc_id}."

@tool
def compensate_and_mark_as_failed(doc_id: str, reason: str) -> str:
    """
    Marks a document as terminally 'Failed'. Use this as a last resort when a document
    cannot be processed after multiple attempts.
    """
    logger.warning(f"ORCHESTRATOR TOOL: Marking document {doc_id} as Failed. Reason: {reason}")
    db = current_app.db
    # BOMB FIX: Converted string doc_id to ObjectId for the MongoDB query.
    db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Failed', 'status_message': reason}})
    return f"Document {doc_id} has been marked as Failed."

@tool
def human_override_and_dispatch(doc_id: str, override_action: str) -> str:
    """
    Dispatches a processing pipeline for a document based on a human operator's explicit command.
    Use this ONLY when a human_override_action is provided.
    """
    logger.warning(f"ORCHESTRATOR TOOL: Human override for doc {doc_id} with action: {override_action}")
    
    if override_action == 'force_reprocess':
        # BOMB FIX: Added the missing execute_playbook_task to the reprocessing chain.
        full_chain = chain(
            extract_text_task.s(doc_id),
            route_to_category_task.s(),
            chunk_and_embed_task.s(),
            execute_playbook_task.s()
        )
        full_chain.apply_async()
        return f"Full reprocessing pipeline has been dispatched for document {doc_id}."
    elif override_action == 'force_run_playbook':
        execute_playbook_task.delay(doc_id=doc_id)
        return f"Playbook execution has been dispatched for document {doc_id}."
    else:
        return f"Unknown override action: {override_action}"

def get_orchestrator_tools():
    """
    Returns a list of all available tools for the orchestrator agent.
    """
    return [
        get_document_details,
        dispatch_full_processing_pipeline,
        dispatch_playbook_execution,
        compensate_and_mark_as_failed,
        human_override_and_dispatch
    ]
