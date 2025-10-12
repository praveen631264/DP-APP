
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import document_store
import playbooks
import chat_service
import e2e_test_runner # Import the new E2E test runner
import os
import logging
import logging_config

# --- Logging Setup ---
logging_config.setup_logging()
logger = logging.getLogger(__name__)

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app) # Enable CORS for all routes

# --- UI Endpoints ---

@app.route("/")
def index():
    """Serves the main incident monitoring dashboard UI."""
    logger.info("UI dashboard requested. Serving index.html.")
    return render_template('index.html')

# --- API Endpoints ---

@app.route("/api/v1/system/health", methods=['GET'])
def system_health():
    """Provides a simulated snapshot of the system's health."""
    logger.info("System health endpoint was queried.")
    health_data = document_store.get_simulated_system_health()
    return jsonify(health_data)

@app.route("/api/v1/documents/<string:document_id>", methods=['GET'])
def get_document_status(document_id: str):
    logger.info(f"Request received for document status: {document_id}")
    record = document_store.get_document_record(document_id)
    if not record:
        logger.warning(f"Document with ID '{document_id}' not found.")
        return jsonify({"error": f"Document with ID '{document_id}' not found."}), 404
    return jsonify(record)

@app.route("/api/v1/documents/run-playbook", methods=['POST'])
def run_document_playbook():
    data = request.get_json()
    logger.info(f"Playbook run requested with data: {data}")
    if not data or not all(k in data for k in ["document_id", "playbook_id", "catalog_id"]):
        logger.error("Playbook run request failed: Missing required fields.")
        return jsonify({"error": "Missing required fields"}), 400
    
    doc_id = data['document_id']
    if not document_store.get_document_record(doc_id):
        logger.info(f"No existing record for {doc_id}. Creating new document record.")
        document_store.create_document_record(doc_id, f"/uploads/{doc_id}.pdf")

    try:
        final_record = playbooks.run_playbook(
            document_id=doc_id,
            playbook_id=data['playbook_id'],
            catalog_id=data['catalog_id']
        )
        logger.info(f"Playbook for document {doc_id} completed successfully.")
        return jsonify(final_record), 200
    except Exception as e:
        logger.exception(f"Playbook execution failed for document {doc_id}. Error: {e}")
        return jsonify({"error": f"Playbook execution failed: {str(e)}"}), 500

@app.route("/api/v1/chat", methods=['POST'])
def handle_chat():
    data = request.get_json()
    if not data or "message" not in data:
        logger.error("Chat request failed: Missing 'message' field.")
        return jsonify({"error": "Request must include a 'message' field."}), 400

    message = data["message"]
    logger.info(f"Received chat message: '{message}'")
    response = chat_service.handle_chat_message(message)
    status_code = 400 if response.get("status") == "error" else 200
    logger.info(f"Returning chat response with status {status_code}: {response}")
    return jsonify(response), status_code

@app.route("/api/v1/incidents", methods=['GET'])
def get_incidents():
    """Provides a list of all recorded incidents for the UI."""
    logger.info("Request received for all incidents.")
    incidents = document_store.get_all_incidents()
    return jsonify(incidents)

# --- E2E Testing Endpoint ---

@app.route("/api/v1/testing/run", methods=['POST'])
def run_e2e_tests_endpoint():
    """Triggers a full end-to-end test suite run."""
    logger.info("E2E test run triggered via API.")
    try:
        report = e2e_test_runner.run_e2e_tests()
        # Determine final status code based on report
        status_code = 200 if report.get('overall_status') == 'SUCCESS' else 500
        return jsonify(report), status_code
    except Exception as e:
        logger.critical(f"The E2E test runner itself failed: {e}", exc_info=True)
        return jsonify({"error": "The test runner failed to execute", "details": str(e)}), 500

# --- Main Execution ---

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask server on host 0.0.0.0, port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
