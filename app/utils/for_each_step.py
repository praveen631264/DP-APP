import logging
from .base_step import PlaybookStep
from .playbook_utils import _get_value_from_context
import copy

logger = logging.getLogger(__name__)

class ForEachStep(PlaybookStep):
    """
    A powerful control flow step that iterates over a list in the playbook
    context and executes a block of sub-steps for each item.

    This enables complex data processing workflows, such as running an analysis
    on each line item returned from an API call.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        input_list_path = step_config.get('input_list')
        loop_variable_name = step_config.get('loop_variable', 'item') # Default to 'item'
        index_variable_name = step_config.get('index_variable', 'index') # Default to 'index'
        steps_to_execute = step_config.get('steps', [])
        step_name = step_config.get('name', 'ForEach Step')

        if not all([input_list_path, steps_to_execute]):
            msg = "ForEachStep is missing 'input_list', 'loop_variable', or 'steps' configuration."
            logger.error(msg)
            raise ValueError(msg)

        # Retrieve the list to iterate over from the context
        target_list = _get_value_from_context(input_list_path, context)

        if not isinstance(target_list, list):
            logger.warning(f"The path '{input_list_path}' in ForEachStep did not resolve to a list. Skipping.")
            return

        logger.info(f"Executing ForEachStep '{step_name}': iterating over {len(target_list)} items from '{input_list_path}'.")

        # Iterate over each item in the target list
        for index, item in enumerate(target_list):
            logger.info(f"Loop {index + 1}/{len(target_list)}: processing item.")
            
            # Create a deep copy of the context for this iteration to prevent side effects
            loop_context = copy.deepcopy(context)
            
            # Inject the current item and its index into the loop's context
            loop_context[loop_variable_name] = item
            loop_context[index_variable_name] = index
            
            # Execute the sub-steps with the new, scoped context
            playbook_executor.execute_steps(steps_to_execute, loop_context)

            # After the sub-steps run, merge the outputs from the loop context back into the main context
            # This allows the main flow to access results from all iterations.
            if 'outputs' in loop_context:
                context['outputs'].update(loop_context['outputs'])