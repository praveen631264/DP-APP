import logging
from app.celery_worker import celery
from app.ai_models import get_llm
from app.orchestrator_tools import get_orchestrator_tools
from app.blueprints.stream import publish_status_update
from langchain.agents import AgentExecutor, create_tool_calling_agent
from bson import ObjectId
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are the central "Brain" and Orchestrator for a document processing system.
Your job is to decide the correct sequence of actions for a document based on its current state.

You have the following tools at your disposal:
- `get_document_details`: To check the current status of a document.
- `dispatch_full_processing_pipeline`: To start the complete, end-to-end processing for a new document.
- `dispatch_playbook_execution`: To run only the playbook for a document that has already been processed.
- `human_override_and_dispatch`: A privileged tool to be used ONLY when a human operator has issued a specific command.
- `compensate_and_mark_as_failed`: As a last resort, to mark a document as terminally failed.

**Your Logic:**
1.  Always start by using `get_document_details` to understand the document's current status.
2.  If a `human_override_action` is provided in the input, you MUST use the `human_override_and_dispatch` tool with that action.
3.  If no override is present, follow these rules:
    - If status is 'Queued for Orchestration', use `dispatch_full_processing_pipeline`.
    - If status is 'Playbook Failed', use `dispatch_playbook_execution` to retry the playbook.
    - If status is 'Orchestration Failed' or 'Processing', it may have been interrupted. Use `dispatch_full_processing_pipeline` to safely restart the full process.
    - If a document fails repeatedly (e.g., it is in 'Failed' state), use `compensate_and_mark_as_failed`.
4.  Think step-by-step and justify your choice of tool.
"""),
        ("human", "An event has occurred for document with ID: {doc_id}. Human override action: {human_override_action}. Please determine the next action."),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

@celery.task(bind=True, name='orchestrator_agent_task')
def orchestrator_agent_task(self, doc_id: str, human_override_action: str = "None"):
    """
    Invokes the central "Brain" agent to decide the fate of a document.
    """
    db = self.db
    logger.info(f"Orchestrator Agent invoked for document: {doc_id}")
    publish_status_update(doc_id, "Orchestrating", "The 'central brain' is deciding the next action.")
    try:
        llm = get_llm()
        tools = get_orchestrator_tools()

        agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        result = agent_executor.invoke({"doc_id": doc_id, "human_override_action": human_override_action}, {"callbacks": []})
        logger.info(f"Orchestrator Agent finished for doc {doc_id}. Final output: {result.get('output')}")

    except Exception as e:
        logger.critical(f"A critical error occurred in the Orchestrator Agent for doc {doc_id}: {e}", exc_info=True)
        publish_status_update(doc_id, "Failed", "A critical error occurred in the orchestrator agent.")
        # If the brain itself fails, we must mark the document as failed.
        # This now correctly uses the task's database context.
        db.documents.update_one({'_id': ObjectId(doc_id)}, {'$set': {'status': 'Failed', 'status_message': 'Orchestrator agent itself failed.'}})