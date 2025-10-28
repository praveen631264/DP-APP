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
    active_job_tracker.current_job_id = None
    active_job_tracker.current_job_type = None

    if task.name == 'fine_tune_model_task':
        job_id = kwargs.get('kwargs', {}).get('job_id') or str(uuid.uuid4())
        active_job_tracker.current_job_id = job_id
        active_job_tracker.current_job_type = 'training'
    elif task.name == 'batch_process_chunks_task':
        doc_id = kwargs.get('args', [None])[0]
        active_job_tracker.current_job_id = doc_id
        active_job_tracker.current_job_type = 'document_processing'

@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """
    Handles graceful shutdown. Marks any 'RUNNING' job as 'INTERRUPTED'.
    """
    logger.warning("Celery worker shutting down. Checking for active jobs...")
    if hasattr(active_job_tracker, 'current_job_id') and active_job_tracker.current_job_id:
        job_id = active_job_tracker.current_job_id
        job_type = getattr(active_job_tracker, 'current_job_type', None)
        
        from app.database import MongoDatabase
        from config import Config
        db = MongoDatabase(Config.MONGO_URI, Config.VECTOR_DIMENSIONS)

        if job_type == 'training':
            db.update_job_status(job_id, 'INTERRUPTED', {"reason": "Worker shutdown."})
            logger.warning(f"Marked training job {job_id} as 'INTERRUPTED'.")
        elif job_type == 'document_processing':
            db.documents.update_one({'_id': ObjectId(job_id)}, {'$set': {'status': 'INTERRUPTED', 'status_message': 'Processing interrupted.'}})
            logger.warning(f"Marked document {job_id} as 'INTERRUPTED'.")

@celery.task(name="global_chat_agent_task")
def global_chat_agent_task(query: str, session_id: str):
    """
    Celery task to run the global chat agent and stream the response via Socket.IO.
    """
    logger.info(f"CELERY TASK: Starting global chat agent for session {session_id} with query: '{query}'")
    
    socketio = current_app.extensions.get('socketio')
    if not socketio:
        logger.error("SocketIO extension not found. Cannot stream response.")
        return

    try:
        # Import here to avoid circular dependencies at module load time
        from app.blueprints.chat import get_global_agent_executor
        
        llm = get_llm()
        agent_executor = get_global_agent_executor(llm)

        # Use the 'stream' method to get a real-time token stream
        for chunk in agent_executor.stream({"input": query}):
            # The stream yields a dictionary. We check for the answer chunk.
            if "messages" in chunk:
                # The actual content is in the last message of the list
                message = chunk["messages"][-1]
                if hasattr(message, 'content'):
                    token = message.content
                    # Emit each token as it arrives
                    socketio.emit('chat_token', {'token': token}, room=session_id)
        
        # Signal the end of the stream
        socketio.emit('chat_stream_end', room=session_id)
        logger.info(f"CELERY TASK: Agent stream finished for session {session_id}.")

    except Exception as e:
        logger.error(f"Error during agent execution for session {session_id}: {e}", exc_info=True)
        if socketio:
            socketio.emit('chat_error', {'error': 'An error occurred processing your request.'}, room=session_id)
