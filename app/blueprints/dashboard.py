from flask import Blueprint, jsonify, current_app

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Returns a full suite of dashboard statistics."""
    db = current_app.db
    stats = db.get_dashboard_statistics()
    return jsonify(stats)
