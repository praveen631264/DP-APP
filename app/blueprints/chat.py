import logging
import datetime
import json
from flask import Blueprint, request, jsonify
from flask_security import auth_required
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_core.language_models.base import BaseLanguageModel
from app.vector_store import get_vector_store
from app.ai_models import get_llm, get_embeddings
from app.utils.doc_utils import extract_text
from bson import ObjectId
from app.celery_worker import global_chat_agent_task
from app.models import Document  # Import the Document model
from app import database

bp = Blueprint('chat_bp', __name__)
logger = logging.getLogger(__name__)

# --- AGENT TOOLS ---
@tool
def search_documents_by_category_and_query(query: str, category: str = None) -> str:
    """
    Searches for relevant document snippets based on a user's query.
    Can be filtered by a specific document category.
    """
    logger.info(f"AGENT TOOL: Running search with query='{query}' and category='{category}'")
    
    embeddings = get_embeddings()
    vector_store = get_vector_store(database, embeddings)

    search_kwargs = {"k": 5}
    if category and category.lower() != "all":
        search_kwargs["filter"] = {"category": category}
    
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    results = retriever.get_relevant_documents(query)
    
    if not results:
        return "No relevant documents found."

    # Correctly format results using metadata from the vector store documents
    formatted_results = "\n\n---\n\n".join([
        f"Source (ID: {doc.metadata.get('doc_id', 'N/A')}, Filename: {doc.metadata.get('filename', 'N/A')}, Category: {doc.metadata.get('category', 'N/A')})\nContent: {doc.page_content}"
        for doc in results
    ])
    return formatted_results

# --- AGENT SETUP ---
AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a helpful assistant with access to a document retrieval system. Your job is to answer user questions by finding relevant information in the documents. You must cite your sources using the format `[Filename]`.

1. Deconstruct the user's question.
2. Use the `search_documents_by_category_and_query` tool to find information.
3. Synthesize the answer and provide citations.
4. If you can't find the answer, say so.""",), 
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"), 
    ]
)

def get_global_agent_executor(llm: BaseLanguageModel) -> AgentExecutor:
    tools = [search_documents_by_category_and_query]
    agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

@bp.route('/global', methods=['POST'])
@auth_required('token')
def trigger_global_chat_agent():
    data = request.get_json()
    query = data.get('message')
    session_id = data.get('sid')

    if not query or not session_id:
        return jsonify({"error": "Fields 'message' and 'sid' are required"}), 400

    global_chat_agent_task.delay(query=query, session_id=session_id)
    logger.info(f"Dispatched global chat task for session {session_id}")
    return jsonify({"message": "Agent processing started. Response will be streamed."}), 202

# --- DOCUMENT-SPECIFIC CHAT ---
DOC_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are an AI assistant focused on a single document. Answer questions based only on the provided text and KVPs. If the answer isn't in the document, say so.

**Context:**
---
**Extracted KVPs:**
{kvps}
---
**Document Text:**
{document_text}
---
""",),
        ("human", "{input}"),
    ]
)

@bp.route('/document', methods=['POST'])
@auth_required('token')
def chat_with_document():
    data = request.get_json()
    doc_id = data.get('document_id')
    message = data.get('message')

    if not doc_id or not message:
        return jsonify({"error": "Missing 'document_id' or 'message'"}), 400

    if not ObjectId.is_valid(doc_id):
        return jsonify({"error": "Invalid document ID format"}), 400

    try:
        # --- CORRECTED LOGIC ---
        document = Document.objects(id=doc_id).first()

        if not document:
            return jsonify({"error": "Document not found"}), 404

        # Read file content from GridFS
        if not document.file or not document.file.grid_id:
            return jsonify({"error": "Document file content not found."}), 404

        file_content = document.file.read()
        document_text = extract_text(file_content, document.content_type)
        kvps = document.kvps or {}

        llm = get_llm()
        chain = DOC_CHAT_PROMPT | llm
        
        logger.info(f"Invoking document-specific chat for doc {doc_id}")
        result = chain.invoke({"input": message, "document_text": document_text[:8000], "kvps": json.dumps(kvps)})

        answer = result.content if hasattr(result, 'content') else str(result)

        return jsonify({"sender": "ai", "text": answer, "timestamp": datetime.datetime.utcnow().isoformat()})

    except Exception as e:
        logger.error(f"Error in document-specific chat for doc {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
