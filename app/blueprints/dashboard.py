
from flask import Blueprint, jsonify
from app.models import Document, User

bp = Blueprint('dashboard', __name__)

@bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Provides a high-level overview of system statistics.
    """
    try:
        # Count total non-deleted documents
        total_documents = Document.objects(is_deleted=False).count()

        # Aggregate counts for documents by status
        status_pipeline = [
            {'$match': {'is_deleted': False}},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]
        status_counts_cursor = Document.objects.aggregate(status_pipeline)
        status_counts = {item['_id']: item['count'] for item in status_counts_cursor}

        # Aggregate counts for documents by category
        category_pipeline = [
            {'$match': {'is_deleted': False, 'category': {'$ne': None}}},
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}}
        ]
        category_counts_cursor = Document.objects.aggregate(category_pipeline)
        # Correctly create a dictionary for category_counts, converting ObjectId to string
        category_counts = {str(item['_id']): item['count'] for item in category_counts_cursor}

        # Count users who are not yet active
        pending_users = User.objects(active=False).count()

        stats = {
            'total_documents': total_documents,
            'status_counts': status_counts,
            'category_counts': category_counts,
            'pending_users': pending_users
        }

        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching dashboard stats', 'details': str(e)}), 500
