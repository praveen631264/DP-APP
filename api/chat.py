
from flask import Blueprint, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.llms.fake import FakeListLLM # Using a fake LLM for demonstration
from langchain.vectorstores import Chroma

# --- Blueprint Setup ---
chat_api = Blueprint('chat_api', __name__)

# --- Constants ---
CHROMA_PERSIST_DIR = "chroma_db"
CHROMA_COLLECTION_NAME = "knowledge_base"

# --- Load Models and Clients ---
# These are loaded once when the Flask app starts to ensure efficiency.
print("Loading SentenceTransformer model for chat...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Chat model loaded.")

print("Connecting to ChromaDB for chat...")
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
vectorstore = Chroma(
    client=chroma_client,
    collection_name=CHROMA_COLLECTION_NAME,
    embedding_function=embedding_model # This will use the model to embed queries
)
print("ChromaDB connection established for chat.")


# --- RAG Endpoint ---

@chat_api.route('/api/v1/ai/rag_query', methods=['POST'])
def rag_query():
    """
    Handles a user query using the Retrieval-Augmented Generation (RAG) pipeline.
    """
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "'query' is a required field."}), 400

    print(f"Received RAG query: {query}")

    # 1. Retrieve relevant documents from ChromaDB
    # The vectorstore automatically handles embedding the query and finding similar docs.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    # k=5 means it will retrieve the top 5 most relevant chunks.

    # 2. Define the Prompt Template
    # This guides the LLM to answer based *only* on the provided context.
    prompt_template = """
    You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.

    Context: {context}
    Question: {question}

    Answer:
    """
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # 3. Set up the RAG Chain
    # We use a FakeListLLM for demonstration purposes. In a real application,
    # you would replace this with a connection to a real LLM (e.g., from OpenAI, Anthropic, or a local one).
    # The response from the fake LLM will be based on the retrieved context.
    llm = FakeListLLM(responses=["Based on the documents, the answer is...", "I found relevant information indicating that...", "The context suggests that..."])
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff", # "stuff" means it will "stuff" all retrieved chunks into the prompt
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    # 4. Execute the chain and get the result
    try:
        result = qa_chain({"query": query})
        
        source_docs = [{
            "content": doc.page_content,
            "metadata": doc.metadata
        } for doc in result['source_documents']]

        return jsonify({
            "answer": result['result'],
            "source_documents": source_docs
        })

    except Exception as e:
        # This could happen if the database is empty or another error occurs.
        print(f"An error occurred during the RAG chain execution: {e}")
        return jsonify({"error": "Failed to process the query. The knowledge base might be empty or an internal error occurred."}), 500
