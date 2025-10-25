import logging
from .base_step import PlaybookStep
from .playbook_utils import render_template
from bson import ObjectId

logger = logging.getLogger(__name__)

class PlaybookTerminalException(Exception):
    """Custom exception to signal an intentional and immediate stop of the playbook."""
    pass

class FailStep(PlaybookStep):
    """
    An explicit control flow step that intentionally fails the playbook
    and halts all further execution.

    This is a crucial step for robust error handling, allowing a playbook to
    terminate gracefully with a clear, business-relevant message when its
    own logic determines it cannot proceed.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        message_template = step_config.get('message', 'Playbook was intentionally failed.')

        # Render the failure message with data from the context
        failure_message = render_template(message_template, context)

        logger.error(f"Executing FailStep: {failure_message}")

        # Update the document's status to reflect the failure
        db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Playbook Failed', 'status_message': failure_message}})

        # Raise a special exception to signal the executor to stop immediately
        raise PlaybookTerminalException(failure_message)