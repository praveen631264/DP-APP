
import os
import json
from datetime import datetime
import uuid
import random

# --- Constants ---
DOCUMENT_STORE_DIR = "document_data"
INCIDENT_STORE_DIR = os.path.join(DOCUMENT_STORE_DIR, "incidents")

# --- Utility Functions ---
def _get_document_path(document_id: str) -> str:
    """Gets the full path for a given document ID."""
    os.makedirs(DOCUMENT_STORE_DIR, exist_ok=True)
    return os.path.join(DOCUMENT_STORE_DIR, f"{document_id}.json")

def _get_incident_path(incident_id: str) -> str:
    """Gets the full path for a given incident ID."""
    os.makedirs(INCIDENT_STORE_DIR, exist_ok=True)
    return os.path.join(INCIDENT_STORE_DIR, f"{incident_id}.json")

# --- Core Data Management (with Category support) ---

def create_document_record(document_id: str, original_file_path: str, category: str = "uncategorized") -> dict:
    """Creates a new JSON file for a document record, including its category."""
    path = _get_document_path(document_id)
    if os.path.exists(path):
        raise FileExistsError(f"Record for document '{document_id}' already exists.")
    record = {
        "document_id": document_id, "original_file_path": original_file_path, "category": category,
        "status": "new", "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat(),
        "global_key_values": {}, "playbook_runs": []
    }
    with open(path, 'w') as f:
        json.dump(record, f, indent=2)
    return record

def get_document_record(document_id: str) -> dict:
    path = _get_document_path(document_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def update_document_record(document_id: str, updates: dict) -> dict:
    path = _get_document_path(document_id)
    updates['updated_at'] = datetime.utcnow().isoformat()
    with open(path, 'w') as f:
        json.dump(updates, f, indent=2)
    return updates

def update_document_category(document_id: str, new_category: str) -> dict:
    record = get_document_record(document_id)
    if not record:
        raise FileNotFoundError(f"Record for document '{document_id}' not found.")
    record['category'] = new_category.lower().strip()
    return update_document_record(document_id, record)

def get_documents_by_category(category: str) -> list:
    # ... (existing function content) ...
    pass

# --- Incident Management ---

def create_incident_record(log_line: str, error_type: str, status: str = "new_incident") -> dict:
    """Creates a new JSON file for a system incident."""
    incident_id = f"incident_{uuid.uuid4()}"
    path = _get_incident_path(incident_id)
    
    record = {
        "incident_id": incident_id,
        "timestamp": datetime.utcnow().isoformat(),
        "log_line": log_line,
        "error_type": error_type,
        "status": status, # e.g., 'new', 'acknowledged', 'resolved'
        "actions_taken": []
    }
    
    with open(path, 'w') as f:
        json.dump(record, f, indent=2)
    return record

def get_all_incidents() -> list:
    """Reads all incident records from the incident store."""
    incidents = []
    if not os.path.exists(INCIDENT_STORE_DIR):
        return incidents
        
    for filename in sorted(os.listdir(INCIDENT_STORE_DIR), reverse=True):
        if filename.endswith('.json'):
            path = os.path.join(INCIDENT_STORE_DIR, filename)
            try:
                with open(path, 'r') as f:
                    incidents.append(json.load(f))
            except (json.JSONDecodeError, KeyError):
                continue # Ignore malformed files
    return incidents

# --- Observability & Task Lifecycle Simulation ---

# ... (all existing playbook and system health functions remain unchanged) ...

def add_playbook_run(document_id: str, playbook_id: str, steps_to_queue: list) -> dict:
    record = get_document_record(document_id)
    if not record:
        raise FileNotFoundError(f"Record for document '{document_id}' not found.")
    # ... (rest of the function)
    pass
