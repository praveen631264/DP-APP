
import logging
import datetime
import json
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from app.orchestrator_worker import orchestrator_agent_task
from io import BytesIO
from app.utils.json_encoder import JSONEncoder
from bson import ObjectId
from app.models import Document, AuditLog
from app import database

bp = Blueprint('documents_bp', __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'xlsx', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    if file and allowed_file(file.filename):
        try:
            new_doc = Document(
                filename=secure_filename(file.filename),
                content_type=file.content_type,
                status='Queued for Orchestration',
                audit_trail=[AuditLog(event_name="File Uploaded")]
            )
            new_doc.file.put(file.stream, content_type=file.content_type)
            new_doc.save()
            doc_id = str(new_doc.id)
            orchestrator_agent_task.delay(doc_id=doc_id)
            logger.info(f"Successfully uploaded document '{new_doc.filename}' with ID {doc_id}. Queued for orchestration.")
            
            # Use to_json and then json.loads to get a proper dict
            doc_json = json.loads(new_doc.to_json())
            return jsonify(doc_json), 202

        except Exception as e:
            logger.error(f"Error during document upload: {e}", exc_info=True)
            return jsonify({"error": "An internal error occurred during file upload"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

@bp.route('/', methods=['GET'])
def get_documents():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        filters = {k: v for k, v in request.args.items() if k not in ['page', 'limit', 'sort_by', 'sort_order']}

        documents, total = database.get_paginated_documents(page, limit, sort_by, sort_order, filters)
        
        # get_paginated_documents already returns a list of dicts
        return jsonify({"items": documents, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        logger.error(f"Error fetching documents: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>', methods=['GET'])
def get_document_details(doc_id):
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        document = Document.objects(id=doc_id, is_deleted=False).first()
        
        if document:
            doc_json = json.loads(document.to_json())
            return jsonify(doc_json), 200
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        if database.soft_delete_document(doc_id):
            return jsonify({"message": "Document has been successfully archived."}), 200
        else:
            return jsonify({"error": "Document not found or already deleted"}), 404
    except Exception as e:
        logger.error(f"Error soft-deleting document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/search', methods=['GET'])
def search_documents():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    try:
        # Assuming search_documents should be in database.py or implemented here
        # For now, let's implement a simple search on the Document model
        documents = Document.objects(filename__icontains=query, is_deleted=False)
        docs_json = json.loads(documents.to_json())
        return jsonify(docs_json), 200
    except Exception as e:
        logger.error(f"Error during document search for query '{query}': {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>/download', methods=['GET'])
def download_document(doc_id):
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
            
        doc = Document.objects(id=doc_id).first()
        if not doc or not doc.file:
            return jsonify({"error": "File not found for this document"}), 404
        
        return send_file(
            BytesIO(doc.file.read()),
            mimetype=doc.content_type,
            as_attachment=True,
            download_name=doc.filename
        )
    except Exception as e:
        logger.error(f"Error downloading file for doc {doc_id}: {e}", exc_info=True.to_json())
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>/kvp', methods=['PUT'])
def update_kvp(doc_id):
    data = request.get_json()
    new_kvps = data.get('kvps')
    version = data.get('_version')

    if not isinstance(new_kvps, dict) or version is None:
        return jsonify({"error": "Invalid JSON: body must be a dictionary containing 'kvps' and '_version'"}), 400

    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400

        # Implement optimistic locking directly
        doc = Document.objects(id=doc_id, _version=version).first()
        if not doc:
            # Check if it's a version mismatch or the doc is just gone
            if Document.objects(id=doc_id).first():
                return jsonify({"error": "Conflict: The document has been modified by another process. Please refresh and try again."}), 409
            else:
                return jsonify({"error": "Document not found"}), 404

        doc.kvps = new_kvps
        doc._version += 1
        doc.audit_trail.append(AuditLog(event_name="KVP Updated", details={"source": "user_action"}))
        doc.save()

        updated_doc = json.loads(doc.to_json())
        return jsonify({"message": "KVP updated successfully", "document": updated_doc})

    except Exception as e:
        logger.error(f"Error updating KVP for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>/recategorize', methods=['PUT'])
def recategorize_document(doc_id):
    data = request.get_json()
    new_category = data.get('new_category')
    explanation = data.get('explanation', 'Manual user correction.')

    if not new_category:
        return jsonify({"error": "Missing 'new_category' field"}), 400

    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        doc = Document.objects(id=doc_id).first()
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        original_category = doc.category
        doc.category = new_category
        doc.audit_trail.append(AuditLog(
            event_name="Manual Recategorization", 
            details={
                "original_category": original_category,
                "new_category": new_category,
                "explanation": explanation,
                "source": "user_action"
            }
        ))
        doc.save()

        # Here you might want to create a fine-tuning example for the model
        # This logic can be moved to a Celery task
        
        updated_doc = json.loads(doc.to_json())
        logger.info(f"Document {doc_id} re-categorized to '{new_category}' by user.")
        return jsonify({"message": "Document re-categorized successfully", "document": updated_doc}), 200

    except Exception as e:
        logger.error(f"Error re-categorizing document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>/reprocess', methods=['POST'])
def reprocess_document(doc_id):
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400

        # Check if doc exists before queueing task
        if not Document.objects(id=doc_id).first():
            return jsonify({"error": "Document not found"}), 404

        orchestrator_agent_task.delay(doc_id=doc_id, human_override_action="reprocess")
        
        logger.info(f"Human operator triggered reprocessing for document {doc_id}")
        return jsonify({"message": "Document has been queued for reprocessing."}), 202
    except Exception as e:
        logger.error(f"Error triggering reprocessing for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>/stop', methods=['POST'])
def stop_document_processing_route(doc_id): # Renamed to avoid conflict
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400

        # The logic for this is in database.py and seems correct.
        # Let's call it.
        success = database.stop_document_processing(doc_id)
        
        if success:
             return jsonify({"message": "Document processing has been signaled to stop."}), 202
        else:
            # The function returns False if the doc is not found or not in a stoppable state.
            doc = Document.objects(id=doc_id).first()
            if not doc:
                return jsonify({"error": "Document not found"}), 404
            else:
                 return jsonify({"error": f"Document is not in a stoppable state. Current status: '{doc.status}'"}), 409

    except Exception as e:
        logger.error(f"Error stopping processing for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/<doc_id>/history', methods=['GET'])
def get_document_history(doc_id):
    try:
        if not ObjectId.is_valid(doc_id):
            return jsonify({"error": "Invalid document ID format"}), 400
        
        if not Document.objects(id=doc_id).first():
            return jsonify({"error": "Document not found"}), 404

        # This function in database.py seems correct.
        history = list(database.get_document_audit_trail(doc_id))
        
        # Use the custom JSONEncoder to handle ObjectId and datetime
        return current_app.response_class(JSONEncoder().encode(history), mimetype='application/json')
    except Exception as e:
        logger.error(f"Error fetching history for document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
