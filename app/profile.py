import logging
from flask import Blueprint, jsonify, request
from flask_security import auth_required, current_user, utils
import pyotp
import qrcode
import io

profile_bp = Blueprint('profile_bp', __name__)
logger = logging.getLogger(__name__)

@profile_bp.route('/profile', methods=['GET'])
@auth_required('token')
def get_profile():
    """
    Retrieves the profile and preferences for the currently authenticated user.
    """
    # The 'current_user' proxy is populated by Flask-Security-Too
    user_data = {
        "email": current_user.email,
        "roles": [role.name for role in current_user.roles],
        "preferences": current_user.preferences or {},
        "mfa_enabled": current_user.mfa_enabled
    }
    return jsonify(user_data)

@profile_bp.route('/profile/preferences', methods=['PUT'])
@auth_required('token')
def update_preferences():
    """
    Updates the preferences for the currently authenticated user.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body cannot be empty"}), 400

    try:
        # Merge new preferences with existing ones
        new_prefs = {**current_user.preferences, **data}
        current_user.preferences = new_prefs
        current_user.save()
        logger.info(f"Updated preferences for user {current_user.email}")
        return jsonify({"message": "Preferences updated successfully", "preferences": new_prefs})
    except Exception as e:
        logger.error(f"Error updating preferences for user {current_user.email}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

@profile_bp.route('/profile/change-password', methods=['POST'])
@auth_required('token')
def change_password():
    """
    Allows the currently authenticated user to change their password.
    """
    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not current_password or not new_password:
        return jsonify({"error": "Current and new passwords are required."}), 400

    # Verify the user's current password
    if not utils.verify_password(current_password, current_user.password):
        return jsonify({"error": "Invalid current password."}), 401

    # Hash and set the new password
    try:
        current_user.password = utils.hash_password(new_password)
        current_user.save()
        logger.info(f"User {current_user.email} successfully changed their password.")
        return jsonify({"message": "Password changed successfully."}), 200
    except Exception as e:
        logger.error(f"Error changing password for user {current_user.email}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

@profile_bp.route('/profile/mfa/setup', methods=['POST'])
@auth_required('token')
def mfa_setup():
    """
    Generates a new TOTP secret and a provisioning URI for QR code scanning.
    The secret is saved to the user but MFA is not yet enabled.
    """
    try:
        # Generate a new TOTP secret
        secret = pyotp.random_base32()
        current_user.totp_secret = secret
        current_user.mfa_enabled = False # Ensure MFA is disabled until verified
        current_user.save()

        # Create the provisioning URI
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=current_user.email,
            issuer_name="DocIntel Platform"
        )

        logger.info(f"Generated MFA setup secret for user {current_user.email}")
        return jsonify({"secret": secret, "provisioning_uri": provisioning_uri})

    except Exception as e:
        logger.error(f"Error during MFA setup for user {current_user.email}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

@profile_bp.route('/profile/mfa/verify', methods=['POST'])
@auth_required('token')
def mfa_verify():
    """
    Verifies a TOTP code and enables MFA for the user.
    """
    data = request.get_json()
    totp_code = data.get('totp_code')

    if not totp_code:
        return jsonify({"error": "TOTP code is required."}), 400

    if not current_user.totp_secret:
        return jsonify({"error": "MFA setup has not been initiated."}), 400

    # Verify the code
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(totp_code):
        return jsonify({"error": "Invalid TOTP code."}), 401

    # Enable MFA
    current_user.mfa_enabled = True
    current_user.save()

    logger.info(f"MFA successfully enabled for user {current_user.email}")
    return jsonify({"message": "MFA has been enabled successfully."}), 200

@profile_bp.route('/profile/mfa/disable', methods=['POST'])
@auth_required('token')
def mfa_disable():
    """
    Disables MFA for the current user after verifying a final TOTP code.
    """
    data = request.get_json()
    totp_code = data.get('totp_code')

    if not totp_code:
        return jsonify({"error": "TOTP code is required."}), 400

    if not current_user.mfa_enabled or not current_user.totp_secret:
        return jsonify({"error": "MFA is not enabled for this account."}), 400

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(totp_code):
        return jsonify({"error": "Invalid TOTP code."}), 401

    current_user.mfa_enabled = False
    current_user.totp_secret = None
    current_user.save()

    logger.info(f"MFA successfully disabled for user {current_user.email}")
    return jsonify({"message": "MFA has been disabled successfully."}), 200