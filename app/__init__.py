import os
import logging
from flask import Flask, jsonify
from flask_security import Security, MongoEngineUserDatastore, utils
from app.models import User, Role
from app.database import init_db
import click

# Create the Flask-Security-Too object at the module level
security = Security()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.config['TESTING'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-hard-to-guess-string')
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
    
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

    # Register blueprints, if any, here
    # from .blueprints.your_blueprint import bp
    # app.register_blueprint(bp)

    return app
