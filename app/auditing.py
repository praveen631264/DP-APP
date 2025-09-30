import datetime
from flask import current_app
from bson.objectid import ObjectId

def add_audit_log(document_id, action, user_id=None, details=None):
    """
    Adds an audit log entry for a specific document.

    :param document_id: The ID of the document being changed.
    :param action: The action being performed (e.g., 'delete', 'restore', 'update').
    :param user_id: The ID of the user performing the action (optional).
    :param details: A dictionary with any additional details about the change (optional).
    """
    db = current_app.db
    log_entry = {
        'document_id': ObjectId(document_id),
        'action': action,
        'timestamp': datetime.datetime.utcnow(),
        'user_id': user_id, 
        'details': details
    }
    db.audit_log.insert_one(log_entry)
