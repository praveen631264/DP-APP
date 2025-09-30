from flask import Blueprint, request, jsonify, current_app
from langchain.vectorstores import VectorStore
from langchain.embeddings.base import Embeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import CTransformers
from langchain.embeddings import HuggingFaceEmbeddings
from typing import List, Dict, Any, Optional

chat_bp = Blueprint('chat_bp', __name__)

# --- Global Variables for AI Models ---
llm = None
embeddings = None
chain = None

class MongoVectorStore(VectorStore):
    """
    A LangChain VectorStore implementation that uses MongoDB Atlas Vector Search.
    """
    def __init__(self, db, embeddings_model: Embeddings, collection_name: str = 'documents'):
        self.db = db
        self.collection = self.db.db[collection_name]
        self.embeddings = embeddings_model
        self.index_name = "vector_index" # As defined in database.py

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None, **kwargs: Any) -> List[str]:
        # This is a read-only vector store for this application's purpose
        raise NotImplementedError("Adding texts directly is not supported.")

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Performs a similarity search using MongoDB's $vectorSearch.
        """
        query_embedding = self.embeddings.embed_query(query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 150, # Increased to account for filtering
                    "limit": k, # Number of results to return
                    "filter": {
                        # Exclude soft-deleted documents from the search
                        "deleted_at": {"$exists": False}
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "filename": 1,
                    "text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))
        
        # Format results to match LangChain's expected Document format
        documents = []
        for res in results:
            doc = {
                "page_content": res.get('text', ''),
                "metadata": {
                    'doc_id': str(res.get('_id')),
                    'filename': res.get('filename', ''),
                    'score': res.get('score')
                }
            }
            documents.append(doc)

        return documents
    
    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, metadatas: Optional[List[dict]] = None, **kwargs: Any):
        # This is a read-only vector store
        raise NotImplementedError("from_texts is not supported.")

def init_chat_models():
    """
    Initializes the core AI models (LLM and Embeddings).
    The Vector Store is now instantiated on-demand within the request.
    """
    global llm, embeddings

    if llm is None:
        print("Initializing LLM...")
        llm = CTransformers(
            model="marella-redpajama-incite-chat-3b-v1.Q4_K_M.gguf",
            model_type="gpt_neox",
            max_new_tokens=512,
            temperature=0.1
        )
    
    if embeddings is None:
        print("Initializing Embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

@chat_bp.route('/chat', methods=['POST'])
def chat_with_doc():
    global llm, embeddings, chain

    # Ensure models are loaded
    if llm is None or embeddings is None:
        init_chat_models()

    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({"error": "Query is required"}), 400

    # --- MongoDB Vector Search Integration ---
    # 1. Instantiate the MongoVectorStore
    db = current_app.db
    vector_store = MongoVectorStore(db=db, embeddings_model=embeddings)

    # 2. Create the ConversationalRetrievalChain with the new vector store
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True # Return source documents for reference
    )

    chat_history = [] # For now, history is not persisted across requests
    
    # 3. Execute the chain
    result = chain({"question": query, "chat_history": chat_history})
    answer = result.get('answer', "Sorry, I couldn't find an answer.")
    
    # 4. Format the source documents for the response
    source_documents = []
    if result.get('source_documents'):
        for doc in result['source_documents']:
            source_documents.append({
                "filename": doc.metadata.get('filename'),
                "doc_id": doc.metadata.get('doc_id'),
                "score": doc.metadata.get('score')
            })

    return jsonify({"answer": answer, "source_documents": source_documents})
