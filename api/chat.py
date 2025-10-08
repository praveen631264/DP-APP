from flask import Blueprint, request, jsonify

chat_api = Blueprint('chat_api', __name__)

@chat_api.route('/api/v1/chat/correct', methods=['POST'])
def correct_kv_pair():
    """
    Endpoint for users to submit corrections for extracted key-value pairs.
    This data can be used for fine-tuning the AI model.
    """
    data = request.get_json()
    # In a real application, you would log this correction
    # and use it to improve your model.
    print(f"Received correction: {data}")
    return jsonify({"message": "Correction received. Thank you for your feedback!"})

@chat_api.route('/api/v1/chat/global', methods=['POST'])
def global_chat():
    """
    A global chat endpoint for general questions or commands.
    """
    data = request.get_json()
    user_message = data.get('message')
    # In a real application, you would process the message
    # and generate a response from the AI.
    print(f"Received global chat message: {user_message}")
    return jsonify({"reply": f"AI response to: '{user_message}'"})

@chat_api.route('/api/v1/chat/category', methods=['POST'])
def category_chat():
    """
    A chat endpoint for questions within a specific document category.
    """
    data = request.get_json()
    user_message = data.get('message')
    category = data.get('category')
    # In a real application, you would use the category to
    # provide a more context-aware response from the AI.
    print(f"Received category chat message for '{category}': {user_message}")
    return jsonify({"reply": f"AI response for category '{category}' to: '{user_message}'"})
