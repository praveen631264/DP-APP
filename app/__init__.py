import os
import logging
from flask import Flask
from flask_security import Security, MongoEngineUserDatastore, utils
from mongoengine import connect
from config import Config
from app.database import init_db
from app.celery_worker import make_celery
from app.logging_config import setup_logging

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

    app.config.from_object(Config)

    # Add security configurations for user approval
    # --- Security & JWT Configuration ---
    # Use a secure, randomly generated secret key and password salt in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key-for-dev')
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'super-secret-salt-for-dev')
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False # Assuming no email server for now
    app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ('email',)
    app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authorization'
    app.config['SECURITY_TOKEN_AUTHENTICATION_KEY'] = 'access_token'
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for stateless JWT API

    init_db(app)

    # Initialize MongoEngine to use the same client as our pymongo-based db layer.
    # This ensures both MongoEngine (for Flask-Security) and our direct pymongo access
    # share the same connection pool.
    connect(db=app.db.name, host=app.db.client.HOST, port=app.db.client.PORT)

    # Initialize Flask-Security-Too
    from app.models import User, Role
    user_datastore = MongoEngineUserDatastore(app.db, User, Role)
    security = Security(app, user_datastore)

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
    from app.blueprints.auth import auth_bp
    from app.blueprints.chat import chat_bp
    from app.blueprints.documents import documents_bp
    from app.blueprints.health import health_bp
    from app.blueprints.categories import categories_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.profile import profile_bp
    from app.blueprints.admin import admin_bp

    # Auth blueprint provides /login, /logout, /register
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    # These blueprints will be protected by authentication
    app.register_blueprint(chat_bp, url_prefix='/api/v1')
    app.register_blueprint(documents_bp, url_prefix='/api/v1')
    app.register_blueprint(health_bp) # No prefix for health check
    app.register_blueprint(categories_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1')
    app.register_blueprint(profile_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')

    # A simple route to test the server is running
    @app.route('/hello')
    def hello():
        return "Hello, World!"

    # --- One-time setup: Create default roles and an admin user ---
    @app.before_first_request
    def create_initial_user_and_roles():
        logger.info("Running first-time setup...")
        if not user_datastore.find_role("admin"):
            user_datastore.create_role(name="admin", description="Full system access")
        if not user_datastore.find_role("user"):
            user_datastore.create_role(name="user", description="Standard user access")
        
        # Use environment variables for the initial admin user
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'password')

        if not user_datastore.find_user(email=admin_email):
            logger.info(f"Creating initial admin user: {admin_email}")
            user_datastore.create_user(email=admin_email, password=utils.hash_password(admin_password), roles=["admin"])

    logger.info("Flask application created successfully")
    return app, celery
