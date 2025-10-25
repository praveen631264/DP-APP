import logging
from .base_step import PlaybookStep
from app.playbook_subtask_worker import execute_playbook_subtask
from celery import group

logger = logging.getLogger(__name__)

class ParallelStep(PlaybookStep):
    """
    A powerful playbook step that executes a list of sub-steps in parallel
    across the entire Celery worker cluster. It collects the results from
    all parallel branches and merges them back into the main context.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        parallel_steps = step_config.get('steps', [])
        step_name = step_config.get('name', 'Parallel Step')

        if not parallel_steps:
            logger.warning("ParallelStep has no sub-steps to execute.")
            return

        logger.info(f"Dispatching {len(parallel_steps)} sub-steps in parallel for step '{step_name}'.")

        # Create a Celery 'group' of sub-tasks. Each sub-task will execute one of the
        # steps defined in the 'steps' array of this ParallelStep.
        # We pass a copy of the current context to each sub-task.
        # The sub-task will return the 'outputs' it generated.
        sub_tasks = group(
            execute_playbook_subtask.s(step, context.copy(), doc_id) for step in parallel_steps
        )

        try:
            # Execute the group and wait for all tasks to complete.
            result_group = sub_tasks.apply_async()
            
            # This is a blocking call that waits for all tasks in the group to finish.
            # A timeout is added to prevent indefinite hanging.
            results = result_group.get(timeout=300) # 5-minute timeout

            logger.info(f"All parallel sub-steps for '{step_name}' have completed.")

            # --- Intelligent Result Merging ---
            # Iterate through the results from each sub-task and merge their 'outputs'
            # back into the main playbook context.
            for sub_task_outputs in results:
                if isinstance(sub_task_outputs, dict):
                    context['outputs'].update(sub_task_outputs)
            
            logger.info("Successfully merged outputs from all parallel branches into the main context.")

        except Exception as e:
            logger.error(f"ParallelStep '{step_name}' failed. One or more sub-tasks may have failed. Error: {e}", exc_info=True)
            # Re-raise the exception to be handled by the main PlaybookExecutor's
            # failure policy (abort, retry, skip).
            raise