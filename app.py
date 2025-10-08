from flask import Flask, jsonify, request
import time
import random
from flask_cors import CORS
from api.chat import chat_api

# Create a Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register the chat API blueprint
app.register_blueprint(chat_api)

# In-memory data store
documents = []
next_document_id = 1

def find_document_by_id(doc_id):
    for doc in documents:
        if doc['id'] == doc_id:
            return doc
    return None

@app.route('/api/v1/uploads', methods=['POST'])
def upload_file():
    global next_document_id
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    if file:
        document = {
            'id': next_document_id,
            'name': file.filename,
            'status': 'uploaded',
            'category': None,
            'kv_pairs': None
        }
        documents.append(document)
        next_document_id += 1
        return jsonify(documents)

@app.route('/api/v1/documents', methods=['GET'])
def get_documents():
    return jsonify(documents)

@app.route('/api/v1/documents/<int:doc_id>/categorize', methods=['POST'])
def categorize_document(doc_id):
    doc = find_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    
    doc['status'] = 'categorizing'
    # Simulate AI processing time
    time.sleep(2)
    
    # Simulate success or error
    if random.random() > 0.2: # 80% success rate
        doc['status'] = 'categorized'
        doc['category'] = random.choice(['invoice', 'receipt', 'contract', 'report'])
    else:
        doc['status'] = 'error'
        doc['category'] = 'unknown'
        
    return jsonify(doc)

@app.route('/api/v1/documents/<int:doc_id>/extract', methods=['POST'])
def extract_kv_pairs(doc_id):
    doc = find_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    if doc['status'] != 'categorized':
        return jsonify({'error': 'Document must be categorized before extraction'}), 400

    doc['status'] = 'extracting'
    # Simulate AI processing time
    time.sleep(3)

    doc['status'] = 'extracted'
    doc['kv_pairs'] = [
        {'key': 'Invoice Number', 'value': 'INV-12345'},
        {'key': 'Date', 'value': '2025-10-26'},
        {'key': 'Total Amount', 'value': '$5,000'}
    ]
    return jsonify(doc)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
