import logging
from flask import Blueprint, jsonify, current_app

document_bp = Blueprint('document_bp', __name__)
logger = logging.getLogger(__name__)

@document_bp.route('/documents/<doc_id>', methods=['DELETE'])
def soft_delete_document(doc_id):
    """Marks a document as deleted (soft delete)."""
    try:
        if current_app.db.soft_delete_document(doc_id):
            logger.info(f"Successfully soft-deleted document with ID {doc_id}")
            return jsonify({"message": "Document marked as deleted"}), 200
        else:
            logger.warning(f"Soft delete failed: Document with ID {doc_id} not found or already deleted.")
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        logger.error(f"Error soft-deleting document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@document_bp.route('/documents/<doc_id>/restore', methods=['POST'])
def restore_document(doc_id):
    """Restores a soft-deleted document."""
    try:
        if current_app.db.restore_document(doc_id):
            logger.info(f"Successfully restored document with ID {doc_id}")
            return jsonify({"message": "Document restored successfully"}), 200
        else:
            logger.warning(f"Restore failed: Document with ID {doc_id} not found or not deleted.")
            return jsonify({"error": "Document not found or not deleted"}), 404
    except Exception as e:
        logger.error(f"Error restoring document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
