import logging
import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_security import auth_required
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_core.language_models.base import BaseLanguageModel
from app.vector_store import get_vector_store
from app.ai_models import get_llm, get_embeddings
from app.utils.doc_utils import extract_text
from bson import ObjectId
from app.chat_worker import global_chat_agent_task

chat_bp = Blueprint('chat_bp', __name__)
logger = logging.getLogger(__name__)

# --- AGENT TOOLS ---
# These are the functions the agent can decide to call.

@tool
def search_documents_by_category_and_query(query: str, category: str = None) -> str:
    """
    Searches for relevant document snippets based on a user's query.
    Can be filtered by a specific document category.
    Returns a formatted string of the findings.
    """
    logger.info(f"AGENT TOOL: Running search_documents_by_category_and_query with query='{query}' and category='{category}'")
    
    # We need access to the vector store, which is on the current_app context.
    # This is a common challenge when using agents in Flask.
    # A simple solution is to re-get the vector store inside the tool.
    embeddings = get_embeddings()
    vector_store = get_vector_store(current_app.db, embeddings)

    search_kwargs = {"k": 5}
    if category and category.lower() != "all":
        search_kwargs["filter"] = {"category": category}
    
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    results = retriever.get_relevant_documents(query)
    
    if not results:
        return "No relevant documents found."

    # Format the results for the LLM to synthesize
    formatted_results = "\n\n---\n\n".join([
        f"Source (ID: {doc.metadata.get('doc_id', 'N/A')}, Filename: {doc.metadata.get('filename', 'N/A')}, Category: {doc.metadata.get('category', 'N/A')})\nContent: {doc.page_content}"
        for doc in results
    ])
    return formatted_results

# --- AGENT SETUP ---

# The prompt is the agent's "brain" and instructions.
# It tells the GLOBAL agent about its purpose, the tools it has, and how to reason.
AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a helpful and powerful assistant that has access to a document retrieval system.

Your main job is to answer a user's question by finding the most relevant information from the available documents.

1.  **Deconstruct the Question**: If the user asks a complex question (e.g., "Compare financial performance to legal risks"), break it down into smaller, logical sub-questions.
2.  **Select the Right Tool**: For each sub-question, decide which tool is best. Use the `search_documents_by_category_and_query` tool. If you can infer a category from the user's question (e.g., "invoices", "contracts"), use the `category` parameter for a more focused search. Otherwise, search across all categories.
3.  **Synthesize the Answer**: Once you have the information from your tools, synthesize it into a single, clear, and comprehensive answer for the user.
4.  **Cite Your Sources**: If you use information from a document, you MUST cite it using a markdown link. Use the `doc_id` from the search result to create the link in the format `Filename`. For example: `invoice_123.pdf`.
5.  **Be Honest**: If you cannot find an answer in the documents, say so. Do not make up information.""",), # This is where the agent's thought process is stored.
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"), 
    ]
)

def get_global_agent_executor(llm: BaseLanguageModel) -> AgentExecutor:
    """
    Helper function to create and return the global agent executor.
    """
    tools = [search_documents_by_category_and_query]
    agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

@chat_bp.route('/chat/global', methods=['POST'])
@auth_required('token')
def trigger_global_chat_agent():
    """
    Handles global chat queries by asynchronously dispatching the agent task.
    This endpoint returns immediately with a 202 Accepted status.
    The actual response will be streamed back to the client via Socket.IO.
    """
    data = request.get_json()
    query = data.get('message')
    session_id = data.get('sid') # The client must send its Socket.IO session ID

    if not query or not session_id:
        logger.warning("Chat request received with no query.")
        return jsonify({"error": "Fields 'message' and 'sid' are required"}), 400

    # Dispatch the background task
    global_chat_agent_task.delay(query=query, session_id=session_id)

    logger.info(f"Dispatched global chat task for session {session_id}")
    return jsonify({"message": "Agent processing started. Response will be streamed."}), 202

# --- DOCUMENT-SPECIFIC CHAT ---

DOC_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a helpful AI assistant focused on a single document.
Your goal is to help the user understand, summarize, and find specific information within the provided document text.

You have access to the document's text and its currently extracted Key-Value Pairs (KVPs).

**Your Capabilities:**
1.  **Answer Questions**: Answer questions based *only* on the provided document text.
2.  **Find Information**: If a user asks for a piece of information (e.g., "what is the invoice number?"), check the KVPs first. If it's there, provide it. If not, scan the text to find it.
3.  **Summarize**: Provide summaries of the document if requested.
4.  **Be Honest**: If the information is not in the document text or the KVPs, state that you cannot find it. Do not make up information.

**Context:**
---
**Extracted KVPs:**
{kvps}
---
**Document Text:**
{document_text}
---
"""),
        ("human", "{input}"),
    ]
)

@chat_bp.route('/chat/document', methods=['POST'])
@auth_required('token')
def chat_with_document():
    """
    Handles chat messages related to a single, specific document.
    This agent is sandboxed and does not have external tools.
    """
    data = request.get_json()
    doc_id = data.get('document_id')
    message = data.get('message')

    if not doc_id or not message:
        return jsonify({"error": "Missing 'document_id' or 'message'"}), 400

    if not ObjectId.is_valid(doc_id):
        return jsonify({"error": "Invalid document ID format"}), 400

    db = current_app.db
    document = db.get_document(doc_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    try:
        # Extract text from the document stored in GridFS
        file_data = db.get_file(document['file_id'])
        if not file_data:
            return jsonify({"error": "Document file content not found."}), 404
        
        document_text = extract_text(file_data, document['content_type'])
        kvps = document.get('kvp', {})

        llm = get_llm()
        chain = DOC_CHAT_PROMPT | llm
        
        logger.info(f"Invoking document-specific chat for doc {doc_id}")
        result = chain.invoke({"input": message, "document_text": document_text[:8000], "kvps": kvps}) # Truncate for context window

        answer = result.content if hasattr(result, 'content') else str(result)

        return jsonify({"sender": "ai", "text": answer, "timestamp": datetime.datetime.utcnow().isoformat()})

    except Exception as e:
        logger.error(f"Error in document-specific chat for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred in the chat service"}), 500