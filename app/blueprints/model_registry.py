from flask import Blueprint, jsonify, current_app
from mongoengine.connection import get_db
from bson import json_util
import json

# Create a new blueprint
bp = Blueprint('model_registry_bp', __name__, url_prefix='/api/v1/registry')

@bp.route('/models', methods=['GET'])
def list_models():
    """
    Lists all models in the registry by querying the 'models' collection.
    """
    try:
        db = get_db()
        # Assumes a collection named 'models' exists for the registry
        models_collection = db.models
        models = list(models_collection.find())
        
        # Use json_util to handle BSON types like ObjectId
        return jsonify(json.loads(json_util.dumps(models)))
    except Exception as e:
        current_app.logger.error(f"Error listing models from registry: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
