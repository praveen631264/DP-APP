from app import create_app
from app.celery_worker import celery

app = create_app()
