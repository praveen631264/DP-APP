import logging
import types
import time
import datetime
from app.celery_worker import celery
from app.blueprints.stream import publish_status_update
from app.database import Database
from bson import ObjectId
from app.utils.base_step import PlaybookStep
from app.utils.fail_step import PlaybookTerminalException
from app.playbook_steps import get_step_plugins

logger = logging.getLogger(__name__)



class PlaybookExecutor:
    """
    Orchestrates the execution of a playbook using a dynamic plugin system for steps.
    """
    def __init__(self, db, doc_id):
        self.db = db
        self.doc_id = doc_id
        self.step_plugins = get_step_plugins()

    def execute_steps(self, steps, context):
        """Executes a list of playbook steps with error handling and retry logic."""
        for i, step in enumerate(steps):
            step_name = step.get('name', f"Unnamed Step {i+1}")
            on_failure = step.get('on_failure', {'policy': 'abort'})
            
            retry_policy = on_failure if on_failure.get('policy') == 'retry' else None
            max_retries = retry_policy.get('retries', 3) if retry_policy else 1
            delay = retry_policy.get('delay', 5) if retry_policy else 0

            for attempt in range(max_retries):
                try:
                    current_doc_state = self.db.get_document(self.doc_id)
                    if current_doc_state.get('status') == 'Force Stopped':
                        logger.warning(f"Force stop signal received for document {self.doc_id}. Halting.")
                        return False

                    step_type = step.get('type')
                    plugin = self.step_plugins.get(step_type)

                    if plugin:
                        plugin.execute(step, context, self.db, self.doc_id, self)
                    else:
                        logger.warning(f"Unknown step type '{step_type}' for step '{step_name}'. Skipping.")
                    
                    break # Success, break retry loop

                except PlaybookTerminalException as pte:
                    # This is a special case where a step (like FailStep) intentionally stops the playbook.
                    logger.error(f"Playbook execution was intentionally terminated by step '{step_name}': {pte}")
                    raise # Re-raise to stop the entire playbook execution.

                except Exception as e:
                    logger.error(f"Step '{step_name}' failed on attempt {attempt + 1}/{max_retries}. Error: {e}", exc_info=True)
                    if attempt + 1 >= max_retries:
                        if on_failure.get('policy') == 'skip':
                            logger.warning(f"Step '{step_name}' failed, but policy is 'skip'. Continuing.")
                            break
                        else:
                            logger.error(f"Step '{step_name}' failed and policy is 'abort'. Aborting playbook.")
                            raise
                    else:
                        logger.info(f"Retrying step '{step_name}' in {delay} seconds...")
                        time.sleep(delay)
        return True


@celery.task(bind=True, name='execute_playbook_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_playbook_task(self, previous_task_result: dict, doc_id: str):
    """
    Asynchronous task to execute a full playbook for a given document.
    It assembles the document text from chunks before execution.
    """
    db: Database = self.db
    logger.info(f"[PLAYBOOK_START] Attempting to execute playbook for document {doc_id}")

    # The result from the previous task in the chain is passed as the first argument.
    # We can use this to verify the chain is executing as expected.
    if not previous_task_result or previous_task_result.get('status') != 'success':
        logger.error(f"Playbook for doc {doc_id} did not receive a success signal from the previous task. Aborting.")
        publish_status_update(doc_id, "Playbook Failed", "Prerequisite task (chunk embedding) failed.")
        return



    try:
        document = db.get_document(doc_id)
        if not document:
            logger.error(f"Document {doc_id} not found. Aborting playbook execution.")
            return
        
        publish_status_update(doc_id, "Processing", "Executing playbook for final analysis.")

        # The full text was extracted and saved to the document record by the orchestrator task.
        # We use this text to ensure the LLM gets the most pristine version for KVP extraction.
        full_text = document.get('text')
        if not full_text:
            logger.error(f"Full text not found on document record {doc_id}. Aborting playbook.")
            publish_status_update(doc_id, "Playbook Failed", "Full text was missing from document record.")
            db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Error', 'status_message': 'Missing full text for playbook'}})
            return

        category_name = document.get('category')
        if not category_name:
            logger.warning(f"Document {doc_id} has no category. Skipping playbook execution.")
            publish_status_update(doc_id, "Categorization Failed", "Document could not be assigned to a category.")
            db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Categorization Failed'}})
            return

        playbook = db.get_playbook_for_category(category_name)
        if not playbook:
            logger.info(f"No playbook found for category '{category_name}'. Document processing is complete.")
            publish_status_update(doc_id, "Processed", "No playbook required for this category. Processing complete.")
            db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Processed'}})
            return
            
        playbook_id = playbook['_id']
        publish_status_update(doc_id, "Processing", f"Running playbook '{playbook['name']}'.")
        logger.info(f"Found playbook {playbook_id} ('{playbook['name']}') for category '{category_name}'.")

        context = {
            "document": document, 
            "full_text": full_text,
            "outputs": {}
        }
        
        executor = PlaybookExecutor(db, doc_id)
        executor.execute_steps(playbook.get('steps', []), context)

        # Merge all dictionary outputs into the document's KVP field
        final_kvps = document.get('kvps', {})
        for output in context['outputs'].values():
            if isinstance(output, dict):
                final_kvps.update(output)

        # Make the final status metadata-driven by the playbook itself.
        # Fallback to a sensible default if not specified.
        final_status = playbook.get('final_status', 'Processed')
        
        # Update the document with the results, using optimistic locking
        update_result = db.documents.update_one(
            {'_id': ObjectId(doc_id), '_version': document.get('_version', 1)},
            {'$set': {
                'kvps': final_kvps,
                'status': final_status,
                'processed_at': datetime.datetime.utcnow()
            },
             '$inc': {'_version': 1}}
        )

        if update_result.modified_count == 0:
            # This means another process modified the document while the playbook was running.
            publish_status_update(doc_id, "Playbook Failed", "A concurrent modification prevented saving results.")
            logger.warning(f"Optimistic lock failed for document {doc_id}. A concurrent update occurred. Aborting playbook.")
            raise Exception("Optimistic lock failed due to concurrent document modification.")

        logger.info(f"[PLAYBOOK_SUCCESS] Playbook {playbook_id} completed for document {doc_id}")
        publish_status_update(doc_id, final_status, "Playbook execution completed successfully.")
        return {"status": "success", "doc_id": doc_id, "playbook_id": playbook_id}

    except Exception as e:
        logger.error(f"[PLAYBOOK_FAILURE] Error executing playbook for doc {doc_id}: {e}", exc_info=True)
        publish_status_update(doc_id, "Playbook Failed", "A critical error occurred during playbook execution.")
        db.documents.update_one(
            {'_id': ObjectId(doc_id)},
            {'$set': {'status': 'Playbook Failed'}}
        )
        raise
