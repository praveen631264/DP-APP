import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

# 1. Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Get the embedding dimension
dimension = embedding_model.get_sentence_embedding_dimension()

# 3. Initialize the FAISS index
# We use IndexFlatL2, which is a simple and effective index for dense vectors.
faiss_index = faiss.IndexFlatL2(dimension)

# In-memory store for the actual text chunks
document_chunks = []

def add_text_to_index(text, doc_id):
    """
    Chunks the text, generates embeddings, and adds them to the FAISS index.
    """
    # Simple chunking strategy (e.g., by paragraph)
    chunks = text.split('\n')
    chunks = [chunk for chunk in chunks if chunk.strip()] # Remove empty chunks

    if not chunks:
        return

    # Generate embeddings for the chunks
    embeddings = embedding_model.encode(chunks)

    # Add embeddings to the FAISS index
    faiss_index.add(np.array(embeddings, dtype=np.float32))

    # Store the chunks with their corresponding document ID
    for chunk in chunks:
        document_chunks.append({"doc_id": doc_id, "chunk": chunk})

def search_index(query, k=5):
    """
    Searches the FAISS index for the most relevant chunks to a query.
    """
    if faiss_index.ntotal == 0:
        return []
        
    # Generate embedding for the query
    query_embedding = embedding_model.encode([query])

    # Search the index
    distances, indices = faiss_index.search(np.array(query_embedding, dtype=np.float32), k)

    # Retrieve the relevant chunks
    results = []
    for i in indices[0]:
        if i < len(document_chunks):
            results.append(document_chunks[i])

    return results
