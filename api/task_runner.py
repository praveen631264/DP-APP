from flask import Blueprint, request, jsonify
from tasks import process_document_task

# --- Blueprint Setup ---
task_api = Blueprint('task_api', __name__)


# --- Task Trigger Endpoint ---

@task_api.route('/api/v1/documents/process', methods=['POST'])
def trigger_document_processing():
    """
    This endpoint receives document data and puts it on the task queue for processing.
    """
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({"error": "Invalid payload. 'name' is required."}), 400

    # This is the key part: we call .delay() on our task.
    # Celery will now pick this up and process it in the background.
    process_document_task.delay(data)

    return jsonify({
        "message": "Document processing has been queued.",
        "data": data
    }), 202
