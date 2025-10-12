
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import redis

# Import the main Celery app instance
from tasks import celery_app

# --- Blueprint Setup ---
processing_api = Blueprint('processing_api', __name__)

# --- API Endpoints ---

@processing_api.route('/api/v1/upload', methods=['POST'])
def upload_and_pre_analyze():
    """
    Handles file uploads, creates a persistent record in Redis, 
    and triggers a background task for AI pre-analysis.
    """
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400

    try:
        redis_client = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'], db=current_app.config['REDIS_DB'], decode_responses=True)
        
        filename = file.filename
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        doc_id = str(uuid.uuid4())
        doc_key = f"doc:{doc_id}"
        doc_metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "file_path": file_path,
            "status": "pending",
            "uploaded_at": datetime.utcnow().isoformat(),
            "suggested_category": "processing...",
            "category": None,
            "task_id": None
        }
        redis_client.hset(doc_key, mapping=doc_metadata)

        task = celery_app.send_task('tasks.pre_analyze_document_task', args=[doc_id])
        redis_client.hset(doc_key, "task_id", task.id)

        return jsonify({"message": "File uploaded. AI pre-analysis started.", "doc_id": doc_id, "task_id": task.id}), 202

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@processing_api.route('/api/v1/document/<string:doc_id>/process', methods=['POST'])
def trigger_playbook_execution(doc_id):
    """
    Initiates the full, end-to-end processing of a document by triggering the
    playbook execution orchestrator task. This is called after a user has confirmed
    or set the document's category.
    """
    try:
        redis_client = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'], db=current_app.config['REDIS_DB'], decode_responses=True)

        doc_key = f"doc:{doc_id}"
        if not redis_client.exists(doc_key):
            return jsonify({"error": "Document not found"}), 404

        doc_data = redis_client.hgetall(doc_key)
        if not doc_data.get('category'):
            return jsonify({"error": "Document must be categorized before processing."}), 400

        # --- Trigger the Playbook Execution Orchestrator ---
        # This single task now handles the entire automation and indexing workflow.
        task = celery_app.send_task('tasks.execute_playbook_task', args=[doc_id])

        # Update Redis with the new task ID and a clear status
        redis_client.hset(doc_key, mapping={
            "task_id": task.id,
            "status": "queued_for_playbook"
        })

        return jsonify({
            "message": "Document has been queued for automated playbook execution and indexing.",
            "doc_id": doc_id,
            "task_id": task.id
        }), 202

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500
