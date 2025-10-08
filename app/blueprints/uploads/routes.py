from . import uploads_bp
from flask import request, jsonify
import os

@uploads_bp.route('/uploads', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = file.filename
        # In a real application, you'd want to secure the filename
        # and ensure the upload directory exists.
        # For now, we'll save it in a folder named 'uploads' in the project root.
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file.save(os.path.join(upload_folder, filename))
        return jsonify({'message': f'File {filename} uploaded successfully'})
