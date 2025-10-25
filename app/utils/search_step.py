import logging
from .base_step import PlaybookStep
from app.vector_store import get_vector_store
from app.ai_models import get_embeddings
from .playbook_utils import render_template
import dpath

logger = logging.getLogger(__name__)

class SearchStep(PlaybookStep):
    """
    A playbook step that performs a vector search against the document chunks.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        query = step_config.get('query')
        output_key = step_config.get('output_key')

        top_n = step_config.get('top_n', 3)

        if not query or not output_key:
            logger.error("SearchStep is missing 'query' or 'output_key' in its configuration.")
            return

        formatted_query = render_template(query, context)

        # --- 1. Initial Retrieval --- 
        # Fetch more documents than we need (e.g., 20) to give the re-ranker a good set of candidates.
        embeddings = get_embeddings()
        vector_store = get_vector_store(db, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 20})
        logger.info(f"Executing vector search for step '{step_config.get('name')}' with query: '{formatted_query}'")
        initial_results = retriever.get_relevant_documents(formatted_query)

        # --- 2. Re-ranking with Cross-Encoder --- 
        logger.info(f"Re-ranking {len(initial_results)} documents with cross-encoder.")
        cross_encoder = get_cross_encoder()
        
        # Create pairs of [query, document_content] for the cross-encoder
        pairs = [[formatted_query, doc.page_content] for doc in initial_results]
        scores = cross_encoder.predict(pairs)

        # Combine documents with their new scores
        scored_results = list(zip(scores, initial_results))

        # Sort by score in descending order
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # --- 3. Final Results --- 
        # Take the top N results after re-ranking
        final_results = [doc for score, doc in scored_results[:top_n]]

        formatted_results = "\n\n---\n\n".join([doc.page_content for doc in final_results])
        
        dpath.new(context, f"outputs.{output_key}", formatted_results)
        logger.info(f"Vector search and re-ranking step completed. Stored result in context at 'outputs.{output_key}'.")