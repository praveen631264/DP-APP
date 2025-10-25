
import logging
from app.utils.api_call_step import ApiCallStep
from app.utils.conditional_step import ConditionalStep
from app.utils.fail_step import FailStep
from app.utils.for_each_step import ForEachStep
from app.utils.json_parse_step import JsonParseStep
from app.utils.llm_prompt_step import LLMPromptStep
from app.utils.notification_step import NotificationStep
from app.utils.parallel_step import ParallelStep
from app.utils.search_step import SearchStep
from app.utils.switch_step import SwitchStep
from app.utils.update_document_step import UpdateDocumentStep

logger = logging.getLogger(__name__)

# The static, secure registry of all available playbook steps.
# The key is the 'type' used in the playbook JSON, and the value is an instance of the step's class.
STEP_REGISTRY = {
    'api_call': ApiCallStep(),
    'conditional': ConditionalStep(),
    'fail': FailStep(),
    'for_each': ForEachStep(),
    'json_parse': JsonParseStep(),
    'llm_prompt': LLMPromptStep(),
    'notification': NotificationStep(),
    'parallel': ParallelStep(),
    'search': SearchStep(),
    'switch': SwitchStep(),
    'update_document': UpdateDocumentStep(),
}

# Metadata for the frontend playbook editor.
# This provides the necessary information for the UI to dynamically render a form for each step.
STEP_METADATA = {
    "api_call": {
        "name": "API Call",
        "description": "Make a generic call to an external API and map the response back to the context.",
        "params": [
            {"name": "url", "type": "string", "required": True, "description": "The URL of the API endpoint. Can use template variables."},
            {"name": "method", "type": "string", "required": False, "default": "POST", "description": "HTTP method (e.g., GET, POST, PUT)."},
            {"name": "headers_template", "type": "dict", "required": False, "description": "A dictionary of headers. Can use template variables."},
            {"name": "body_template", "type": "dict", "required": False, "description": "The request body/payload. Can use template variables."},
            {"name": "auth", "type": "dict", "required": False, "description": "Authentication configuration (e.g., for bearer token or basic auth)."},
            {"name": "secrets", "type": "list", "required": False, "description": "A list of secret names to fetch from the secure store."},
            {"name": "response_mapping", "type": "dict", "required": True, "description": "JMESPath expressions to map the API response to the context."},
        ]
    },
    "conditional": {
        "name": "Conditional",
        "description": "Execute a block of sub-steps only if a condition is met.",
        "params": [
            {"name": "condition", "type": "string", "required": True, "description": "The condition to evaluate. Can use template variables."},
            {"name": "then", "type": "list", "required": True, "description": "A list of steps to execute if the condition is true."}
        ]
    },
    "fail": {
        "name": "Fail",
        "description": "Intentionally stop the playbook and mark it as failed.",
        "params": [
            {"name": "message", "type": "string", "required": True, "description": "The failure message. Can use template variables."}
        ]
    },
    "for_each": {
        "name": "For Each",
        "description": "Loop over a list and execute sub-steps for each item.",
        "params": [
            {"name": "input_list", "type": "string", "required": True, "description": "The path to the list in the context (e.g., 'outputs.my_list')."},
            {"name": "loop_variable", "type": "string", "required": False, "default": "item", "description": "The name of the variable for the current item in the loop."},
            {"name": "steps", "type": "list", "required": True, "description": "The steps to execute for each item."}
        ]
    },
    "json_parse": {
        "name": "JSON Parse",
        "description": "Parse a JSON string from the context into an object.",
        "params": [
            {"name": "input_path", "type": "string", "required": True, "description": "The path to the JSON string in the context."},
            {"name": "output_key", "type": "string", "required": True, "description": "The key where the parsed object will be stored in the outputs."}
        ]
    },
    "llm_prompt": {
        "name": "LLM Prompt",
        "description": "Execute a prompt against the configured Large Language Model.",
        "params": [
            {"name": "prompt", "type": "string", "required": True, "description": "The prompt template. Can use variables from the context."},
            {"name": "output_key", "type": "string", "required": True, "description": "The key where the LLM's response will be stored in the outputs."}
        ]
    },
    "notification": {
        "name": "Send Notification",
        "description": "Send a notification to an external system via a webhook.",
        "params": [
            {"name": "url", "type": "string", "required": True, "description": "The webhook URL."},
            {"name": "message", "type": "string", "required": True, "description": "The notification message. Can use template variables."}
        ]
    },
    "parallel": {
        "name": "Parallel",
        "description": "Execute a list of sub-steps in parallel.",
        "params": [
            {"name": "steps", "type": "list", "required": True, "description": "A list of steps to execute in parallel."}
        ]
    },
    "search": {
        "name": "Vector Search",
        "description": "Perform a vector search against the document's content.",
        "params": [
            {"name": "query", "type": "string", "required": True, "description": "The search query. Can use template variables."},
            {"name": "output_key", "type": "string", "required": True, "description": "The key where the search results will be stored in the outputs."}
        ]
    },
    "switch": {
        "name": "Switch",
        "description": "Execute a specific block of steps based on the value of a variable.",
        "params": [
            {"name": "on", "type": "string", "required": True, "description": "The path to the variable in the context to switch on."},
            {"name": "cases", "type": "dict", "required": True, "description": "A dictionary where keys are possible values and values are lists of steps."},
            {"name": "default", "type": "list", "required": False, "description": "A list of steps to execute if no case matches."}
        ]
    },
    "update_document": {
        "name": "Update Document",
        "description": "Update the metadata of the current document.",
        "params": [
            {"name": "updates", "type": "dict", "required": True, "description": "A dictionary of fields and values to update on the document."}
        ]
    },
    "tool_using_llm": {
        "name": "Tool-Using LLM",
        "description": "Use an LLM agent with tools to perform a task.",
        "params": [
            {"name": "prompt", "type": "string", "required": True, "description": "The prompt for the agent. Can use template variables."},
            {"name": "tools", "type": "list", "required": True, "description": "A list of tool names (e.g., [\"calculator\", \"get_current_date\"]) for the agent to use."},
            {"name": "output_key", "type": "string", "required": True, "description": "The key where the agent's response will be stored in the outputs."}
        ]
    }
}

def get_step_plugins():
    """Returns the registry of step plugins."""
    return STEP_REGISTRY

def get_step_metadata():
    """Returns the metadata for all step plugins."""
    return STEP_METADATA

logger.info(f"Successfully registered {len(STEP_REGISTRY)} playbook steps.")
