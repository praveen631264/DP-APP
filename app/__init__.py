import os
import logging
from flask import Flask
from config import Config
from .database import init_db
from .celery_worker import make_celery
from .logging_config import setup_logging

def create_app():
    """
    Application factory function. 
    
    This function creates and configures the Flask application, initializes the database,
    and registers the blueprints.
    """
    # Set up logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    app = Flask(__name__)

    # 1. Load configuration from the 'config.py' file
    app.config.from_object(Config)

    # 2. Initialize the database connection
    init_db(app)

    # 3. Initialize Celery
    app.config.update(
        CELERY_BROKER_URL=app.config["CELERY_BROKER_URL"],
        CELERY_RESULT_BACKEND=app.config["CELERY_RESULT_BACKEND"],
    )
    celery = make_celery(app)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 4. Register Blueprints
    from app.blueprints.chat import chat_bp
    from app.blueprints.documents import documents_bp
    from app.blueprints.health import health_bp
    from app.blueprints.categories import categories_bp
    from app.blueprints.dashboard import dashboard_bp

    app.register_blueprint(chat_bp, url_prefix='/api/v1')
    app.register_blueprint(documents_bp, url_prefix='/api/v1')
    app.register_blueprint(health_bp) # No prefix for health check
    app.register_blueprint(categories_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1')

    # A simple route to test the server is running
    @app.route('/hello')
    def hello():
        return "Hello, World!"

    logger.info("Flask application created successfully")
    return app, celery
