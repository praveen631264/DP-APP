
import os
from flask import Flask, current_app
from app.socket_instance import socketio
from app.blueprints.playbooks import bp as playbooks_bp
from app.blueprints.dashboard import bp as dashboard_bp
from app.blueprints.documents import bp as documents_bp
from app.blueprints.categories import bp as categories_bp
from app.blueprints.admin import bp as admin_bp
from app.database import db
import app.playbook_events # Important to register the events

def setup_default_category_and_playbook(app):
    """
    Creates a default category and a KVP extraction playbook on startup
    if they don't already exist.
    """
    with app.app_context():
        db_instance = current_app.db
        default_category_name = "Default"
        default_playbook_name = "Default Key-Value Extraction"

        # 1. Check and create the Default Category if it doesn't exist
        # Using a more generic db call in case get_by_name isn't on the class
        category_collection = db_instance.get_collection('categories')
        if category_collection.find_one({'name': default_category_name}) is None:
            db_instance.create_category({
                "name": default_category_name,
                "keywords": [] # No keywords, it acts as a fallback
            })
            print(f"INFO: Created default category: '{default_category_name}'")

        # 2. Check and create the Default Playbook if it doesn't exist
        playbook_collection = db_instance.get_collection('playbooks')
        if playbook_collection.find_one({'name': default_playbook_name}) is None:
            playbook_data = {
                "name": default_playbook_name,
                "category_name": default_category_name,
                "steps": [
                    {
                        "type": "llm_prompt_step",
                        "name": "Extract Key-Value Pairs from Document",
                        "prompt": '''Analyze the following document text and extract all relevant key-value pairs. The output MUST be a single, valid JSON object. For example: { "invoice_number": "INV-123", "due_date": "2024-05-31", "total_amount": 500.00 }. If no key-value pairs are found, return an empty JSON object {}. Document Content:\n\n{{document.text}}''',
                        "output_variable": "extracted_kvp"
                    },
                    {
                        "type": "update_document_step",
                        "name": "Save Extracted Data to Document",
                        "field": "metadata.kvp",
                        "value": "{{extracted_kvp}}"
                    }
                ],
                "final_status": "Processed"
            }
            db_instance.create_playbook(playbook_data)
            print(f"INFO: Created default playbook: '{default_playbook_name}'")

# --- App Initialization ---
app = Flask(__name__)

# Database configuration
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/my-project')
db.init_app(app)

# Register blueprints
app.register_blueprint(playbooks_bp, url_prefix='/api/v1/playbooks')
app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
app.register_blueprint(documents_bp, url_prefix='/api/v1/documents')
app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')
app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')


# SocketIO configuration
socketio.init_app(app, cors_allowed_origins='*')

# Setup the default items after the app is configured
setup_default_category_and_playbook(app)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
