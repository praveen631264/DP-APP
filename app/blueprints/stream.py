import logging
import json
from flask import Blueprint, Response, current_app
import redis

stream_bp = Blueprint('stream_bp', __name__)
logger = logging.getLogger(__name__)

def publish_status_update(doc_id: str, status: str, message: str):
    """
    Publishes a status update to a Redis channel.
    This function can be called from anywhere, including Celery tasks.
    """
    try:
        redis_url = current_app.config.get('CELERY_BROKER_URL')
        r = redis.from_url(redis_url)
        channel = f"doc-status:{doc_id}"
        payload = json.dumps({'status': status, 'message': message})
        r.publish(channel, payload)
        logger.info(f"Published status update to Redis channel '{channel}': {status}")
    except Exception as e:
        logger.error(f"Failed to publish status update for doc {doc_id} to Redis: {e}", exc_info=True)

@stream_bp.route('/documents/<doc_id>/status-stream')
def status_stream(doc_id):
    """
    This endpoint provides a stream of status updates for a specific document
    using Server-Sent Events (SSE).
    """
    redis_url = current_app.config.get('CELERY_BROKER_URL')
    r = redis.from_url(redis_url)
    pubsub = r.pubsub()
    channel = f"doc-status:{doc_id}"
    pubsub.subscribe(channel)

    def event_stream():
        try:
            logger.info(f"Client connected to SSE stream for channel: {channel}")
            for message in pubsub.listen():
                if message['type'] == 'message':
                    # SSE data format is "data: <json_string>\n\n"
                    yield f"data: {message['data'].decode('utf-8')}\n\n"
        except GeneratorExit:
            logger.info(f"Client disconnected from SSE stream for channel: {channel}")
        finally:
            pubsub.close()

    return Response(event_stream(), mimetype='text/event-stream')