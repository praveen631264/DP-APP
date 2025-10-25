from abc import ABC, abstractmethod

class PlaybookStep(ABC):
    """
    Abstract Base Class (Interface) for all playbook steps.

    This class defines the contract that all playbook step plugins must adhere to.
    Each step must implement the `execute` method.
    """

    @abstractmethod
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        """
        Executes the logic for this playbook step.
        
        :param step_config: The configuration dictionary for this specific step from the playbook.
        :param context: The shared context dictionary for the playbook execution, used to pass data between steps.
        :param db: The database client instance.
        :param doc_id: The ID of the document being processed.
        :param playbook_executor: The instance of the PlaybookExecutor running the playbook, allowing steps to call back into the executor (e.g., for conditional sub-steps).
        """
        pass