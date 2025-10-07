import logging
from flask import Blueprint, request, jsonify, current_app

categories_bp = Blueprint('categories_bp', __name__)
logger = logging.getLogger(__name__)

@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get Categories
    ---
    tags:
      - Categories
    summary: Fetches a list of all unique, non-deleted document categories.
    responses:
      200:
        description: A list of categories.
    """
    db = current_app.db
    try:
        categories = db.get_all_categories()
        return jsonify({"categories": categories})
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while fetching categories"}), 500

@categories_bp.route('/categories', methods=['POST'])
def add_category():
    """
    Add Category
    ---
    tags:
      - Categories
    summary: Creates a new document category.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
                description: The name of the new category.
    responses:
      201:
        description: Category created successfully.
      400:
        description: Category name is required.
      409:
        description: Category already exists.
    """
    db = current_app.db
    data = request.get_json()
    category_name = data.get('name')

    if not category_name:
        return jsonify({"error": "Category name is required"}), 400

    try:
        if db.create_category(category_name):
            logger.info(f"Successfully created category: {category_name}")
            return jsonify({"message": f"Category '{category_name}' created successfully"}), 201
        else:
            logger.warning(f"Attempted to create a category that already exists: {category_name}")
            return jsonify({"error": "Category already exists"}), 409 # 409 Conflict
    except Exception as e:
        logger.error(f"Error creating category {category_name}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@categories_bp.route('/categories/<path:category_name>', methods=['DELETE'])
def delete_category(category_name):
    """
    Delete Category
    ---
    tags:
      - Categories
    summary: Deletes a category only if it has no associated documents.
    parameters:
      - name: category_name
        in: path
        required: true
        schema:
          type: string
        description: The name of the category to delete.
    responses:
      200:
        description: Category deleted successfully.
      404:
        description: Category not found.
      409:
        description: Category is in use.
    """
    db = current_app.db
    try:
        result = db.delete_category(category_name)
        if result == "deleted":
            logger.info(f"Successfully deleted category: {category_name}")
            return jsonify({"message": f"Category '{category_name}' deleted successfully."}), 200
        elif result == "in_use":
            logger.warning(f"Attempted to delete a category that is in use: {category_name}")
            return jsonify({"error": "Cannot delete category: it is currently in use by one or more documents."}), 409 # Conflict
        else: # not_found
            logger.warning(f"Attempted to delete a non-existent category: {category_name}")
            return jsonify({"error": "Category not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting category {category_name}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
