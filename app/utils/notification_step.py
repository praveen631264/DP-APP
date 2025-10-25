import logging
import requests
from .base_step import PlaybookStep
from .playbook_utils import render_template

logger = logging.getLogger(__name__)

class NotificationStep(PlaybookStep):
    """
    A playbook step that sends a notification to an external system via a webhook.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        webhook_url = step_config.get('url')
        message_template = step_config.get('message', "Document {document.filename} has been processed.")

        if not webhook_url:
            logger.error("NotificationStep is missing the 'url' for the webhook.")
            return

        try:
            formatted_message = render_template(message_template, context)
            payload = {"text": formatted_message}
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully sent notification for doc {doc_id} to {webhook_url}.")
        except Exception as e:
            logger.error(f"Failed to send notification for doc {doc_id}: {e}", exc_info=True)