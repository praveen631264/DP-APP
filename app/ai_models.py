import logging
import threading
from flask import current_app
from langchain_community.chat_models import ChatOllama
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from app.agents import propose_add_kvp, propose_update_kvp, propose_delete_kvp

# --- Globals for AI Models ---
# Using threading locks to ensure thread-safe, single initialization of models.
l_llm = None
l_embeddings = None
llm_lock = threading.Lock()
embeddings_lock = threading.Lock()

logger = logging.getLogger(__name__)

def get_llm():
    """
    Provides a thread-safe, global instance of the ChatOllama model.
    Initializes the model on the first call.
    """
    global l_llm
    with llm_lock:
        if l_llm is None:
            try:
                logger.info("Initializing ChatOllama model for the first time...")
                l_llm = ChatOllama(
                    base_url=current_app.config['OLLAMA_BASE_URL'],
                    model=current_app.config['CHAT_MODEL_NAME'],
                    temperature=0
                )
                logger.info(f"ChatOllama model initialized successfully. Using model: {current_app.config['CHAT_MODEL_NAME']}")
            except Exception as e:
                logger.critical(f"Failed to initialize the Ollama LLM. Ensure Ollama is running and the model is available. Error: {e}", exc_info=True)
                raise ConnectionError("Could not connect to the local AI model via Ollama.") from e
    return l_llm

def get_embeddings():
    """
    Provides a thread-safe, global instance of the HuggingFace Embeddings model.
    Initializes the model on the first call.
    """
    global l_embeddings
    with embeddings_lock:
        if l_embeddings is None:
            try:
                model_name = current_app.config['EMBEDDINGS_MODEL_NAME']
                logger.info(f"Initializing HuggingFace Embeddings model '{model_name}' for the first time...")
                # For local, CPU-based inference, we specify the device as 'cpu'
                model_kwargs = {'device': 'cpu'} 
                encode_kwargs = {'normalize_embeddings': False}
                l_embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs=model_kwargs,
                    encode_kwargs=encode_kwargs
                )
                logger.info("HuggingFace Embeddings model initialized successfully.")
            except Exception as e:
                logger.critical(f"Failed to download or initialize the embeddings model. Error: {e}", exc_info=True)
                raise RuntimeError(f"Could not load the local embeddings model '{model_name}'.") from e
    return l_embeddings

def get_document_chat_agent(llm, doc_text: str):
    """
    Creates a ReAct agent that can chat about a document and propose KVP modifications.
    """
    tools = [propose_add_kvp, propose_update_kvp, propose_delete_kvp]
    
    # Use a pre-defined prompt from LangChain Hub that is optimized for ReAct agents.
    prompt = hub.pull("hwchase17/react")
    
    # The agent prompt needs to be partially filled with the document context and KVP info.
    # This gives the agent the necessary information to answer questions and use tools.
    prompt = prompt.partial(
        document_context=doc_text,
    )

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    
    return agent_executor
