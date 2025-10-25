import logging
from .base_step import PlaybookStep
from .playbook_utils import evaluate_condition, render_template

logger = logging.getLogger(__name__)

class ConditionalStep(PlaybookStep):
    """
    A playbook step that executes a block of sub-steps only if a condition is met.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        condition = step_config.get('condition')
        then_steps = step_config.get('then', [])

        if not condition or not then_steps:
            logger.error("ConditionalStep is missing 'condition' or 'then' block in its configuration.")
            return

        try:
            # First, render any template variables within the condition string itself
            rendered_condition = render_template(condition, context)
            
            if evaluate_condition(rendered_condition, context):
                logger.info(f"Condition '{rendered_condition}' evaluated to True. Executing 'then' block.")
                playbook_executor.execute_steps(then_steps, context)
            else:
                logger.info(f"Condition '{rendered_condition}' evaluated to False. Skipping 'then' block.")
        except Exception as e:
            logger.error(f"Failed to evaluate condition '{condition}': {e}", exc_info=True)