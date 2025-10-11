
from flask import Blueprint, request, jsonify
from tasks import process_document_task # Assuming tasks are in tasks.py
import os

processing_api = Blueprint('processing_api', __name__)

@processing_api.route('/api/v1/process-document', methods=['POST'])
def process_document():
    """
    Receives a document and queues it for processing.
    This is where the "Reject" logic lives.
    """
    data = request.get_json()

    # --- REJECTION LOGIC ---
    # 1. Reject if data is missing or malformed
    if not data or 'doc_id' not in data or 'content' not in data:
        return jsonify({
            "error": "Invalid request. Missing 'doc_id' or 'content'.",
            "key": "Error",
            "value": "Invalid input. Task rejected, not queued."
        }), 400 # Bad Request

    # 2. Reject based on business rules (e.g., content too short)
    if len(data['content']) < 100:
        return jsonify({
            "error": "Content too short for processing.",
            "key": "Error",
            "value": "Business rule validation failed. Task rejected, not queued."
        }), 422 # Unprocessable Entity

    # --- If validation passes, send the task to the queue ---
    # The .delay() method sends the job to your Celery worker.
    task = process_document_task.delay(data)

    # Respond immediately to the client
    return jsonify({
        "message": "Task has been accepted for processing.",
        "task_id": task.id
    }), 202 # Accepted
