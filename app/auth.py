import logging
from flask import Blueprint, request, jsonify, current_app
from flask_security import utils, auth_required, current_user
import pyotp

auth_bp = Blueprint('auth_bp', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Logs a user in by validating their credentials and returning a JSON Web Token (JWT).
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Use Flask-Security's datastore to find the user
    user = current_app.security.datastore.find_user(email=email)

    if not user:
        logger.warning(f"Login failed for non-existent user: {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    if not utils.verify_password(password, user.password):
        logger.warning(f"Login failed for user {email}: incorrect password")
        return jsonify({"error": "Invalid credentials"}), 401

    # Check if MFA is enabled for this user
    if user.mfa_enabled and user.totp_secret:
        logger.info(f"MFA is enabled for user {email}. Awaiting TOTP code.")
        # Do not issue a token yet. Signal to the frontend that MFA is required.
        return jsonify({"mfa_required": True}), 200

    # Generate and return the authentication token
    # Flask-Security-Too handles JWT generation automatically
    token = utils.get_token_status(user)
    
    logger.info(f"User {email} logged in successfully.")
    return jsonify({"message": "Login successful", "token": token})

@auth_bp.route('/login/mfa', methods=['POST'])
def login_mfa():
    """
    Handles the second factor of authentication (TOTP code).
    """
    data = request.get_json()
    email = data.get('email')
    totp_code = data.get('totp_code')

    if not email or not totp_code:
        return jsonify({"error": "Email and TOTP code are required"}), 400

    user = current_app.security.datastore.find_user(email=email)
    if not user or not user.mfa_enabled or not user.totp_secret:
        return jsonify({"error": "Invalid user or MFA not enabled"}), 401

    # Verify the code
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(totp_code):
        return jsonify({"error": "Invalid TOTP code."}), 401

    # If the code is valid, issue the final access token
    token = utils.get_token_status(user)
    response = jsonify({"message": "Login successful"})
    response.set_cookie('auth_token', token, httponly=True, secure=True, samesite='Lax')
    logger.info(f"User {email} completed MFA login successfully.")
    return response

@auth_bp.route('/logout', methods=['POST'])
@auth_required()
def logout():
    """
    Logs the user out by clearing the authentication cookie.
    """
    response = jsonify({"message": "Logout successful"})
    response.set_cookie('auth_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
    return response