from langchain.tools import tool
import datetime

# This file will serve as a library of tools that can be used by the ToolUsingLLMStep in playbooks.

@tool
def calculator(a: int, b: int, operation: str) -> int:
    """A simple calculator tool. Operation can be 'add' or 'subtract'."""
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    else:
        return "Invalid operation"

@tool
def get_current_date() -> str:
    """Returns the current date."""
    return datetime.date.today().isoformat()


# A registry of all available tools
TOOL_REGISTRY = {
    "calculator": calculator,
    "get_current_date": get_current_date,
}
