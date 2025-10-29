import logging
from flask import Blueprint, jsonify, current_app, request
from flask_security import auth_required, roles_required
from app.models import User, Role
from app.audit import log_audit_event
from bson import json_util, ObjectId
from app.models import User, Role

bp = Blueprint('admin_bp', __name__)
logger = logging.getLogger(__name__)

@bp.route('/users/pending', methods=['GET'])
@auth_required('token')
@roles_required('admin')
def get_pending_users():
    """
    Retrieves a list of all users awaiting approval.
    """
    try:
        # Use the MongoEngine model to query for users
        pending_users = User.objects(approved=False)
        # Convert MongoEngine documents to JSON
        users_json = [user.to_mongo().to_dict() for user in pending_users]
        # Use json_util to handle BSON types like ObjectId
        return json_util.dumps(users_json), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error fetching pending users: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/users/<user_id>/approve', methods=['POST'])
@auth_required('token')
@roles_required('admin')
def approve_user(user_id):
    """
    Approves a registered user, allowing them to log in.
    """
    try:
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.approved:
            return jsonify({"message": "User is already approved"}), 200

        user.approved = True
        user.save()

        logger.info(f"Admin approved user {user.email} (ID: {user_id})")
        
        user_json = user.to_mongo().to_dict()
        return jsonify({
            "message": "User approved successfully",
            "user": json_util.loads(json_util.dumps(user_json))
        }), 200

    except Exception as e:
        logger.error(f"Error approving user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

# --- AACL Policy Management Endpoints ---

@bp.route('/policies', methods=['GET'])
@auth_required('token')
@roles_required('admin')
def get_all_policies():
    """Retrieves all AACL policies from the database."""
    db = current_app.db
    try:
        policies = db.get_all_policies()
        return json_util.dumps(policies), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error fetching AACL policies: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/users/<user_id>/reset-mfa', methods=['POST'])
@auth_required('token')
@roles_required('admin')
def reset_mfa(user_id):
    """
    Allows an admin to reset/disable MFA for a specific user.
    """
    if not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid user ID format"}), 400

    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.mfa_enabled = False
    user.totp_secret = None
    user.save()

    log_audit_event("ADMIN_MFA_RESET", {"target_user_id": user_id})
    logger.info(f"Admin has reset MFA for user {user.email}")
    return jsonify({"message": f"MFA has been reset for user {user.email}."}), 200

@bp.route('/audit-log', methods=['GET'])
@auth_required('token')
@roles_required('admin')
def get_audit_log():
    """
    Retrieves a paginated list of audit log events.
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit
        
        # Build a dynamic filter query
        filters = {}
        action_filter = request.args.get('action')
        user_filter = request.args.get('user_email')
        if action_filter:
            filters['action'] = action_filter
        if user_filter:
            filters['user_email'] = {'$regex': user_filter, '$options': 'i'} # Case-insensitive search

        db = current_app.db
        total = db.audit_log.count_documents(filters)
        logs = list(db.audit_log.find(filters).sort('timestamp', -1).skip(skip).limit(limit))

        return jsonify({"items": logs, "total": total})

    except Exception as e:
        logger.error(f"Error fetching audit log: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

@bp.route('/policies/<path:resource>', methods=['DELETE'])
@auth_required('token')
@roles_required('admin')
def delete_policy(resource):
    """Deletes an AACL policy for a given resource."""
    db = current_app.db
    try:
        result = db.delete_policy_for_resource(resource)
        if result:
            logger.info(f"Deleted AACL policy for resource '{resource}'")
            return jsonify({
                "message": "Policy deleted successfully",
                "resource": resource
            }), 200
        else:
            return jsonify({"error": "Policy not found for the given resource"}), 404
    except Exception as e:
        logger.error(f"Error deleting AACL policy for '{resource}': {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

@bp.route('/policies', methods=['POST'])
@auth_required('token')
@roles_required('admin')
def set_policy():
    """Creates or updates an AACL policy for a specific resource."""
    db = current_app.db
    data = request.get_json()
    resource = data.get('resource')
    policy = data.get('policy')
    description = data.get('description', '')

    if not resource or not isinstance(policy, dict):
        return jsonify({"error": "Missing required fields: 'resource' (string) and 'policy' (object)"}), 400

    try:
        db.set_policy_for_resource(resource, policy, description)
        logger.info(f"Set AACL policy for resource '{resource}'")
        return jsonify({
            "message": "Policy set successfully",
            "resource": resource,
            "policy": policy
        }), 200
    except Exception as e:
        logger.error(f"Error setting AACL policy for '{resource}': {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/users', methods=['GET'])
@auth_required('token')
@roles_required('admin')
def list_users():
    """
    Provides a list of all users in the system for administration.
    """
    try:
        users = User.objects.all()
        user_list = []
        for user in users:
            user_list.append({
                "id": str(user.id),
                "email": user.email,
                "active": user.active,
                "approved": user.approved,
                "roles": [role.name for role in user.roles],
                "confirmed_at": user.confirmed_at,
                "created_at": user.created_at
            })
        return jsonify(user_list)
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500
