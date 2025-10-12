
import document_store
import os
import time
import random
import requests
from dotenv import load_dotenv
import logging

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Load Configuration ---
load_dotenv() # Load environment variables from .env file

# --- Constants & Playbook Definitions ---
PLAYBOOK_CATALOG = {
    "cat_monitor_test": {
        "id": "pb_monitor_test",
        "name": "System Monitoring Test Playbook",
        "description": "A playbook with steps designed to test the monitoring system.",
        "steps": [
            {
                "step": 1,
                "name": "Execute Live API Call",
                "description": "Calls a real external API to get data.",
                "task_type": "api_call"
            },
            {
                "step": 2,
                "name": "Process Data",
                "description": "A placeholder for processing the data from the API call.",
                "task_type": "data_processing"
            }
        ]
    }
}

# --- Production-Ready Task Execution ---

def _execute_api_call_task():
    """Performs a real API call and returns the result."""
    api_url = os.getenv("EXTERNAL_API_URL")
    if not api_url:
        logger.error("EXTERNAL_API_URL is not set in .env file.")
        return False, {"error": "EXTERNAL_API_URL is not set in .env file."}

    try:
        logger.info(f"Calling External API: {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() 
        logger.info(f"API call successful, status code {response.status_code}")
        return True, response.json()
    except requests.exceptions.RequestException as e:
        # This is a critical log for the Bugger Agent to find!
        logger.error(f"API request failed: {e}", exc_info=True)
        return False, {"error": f"API request failed: {str(e)}"}

# --- Main Playbook Runner ---

def run_playbook(document_id: str, playbook_id: str, catalog_id: str):
    playbook_data = PLAYBOOK_CATALOG.get(catalog_id)
    if not playbook_data or playbook_data['id'] != playbook_id:
        logger.error(f"Playbook '{playbook_id}' not found in catalog '{catalog_id}'.")
        raise ValueError(f"Playbook '{playbook_id}' not found in catalog '{catalog_id}'.")

    logger.info(f"Starting Playbook Run: {playbook_id} for Document: {document_id}")
    
    run_record = document_store.add_playbook_run(document_id, playbook_id, playbook_data.get('steps', []))
    current_run = run_record['playbook_runs'][-1]
    run_id = current_run['run_id']

    for step in current_run['steps']:
        step_id = step['step_id']
        worker_id = f"celery@worker-{random.randint(1, 3)}.local"
        
        document_store.start_playbook_step(document_id, run_id, step_id, worker_id)
        logger.info(f"Worker '{worker_id}' picked up step: '{step['name']}'")
        
        step_template = next((t for t in playbook_data['steps'] if t['step'] == step['step_order']), {})
        task_type = step_template.get("task_type")
        
        success, result = False, None

        if task_type == "api_call":
            success, result = _execute_api_call_task()
        elif task_type == "data_processing":
            success, result = True, {"message": "Data processed successfully"}
        else:
            logger.error(f"Unknown task type specified in playbook: {task_type}")
            success, result = False, {"error": f"Unknown task type: {task_type}"}

        document_store.complete_playbook_step(document_id, run_id, step_id, result, has_error=(not success))
        
        if success:
            logger.info(f"Step '{step['name']}' SUCCEEDED.")
        else:
            logger.error(f"Step '{step['name']}' FAILED. See result for details: {result}")
            break

    final_record = document_store.get_document_record(document_id)
    final_run_status = final_record['playbook_runs'][-1]['status']
    logger.info(f"Playbook Run {final_run_status.upper()} for run_id '{run_id}' is complete.")
    
    return final_record
