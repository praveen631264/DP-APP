import logging
import json
from flask import Blueprint, request, jsonify, current_app
from langchain.chains import ConversationalRetrievalChain
from app.vector_store import get_vector_store # Centralized vector store access
from app.ai_models import get_llm, get_embeddings, get_document_chat_agent # Centralized model access

chat_bp = Blueprint('chat_bp', __name__)
logger = logging.getLogger(__name__)

@chat_bp.route('/chat', methods=['POST'])
def chat_with_doc():
    """
    Handles chat queries for all documents or a specific document.
    """
    data = request.get_json()
    query = data.get('query')
    doc_id = data.get('doc_id') # Optional document ID to scope the chat
    # chat_history is currently not implemented on the frontend, but the backend supports it.
    chat_history = data.get('chat_history', []) 

    if not query:
        logger.warning("Chat request received with no query.")
        return jsonify({"error": "Query is required"}), 400

    try:
        # 1. Get the globally managed AI models and vector store
        llm = get_llm()
        embeddings = get_embeddings()
        vector_store = get_vector_store(current_app.db, embeddings)

        # 2. Configure the retriever
        # If a doc_id is provided, the search is filtered to that specific document.
        search_kwargs = {"k": 4}
        if doc_id:
            logger.info(f"Chat query scoped to doc_id: {doc_id}")
            search_kwargs["filter"] = {"doc_id": doc_id}
            # When querying a single doc, we can retrieve more chunks
            search_kwargs["k"] = 6
        
        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

        # 3. Create and run the Conversational Retrieval Chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            retriever=retriever,
            return_source_documents=True,
            chain_type="stuff",
        )

        logger.info(f"Invoking retrieval chain for query: '{query[:50]}...'")
        result = qa_chain({"question": query, "chat_history": chat_history})
        answer = result.get('answer', "Sorry, I couldn't find an answer based on the provided documents.")

        # 4. Format the source documents for the response
        source_documents = []
        if result.get('source_documents'):
            for doc in result['source_documents']:
                source_documents.append({
                    "filename": doc.metadata.get('filename', 'N/A'),
                    "doc_id": str(doc.metadata.get('doc_id')),
                    "score": doc.metadata.get('score', 'N/A')
                })

        return jsonify({"answer": answer, "source_documents": source_documents})

    except Exception as e:
        logger.error(f"Error during chat processing: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while processing your chat message."}), 500

@chat_bp.route('/documents/<doc_id>/chat', methods=['POST'])
def document_specific_chat(doc_id):
    """
    Handles interactive chat for a single document, with the ability for the AI
    to propose KVP modifications.
    """
    data = request.get_json()
    query = data.get('query')
    # chat_history is not used by the agent but is included for future use.
    chat_history = data.get('chat_history', []) 

    if not query:
        logger.warning(f"Document chat request for {doc_id} with no query.")
        return jsonify({"error": "Query is required"}), 400

    db = current_app.db
    doc = db.get_document(doc_id)
    if not doc or not doc.get('text'):
        logger.error(f"Could not find document or its text content for doc_id: {doc_id}")
        return jsonify({"error": "Document not found or not processed"}), 404

    try:
        llm = get_llm()
        
        # The document text is passed to the agent prompt.
        agent_executor = get_document_chat_agent(llm, doc['text'])
        
        logger.info(f"Invoking document agent for doc {doc_id} with query: '{query[:50]}...'")
        # The agent returns either a final answer or a proposed KVP modification.
        result = agent_executor.invoke({"input": query, "chat_history": chat_history})
        
        output = result.get('output')

        try:
            # If the agent proposes a KVP change, the output will be a JSON string.
            proposed_action = json.loads(output)
            response = {"proposed_action": proposed_action}
            logger.info(f"Agent for doc {doc_id} proposed an action: {proposed_action}")
        except (json.JSONDecodeError, TypeError):
            # Otherwise, it's a standard text answer.
            response = {"answer": output}

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error during document-specific chat processing for {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
