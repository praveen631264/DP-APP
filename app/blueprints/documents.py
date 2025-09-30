import os
import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from io import BytesIO

documents_bp = Blueprint('documents_bp', __name__)

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
    docs = db.get_documents(category=category)
    return jsonify(docs)

@documents_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document_details(doc_id):
    db = current_app.db
    doc = db.get_document(doc_id)
    if doc:
        return jsonify({"document": doc})
    else:
        return jsonify({"error": "Document not found"}), 404

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

    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    db.recategorize_document(doc_id, new_category, explanation)
    
    fine_tuning_data = {"text": doc.get('text', ''), "category": new_category}
    db.save_fine_tuning_data(fine_tuning_data)

    updated_doc = db.get_document(doc_id)
    return jsonify({"message": f"Document re-categorized to '{new_category}'", "document": updated_doc})

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

@documents_bp.route('/documents/search', methods=['GET'])
def search_documents():
    db = current_app.db
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = db.search_documents(query)
    return jsonify(results)
