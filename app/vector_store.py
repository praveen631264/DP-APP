from langchain_community.vectorstores import MongoDBAtlasVectorSearch

def get_vector_store(db, embeddings):
    """
    Initializes and returns the MongoDB Atlas Vector Search instance.
    """
    collection = db.document_chunks
    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="chunk_vector_index",
        text_key="text",
        embedding_key="embedding"
    )
    return vector_store