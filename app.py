
import os
import uuid
import threading
import time
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Application Setup ---
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing to allow the frontend to call the backend
CORS(app)

# --- In-Memory Database & Configuration ---
# Create a directory to store uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# This dictionary will act as our simple in-memory "database" to track the status
# of processing jobs. In a real application, this would be a real database.
# Structure: { "file_id": {"status": "pending/completed", "result": {...}} }
jobs = {}

# --- Background AI Simulation ---

def simulate_ai_processing(file_id, file_path):
    """
    This function runs in a separate thread to simulate a long-running AI task.
    It waits for a random time, generates fake data, and updates the job status.
    """
    print(f"Starting AI processing for file_id: {file_id}...")
    
    # Simulate the time it takes for the AI to process the document
    time.sleep(random.randint(5, 10))
    
    # Simulate extracting data from the document
    # In a real system, this is where you would call the n8n workflow or AI model
    fake_extracted_data = {
        "invoice_number": f"INV-{random.randint(1000, 9999)}",
        "vendor_name": random.choice(["ACME Corp", "Stark Industries", "Wayne Enterprises"]),
        "total_amount": round(random.uniform(100.0, 5000.0), 2),
        "extracted_at": time.ctime()
    }
    
    # Update the jobs dictionary with the final result
    jobs[file_id]['status'] = 'completed'
    jobs[file_id]['result'] = fake_extracted_data
    
    print(f"Completed AI processing for file_id: {file_id}.")

# --- API Endpoints ---

@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    """
    Handles the file upload from the user.
    Saves the file, creates a job ID, and starts the background processing.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file:
        # Save the file to the uploads folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Create a unique ID for this processing job
        file_id = str(uuid.uuid4())
        
        # Create a new entry in our jobs dictionary
        jobs[file_id] = {"status": "pending", "result": None}
        
        # Start the background AI processing task in a new thread
        # We pass the file_id and path to the background function
        thread = threading.Thread(target=simulate_ai_processing, args=(file_id, file_path))
        thread.start()
        
        # Immediately return the file_id to the client
        return jsonify({"message": "File uploaded successfully, processing started.", "file_id": file_id}), 202

@app.route('/api/v1/results/<string:file_id>', methods=['GET'])
def get_result(file_id):
    """
    Called by the frontend to check the status of a processing job.
    Returns the result if completed, otherwise returns the pending status.
    """
    job = jobs.get(file_id)
    
    if not job:
        return jsonify({"error": "Invalid file_id"}), 404
        
    return jsonify(job)

if __name__ == '__main__':
    # Runs the Flask application
    app.run(debug=True, port=5000)
