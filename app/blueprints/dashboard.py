import logging
from flask import Blueprint, jsonify, current_app
from flask_security import auth_required
import datetime
from app.models import User, Document

bp = Blueprint('dashboard_bp', __name__)
logger = logging.getLogger(__name__)

@bp.route('/stats', methods=['GET'])
# @auth_required('token')
def get_dashboard_stats():
    """
    Retrieves aggregated statistics for the main dashboard.
    """
    try:
        # Total documents
        total_docs = Document.objects.count()

        # Documents by status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = list(Document.objects.aggregate(status_pipeline))

        # Documents by category
        category_pipeline = [
            {"$match": {"category": {"$ne": "Uncategorized"}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        category_counts = list(Document.objects.aggregate(category_pipeline))

        # Documents processed over the last 30 days
        thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        docs_over_time_pipeline = [
            {"$match": {"created_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {"name": "$_id", "value": "$count", "_id": 0}}
        ]
        docs_over_time = list(Document.objects.aggregate(docs_over_time_pipeline))

        # Pending users
        pending_users = User.objects(approved=False).count()

        stats = {
            "total_documents": total_docs,
            "status_counts": {item['_id']: item['count'] for item in status_counts},
            "category_counts": [{"name": item['_id'], "value": item['count']} for item in category_counts],
            "docs_over_time": docs_over_time,
            "pending_users": pending_users
        }

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500