import logging
from typing import Any, Iterable, List, Optional
from langchain.vectorstores.base import VectorStore
from langchain.schema.embeddings import Embeddings
from langchain.schema.document import Document
from bson import ObjectId

logger = logging.getLogger(__name__)

# --- Global Vector Store ---
# This will hold the single, shared instance of the MongoVectorStore.
g_vector_store = None

def get_vector_store(db_client, embeddings_model):
    """
    Returns a global instance of the MongoVectorStore.
    """
    global g_vector_store
    if g_vector_store is None:
        g_vector_store = MongoVectorStore(db_client, embeddings_model)
    return g_vector_store


class MongoVectorStore(VectorStore):
    """
    A custom LangChain VectorStore that uses MongoDB as the backend.
    It uses the `$vectorSearch` aggregation pipeline for similarity searches.
    """
    def __init__(self, db_client: Any, embeddings_model: Embeddings, collection_name: str = 'documents', index_name: str = "vector_index"):
        self._db_client = db_client
        self._collection = self._db_client.db[collection_name]
        self._embeddings = embeddings_model
        self._index_name = index_name
        logger.info("MongoVectorStore initialized.")

    def add_texts(self, texts: Iterable[str], metadatas: Optional[List[dict]] = None, **kwargs: Any) -> List[str]:
        """This method is not used in this application, as documents are added via the database methods."""
        logger.warning("add_texts is not implemented for this vector store.")
        raise NotImplementedError("Adding texts directly is not supported.")

    def similarity_search(
        self, query: str, k: int = 4, filter: Optional[dict] = None, **kwargs: Any
    ) -> List[Document]:
        """
        Performs a similarity search in MongoDB using the $vectorSearch aggregation stage.

        Args:
            query: The text to search for.
            k: The number of results to return.
            filter: An optional MongoDB filter to apply before the vector search.

        Returns:
            A list of LangChain Document objects matching the search.
        """
        logger.info(f"Performing similarity search for query: '{query[:30]}...'")
        query_embedding = self._embeddings.embed_query(query)

        # Base filter excludes soft-deleted documents by default
        pre_filter = {"deleted_at": {"$exists": False}}
        if filter:
            pre_filter.update(filter)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 150,
                    "limit": k,
                    "filter": pre_filter
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "filename": 1,
                    "text": 1, # The raw text content of the document
                    "category": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        try:
            results = list(self._collection.aggregate(pipeline))
            logger.info(f"Found {len(results)} documents in vector search.")
        except Exception as e:
            logger.error(f"Error during MongoDB vector search: {e}", exc_info=True)
            # This can happen if the index is not ready or the query is malformed.
            return []
        
        # Convert MongoDB documents to LangChain's Document format
        documents = []
        for res in results:
            doc = Document(
                page_content=res.get('text', ''),
                metadata={
                    'doc_id': str(res.get('_id')),
                    'filename': res.get('filename', 'N/A'),
                    'category': res.get('category', 'N/A'),
                    'score': res.get('score')
                }
            )
            documents.append(doc)

        return documents

    @classmethod
    def from_texts(cls, *args, **kwargs):
        """This method is not applicable for this implementation."""
        raise NotImplementedError("from_texts is not supported.")
