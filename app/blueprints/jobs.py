import logging
from flask import Blueprint, jsonify, current_app
from bson import json_util
from flask_security import roles_required

bp = Blueprint('jobs_bp', __name__)
logger = logging.getLogger(__name__)

# @roles_required('Admin')
def get_all_jobs():
    """
    Retrieves a list of all background jobs (e.g., training runs) from the registry.
    """
    db = current_app.db
    try:
        # Find all jobs and sort by creation date
        jobs = list(db.jobs.find({}).sort('created_at', -1))
        # Use json_util to handle BSON types like ObjectId and datetime
        return json_util.dumps(jobs), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

# @roles_required('Admin')
def stop_job(job_id):
    """
    Sends a 'STOP' command to a running background job.
    This is a cooperative stop; the job must check for this command.
    """
    db = current_app.db
    try:
        job = db.jobs.find_one({'_id': job_id})
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.get('status') != 'RUNNING':
            return jsonify({"error": f"Job is not running. Current status: {job.get('status')}"}), 409

        # Set the command flag in the job's document
        result = db.jobs.update_one(
            {'_id': job_id},
            {'$set': {'command': 'STOP'}}
        )

        if result.modified_count > 0:
            logger.info(f"Sent STOP command to job {job_id}")
            return jsonify({"message": f"Stop signal sent to job {job_id}. It will terminate on its next cooperative check."}), 202
        else:
            return jsonify({"error": "Failed to send stop signal"}), 500

    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500