import logging
from app.celery_worker import celery
from app.models import Document, DocumentChunk
from app.ai_models import get_embeddings

logger = logging.getLogger(__name__)

@celery.task(name='batch_process_chunks_task', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def batch_process_chunks_task(doc_id: str):
    """
    Asynchronous task to process ALL chunks for a document in a single batch using MongoEngine.
    """
    if not doc_id:
        logger.warning("batch_process_chunks_task called without doc_id.")
        return

    logger.info(f"[BATCH_CHUNK_START] Processing all chunks for document ID: {doc_id}")

    try:
        doc = Document.objects(id=doc_id).first()
        if not doc:
            logger.error(f"Cannot process chunks: Document {doc_id} not found.")
            return

        if doc.status == 'Force Stopped':
            logger.warning(f"Force stop signal received for document {doc_id}. Aborting batch chunk processing.")
            return

        # Find all pending chunks for this document
        pending_chunks = DocumentChunk.objects(doc_id=doc.id, status='PENDING')
        
        if not pending_chunks:
            logger.info(f"No pending chunks to process for document {doc_id}. Task may be complete.")
            # Even if no chunks, we should probably update the doc status to something meaningful
            doc.status = 'Chunks Processed'
            doc.status_message = 'No pending chunks found to process.'
            doc.save()
            return {"status": "success", "doc_id": doc_id, "processed_chunks": 0}

        logger.info(f"Found {len(pending_chunks)} chunks to embed for document {doc_id}.")
        
        embeddings_model = get_embeddings()
        
        # Get all text from chunks to embed them in a single batch call
        texts_to_embed = [chunk.text for chunk in pending_chunks]
        embeddings = embeddings_model.embed_documents(texts_to_embed)

        # Update each chunk with its new embedding and status
        updated_count = 0
        for i, chunk in enumerate(pending_chunks):
            chunk.embedding = embeddings[i]
            chunk.status = 'COMPLETED'
            chunk.save()
            updated_count += 1
        
        logger.info(f"Successfully updated and embedded {updated_count} chunks in the database.")

        # On success, update the parent document's status
        doc.status = 'Chunks Processed'
        doc.status_message = 'Embeddings generated successfully.'
        doc.save()
        
        logger.info(f"[BATCH_CHUNK_SUCCESS] Successfully processed {len(pending_chunks)} chunks for document ID: {doc_id}")
        return {"status": "success", "doc_id": doc_id, "processed_chunks": len(pending_chunks)}
    except Exception as e:
        logger.error(f"[BATCH_CHUNK_FAILURE] Error during batch processing for doc {doc_id}: {e}", exc_info=True)
        # Attempt to update the document to reflect the error
        doc = Document.objects(id=doc_id).first()
        if doc:
            doc.status = 'Error'
            doc.status_message = 'Failed to generate embeddings.'
            doc.save()
        raise