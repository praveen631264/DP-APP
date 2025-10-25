import logging
import datetime
from flask import current_app, request
from flask_security import current_user

logger = logging.getLogger(__name__)

def log_audit_event(action: str, details: dict = None):
    """
    Logs an audit event to the database.

    :param action: A string describing the action (e.g., 'USER_LOGIN').
    :param details: A dictionary with additional context about the event.
    """
    try:
        db = current_app.db
        log_entry = {
            "timestamp": datetime.datetime.utcnow(),
            "user_email": current_user.email if current_user and not current_user.is_anonymous else "System",
            "user_id": str(current_user.id) if current_user and not current_user.is_anonymous else None,
            "action": action,
            "details": details or {},
            "ip_address": request.remote_addr
        }
        db.audit_log.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Failed to log audit event '{action}': {e}", exc_info=True)