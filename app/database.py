import logging
from flask import current_app
import datetime
from pymongo import MongoClient
from pymongo import ASCENDING, DESCENDING
from pymongo.cursor import Cursor
from gridfs import GridFS

logger = logging.getLogger(__name__)


def init_db(app):
    mongo_uri = app.config['MONGO_URI']
    try:
        client = MongoClient(mongo_uri)
        app.db = client.get_default_database()
        app.fs = GridFS(app.db)
        logger.info(f"Successfully connected to MongoDB database: {app.db.name}")
    except Exception as e:
        logger.critical(f"Could not connect to MongoDB. Error: {e}", exc_info=True)
        raise


def get_document_audit_trail(doc_id: str) -> Cursor:
    """
    Retrieves the audit trail for a specific document.

    :param doc_id: The ID of the document.
    :return: A cursor for the audit trail events, sorted by timestamp.
    """
    db = current_app.db
    return db.documents_audit.find({'document_id': doc_id}).sort('timestamp', 1)

def get_paginated_documents(self, page: int = 1, limit: int = 10, sort_by: str = 'created_at', sort_order: str = 'desc', filters: dict = None):
    """
    Retrieves a paginated, sorted, and filtered list of documents.

    :param page: The page number to retrieve.
    :param limit: The number of documents per page.
    :param sort_by: The field to sort by.
    :param sort_order: The sort order ('asc' or 'desc').
    :param filters: A dictionary of filters to apply.
    :return: A tuple containing the list of documents and the total count of matching documents.
    """
    query = {}
    if filters:
        for key, value in filters.items():
            if value:
                # Use regex for partial, case-insensitive string matching
                query[key] = {'$regex': value, '$options': 'i'}

    # Ensure soft-deleted documents are not included unless explicitly requested
    if 'is_deleted' not in query:
        query['is_deleted'] = {'$ne': True}

    # Determine sort direction
    direction = DESCENDING if sort_order == 'desc' else ASCENDING

    # Calculate the number of documents to skip
    skip = (page - 1) * limit

    # Execute query to get the documents for the current page
    cursor = self.documents.find(query).sort(sort_by, direction).skip(skip).limit(limit)
    documents = list(cursor)

    # Get the total count of documents matching the filter
    # We use estimated_document_count for performance if no filter is applied
    if query == {'is_deleted': {'$ne': True}}:
        total_count = self.documents.estimated_document_count()
    else:
        total_count = self.documents.count_documents(query)

    return documents, total_count

def stop_document_processing(self, doc_id: str) -> bool:
    """
    Sets a document's status to 'Force Stopped' to cooperatively halt processing.

    :param doc_id: The ID of the document to stop.
    :return: True if the document was found and updated, False otherwise.
    """
    result = self.documents.update_one(
        {'_id': ObjectId(doc_id)},
        {'$set': {'status': 'Force Stopped', 'status_message': 'Processing stopped by user.'}}
    )
    if result.modified_count > 0:
        self.add_audit_log(doc_id, "Force Stopped", {"source": "user_action"})
        return True
    return False

def soft_delete_document(self, doc_id: str) -> bool:
    """
    Soft-deletes a document by setting its 'is_deleted' flag to True.

    :param doc_id: The ID of the document to soft-delete.
    :return: True if the document was found and updated, False otherwise.
    """
    result = self.documents.update_one(
        {'_id': ObjectId(doc_id)},
        {'$set': {'is_deleted': True, 'status': 'Archived', 'status_message': 'Document has been archived by user.'}}
    )
    if result.modified_count > 0:
        self.add_audit_log(doc_id, "Archived", {"source": "user_action", "is_deleted": True})
        return True
    return False
