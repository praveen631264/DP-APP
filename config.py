import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Main configuration class. 
    
    All application-wide settings are defined here as class variables.
    """
    # Secret key for signing sessions and other security-related needs
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-hard-to-guess-string')

    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/doc_management')

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'mongodb://localhost:27017/doc_management')

    # Vector Search Configuration
    VECTOR_DIMENSIONS = int(os.environ.get('VECTOR_DIMENSIONS', 384))
    EMBEDDINGS_MODEL_NAME = os.environ.get('EMBEDDINGS_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
