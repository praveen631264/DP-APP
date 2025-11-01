
import logging
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional, Literal, Union

bp = Blueprint('playbooks_bp', __name__)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Validation ---

# Base model for common step fields
class BaseStep(BaseModel):
    name: str
    description: Optional[str] = None

# Specific model for the 'LLM_PROMPT' step
class LLMPromptStepModel(BaseStep):
    type: Literal['LLM_PROMPT']
    prompt_template: str
    output_key: str

# Specific model for the 'VECTOR_SEARCH' step
class SearchStepModel(BaseStep):
    type: Literal['VECTOR_SEARCH']
    query_template: str
    max_results: int = 3

# Create a Discriminated Union of the specific step models.
# The 'type' field is the discriminator. Pydantic will use it to determine
# which model to use for validation.
PlaybookStepModels = Union[LLMPromptStepModel, SearchStepModel]

# The main Playbook model now uses a list of the discriminated union of step models.
# This enforces that every step in the list conforms to one of the defined step schemas.
class PlaybookModel(BaseModel):
    name: str
    category_name: str
    steps: List[PlaybookStepModels] = Field(..., discriminator='type')
    final_status: Optional[str] = 'Processed'

@bp.route('/playbooks', methods=['POST'])
def create_playbook():
    """Creates a new playbook with strict validation for each step type."""
    db = current_app.db
    data = request.get_json()

    try:
        # Validate the incoming data. Pydantic will automatically use the `type`
        # field on each step to apply the correct model (PromptStepModel, etc.)
        validated_data = PlaybookModel(**data).dict()
        playbook_id = db.create_playbook(validated_data)
        playbook = db.get_playbook(playbook_id)
        logger.info(f"Successfully created playbook '{validated_data['name']}' with ID {playbook_id}")
        return jsonify(playbook), 201
    except ValidationError as e:
        logger.warning(f"Playbook creation failed validation: {e.errors()}")
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating playbook: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks', methods=['GET'])
def get_playbooks():
    """Retrieves a list of all playbooks, optionally filtered by category."""
    db = current_app.db
    category_name = request.args.get('category_name')
    try:
        playbooks = db.get_playbooks(category_name=category_name)
        return jsonify(playbooks), 200
    except Exception as e:
        logger.error(f"Error fetching playbooks: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks/<playbook_id>', methods=['GET'])
def get_playbook(playbook_id):
    """Retrieves a single playbook by its ID."""
    db = current_app.db
    try:
        if not ObjectId.is_valid(playbook_id):
            return jsonify({"error": "Invalid playbook ID format"}), 400
            
        playbook = db.get_playbook(playbook_id)
        if playbook:
            return jsonify(playbook), 200
        else:
            return jsonify({"error": "Playbook not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching playbook {playbook_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks/<playbook_id>', methods=['PUT'])
def update_playbook(playbook_id):
    """Updates an existing playbook with strict validation for each step type."""
    db = current_app.db
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body cannot be empty"}), 400

    try:
        if not ObjectId.is_valid(playbook_id):
            return jsonify({"error": "Invalid playbook ID format"}), 400

        # Validate the incoming data against the updated PlaybookModel
        validated_data = PlaybookModel(**data).dict()

        if db.update_playbook(playbook_id, validated_data):
            updated_playbook = db.get_playbook(playbook_id)
            logger.info(f"Successfully updated playbook {playbook_id}")
            return jsonify(updated_playbook), 200
        else:
            return jsonify({"error": "Playbook not found or update failed"}), 404
    except ValidationError as e:
        logger.warning(f"Playbook update failed validation: {e.errors()}")
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error updating playbook {playbook_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks/<playbook_id>', methods=['DELETE'])
def delete_playbook(playbook_id):
    """Deletes a playbook."""
    db = current_app.db
    try:
        if not ObjectId.is_valid(playbook_id):
            return jsonify({"error": "Invalid playbook ID format"}), 400

        if db.delete_playbook(playbook_id):
            logger.info(f"Successfully deleted playbook {playbook_id}")
            return jsonify({"message": "Playbook deleted successfully"}), 200
        else:
            return jsonify({"error": "Playbook not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting playbook {playbook_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
