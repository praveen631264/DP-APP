import logging
import threading
import uuid
from celery import Celery, group, chain
from celery.signals import worker_shutdown, task_prerun
from flask import current_app, Flask, g
from app.ai_models import get_llm
from bson import ObjectId

# Initialize Celery
celery = Celery(__name__)
logger = logging.getLogger(__name__)

# Thread-local storage to track the active job ID for each worker thread
active_job_tracker = threading.local()

def make_celery(app: Flask) -> Celery:
    """
    Factory to create and configure a Celery instance that is integrated
    with the Flask application context.
    """
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        # Pass mongo config to celery so tasks can access it if needed
        MONGO_URI=app.config["MONGO_URI"],
        VECTOR_DIMENSIONS=app.config["VECTOR_DIMENSIONS"]
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                # Use Flask's 'g' object for a request-safe db connection
                if not hasattr(g, 'db'):
                    g.db = current_app.db
                self.db = g.db
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    logger.info("Celery instance configured.")
    return celery

@task_prerun.connect
def on_task_prerun(task_id, task, *args, **kwargs):
    """
    Before a task runs, store its ID in thread-local storage.
    This allows the shutdown handler to know which job was running.
    """
    # Clear any previous job ID from the thread-local storage
    active_job_tracker.current_job_id = None
    active_job_tracker.current_job_type = None

    if task.name == 'fine_tune_model_task':
        # The job_id for training tasks is passed in the arguments
        job_id = kwargs.get('kwargs', {}).get('job_id') or str(uuid.uuid4())
        active_job_tracker.current_job_id = job_id
        active_job_tracker.current_job_type = 'training'
    elif task.name == 'batch_process_chunks_task':
        # For document processing, the job is the document itself.
        doc_id = kwargs.get('args', [None])[0]
        active_job_tracker.current_job_id = doc_id
        active_job_tracker.current_job_type = 'document_processing'

@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """
    Handles graceful shutdown of a Celery worker.
    It finds any 'RUNNING' job associated with this worker and marks it as 'INTERRUPTED'.
    """
    logger.warning("Celery worker shutting down. Checking for active jobs to mark as interrupted.")
    if hasattr(active_job_tracker, 'current_job_id'):
        job_id = active_job_tracker.current_job_id
        # We need a direct DB connection as the app context is gone during shutdown.
        from app.database import MongoDatabase
        from config import Config
        db = MongoDatabase(Config.MONGO_URI, Config.VECTOR_DIMENSIONS)

        if getattr(active_job_tracker, 'current_job_type', None) == 'training':
            db.update_job_status(job_id, 'INTERRUPTED', {"reason": "Worker shutdown."})
            logger.warning(f"Successfully marked active training job {job_id} as 'INTERRUPTED'.")
        elif getattr(active_job_tracker, 'current_job_type', None) == 'document_processing':
            # For documents, we update the document's own status
            db.documents.update_one({'_id': ObjectId(job_id)}, {'$set': {'status': 'INTERRUPTED', 'status_message': 'Processing was interrupted by worker shutdown.'}})
            logger.warning(f"Successfully marked active document {job_id} as 'INTERRUPTED'.")
