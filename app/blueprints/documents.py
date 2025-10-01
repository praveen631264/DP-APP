import os
import datetime
import logging
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from io import BytesIO

documents_bp = Blueprint('documents_bp', __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route('/documents', methods=['POST'])
def upload_document():
    db = current_app.db
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        file_id = db.save_file(file)
        doc_data = {
            "filename": secure_filename(file.filename),
            "content_type": file.content_type,
            "file_id": file_id,
            "status": "Queued for Processing",
            "created_at": datetime.datetime.utcnow(),
            "processed_at": None,
            "kvps": {},
            "category": None,
            "categorization_explanation": None,
            "text": None,
            "embedding": None
        }
        doc_id = db.create_document(doc_data)

        from app.celery_worker import process_document_task
        process_document_task.delay(doc_id)
        
        created_doc = db.get_document(doc_id)
        return jsonify({"message": "File uploaded and queued for processing", "document": created_doc}), 202
    else:
        return jsonify({"error": "File type not allowed"}), 400

@documents_bp.route('/documents', methods=['GET'])
def get_documents():
    """Fetches documents, optionally filtering by category."""
    db = current_app.db
    category = request.args.get('category')
    # Add a new parameter to fetch deleted documents for the trash view
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    docs = db.get_documents(category=category, include_deleted=include_deleted)
    return jsonify(docs)

@documents_bp.route('/documents/recent', methods=['GET'])
def get_recent_documents():
    """Fetches the most recently uploaded documents."""
    db = current_app.db
    limit = request.args.get('limit', 5, type=int)
    docs = db.get_recent_documents(limit=limit)
    return jsonify(docs)

@documents_bp.route('/documents/search', methods=['GET'])
def search_documents():
    db = current_app.db
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = db.search_documents(query)
    return jsonify(results)

@documents_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document_details(doc_id):
    db = current_app.db
    doc = db.get_document(doc_id)
    if doc:
        return jsonify({"document": doc})
    else:
        return jsonify({"error": "Document not found"}), 404

@documents_bp.route('/documents/<doc_id>', methods=['DELETE'])
def soft_delete_document(doc_id):
    """Marks a document as deleted (soft delete)."""
    try:
        if current_app.db.soft_delete_document(doc_id):
            logger.info(f"Successfully soft-deleted document with ID {doc_id}")
            return jsonify({"message": "Document moved to trash"}), 200
        else:
            logger.warning(f"Soft delete failed: Document with ID {doc_id} not found or already deleted.")
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logger.error(f"Error soft-deleting document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@documents_bp.route('/documents/<doc_id>/restore', methods=['POST'])
def restore_document(doc_id):
    """Restores a soft-deleted document."""
    try:
        if current_app.db.restore_document(doc_id):
            logger.info(f"Successfully restored document with ID {doc_id}")
            return jsonify({"message": "Document restored successfully"}), 200
        else:
            logger.warning(f"Restore failed: Document with ID {doc_id} not found or not deleted.")
            return jsonify({"error": "Document not found or not in trash"}), 404
    except Exception as e:
        logger.error(f"Error restoring document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@documents_bp.route('/documents/<doc_id>/download', methods=['GET'])
def download_document(doc_id):
    """Downloads the original file for a given document."""
    db = current_app.db
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    file_data = db.get_file_with_metadata(doc['file_id'])
    if not file_data:
        return jsonify({"error": "File not found in storage"}), 404

    return send_file(
        BytesIO(file_data['content']),
        mimetype=file_data['content_type'],
        as_attachment=True,
        download_name=file_data['filename']
    )

@documents_bp.route('/documents/<doc_id>/kvp', methods=['PUT'])
def update_kvp(doc_id):
    db = current_app.db
    new_kvps = request.get_json()
    if not isinstance(new_kvps, dict):
        return jsonify({"error": "Invalid JSON: body must be a dictionary"}), 400

    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    db.update_document_kvp(doc_id, new_kvps)

    updated_doc = db.get_document(doc_id)
    return jsonify({"message": "KVP updated successfully", "document": updated_doc})

@documents_bp.route('/documents/<doc_id>/recategorize', methods=['PUT'])
def recategorize(doc_id):
    db = current_app.db
    data = request.get_json()
    new_category = data.get('new_category')
    explanation = data.get('explanation', '')

    if not new_category:
        return jsonify({"error": "New category is required"}), 400

    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    db.recategorize_document(doc_id, new_category, explanation)

    updated_doc = db.get_document(doc_id)
    return jsonify({"message": f"Document re-categorized to '{new_category}'", "document": updated_doc})

# --- Interactive KVP Management Endpoints ---

@documents_bp.route('/documents/<doc_id>/kvp/add', methods=['POST'])
def add_kvp_interactively(doc_id):
    """
    Adds a single Key-Value Pair to a document, as instructed by a user
    through the interactive chat. This action is logged for AI fine-tuning.
    """
    db = current_app.db
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')

    if not key or value is None: # value can be an empty string
        return jsonify({"error": "Both 'key' and 'value' are required"}), 400

    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    try:
        # This new DB function will add the KVP and log for fine-tuning
        db.add_interactive_kvp(doc_id, key, value)
        updated_doc = db.get_document(doc_id)
        logger.info(f"Interactively added KVP '{key}' to document {doc_id}")
        return jsonify({"message": "KVP added and logged for training", "document": updated_doc}), 200
    except Exception as e:
        logger.error(f"Error interactively adding KVP to {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@documents_bp.route('/documents/<doc_id>/kvp/update', methods=['PATCH'])
def update_kvp_interactively(doc_id):
    """
    Updates a single Key-Value Pair for a document, as instructed by a user
    through the interactive chat. This action is logged for AI fine-tuning.
    """
    db = current_app.db
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')

    if not key or value is None:
        return jsonify({"error": "Both 'key' and 'value' are required"}), 400

    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    try:
        # This new DB function will update the KVP and log for fine-tuning
        result = db.update_interactive_kvp(doc_id, key, value)
        if not result:
             return jsonify({"error": f"KVP with key '{key}' not found in document"}), 404
        
        updated_doc = db.get_document(doc_id)
        logger.info(f"Interactively updated KVP '{key}' in document {doc_id}")
        return jsonify({"message": "KVP updated and logged for training", "document": updated_doc}), 200
    except Exception as e:
        logger.error(f"Error interactively updating KVP in {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@documents_bp.route('/documents/<doc_id>/kvp/delete', methods=['DELETE'])
def delete_kvp_interactively(doc_id):
    """
    Deletes a single Key-Value Pair from a document, as instructed by a user
    through the interactive chat. This action is logged for AI fine-tuning.
    """
    db = current_app.db
    data = request.get_json()
    key = data.get('key')

    if not key:
        return jsonify({"error": "'key' is required in the request body"}), 400

    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    try:
        # This new DB function will delete the KVP and log for fine-tuning
        result = db.delete_interactive_kvp(doc_id, key)
        if not result:
            return jsonify({"error": f"KVP with key '{key}' not found in document"}), 404

        updated_doc = db.get_document(doc_id)
        logger.info(f"Interactively deleted KVP '{key}' from document {doc_id}")
        return jsonify({"message": "KVP deleted and logged for training", "document": updated_doc}), 200
    except Exception as e:
        logger.error(f"Error interactively deleting KVP from {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@documents_bp.route('/documents/<doc_id>/reprocess', methods=['POST'])
def reprocess_document(doc_id):
    """
    Re-triggers the AI processing for a document, typically after a failure.
    """
    db = current_app.db
    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    db.update_document_for_reprocessing(doc_id)

    from app.celery_worker import process_document_task
    process_document_task.delay(doc_id)

    updated_doc = db.get_document(doc_id)

    return jsonify({
        "message": "Document has been re-queued for processing.",
        "document": updated_doc
    }), 202
