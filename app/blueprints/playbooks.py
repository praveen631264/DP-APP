
import logging
from flask import Blueprint, request, jsonify
from bson import ObjectId, json_util
import json
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal, Union
from app.models import Playbook, PlaybookStep  # Import the MongoEngine models

bp = Blueprint('playbooks_bp', __name__)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Validation (remain the same) ---
class BaseStep(BaseModel):
    name: str
    description: Optional[str] = None

class LLMPromptStepModel(BaseStep):
    type: Literal['LLM_PROMPT']
    prompt_template: str
    output_key: str

class SearchStepModel(BaseStep):
    type: Literal['VECTOR_SEARCH']
    query_template: str
    max_results: int = 3

PlaybookStepModels = Union[LLMPromptStepModel, SearchStepModel]

class PlaybookModel(BaseModel):
    name: str
    category_name: str
    steps: List[PlaybookStepModels] = Field(..., discriminator='type')
    final_status: Optional[str] = 'Processed'

@bp.route('/playbooks', methods=['POST'])
def create_playbook():
    """Creates a new playbook using MongoEngine models."""
    data = request.get_json()
    try:
        validated_data = PlaybookModel(**data).dict()
        
        # --- CORRECTED LOGIC ---
        new_playbook = Playbook(**validated_data)
        new_playbook.save()
        
        logger.info(f"Successfully created playbook '{new_playbook.name}' with ID {new_playbook.id}")
        return jsonify(json.loads(new_playbook.to_json())), 201
    except ValidationError as e:
        logger.warning(f"Playbook creation failed validation: {e.errors()}")
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating playbook: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks', methods=['GET'])
def get_playbooks():
    """Retrieves playbooks using MongoEngine queries."""
    category_name = request.args.get('category_name')
    try:
        # --- CORRECTED LOGIC ---
        if category_name:
            playbooks = Playbook.objects(category_name=category_name)
        else:
            playbooks = Playbook.objects()
            
        return jsonify(json.loads(playbooks.to_json())), 200
    except Exception as e:
        logger.error(f"Error fetching playbooks: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks/<playbook_id>', methods=['GET'])
def get_playbook(playbook_id):
    """Retrieves a single playbook by its ID."""
    try:
        if not ObjectId.is_valid(playbook_id):
            return jsonify({"error": "Invalid playbook ID format"}), 400
        
        # --- CORRECTED LOGIC ---
        playbook = Playbook.objects(id=playbook_id).first()
        if playbook:
            return jsonify(json.loads(playbook.to_json())), 200
        else:
            return jsonify({"error": "Playbook not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching playbook {playbook_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks/<playbook_id>', methods=['PUT'])
def update_playbook(playbook_id):
    """Updates an existing playbook."""
    data = request.get_json()
    try:
        if not ObjectId.is_valid(playbook_id):
            return jsonify({"error": "Invalid playbook ID format"}), 400
            
        validated_data = PlaybookModel(**data).dict()

        # --- CORRECTED LOGIC ---
        playbook = Playbook.objects(id=playbook_id).first()
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        playbook.update(**validated_data)
        playbook.reload() # Fetch the updated document

        logger.info(f"Successfully updated playbook {playbook_id}")
        return jsonify(json.loads(playbook.to_json())), 200
    except ValidationError as e:
        logger.warning(f"Playbook update failed validation: {e.errors()}")
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error updating playbook {playbook_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@bp.route('/playbooks/<playbook_id>', methods=['DELETE'])
def delete_playbook(playbook_id):
    """Deletes a playbook."""
    try:
        if not ObjectId.is_valid(playbook_id):
            return jsonify({"error": "Invalid playbook ID format"}), 400

        # --- CORRECTED LOGIC ---
        playbook = Playbook.objects(id=playbook_id).first()
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        playbook.delete()
        logger.info(f"Successfully deleted playbook {playbook_id}")
        return jsonify({"message": "Playbook deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting playbook {playbook_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
