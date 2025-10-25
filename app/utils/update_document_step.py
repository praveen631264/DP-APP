import logging
from bson import ObjectId
from .base_step import PlaybookStep
from .playbook_utils import render_template

logger = logging.getLogger(__name__)

class UpdateDocumentStep(PlaybookStep):
    """
    A powerful playbook step that can update the metadata of the currently
    processing document in the database.

    This allows for dynamic changes to the document's state during playbook
    execution, such as setting a custom status or adding new metadata fields.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        updates = step_config.get('updates')

        if not isinstance(updates, dict):
            logger.error("UpdateDocumentStep requires 'updates' to be a dictionary.")
            raise ValueError("UpdateDocumentStep 'updates' must be a dictionary.")

        # Render any template variables within the update values
        rendered_updates = render_template(updates, context)

        logger.info(f"Executing UpdateDocumentStep '{step_config.get('name')}': updating document {doc_id} with {rendered_updates}")

        try:
            # Use $set to update only the specified fields
            db.documents.update_one(
                {'_id': ObjectId(doc_id)},
                {'$set': rendered_updates}
            )
            logger.info(f"Successfully updated document {doc_id}.")
        except Exception as e:
            logger.error(f"UpdateDocumentStep failed to update document {doc_id}: {e}", exc_info=True)
            raise