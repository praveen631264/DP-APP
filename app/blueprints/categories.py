import logging
from flask import Blueprint, request, jsonify, current_app

categories_bp = Blueprint('categories_bp', __name__)
logger = logging.getLogger(__name__)

@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Retrieves a list of all defined categories and their configurations.
    """
    try:
        db = current_app.db
        # The 'categories' collection will store our playbooks.
        # We project to exclude the internal '_id' from the response.
        all_categories = list(db.categories.find({}, {'_id': 0}))
        return jsonify(all_categories), 200
    except Exception as e:
        logger.error(f"Error retrieving categories: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@categories_bp.route('/categories', methods=['POST'])
def create_category():
    """
    Creates a new category playbook configuration.
    This will be used by the future Category Configuration Agent.
    """
    data = request.get_json()
    
    # Basic validation
    if not data or 'name' not in data:
        return jsonify({"error": "Category 'name' is required."}), 400

    category_name = data['name']
    
    try:
        db = current_app.db
        
        # Ensure the category doesn't already exist
        if db.categories.find_one({"name": category_name}):
            return jsonify({"error": f"Category '{category_name}' already exists."}), 409 # 409 Conflict

        # Insert the new category configuration
        db.categories.insert_one(data)
        logger.info(f"Successfully created new category playbook: '{category_name}'")
        return jsonify({"message": "Category created successfully.", "category": data}), 201
    except Exception as e:
        logger.error(f"Error creating category '{category_name}': {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500