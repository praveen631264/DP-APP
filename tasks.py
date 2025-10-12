
import os
import time
import json
import redis
from celery import Celery
from google.cloud import storage
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# --- Use the new, more powerful category-based playbook runner ---
from playbooks import run_category_playbooks

# --- Celery Configuration ---
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# --- Service & Model Configuration ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
CHROMA_PERSIST_DIR = "chroma_db"
CHROMA_COLLECTION_NAME = "knowledge_base"
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')

# --- Lazy-loading for Embedding Model ---
embedding_model = None
def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model

# --- Task 1: AI Pre-Analysis ---
@celery_app.task(name='tasks.pre_analyze_document_task')
def pre_analyze_document_task(doc_id):
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    doc_key = f"doc:{doc_id}"
    try:
        gcs_path = redis_client.hget(doc_key, 'gcs_path')
        storage_client = storage.Client()
        blob = storage_client.bucket(GCS_BUCKET_NAME).blob(gcs_path)
        content = blob.download_as_string().decode('utf-8')

        suggested_category = "unclassified" # Default
        content_lower = content.lower()
        if "invoice" in content_lower: suggested_category = "vendor_invoice"
        elif "agreement" in content_lower: suggested_category = "legal_agreement"
        
        redis_client.hset(doc_key, mapping={'suggested_category': suggested_category, 'status': 'AWAITING_CATEGORIZATION'})
        return {'status': 'SUCCESS', 'suggested_category': suggested_category}
    except Exception as e:
        redis_client.hset(doc_key, mapping={'status': 'FAILED', 'error': str(e)})
        raise e

# --- Task 2: Playbook Category Execution ---
@celery_app.task(name='tasks.execute_playbook_task')
def execute_playbook_task(doc_id):
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    doc_key = f"doc:{doc_id}"
    try:
        doc_data = redis_client.hgetall(doc_key)
        category_id = doc_data.get('category')
        if not category_id: raise ValueError("Document is missing a final category.")

        storage_client = storage.Client()
        blob = storage_client.bucket(GCS_BUCKET_NAME).blob(doc_data['gcs_path'])
        content = blob.download_as_string().decode('utf-8')

        redis_client.hset(doc_key, 'status', 'AUTOMATION_RUNNING')
        
        # --- Call the new, powerful category-based runner ---
        playbook_results = run_category_playbooks(category_id, content)

        redis_client.hset(doc_key, "playbook_results", json.dumps(playbook_results))

        if any(step['status'] == 'FAILURE' for step in playbook_results['audit_trail']):
             redis_client.hset(doc_key, 'status', 'AUTOMATION_FAILED')
             raise Exception("Playbook execution failed. See audit trail for details.")

        redis_client.hset(doc_key, "status", "AUTOMATION_COMPLETE")

        index_document_task.delay(doc_id)
        
        return {'status': 'SUCCESS', 'category': category_id}

    except Exception as e:
        redis_client.hset(doc_key, mapping={'status': 'FAILED', 'error': str(e)})
        raise e

# --- Task 3: RAG Indexing ---
@celery_app.task(name='tasks.index_document_task')
def index_document_task(doc_id):
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    doc_key = f"doc:{doc_id}"
    try:
        redis_client.hset(doc_key, 'status', 'INDEXING')
        doc_data = redis_client.hgetall(doc_key)
        
        storage_client = storage.Client()
        blob = storage_client.bucket(GCS_BUCKET_NAME).blob(doc_data['gcs_path'])
        content = blob.download_as_string().decode('utf-8')
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(content)
        if not chunks: return {'status': 'SUCCESS', 'chunks_indexed': 0}

        model = get_embedding_model()
        embeddings = model.encode(chunks).tolist()
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{'document_id': doc_id, 'category': doc_data.get('category')} for i in range(len(chunks))]

        chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        collection.add(embeddings=embeddings, documents=chunks, metadatas=metadatas, ids=chunk_ids)
        
        redis_client.hset(doc_key, mapping={
            "status": "PROCESSED", "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        return {'status': 'SUCCESS', 'chunks_indexed': len(chunks)}

    except Exception as e:
        redis_client.hset(doc_key, mapping={'status': 'FAILED', 'error': str(e)})
        raise e
