import logging
import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from app.security import attribute_required
from app.orchestrator_worker import orchestrator_agent_task
from io import BytesIO
from app.utils.json_encoder import JSONEncoder
from bson import ObjectId
from app import database

bp = Blueprint('documents_bp', __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'xlsx', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/documents', methods=['POST'])
def upload_document():
    """
    Uploads a new document for processing.
    The file should be sent as multipart/form-data in the 'file' field.
    """
    db = current_app.db
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400
    if file and allowed_file(file.filename):
        try:
            file_id = db.save_file(file)
            doc_data = {
                'filename': secure_filename(file.filename),
                'content_type': file.content_type,
                'file_id': file_id,
                'status': 'Queued for Orchestration',
                'created_at': datetime.datetime.utcnow()
            }
            doc_id = db.create_document(doc_data)
            
            # Invoke the central brain to decide what to do next
            orchestrator_agent_task.delay(doc_id=doc_id)
            
            created_doc = db.get_document(doc_id)
            logger.info(f"Successfully uploaded document '{created_doc['filename']}' with ID {doc_id}")
            return jsonify(created_doc), 202
        except Exception as e:
            logger.error(f"Error during document upload: {e}", exc_info=True)
            return jsonify({"error": "An internal error occurred during file upload"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

@bp.route('/', methods=['GET'])
def get_documents():
    """
    Retrieves a paginated, sorted, and filtered list of documents.
    Query Params:
    - page: The page number (default: 1)
    - limit: The number of items per page (default: 10)
    - sort_by: The field to sort by (default: 'created_at')
    - sort_order: 'asc' or 'desc' (default: 'desc')
    - Any other query param is treated as a filter (e.g., ?status=Completed)
    """
    db = current_app.db
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Collect all other query parameters as filters
        filters = {k: v for k, v in request.args.items() if k not in ['page', 'limit', 'sort_by', 'sort_order']}

        documents, total = database.get_paginated_documents(page, limit, sort_by, sort_order, filters)
        return jsonify({"items": documents, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        logger.error(f"Error fetching documents: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>', methods=['GET'])
def get_document_details(doc_id):
    """Retrieves all details for a single document by its ID."""
    db = current_app.db
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        document = db.get_document(doc_id)
        if document:
            return jsonify(document), 200
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """
    Soft-deletes a document. This is a non-destructive operation.
    The orchestrator should ensure any in-flight processing is halted.
    """
    db = current_app.db
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        # Here you might want to signal the orchestrator to stop processing before deleting
        # For now, we will directly mark it as deleted.
        if db.soft_delete_document(doc_id):
            return jsonify({"message": "Document has been successfully archived."}), 200
        else:
            return jsonify({"error": "Document not found or already deleted"}), 404
    except Exception as e:
        logger.error(f"Error soft-deleting document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/search', methods=['GET'])
def search_documents():
    """Searches for documents by filename."""
    db = current_app.db
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    try:
        documents = db.search_documents(query)
        return jsonify(documents), 200
    except Exception as e:
        logger.error(f"Error during document search for query '{query}': {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>/download', methods=['GET'])
@attribute_required # The policy is now fetched from the database
def download_document(doc_id):
    """Downloads the original file for a given document."""
    db = current_app.db
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        file_data = db.get_file_with_metadata(doc_id)
        if file_data:
            return send_file(
                BytesIO(file_data['content']),
                mimetype=file_data['content_type'],
                as_attachment=True,
                download_name=file_data['filename']
            )
        else:
            return jsonify({"error": "File not found for this document"}), 404
    except Exception as e:
        logger.error(f"Error downloading file for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>/kvp', methods=['PUT'])
def update_kvp(doc_id):
    db = current_app.db
    data = request.get_json()
    new_kvps = data.get('kvps')
    version = data.get('_version')

    if not isinstance(new_kvps, dict) or version is None:
        return jsonify({"error": "Invalid JSON: body must be a dictionary containing 'kvps' and '_version'"}), 400

    if not db.get_document(doc_id):
        return jsonify({"error": "Document not found"}), 404

    if not db.update_document_kvp(doc_id, version, new_kvps):
        # This indicates a version mismatch (a race condition)
        return jsonify({"error": "Conflict: The document has been modified by another process. Please refresh and try again."}), 409

    updated_doc = db.get_document(doc_id)
    return jsonify({"message": "KVP updated successfully", "document": updated_doc})

@bp.route('/documents/<doc_id>/recategorize', methods=['PUT'])
def recategorize_document(doc_id):
    """
    Manually changes the category of a document and provides an explanation.
    This action also creates a fine-tuning example for the model.
    """
    db = current_app.db
    data = request.get_json()
    new_category = data.get('new_category')
    explanation = data.get('explanation', 'Manual user correction.')

    if not new_category:
        return jsonify({"error": "Missing 'new_category' field"}), 400

    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        success = db.recategorize_document(doc_id, new_category, explanation)
        if success:
            updated_doc = db.get_document(doc_id)
            logger.info(f"Document {doc_id} re-categorized to '{new_category}' by user.")
            return jsonify({"message": "Document re-categorized successfully", "document": updated_doc}), 200
        else:
            return jsonify({"error": "Document not found or update failed"}), 404
    except Exception as e:
        logger.error(f"Error re-categorizing document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>/reprocess', methods=['POST'])
def reprocess_document(doc_id):
    """Re-triggers the entire processing pipeline for a document."""
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400

        # Invoke the central brain with a human override command
        orchestrator_agent_task.delay(doc_id=doc_id, human_override_action="reprocess")
        
        logger.info(f"Human operator triggered reprocessing for document {doc_id}")
        return jsonify({"message": "Document has been queued for reprocessing."}), 202
    except Exception as e:
        logger.error(f"Error triggering reprocessing for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>/stop', methods=['POST'])
def stop_document_processing(doc_id):
    """
    Cooperatively stops the processing of a document by setting its status to 'Force Stopped'.
    This acts as a 'stop' or 'pause' command. Processing can be resumed via the 'reprocess' endpoint.
    """
    db = current_app.db
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400

        doc = db.get_document(doc_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Define states from which processing can be stopped.
        stoppable_statuses = ['Processing', 'Queued for Orchestration', 'Queued for Reprocessing', 'Chunks Processed', 'INTERRUPTED']
        if doc.get('status') not in stoppable_statuses:
            return jsonify({"error": f"Document is not in a stoppable state. Current status: '{doc.get('status')}'"}), 409

        db.stop_document_processing(doc_id)
        return jsonify({"message": "Document processing has been signaled to stop."}), 202
    except Exception as e:
        logger.error(f"Error stopping processing for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/documents/<doc_id>/history', methods=['GET'])
def get_document_history(doc_id):
    """Retrieves the audit trail (history) for a single document."""
    db = current_app.db
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        # Check if document exists
        if not db.get_document(doc_id):
            return jsonify({"error": "Document not found"}), 404

        history = list(database.get_document_audit_trail(doc_id))
        
        # Use the custom JSONEncoder to handle ObjectId and datetime
        return current_app.response_class(JSONEncoder().encode(history), mimetype='application/json')
    except Exception as e:
        logger.error(f"Error fetching history for document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
