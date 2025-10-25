import logging
import time
import uuid
from app.celery_worker import celery
from flask import current_app
from app.database import Database
from app.model_promotion_worker import model_promotion_task

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='fine_tune_model_task')
def fine_tune_model_task(self, category_name: str, job_id: str = None):
    """
    A cooperative, polite training task that fine-tunes a model for a specific category.
    It periodically checks for a stop signal to allow graceful termination.
    """
    db: Database = self.db
    job_id = job_id or str(uuid.uuid4())
    
    db.register_job(job_id, 'model_fine_tuning', {'category': category_name})

    try:
        logger.info(f"Starting fine-tuning for category: '{category_name}'. Job ID: {job_id}")

        # 1. Fetch training data for the category
        # In a real implementation, you'd have a method to get all fine-tuning data for a category.
        # We'll simulate this by fetching recent examples.
        training_data = db.get_fine_tuning_data_for_category(category_name, limit=1000)
        if not training_data or len(training_data) < 50: # Example threshold
            logger.info(f"Not enough training data for '{category_name}'. Skipping.")
            db.update_job_status(job_id, 'SKIPPED', {"message": "Not enough data."})
            return {"status": "skipped", "message": "Not enough data."}

        # 2. Simulate the training loop (the "race")
        total_steps = 100
        for step in range(total_steps):
            # --- Cooperative Check ---
            job_doc = db.jobs.find_one({'_id': job_id})
            if job_doc and job_doc.get('command') == 'STOP':
                logger.warning(f"Stop signal received for job {job_id}. Saving checkpoint and stopping.")
                # In a real implementation, you would save the model checkpoint here.
                db.update_job_status(job_id, 'STOPPED')
                return {"status": "stopped", "job_id": job_id}
            
            # Placeholder for actual training logic
            logger.info(f"[Job {job_id}] Training step {step + 1}/{total_steps} for '{category_name}'...")
            time.sleep(5) # Simulate work

        # 3. Finalize and save the model
        logger.info(f"Fine-tuning for '{category_name}' complete. Saving and deploying expert model.")
        
        # Simulate the model file content
        model_content = f"This is the fine-tuned expert model for {category_name}, version {datetime.datetime.utcnow().isoformat()}".encode('utf-8')
        
        # Create a versioned model name
        model_name = f"expert_{category_name.lower().replace(' ', '_')}_v{int(time.time())}"

        model_metadata = {
            "model_name": model_name,
            "category": category_name,
            "status": "staging", # New models must be validated before production
            "description": f"Fine-tuned expert model for the '{category_name}' category.",
            "training_data_count": len(training_data)
        }
        db.save_model(model_content, model_metadata)
        logger.info(f"Saved new expert model '{model_name}' to the registry.")

        # Trigger the evaluation and promotion task
        logger.info(f"Dispatching model promotion task for '{model_name}'.")
        model_promotion_task.delay(new_model_name=model_name, category_name=category_name)

        db.update_job_status(job_id, 'COMPLETED', {"model_name": model_name})
        return {"status": "success", "category": category_name}

    except Exception as e:
        logger.error(f"[Job {job_id}] An error occurred during fine-tuning: {e}", exc_info=True)
        db.update_job_status(job_id, 'FAILED', {"error": str(e)})
        raise
