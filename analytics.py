
import json
from datetime import datetime
from collections import Counter
import os

# --- Constants ---
EVENT_LOG_FILE = 'events.log'

# --- 1. Event Logging ---

def log_event(category_id: str, playbook_id: str, document_id: str, event_type: str, details: dict = None):
    """
    Logs a structured event to a JSON-lines file.
    
    Args:
        category_id: The category being processed.
        playbook_id: The playbook being executed.
        document_id: The document being processed.
        event_type: The type of event (e.g., 'DOCUMENT_RECEIVED', 'PLAYBOOK_SUCCESS', 'PLAYBOOK_FAILURE').
        details: A dictionary with any additional information (e.g., error messages, file size).
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "category_id": category_id,
        "playbook_id": playbook_id,
        "document_id": document_id,
        "event_type": event_type,
        "details": details or {}
    }
    
    with open(EVENT_LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

# --- 2. Analytics Query Engine ---

def answer_analytics_question(prompt: str) -> dict:
    """
    (Simulated AI) Parses a natural language question about system analytics and returns a structured answer.
    """
    
    # Load all events from the log file
    if not os.path.exists(EVENT_LOG_FILE):
        return {"answer": "No analytics data has been recorded yet."}

    events = []
    with open(EVENT_LOG_FILE, 'r') as f:
        for line in f:
            events.append(json.loads(line))

    # --- Basic Keyword-Based Intent Recognition ---
    
    prompt = prompt.lower()
    
    # Intent: Count total documents
    if "how many documents" in prompt and "total" in prompt:
        doc_ids = {e['document_id'] for e in events}
        return {"answer": f"There have been a total of {len(doc_ids)} documents processed."}

    # Intent: Count documents by status (failed, processed)
    elif "how many documents" in prompt and ("failed" in prompt or "processed" in prompt or "succeeded" in prompt):
        status = "PLAYBOOK_FAILURE" if "failed" in prompt else "PLAYBOOK_SUCCESS"
        target_category_match = re.search(r"in the '([\w\s]+)' category", prompt)
        
        filtered_events = events
        if target_category_match:
            target_category = target_category_match.group(1).strip().lower().replace(" ", "_")
            filtered_events = [e for e in events if e['category_id'] == target_category]

        doc_ids = {e['document_id'] for e in filtered_events if e['event_type'] == status}
        status_text = "failed" if status == "PLAYBOOK_FAILURE" else "successfully processed"
        
        answer = f"There have been {len(doc_ids)} documents that {status_text}."
        if target_category_match:
            answer += f" in the '{target_category}' category"
            
        return {"answer": answer}

    # Intent: File types
    elif "what file types" in prompt or "what kind of files" in prompt:
        file_types = Counter(e['details'].get('file_type') for e in events if e['details'].get('file_type'))
        if not file_types:
            return {"answer": "I don't have any information about file types."}
        
        type_summary = ", ".join([f"{count} {ft}" for ft, count in file_types.items()])
        return {"answer": f"The most common file types are: {type_summary}."}
        
    else:
        return {"answer": "I'm sorry, I can't answer that question yet. I can tell you about total, failed, or successful documents, and about file types."}

