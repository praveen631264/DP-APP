
import logging
from mongoengine import connect
from app.models import Document, AuditLog, Playbook
from bson import ObjectId

logger = logging.getLogger(__name__)

def init_db(app):
    """
    Initializes the MongoEngine connection and returns the client object.
    """
    mongo_uri = app.config['MONGO_URI']
    try:
        client = connect(host=mongo_uri)
        db_name = client.get_default_database().name
        logger.info(f"Successfully connected to MongoDB via MongoEngine. Database: {db_name}")
        return client # <-- CRITICAL FIX ADDED HERE
    except Exception as e:
        logger.critical(f"Could not connect to MongoDB via MongoEngine. Error: {e}", exc_info=True)
        raise

# --- Playbook CRUD Operations ---
def create_playbook(data):
    """Creates a new playbook in the database."""
    playbook = Playbook(**data)
    playbook.save()
    return str(playbook.id)

def get_playbooks(category_name=None):
    """Retrieves all playbooks, optionally filtered by category name."""
    if category_name:
        return Playbook.objects(category_name=category_name).to_json()
    return Playbook.objects().to_json()

def get_playbook(playbook_id):
    """Retrieves a single playbook by its ID."""
    return Playbook.objects(id=ObjectId(playbook_id)).first().to_json()

def update_playbook(playbook_id, data):
    """Updates an existing playbook."""
    playbook = Playbook.objects(id=ObjectId(playbook_id)).first()
    if playbook:
        playbook.update(**data)
        return True
    return False

def delete_playbook(playbook_id):
    """Deletes a playbook from the database."""
    playbook = Playbook.objects(id=ObjectId(playbook_id)).first()
    if playbook:
        playbook.delete()
        return True
    return False

def get_document_audit_trail(doc_id: str):
    """
    Retrieves the audit trail for a specific document.
    :param doc_id: The ID of the document.
    :return: The list of audit log entries.
    """
    document = Document.objects(id=doc_id).first()
    return document.audit_trail if document else []

def get_paginated_documents(page: int = 1, limit: int = 10, sort_by: str = 'created_at', sort_order: str = 'desc', filters: dict = None):
    """
    Retrieves a paginated, sorted, and filtered list of documents using MongoEngine.
    """
    query_filters = {}
    if filters:
        for key, value in filters.items():
            if value:
                query_filters[f"{key}__icontains"] = value

    if 'is_deleted' not in query_filters:
        query_filters['is_deleted'] = False

    sort_key = f"{'-' if sort_order == 'desc' else ''}{sort_by}"
    skip = (page - 1) * limit

    documents_query = Document.objects(**query_filters)
    total_count = documents_query.count()
    documents = documents_query.order_by(sort_key).skip(skip).limit(limit).all()

    return list(documents), total_count

def stop_document_processing(doc_id: str) -> bool:
    """
    Sets a document's status to 'Force Stopped' via MongoEngine.
    """
    document = Document.objects(id=doc_id).first()
    if not document:
        return False
        
    document.status = 'Force Stopped'
    document.status_message = 'Processing stopped by user.'
    document.audit_trail.append(AuditLog(event_name="Force Stopped", details={"source": "user_action"}))
    document.save()
    return True

def soft_delete_document(doc_id: str) -> bool:
    """
    Soft-deletes a document by setting its 'is_deleted' flag to True via MongoEngine.
    """
    document = Document.objects(id=doc_id).first()
    if not document:
        return False
        
    document.is_deleted = True
    document.status = 'Archived'
    document.status_message = 'Document has been archived by user.'
    document.audit_trail.append(AuditLog(event_name="Archived", details={"source": "user_action", "is_deleted": True}))
    document.save()
    return True
