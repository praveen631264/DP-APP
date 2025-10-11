# Intelligent Document Automation: Official Project Blueprint

**Objective:** To build and deliver the foundational, end-to-end core of the Intelligent Document Automation platform. This initial version will establish the full, scalable architecture and deliver the primary user-facing workflow: document ingestion, AI-powered data extraction, and result delivery.

---

### 1. High-Level Architecture & Team Roles

This platform consists of three core microservices connected by a central API. Each service is owned by a specialist, with Praveen acting as the Technical Architect to ensure robust and scalable integration.

*   **Technical Architect & Project Lead:** **Praveen**
    *   **Mission:** Define the master architecture, specify all service-level agreements (SLAs) and API contracts, provide core logic (like AI prompts), and lead integration.
*   **The Frontend Service (UI):** **Appu**
    *   **Mission:** Build the user-facing interface for document upload and results visualization.
*   **The Backend Service (API):** **Tamil**
    *   **Mission:** Build the central Flask API that handles file persistence, orchestrates calls to the workflow engine, and manages data.
*   **The Workflow Service (Automation Engine):** **Ajay**
    *   **Mission:** Build and manage the automation workflows in n8n, which will execute the AI-driven tasks.

![Architecture Diagram](https://i.imgur.com/g0aeZp2.png)

---

### 2. Phase 1: Foundational Services & API Contracts (Target: Day 1-2)

**Goal:** Establish the skeleton of each core service and define the contracts for how they will communicate.

**Praveen (Architect):**

*   [ ] **Define API Contracts:** Finalize and share the official API specifications.
    *   **API Contract 1: Trigger Workflow** (Backend Service sends to Workflow Service)
        *   `POST /webhook/start`
        *   `{"file_path": "/path/to/uploaded_document.pdf", "category": "Invoice"}`
    *   **API Contract 2: Send AI Result** (Workflow Service sends to Backend Service)
        *   `POST /api/v1/results`
        *   `{"file_id": "unique_file_id", "data": {"invoice_number": "INV-123", "total_amount": 500.00, "vendor_name": "ACME Corp"}}`

**Appu (Frontend Service):**

*   [ ] **Task:** Initialize the frontend project and create `index.html` with the file upload form.
*   [ ] **Task:** The form's action will point to the `/api/v1/upload` endpoint on the Backend Service.

**Tamil (Backend Service):**

*   [ ] **Task:** Initialize the Flask application.
*   [ ] **Task:** Create the `/api/v1/upload` endpoint. It must accept a file, save it to a persistent storage location, generate a unique `file_id`, and return the `file_id` to the client.
*   [ ] **Task:** Create the `/api/v1/results` endpoint to receive processed data from the Workflow Service and print it to the console for initial testing.

**Ajay (Workflow Service):**

*   [ ] **Task:** Install and configure the n8n instance.
*   [ ] **Task:** Create a new "Webhook" node which will serve as the entry point for all automation workflows. Share the production URL with Praveen/Tamil.

---

### 3. Phase 2: Implementing the Core Automation Engine (Target: Day 3-4)

**Goal:** Implement the primary data extraction logic and connect the Backend Service to the Workflow Service.

**Praveen (Architect):**

*   [ ] **Task:** Create and version-control the initial set of AI prompts.
    *   **Prompt v1.0 (Invoice):** *"You are a data extraction specialist. Read the following document and extract the vendor name, invoice number, and total amount. Return ONLY a valid JSON object with the keys: 'vendor_name', 'invoice_number', and 'total_amount'."*

**Tamil (Backend Service):**

*   [ ] **Task:** In the `/api/v1/upload` endpoint, immediately after saving the file, add the logic to make an HTTP POST request to the Workflow Service (Ajay's n8n webhook), sending the `file_path` and `file_id`.

**Ajay (Workflow Service):**

*   [ ] **Task:** Build out the version 1.0 "Invoice Processing" workflow:
    1.  **Webhook Node:** Receives the trigger from the Backend Service.
    2.  **Read File Node:** Uses the `file_path` to read the document content.
    3.  **AI/LLM Node:** Calls the AI model using the official prompt (v1.0) supplied by Praveen.
    4.  **HTTP Request Node:** Sends the final JSON output from the AI to the Backend Service's `/api/v1/results` endpoint, including the `file_id`.

---

### 4. Phase 3: Delivering the V1 User Experience (Target: Day 5)

**Goal:** Connect the Frontend to the Backend to deliver the complete, end-to-end user workflow.

**Appu (Frontend Service):**

*   [ ] **Task:** Convert the form to use JavaScript for asynchronous submission.
*   [ ] **Task:** Upon successful upload, display a "Processing..." status to the user.
*   [ ] **Task:** Implement a polling mechanism to call `/api/v1/results/{file_id}` on the Backend Service every 2-3 seconds.
*   [ ] **Task:** Upon receiving the JSON data, render it dynamically into a clean, readable HTML table on the page.

**Tamil (Backend Service):**

*   [ ] **Task:** In the `/api/v1/results` endpoint, save the incoming JSON from the Workflow Service to a database (e.g., MongoDB), linking it to the `file_id`.
*   [ ] **Task:** Create the new `/api/v1/results/{file_id}` endpoint. This endpoint must query the database and return the processed data if it exists, or a "pending" status if it does not.

**Praveen & Full Team:**

*   [ ] **Task:** Conduct full integration testing of the end-to-end flow.
*   [ ] **Task:** Prepare a demonstration of the completed V1 workflow for the ED.
*   [ ] **Task:** Document the V1 API and architecture for future development.