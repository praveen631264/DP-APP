import logging
from app.celery_worker import celery
from app.database import Database
from app.training_worker import fine_tune_model_task, RUNNING_JOBS
from flask import current_app
logger = logging.getLogger(__name__)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Sets up the Celery Beat schedule. This task will run periodically.
    """
    # Run the governor task every 24 hours.
    sender.add_periodic_task(86400.0, training_governor_task.s(), name='check for model retraining daily')

@celery.task(bind=True, name='training_governor_task')
def training_governor_task(self):
    """
    Periodically checks for categories that have enough new correction data
    to warrant a fine-tuning job, and triggers them if they are not already running.
    """
    db: Database = self.db
    logger.info("[GOVERNOR_START] Checking for retraining candidates...")

    # Fetch configuration from the database, with sensible defaults.
    system_config = db.get_system_config() or {}
    governor_config = system_config.get('training_governor', {})
    correction_threshold = governor_config.get('correction_threshold', 100)
    since_days = governor_config.get('since_days', 30)

    try:
        candidates = db.get_retraining_candidates(threshold=correction_threshold, since_days=since_days)
        if not candidates:
            logger.info("[GOVERNOR_END] No categories met the threshold for retraining.")
            return

        for category_name in candidates:
            # Check if a job for this category is already running to avoid duplicate training runs.
            # We also check for interrupted jobs to restart them.
            running_job = db.jobs.find_one({'metadata.category': category_name, 'status': {'$in': ['RUNNING', 'INTERRUPTED']}})
            if not running_job:
                logger.info(f"Category '{category_name}' met the retraining threshold. Dispatching fine-tuning task.")
                fine_tune_model_task.delay(category_name=category_name)
            else:
                logger.info(f"Retraining for category '{category_name}' is already in progress. Skipping.")

    except Exception as e:
        logger.error(f"[GOVERNOR_FAILURE] An error occurred: {e}", exc_info=True)