
import document_store
from typing import Dict, Any

# This is a placeholder for a more sophisticated intent recognition system.
# In a real-world scenario, this might use a library like spaCy, NLTK, or a dedicated NLU service.
def _recognize_intent(message: str) -> Dict[str, Any]:
    """
    Parses the user's message to determine their intent and extract entities.
    """
    # Make the matching case-insensitive and flexible
    lower_message = message.lower().strip()

    # Command: Set category
    # Example: "set category for doc123 to 'invoices'"
    if lower_message.startswith("set category for"):
        parts = message.strip().split()
        try:
            doc_id = parts[3]
            # The category might be in quotes, so we find where it starts and ends
            category_start_index = message.find("to ") + 3
            raw_category = message[category_start_index:].strip(" '\"")
            
            if doc_id and raw_category:
                return {
                    "intent": "set_category",
                    "entities": {
                        "document_id": doc_id,
                        "category": raw_category
                    }
                }
        except (IndexError, ValueError):
            return {"intent": "unknown", "error": "Invalid format for set category command."}

    # Command: Create category (even though categories are created implicitly)
    # Example: "create category 'new-projects'"
    if lower_message.startswith("create category"):
         return {"intent": "informational", "message": "Categories are created automatically when you assign them to a document for the first time!"}

    # Default to a Question/Answering intent
    return {
        "intent": "question_answering",
        "entities": {
            "query": message
        }
    }

def _execute_command(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Executes a command based on the recognized intent."""
    intent = intent_data.get("intent")
    entities = intent_data.get("entities", {})
    
    if intent == "set_category":
        doc_id = entities.get("document_id")
        category = entities.get("category")
        try:
            document_store.update_document_category(doc_id, category)
            return {"status": "success", "message": f"Successfully updated category for '{doc_id}' to '{category}'."}
        except FileNotFoundError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    
    if intent == "informational":
        return {"status": "success", "message": intent_data.get("message")}

    return {"status": "error", "message": "Could not execute unknown or unsupported command."}

def _answer_question(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handles the RAG (Retrieval-Augmented Generation) process."""
    query = intent_data.get("entities", {}).get("query")
    
    # This is a highly simplified RAG implementation.
    # A real system would use vector embeddings (e.g., from OpenAI or a local model) 
    # to find the most relevant document chunks based on semantic similarity to the query.
    
    # For now, we will return a helpful message acknowledging the query.
    # The foundation is here to plug in a real language model.
    response_message = f"This is where a generative AI would answer your question: '{query}'. I would search all documents to find the most relevant information before providing a detailed answer. This feature is ready for a large language model (LLM) to be integrated."
    
    return {"status": "success", "message": response_message}

def handle_chat_message(message: str) -> Dict[str, Any]:
    """Main entry point for the chat service."""
    print(f"--- Handling Chat Message: '{message}' ---")
    
    # 1. Recognize the user's intent
    intent_data = _recognize_intent(message)
    print(f"    - Recognized Intent: {intent_data}")
    
    # 2. Route to the appropriate handler
    intent = intent_data.get("intent")
    
    if intent in ["set_category", "informational"]:
        response = _execute_command(intent_data)
    elif intent == "question_answering":
        response = _answer_question(intent_data)
    else: # Handles "unknown"
        response = {"status": "error", "message": intent_data.get("error", "I'm sorry, I didn't understand that.")}
        
    print(f"    - Generated Response: {response}")
    return response
