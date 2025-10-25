from langchain_community.llms import Ollama
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import InMemoryStore
from fastembed.embedding import DefaultEmbedding
from flask import current_app

llm_instance = None
embeddings_instance = None

# --- Caching Setup ---
# In a production environment, you would want to use a more persistent cache,
# such as RedisCache, to share the cache between multiple worker processes.
# For this example, we will use a simple in-memory cache.
set_llm_cache(InMemoryCache())

def get_llm():
    """
    Returns a singleton instance of the Language Model.
    """
    global llm_instance
    if llm_instance is None:
        # As an optimization, you could use a smaller, faster model for the orchestrator
        # and a more powerful model for the playbook steps.
        llm_instance = Ollama(
            base_url=current_app.config['OLLAMA_BASE_URL'],
            model=current_app.config['CHAT_MODEL_NAME']
        )
    return llm_instance

def get_embeddings():
    """
    Returns a singleton instance of the Embeddings model, with caching enabled.
    This model runs locally and is used for creating vector embeddings.
    """
    global embeddings_instance
    if embeddings_instance is None:
        # The underlying embedding model
        underlying_embeddings = DefaultEmbedding(model_name=current_app.config['EMBEDDINGS_MODEL_NAME'])

        # The in-memory store for cached embeddings
        store = InMemoryStore()

        # The cached embedder
        embeddings_instance = CacheBackedEmbeddings.from_bytes_store(
            underlying_embeddings, store, namespace=underlying_embeddings.model_name
        )

    return embeddings_instance

def get_cross_encoder():
    """
    Returns a singleton instance of the Cross-Encoder model for re-ranking.
    """
    global cross_encoder_instance
    if cross_encoder_instance is None:
        cross_encoder_instance = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return cross_encoder_instance
