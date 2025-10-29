import logging
import time
import datetime
from app.celery_worker import celery
from app.blueprints.stream import publish_status_update
from app.models import Document, Playbook
from app.utils.base_step import PlaybookStep
from app.utils.fail_step import PlaybookTerminalException
from app.playbook_steps import get_step_plugins

logger = logging.getLogger(__name__)

class PlaybookExecutor:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.step_plugins = get_step_plugins()

    def execute_steps(self, steps, context):
        for i, step_config in enumerate(steps):
            step_name = step_config.get('name', f"Unnamed Step {i+1}")
            on_failure = step_config.get('on_failure', {'policy': 'abort'})
            retry_policy = on_failure if on_failure.get('policy') == 'retry' else None
            max_retries = retry_policy.get('retries', 3) if retry_policy else 1
            delay = retry_policy.get('delay', 5) if retry_policy else 0

            for attempt in range(max_retries):
                try:
                    current_doc = Document.objects(id=self.doc_id).first()
                    if not current_doc:
                        raise PlaybookTerminalException("Document disappeared during execution.")
                    if current_doc.status == 'Force Stopped':
                        logger.warning(f"Force stop for doc {self.doc_id}. Halting playbook.")
                        return False 

                    step_type = step_config.get('type')
                    plugin = self.step_plugins.get(step_type)

                    if plugin:
                        # Pass 'self' (the executor instance) to the plugin
                        plugin.execute(step_config, context, self.doc_id, self)
                    else:
                        logger.warning(f"Unknown step type '{step_type}' for step '{step_name}'. Skipping.")
                    
                    break

                except PlaybookTerminalException as pte:
                    logger.error(f"Playbook terminated by step '{step_name}': {pte}")
                    raise 

                except Exception as e:
                    logger.error(f"Step '{step_name}' failed attempt {attempt + 1}/{max_retries}: {e}", exc_info=True)
                    if attempt + 1 >= max_retries:
                        if on_failure.get('policy') == 'skip':
                            logger.warning(f"Skipping failed step '{step_name}'.")
                            break
                        else:
                            logger.error(f"Aborting playbook due to failed step '{step_name}'.")
                            raise
                    else:
                        time.sleep(delay)
        return True


@celery.task(name='execute_playbook_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_playbook_task(previous_task_result: dict, doc_id: str):
    if not previous_task_result or previous_task_result.get('status') != 'success':
        logger.error(f"Playbook for doc {doc_id} aborted due to previous task failure.")
        publish_status_update(doc_id, "Playbook Failed", "Prerequisite task (chunk embedding) failed.")
        return

    logger.info(f"[PLAYBOOK_START] Executing playbook for document {doc_id}")
    
    doc = Document.objects(id=doc_id).first()
    if not doc:
        logger.error(f"Document {doc_id} not found. Aborting playbook.")
        return

    try:
        publish_status_update(doc_id, "Processing", "Executing playbook for final analysis.")

        if not doc.text:
            raise ValueError("Full text is missing from the document record.")
        
        if not doc.category:
            doc.status = 'Categorization Failed'
            doc.save()
            publish_status_update(doc_id, "Categorization Failed", "Document could not be assigned to a category.")
            logger.warning(f"Doc {doc_id} has no category. Skipping playbook.")
            return

        playbook = Playbook.objects(category=doc.category).first()
        if not playbook:
            doc.status = 'Processed'
            doc.status_message = 'No playbook required for this category.'
            doc.save()
            publish_status_update(doc_id, "Processed", "Processing complete (no playbook).")
            logger.info(f"No playbook for category '{doc.category}'. Processing complete for doc {doc_id}.")
            return
            
        publish_status_update(doc_id, "Processing", f"Running playbook '{playbook.name}'.")
        logger.info(f"Found playbook {playbook.id} ('{playbook.name}') for category '{doc.category}'.")

        context = {
            "document": doc, 
            "full_text": doc.text,
            "outputs": {}
        }
        
        executor = PlaybookExecutor(doc_id)
        executor.execute_steps(playbook.steps, context)

        # Reload the document to get the absolute latest state
        doc.reload()
        
        final_kvps = doc.kvps or {}
        for output in context['outputs'].values():
            if isinstance(output, dict):
                final_kvps.update(output)
        
        doc.kvps = final_kvps
        doc.status = playbook.final_status or 'Processed'
        doc.processed_at = datetime.datetime.utcnow()
        doc.save()

        logger.info(f"[PLAYBOOK_SUCCESS] Playbook {playbook.id} completed for document {doc_id}")
        publish_status_update(doc_id, doc.status, "Playbook execution completed successfully.")
        return {"status": "success", "doc_id": str(doc_id), "playbook_id": str(playbook.id)}

    except Exception as e:
        logger.error(f"[PLAYBOOK_FAILURE] Error executing playbook for doc {doc_id}: {e}", exc_info=True)
        if 'doc' in locals() and doc:
            doc.reload()
            doc.status = 'Playbook Failed'
            doc.status_message = "A critical error occurred during playbook execution."
            doc.save()
        publish_status_update(doc_id, "Playbook Failed", "A critical error occurred.")
        raise
