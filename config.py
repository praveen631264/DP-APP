import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Main configuration class. 
    
    All application-wide settings are defined here as class variables.
    Settings are loaded from environment variables, with sensible defaults for local development.
    """
    # Secret key for signing sessions and other security-related needs
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-hard-to-guess-string')

    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/doc_analyzer_db')

    # Celery Configuration (using Redis)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # --- AI Model Configuration ---

    # On-premise LLM Server URL (Ollama)
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')

    # Name of the local embeddings model (runs in-app)
    EMBEDDINGS_MODEL_NAME = os.environ.get('EMBEDDINGS_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
    
    # Dimensions of the embeddings model output vector
    VECTOR_DIMENSIONS = int(os.environ.get('VECTOR_DIMENSIONS', 384))

    # Name of the chat/extraction model served by Ollama
    CHAT_MODEL_NAME = os.environ.get('CHAT_MODEL_NAME', 'phi3:mini')
