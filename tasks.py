
from celery import Celery
import time
import random

# --- Celery Configuration ---
# The broker URL points to Redis. Celery uses this to pass messages.
# The backend URL is also Redis. This is used to store task state and results.

# Define the Dead-Letter Queue
task_acks_late = True
task_reject_on_worker_lost = True

# Configure a specific queue for dead-lettered tasks
task_routes = {
    'tasks.process_document_task': {
        'queue': 'processing',
        'routing_key': 'processing',
        'exchange': 'processing',
        'exchange_type': 'direct'
    }
}

# Dead letter queue configuration
dead_letter_queue_name = 'dead_letter'

celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_acks_late=task_acks_late,
    task_reject_on_worker_lost=task_reject_on_worker_lost,
    task_routes=task_routes,
)

# --- The Actual Task ---

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60) # Retry 3 times, wait 60s between retries
def process_document_task(self, data):
    """
    This is the FAILURE logic.
    It will retry if the external service fails.
    If it fails all retries, it moves to the DLQ.
    """
    doc_id = data.get('doc_id')
    print(f"Processing document: {doc_id}")

    try:
        # Simulate calling an external AI service that might fail
        if random.random() < 0.6: # 60% chance of failure for demonstration
            print(f"Task for doc_id: {doc_id} is failing, will retry...")
            raise ConnectionError("Could not connect to external AI service")

        # If the call succeeds
        print(f"Successfully processed document: {doc_id}")
        return {"status": "SUCCESS", "doc_id": doc_id}

    except ConnectionError as exc:
        # The `retry` method will re-queue the task.
        # Celery automatically knows it's a retry attempt.
        # If max_retries is exceeded, it will raise an exception and move to DLQ.
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            print(f"Task for doc_id: {doc_id} exceeded max retries. Moving to DLQ.")
            # Manually move to DLQ
            send_to_dead_letter_queue(self.request)


def send_to_dead_letter_queue(request):
    """
    Manually sends a task to the dead letter queue.
    """
    # Create a new message with the failed task's properties
    message = {
        'id': request.id,
        'task': request.task,
        'args': request.args,
        'kwargs': request.kwargs,
        'retries': request.retries,
        'exception': repr(request.excinfo.exception) if request.excinfo else None
    }
    # Send it to the DLQ
    with celery_app.producer_or_acquire() as producer:
        producer.publish(
            message,
            exchange='',
            routing_key=dead_letter_queue_name,
            serializer='json',
            retry=False # Do not retry sending to DLQ
        )
