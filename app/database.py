import re
import gridfs
import datetime
import logging
from bson import ObjectId
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from abc import ABC, abstractmethod
from .auditing import add_audit_log

# Global variable to hold the database instance
db_client = None
logger = logging.getLogger(__name__)


def _format_document(doc):
    """Helper to format document fields for JSON serialization."""
    if not doc:
        return None
    doc['_id'] = str(doc['_id'])
    if 'created_at' in doc and isinstance(doc['created_at'], datetime.datetime):
        doc['created_at'] = doc['created_at'].isoformat()
    if 'processed_at' in doc and isinstance(doc['processed_at'], datetime.datetime):
        doc['processed_at'] = doc['processed_at'].isoformat()
    return doc

class Database(ABC):
    """
    Abstract base class (Interface) for all database operations.
    """

    @abstractmethod
    def save_file(self, file_storage):
        pass

    @abstractmethod
    def get_file_content(self, file_id):
        pass

    @abstractmethod
    def get_file_with_metadata(self, file_id):
        pass

    @abstractmethod
    def create_document(self, doc_data):
        pass

    @abstractmethod
    def get_document(self, doc_id):
        pass

    @abstractmethod
    def get_documents(self, category=None):
        pass

    @abstractmethod
    def search_documents(self, query):
        pass

    @abstractmethod
    def update_document_status(self, doc_id, status, kvps, category, text, embedding):
        pass

    @abstractmethod
    def update_document_kvp(self, doc_id, new_kvps):
        pass

    @abstractmethod
    def recategorize_document(self, doc_id, new_category, explanation):
        pass

    @abstractmethod
    def save_fine_tuning_data(self, data):
        pass

    @abstractmethod
    def update_document_for_reprocessing(self, doc_id):
        pass

    @abstractmethod
    def get_dashboard_statistics(self):
        pass

    @abstractmethod
    def soft_delete_document(self, doc_id):
        pass

    @abstractmethod
    def restore_document(self, doc_id):
        pass

class MongoDatabase(Database):
    """
    MongoDB implementation of the Database interface.
    """
    def __init__(self, mongo_uri, vector_dimensions):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_default_database()
        self.fs = gridfs.GridFS(self.db)
        self.documents = self.db.documents
        self.fine_tuning_data = self.db.fine_tuning_data
        self.audit_log = self.db.audit_log
        self.vector_dimensions = vector_dimensions

    def save_file(self, file_storage):
        filename = secure_filename(file_storage.filename)
        file_id = self.fs.put(file_storage.read(), filename=filename, content_type=file_storage.content_type)
        return str(file_id)

    def get_file_content(self, file_id):
        try:
            grid_out = self.fs.get(ObjectId(file_id))
            return grid_out.read()
        except gridfs.errors.NoFile:
            return None
            
    def get_file_with_metadata(self, file_id):
        """Retrieves a file and its metadata from GridFS."""
        try:
            grid_out = self.fs.get(ObjectId(file_id))
            return {
                "content": grid_out.read(),
                "filename": grid_out.filename,
                "content_type": grid_out.content_type
            }
        except gridfs.errors.NoFile:
            return None

    def create_document(self, doc_data):
        result = self.documents.insert_one(doc_data)
        return str(result.inserted_id)

    def get_document(self, doc_id):
        doc = self.documents.find_one({'_id': ObjectId(doc_id), 'deleted_at': {'$exists': False}})
        return _format_document(doc)

    def get_documents(self, category=None):
        query = {'deleted_at': {'$exists': False}}
        if category:
            query['category'] = category
        
        docs = self.documents.find(query)
        return [_format_document(doc) for doc in docs]

    def search_documents(self, query):
        regex = re.compile(f'.*{re.escape(query)}.*', re.IGNORECASE)
        search_query = {
            'filename': regex,
            'deleted_at': {'$exists': False}
        }
        
        docs = self.documents.find(search_query)
        return [_format_document(doc) for doc in docs]

    def update_document_status(self, doc_id, status, kvps, category, text, embedding):
        update_data = {
            'status': status,
            'kvps': kvps,
            'category': category,
            'text': text,
            'embedding': embedding
        }
        if status == 'Processed':
            update_data['processed_at'] = datetime.datetime.utcnow()

        self.documents.update_one(
            {'_id': ObjectId(doc_id), 'deleted_at': {'$exists': False}},
            {'$set': update_data}
        )

    def update_document_kvp(self, doc_id, new_kvps):
        self.documents.update_one(
            {'_id': ObjectId(doc_id), 'deleted_at': {'$exists': False}},
            {'$set': {
                'kvps': new_kvps,
                'status': 'Validated'
            }}
        )

    def recategorize_document(self, doc_id, new_category, explanation):
        self.documents.update_one(
            {'_id': ObjectId(doc_id), 'deleted_at': {'$exists': False}},
            {'$set': {
                'category': new_category,
                'categorization_explanation': explanation,
                'status': 'Re-categorized'
            }}
        )

    def update_document_for_reprocessing(self, doc_id):
        self.documents.update_one(
            {'_id': ObjectId(doc_id), 'deleted_at': {'$exists': False}},
            {'$set': {'status': 'Queued for Processing'}}
        )

    def soft_delete_document(self, doc_id):
        result = self.documents.update_one(
            {'_id': ObjectId(doc_id), 'deleted_at': {'$exists': False}},
            {'$set': {'deleted_at': datetime.datetime.utcnow()}}
        )
        if result.modified_count > 0:
            add_audit_log(doc_id, 'soft_delete')
        return result.modified_count > 0

    def restore_document(self, doc_id):
        result = self.documents.update_one(
            {'_id': ObjectId(doc_id), 'deleted_at': {'$exists': True}},
            {'$unset': {'deleted_at': ''}}
        )
        if result.modified_count > 0:
            add_audit_log(doc_id, 'restore')
        return result.modified_count > 0

    def save_fine_tuning_data(self, data):
        self.fine_tuning_data.insert_one(data)

    def get_dashboard_statistics(self):
        pipeline = [
            {
                '$match': {
                    'deleted_at': {'$exists': False}
                }
            },
            {
                '$facet': {
                    'overall_stats': [
                        {
                            '$group': {
                                '_id': None,
                                'total_documents': {'$sum': 1},
                                'processed_count': {
                                    '$sum': {
                                        '$cond': [{'$in': ['$status', ['Processed', 'Validated', 'Re-categorized']]}, 1, 0]
                                    }
                                },
                                'auto_classified_count': {
                                    '$sum': {
                                        '$cond': [{'$eq': ['$status', 'Processed']}, 1, 0]
                                    }
                                },
                                'avg_processing_time_ms': {
                                    '$avg': {
                                        '$subtract': ['$processed_at', '$created_at']
                                    }
                                }
                            }
                        }
                    ],
                    'document_pools': [
                        {
                            '$match': {'category': {'$ne': None}}
                        },
                        {
                            '$group': {
                                '_id': '$category',
                                'document_count': {'$sum': 1},
                                'accuracy_numerator': {
                                    '$sum': {
                                        '$cond': [{'$in': ['$status', ['Processed', 'Validated']]}, 1, 0]
                                    }
                                },
                                'processing_count': {
                                    '$sum': {
                                        '$cond': [{'$in': ['$status', ['Queued for Processing', 'Processing']]}, 1, 0]
                                    }
                                }
                            }
                        },
                        {
                            '$project': {
                                'pool_name': '$_id',
                                'document_count': 1,
                                'status': {
                                    '$cond': [{'$gt': ['$processing_count', 0]}, 'processing', 'active']
                                },
                                'accuracy': {
                                    '$cond': [
                                        {'$eq': ['$document_count', 0]},
                                        0,
                                        {'$multiply': [{'$divide': ['$accuracy_numerator', '$document_count']}, 100]}
                                    ]
                                },
                                '_id': 0
                            }
                        }
                    ],
                    'unknown_pool': [
                        {
                            '$match': {'category': None}
                        },
                        {
                            '$count': 'document_count'
                        }
                    ]
                }
            }
        ]

        result = list(self.documents.aggregate(pipeline))
        
        if not result:
            return {}
        
        stats = result[0]
        overall = stats['overall_stats'][0] if stats['overall_stats'] else {}
        total_docs = overall.get('total_documents', 0)
        processed_count = overall.get('processed_count', 0)

        processing_accuracy = (processed_count / total_docs * 100) if total_docs > 0 else 0
        auto_classified_accuracy = (overall.get('auto_classified_count', 0) / processed_count * 100) if processed_count > 0 else 0
        avg_time_ms = overall.get('avg_processing_time_ms')
        avg_processing_time = (avg_time_ms / 1000) if avg_time_ms is not None else None

        dashboard_data = {
            'total_documents': total_docs,
            'processing_accuracy': round(processing_accuracy, 2),
            'avg_processing_time': round(avg_processing_time, 2) if avg_processing_time is not None else None,
            'auto_classified_accuracy': round(auto_classified_accuracy, 2),
            'document_pools': stats.get('document_pools', [])
        }

        if stats.get('unknown_pool'):
            dashboard_data['document_pools'].append({
                'pool_name': 'Unknown Pool',
                'document_count': stats['unknown_pool'][0]['document_count'],
                'status': 'pending',
                'accuracy': 0
            })

        return dashboard_data

    def create_vector_search_index(self):
        index_name = "vector_index"
        if index_name in self.documents.list_search_indexes():
            logger.info(f"Vector search index '{index_name}' already exists.")
            return

        logger.info(f"Creating vector search index '{index_name}'. This may take a minute...")
        index_definition = {
            "name": index_name,
            "definition": {
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        "embedding": {
                            "type": "vector",
                            "dimensions": self.vector_dimensions,
                            "similarity": "cosine"
                        }
                    }
                }
            }
        }
        self.documents.create_search_index(index_definition)
        logger.info("Vector search index created successfully.")

def init_db(app):
    global db_client
    if db_client is None:
        mongo_uri = app.config['MONGO_URI']
        vector_dimensions = app.config.get('VECTOR_DIMENSIONS', 384)
        db_client = MongoDatabase(mongo_uri, vector_dimensions)
    
    app.db = db_client
    app.db.create_vector_search_index()
