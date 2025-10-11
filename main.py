

"""
This file is the main entry point for the application.
It creates the Flask app and the Celery app instances so that they
can be discovered by the command-line tools.
"""
from dotenv import load_dotenv

# Load environment variables from .env file before anything else
load_dotenv()

from app import create_app

# The Flask app and Celery app are instantiated here at the module level.
# The `devserver.sh` script and command-line tools (`flask`, `celery`) will look for them here.
app, celery = create_app()
