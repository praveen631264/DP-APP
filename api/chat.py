
import json
from flask import Blueprint, request, jsonify
import boto3
import os

# --- Blueprint Setup ---
# Note: The 'documents' and 'categories' are passed in from the main app factory
chat_api = Blueprint('chat_api', __name__)
documents_ref = None
categories_ref = None

def init_chat_api(documents, categories):
    global documents_ref, categories_ref
    documents_ref = documents
    categories_ref = categories

# --- AWS Bedrock Configuration ---
# It's best practice to configure your region and credentials via environment variables
# or the AWS config file (~/.aws/config).
# Example Environment Variables:
# AWS_REGION="us-east-1"
# AWS_ACCESS_KEY_ID="YOUR_KEY"
# AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime', 
    region_name=os.environ.get("AWS_REGION", "us-east-1") # Default to us-east-1 if not set
)

# --- Chat Endpoint ---

@chat_api.route('/api/v1/ai/chat/<string:doc_id>', methods=['POST'])
def handle_chat(doc_id):
    """
    Handles chat requests for a specific document using AWS Bedrock.
    """
    global documents_ref, categories_ref
    
    data = request.get_json()
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Find the document and its category
    doc = next((d for d in documents_ref if d['id'] == doc_id), None)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
        
    category = next((c for c in categories_ref if c['id'] == doc['categoryId']), None)
    category_name = category['name'] if category else "N/A"

    # --- Construct the Prompt for Bedrock ---
    # This prompt provides context to the model, telling it about the document
    # and what the user is asking.
    prompt = f"""
        Human: You are an intelligent assistant. You are analyzing a document named "{doc['name']}" which is classified as a "{category_name}".
        The full content of the document is:
        <document_content>
        {doc.get('content', 'No content available.')}
        </document_content>

        A user is asking a question about this document.
        User's question: "{user_message}"

        Please provide a helpful and concise answer based *only* on the information contained within the document content provided above. Do not make up information. If the answer is not in the document, say so.

        Assistant:
    """

    # --- Invoke Bedrock (Claude 3 Sonnet) ---
    try:
        # Define the payload for the model
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        })
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            body=body, 
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept='application/json', 
            contentType='application/json'
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        ai_response = response_body.get('content')[0].get('text')

        return jsonify({
            "user_message": user_message,
            "ai_response": ai_response
        })

    except Exception as e:
        # Log the error for debugging
        print(f"Bedrock invocation error: {e}")
        # Return a generic error to the user
        return jsonify({"error": "Failed to communicate with the AI model."}), 500

