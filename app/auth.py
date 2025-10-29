import logging
from flask import Blueprint, jsonify
from flask_security import current_user

auth_bp = Blueprint('auth_bp', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/status', methods=['GET'])
def status():
    """
    Checks the authentication status of the current user.
    Provides a way for the frontend to perform a "preauth check".
    """
    # Use the is_authenticated property provided by Flask-Security-Too
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        return jsonify({
            "is_authenticated": True,
            "user": {
                "email": current_user.email,
                "roles": [role.name for role in current_user.roles]
            }
        }), 200
    else:
        # Return 401 Unauthorized which is more semantically correct for an unauthenticated status check
        return jsonify({"is_authenticated": False}), 401
