
from app import create_app
from app.celery_worker import make_celery

# Create the Flask app instance
app = create_app()

# Use the app context to configure and create the Celery instance
celery = make_celery(app)
