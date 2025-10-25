from flask import Blueprint, jsonify, current_app

# Create a new blueprint
model_registry_bp = Blueprint('model_registry_bp', __name__, url_prefix='/api/v1/registry')

@model_registry_bp.route('/models', methods=['GET'])
def list_models():
    """
    Lists all models in the registry.
    """
    # Note: This is a placeholder. We will need to add proper serialization
    # and error handling like in the other blueprints.
    models = current_app.db.list_models()
    
    # Basic serialization to handle ObjectId
    for model in models:
        if '_id' in model:
            model['_id'] = str(model['_id'])

    return jsonify(models), 200
