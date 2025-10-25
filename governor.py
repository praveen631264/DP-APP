import time
import logging
import os
import psutil
import uuid
from pymongo import MongoClient
from celery import Celery

# NOTE: In a real multi-process production environment, this shared state
# would need to be managed in a dedicated service like Redis, not a global variable.
# This implementation simulates that behavior for demonstration purposes.
from app.training_worker import RUNNING_JOBS, fine_tune_model_task

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TrainingGovernor")

# --- Configuration ---
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/doc_analyzer_db')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
POLL_INTERVAL_SECONDS = 30

# Create a Celery instance to send tasks
celery_app = Celery('governor', broker=CELERY_BROKER_URL)

def find_category_ready_for_training(db, min_examples=50):
    """
    Placeholder function to find a category with enough new data to warrant training.
    In a real implementation, this would track new vs. already-trained data.
    """
    # For now, just grab a random category from the fine-tuning data.
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": min_examples}}},
        {"$limit": 1}
    ]
    result = list(db.fine_tuning_data.aggregate(pipeline))
    if result:
        return result[0]['_id']
    return None

def main():
    logger.info("Starting Training Governor...")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_default_database()
        logger.info("Successfully connected to the database.")
    except Exception as e:
        logger.critical(f"Could not connect to the database. Governor cannot start. Error: {e}", exc_info=True)
        return

    while True:
        try:
            rulebook = db.system_config.find_one() or {}

            if not rulebook.get('resource_monitoring_enabled', False):
                logger.info("Resource monitoring is disabled in the Rulebook. Standing by.")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # Get current resource utilization
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"Current CPU: {cpu_percent}%. Running Jobs: {len(RUNNING_JOBS)}")

            # --- Governor Logic (Stop jobs if overloaded) ---
            stop_threshold = rulebook.get('max_cpu_percent', 80)
            if cpu_percent > stop_threshold and RUNNING_JOBS:
                # Find a running job to stop
                job_to_stop_id = next((job_id for job_id, state in RUNNING_JOBS.items() if state.get('status') == 'RUNNING'), None)
                if job_to_stop_id:
                    logger.warning(f"CPU ({cpu_percent}%) is above threshold ({stop_threshold}%). Signalling job {job_to_stop_id} to stop.")
                    RUNNING_JOBS[job_to_stop_id]["command"] = "STOP"

            # --- Dispatcher Logic (Start jobs if idle) ---
            start_threshold = rulebook.get('start_training_threshold_cpu', 50)
            max_jobs = rulebook.get('max_concurrent_training_jobs', 1)
            if cpu_percent < start_threshold and len(RUNNING_JOBS) < max_jobs:
                logger.info(f"CPU ({cpu_percent}%) is below threshold ({start_threshold}%). Checking for new training jobs.")
                category_to_train = find_category_ready_for_training(db, rulebook.get('min_examples_for_training', 50))
                
                if category_to_train:
                    logger.info(f"Found category '{category_to_train}' ready for training. Dispatching job...")
                    job_id = str(uuid.uuid4())
                    # The task is imported from training_worker but sent via our celery_app instance
                    fine_tune_model_task.delay(category_name=category_to_train, job_id=job_id)
                else:
                    logger.info("No categories with enough new data to start training.")

        except Exception as e:
            logger.error(f"An error occurred in the Governor's main loop: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
