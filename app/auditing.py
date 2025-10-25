import datetime
from flask import current_app

def add_audit_log(doc_id, action, details=None):
    """
    Adds a log entry to the document's audit trail.
    """
    db = current_app.db
    log_entry = {
        "doc_id": doc_id,
        "action": action,
        "timestamp": datetime.datetime.utcnow(),
        "details": details or {}
    }
    db.audit_log.insert_one(log_entry)