
import os
import logging
from flask import Flask, jsonify
from flask_security import Security, MongoEngineUserDatastore, utils
from app.models import User, Role
from app.database import init_db
import click

# Import blueprints
from app.auth import auth_bp
from app.blueprints.chat import bp as chat_bp
from app.blueprints.documents import bp as documents_bp
from app.blueprints.playbooks import bp as playbooks_bp
from app.blueprints.categories import bp as categories_bp
from app.blueprints.admin import bp as admin_bp
from app.blueprints.dashboard import bp as dashboard_bp
from app.blueprints.health import bp as health_bp
from app.blueprints.jobs import bp as jobs_bp
from app.blueprints.model_registry import bp as models_bp
from app.blueprints.policies import bp as policies_bp
from app.blueprints.stream import bp as stream_bp

# Create the Flask-Security-Too object at the module level
security = Security()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.config['TESTING'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-hard-to-guess-string')
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
    app.config['VECTOR_DIMENSIONS'] = int(os.environ.get('VECTOR_DIMENSIONS', 384))
    app.config['OLLAMA_BASE_URL'] = os.environ.get('OLLAMA_HOST') # Use OLLAMA_HOST
    app.config['CHAT_MODEL_NAME'] = os.environ.get('CHAT_MODEL_NAME', 'llama2')
    app.config['EMBEDDINGS_MODEL_NAME'] = os.environ.get('EMBEDDINGS_MODEL_NAME', 'BAAI/bge-large-en')


    # Celery Configuration
    app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Flask-Security-Too Configuration
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'a-different-hard-to-guess-string')
    app.config["SECURITY_TOKEN_AUTHENTICATION_HEADER"] = "Authorization"
    app.config["SECURITY_TOKEN_AUTHENTICATION_KEY"] = "Bearer"
    app.config['SECURITY_URL_PREFIX'] = '/api/v1/auth'
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    app.config['SECURITY_RECOVERABLE'] = True
    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_UNAUTHORIZED_VIEW'] = None
    
    # Disable CSRF for our stateless API
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECURITY_CSRF_PROTECT_MECHANISMS"] = []
    app.config["SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS"] = True

    # Initialize database
    db = init_db(app)

    # Initialize Flask-Security-Too with the app
    user_datastore = MongoEngineUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)

    # Logging setup
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    # Define a CLI command to initialize the database
    @app.cli.command('init-db')
    def init_db_command():
        """Creates the initial admin user and roles."""
        if not security.datastore.find_role("Admin"):
            security.datastore.create_role(name="Admin", description="Full administrative access")
        if not security.datastore.find_role("User"):
            security.datastore.create_role(name="User", description="General user access")
        
        # Create a default admin user if one doesn't exist
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        if not security.datastore.find_user(email=admin_email):
            admin_password = os.environ.get('ADMIN_PASSWORD', 'password')
            security.datastore.create_user(email=admin_email, password=utils.hash_password(admin_password), roles=['Admin'])
            print(f"Admin user {admin_email} created with default password.")
        else:
            print("Admin user already exists.")
        print("Database initialized.")

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({"message": "Welcome to the IntelliDocs API"})

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/v1/chat')
    app.register_blueprint(documents_bp, url_prefix='/api/v1/documents')
    app.register_blueprint(playbooks_bp, url_prefix='/api/v1/playbooks')
    app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(jobs_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(models_bp, url_prefix='/api/v1/models')
    app.register_blueprint(policies_bp, url_prefix='/api/v1/policies')
    app.register_blueprint(stream_bp, url_prefix='/api/v1/stream')

    return app
