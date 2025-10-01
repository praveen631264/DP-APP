
import json
from langchain.agents import tool

@tool
def propose_add_kvp(key: str, value: str):
    """
    Proposes to add a new key-value pair (KVP) to the document.
    This is used when the user asks to add information that is not yet present.
    Returns a JSON object describing the proposed action.
    """
    return json.dumps({
        "action": "add",
        "key": key,
        "value": value
    })

@tool
def propose_update_kvp(key: str, new_value: str):
    """
    Proposes to update an existing key-value pair (KVP) in the document.
    This is used when the user asks to correct or change a value.
    Returns a JSON object describing the proposed action.
    """
    return json.dumps({
        "action": "update",
        "key": key,
        "value": new_value
    })

@tool
def propose_delete_kvp(key: str):
    """
    Proposes to delete an existing key-value pair (KVP) from the document.
    This is used when the user asks to remove a piece of information.
    Returns a JSON object describing the proposed action.
    """
    return json.dumps({
        "action": "delete",
        "key": key
    })
