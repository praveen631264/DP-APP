
from flask import Blueprint, jsonify

bp = Blueprint('health_bp', __name__)

@bp.route('/health', methods=['GET'])
def health_check():
    """Returns a 200 OK status to indicate the service is running."""
    return jsonify({"status": "ok"}), 200
