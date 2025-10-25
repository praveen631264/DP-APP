from functools import wraps
from flask import request, jsonify, current_app
import logging
from flask_security import auth_required, current_user

logger = logging.getLogger(__name__)

def admin_required(f):
    """
    A decorator to protect routes that require administrative privileges.
    It checks for a valid 'X-Admin-API-Key' in the request headers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_api_key = current_app.config.get('ADMIN_API_KEY')
        if not admin_api_key:
            # If no key is configured, deny access to be safe by default.
            return jsonify({"error": "Administrator access is not configured on the server."}), 500

        provided_key = request.headers.get('X-Admin-API-Key')
        if provided_key != admin_api_key:
            return jsonify({"error": "Unauthorized: A valid admin API key is required."}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def attribute_required(f):
    """
    AACL Decorator. Grants access if the user's attributes match the policy
    defined in the database for the requested resource path.
    """
    @wraps(f)
    @auth_required() # Ensures the user is logged in first
    def decorated_view(*args, **kwargs):
        # The resource is identified by the endpoint rule (e.g., '/api/v1/documents/<doc_id>/download')
        resource_path = request.url_rule.rule
        policy_doc = current_app.db.get_policy_for_resource(resource_path)

        # If no policy is defined for this resource, access is denied by default for safety.
        if not policy_doc or not policy_doc.get('policy'):
            logger.warning(f"AACL check failed for user {current_user.email} on resource '{resource_path}'. No policy defined.")
            return jsonify({"error": "Forbidden: Access policy for this resource is not configured."}), 403

        resource_attributes = policy_doc['policy']
        user_attributes = current_user.attributes

        # Policy: User must have all attributes required by the resource.
        for key, required_value in resource_attributes.items():
            user_value = user_attributes.get(key)
            if user_value != required_value:
                logger.warning(
                    f"AACL check failed for user {current_user.email} on '{resource_path}'. "
                    f"Required: {key}={required_value}, User has: {key}={user_value}"
                )
                return jsonify({"error": "Forbidden: You do not have the required attributes to access this resource."}), 403
        
        return f(*args, **kwargs)
    return decorated_view