import logging
from .base_step import PlaybookStep
from .playbook_utils import _get_value_from_context

logger = logging.getLogger(__name__)

class SwitchStep(PlaybookStep):
    """
    An intelligent control flow step that directs execution based on the
    value of a variable in the context. It functions like a switch-case statement.

    This provides a cleaner alternative to multiple nested ConditionalSteps.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        input_variable_path = step_config.get('on')
        cases = step_config.get('cases', {})
        default_steps = step_config.get('default', [])
        step_name = step_config.get('name', 'Switch Step')

        if not input_variable_path or not cases:
            msg = "SwitchStep is missing 'on' or 'cases' configuration."
            logger.error(msg)
            raise ValueError(msg)

        # Retrieve the value to switch on from the context
        switch_value = _get_value_from_context(input_variable_path, context)

        logger.info(f"Executing SwitchStep '{step_name}': evaluating variable at '{input_variable_path}' with value '{switch_value}'.")

        # Find the matching case and get the corresponding steps
        # We must convert the switch_value to a string to match the JSON keys from the playbook
        steps_to_execute = cases.get(str(switch_value))

        if steps_to_execute:
            logger.info(f"Found matching case for value '{switch_value}'. Executing case block.")
            playbook_executor.execute_steps(steps_to_execute, context)
        elif default_steps:
            logger.info(f"No case matched value '{switch_value}'. Executing default block.")
            playbook_executor.execute_steps(default_steps, context)
        else:
            logger.info(f"No case matched value '{switch_value}' and no default block was provided. Skipping.")