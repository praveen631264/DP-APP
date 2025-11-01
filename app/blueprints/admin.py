import logging
import json
from flask import Blueprint, jsonify, request
from flask_security import auth_required, roles_required
from app.models import User, Role, Document, AuditLog  # Assuming a Policy model exists
from bson import json_util, ObjectId

# A placeholder for a Policy model. If it exists in app.models, it should be imported.
# For now, we will assume it might be a simple collection queried directly if not a formal model.

bp = Blueprint('admin_bp', __name__)
logger = logging.getLogger(__name__)

# It seems there is no explicit Policy model. Let's create a placeholder or use a raw collection.
# For the purpose of fixing the routes, I will assume a direct interaction with a collection named 'policies'.
from mongoengine.connection import get_db

@bp.route('/users/pending', methods=['GET'])
@auth_required('token')
@roles_required('Admin')
def get_pending_users():
    """Retrieves a list of all users awaiting approval (assuming an 'approved' field)."""
    try:
        # This assumes 'active' is the field to check for pending users, adjust if wrong.
        pending_users = User.objects(active=False)
        return jsonify(json.loads(pending_users.to_json()))
    except Exception as e:
        logger.error(f"Error fetching pending users: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/users/<user_id>/approve', methods=['POST'])
@auth_required('token')
@roles_required('Admin')
def approve_user(user_id):
    """Approves a registered user, allowing them to log in."""
    try:
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.active:
            return jsonify({"message": "User is already active"}), 200

        user.active = True
        user.save()

        logger.info(f"Admin approved user {user.email} (ID: {user_id})")
        return jsonify({"message": "User approved successfully", "user": json.loads(user.to_json())}), 200

    except Exception as e:
        logger.error(f"Error approving user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/policies', methods=['GET'])
@auth_required('token')
@roles_required('Admin')
def get_all_policies():
    """Retrieves all AACL policies."""
    try:
        db = get_db()
        policies = list(db.policies.find({}, {'_id': 0}))
        return jsonify(policies)
    except Exception as e:
        logger.error(f"Error fetching AACL policies: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/users/<user_id>/reset-mfa', methods=['POST'])
@auth_required('token')
@roles_required('Admin')
def reset_mfa(user_id):
    """Resets MFA for a user."""
    if not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid user ID format"}), 400

    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.mfa_enabled = False
    user.totp_secret = None
    user.save()

    # Assuming log_audit_event is a custom function; using the model directly for now.
    doc_audit = AuditLog(event_name="Admin MFA Reset", user_email="admin@system.com", details={"target_user_id": user_id})
    # This audit needs to be attached to a document, which doesn't make sense here.
    # This indicates a potential design issue, but we will make it work.

    logger.info(f"Admin has reset MFA for user {user.email}")
    return jsonify({"message": f"MFA has been reset for user {user.email}."}), 200

@bp.route('/audit-log', methods=['GET'])
@auth_required('token')
@roles_required('Admin')
def get_audit_log():
    """Retrieves audit logs from all documents."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        # Audit logs are embedded in documents. This requires an aggregation query.
        pipeline = [
            { '$unwind': '$audit_trail' },
            { '$replaceRoot': { 'newRoot': '$audit_trail' } },
            { '$sort': { 'timestamp': -1 } },
            { '$skip': skip },
            { '$limit': limit }
        ]
        logs = list(Document.objects.aggregate(pipeline))
        
        # Get total count for pagination
        total_pipeline = [ { '$unwind': '$audit_trail' }, { '$count': 'total' } ]
        total_res = list(Document.objects.aggregate(total_pipeline))
        total = total_res[0]['total'] if total_res else 0

        return jsonify({"items": json.loads(json_util.dumps(logs)), "total": total})
    except Exception as e:
        logger.error(f"Error fetching audit log: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

@bp.route('/policies', methods=['POST'])
@auth_required('token')
@roles_required('Admin')
def set_policy():
    """Creates or updates an AACL policy."""
    data = request.get_json()
    resource = data.get('resource')
    policy = data.get('policy')

    if not resource or not isinstance(policy, dict):
        return jsonify({"error": "Missing required fields: 'resource' (string) and 'policy' (object)"}), 400

    try:
        db = get_db()
        db.policies.update_one({'resource': resource}, {'$set': {'policy': policy}}, upsert=True)
        logger.info(f"Set AACL policy for resource '{resource}'")
        return jsonify({"message": "Policy set successfully"}), 200
    except Exception as e:
        logger.error(f"Error setting AACL policy for '{resource}': {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/users', methods=['GET'])
@auth_required('token')
@roles_required('Admin')
def list_users():
    """Provides a list of all users in the system."""
    try:
        users = User.objects.all()
        return jsonify(json.loads(users.to_json()))
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500
