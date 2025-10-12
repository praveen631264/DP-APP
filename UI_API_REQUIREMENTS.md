
# UI & API Requirements Specification v5.1: The Document-Centric AI Platform

## 1. Executive Summary

**This version marks a fundamental architectural shift from a playbook-centric to a document-centric model.** The application's core is no longer the playbook; it is the **Document**. Every action—including playbook runs, AI data extraction, and conversational edits—is now performed in the context of a specific document.

This document serves as the single source of truth for the UI/UX team and front-end developers. It details the new data model, the complete suite of V5 APIs, and the required UI functional components.

---

## 2. The Document Object: The Single Source of Truth

The state of any given document is represented by a single, comprehensive JSON object. The UI **must** use the `GET /api/v1/documents/<document_id>` endpoint to fetch this object and render the entire Document Detail View.

### **Document Object Structure:**
```json
{
  "document_id": "doc_12345",
  "original_file_path": "/path/to/original/invoice.pdf",
  "status": "cancelled", 
  "created_at": "2023-10-27T10:00:00Z",
  "updated_at": "2023-10-27T10:05:00Z",
  "global_key_values": {
    "invoice_number": "INV-2023-001",
    "customer_name": "Acme Corp",
    "total_amount": "5000.00"
  },
  "playbook_runs": [
    {
      "run_id": "run_1698380700",
      "playbook_id": "invoice_processing_v2",
      "run_timestamp": "2023-10-27T10:05:00Z",
      "status": "success",
      "steps": [
        {
          "step": 1,
          "name": "Extract Header Data",
          "timestamp": "2023-10-27T10:05:01Z",
          "status": "success",
          "output": {
            "invoice_number": "INV-2023-001",
            "customer_name": "Acme Corp"
          }
        },
        {
          "step": 2,
          "name": "Push to Accounting API",
          "timestamp": "2023-10-27T10:05:02Z",
          "status": "success",
          "output": { "api_response_code": 201 }
        }
      ]
    }
  ],
  "blind_extraction_results": {
    "status": "success",
    "extracted_data": {
      "due_date": "2023-11-26"
    }
  }
}
```

### **Key Fields Explained:**

- **`status`**: The current state of the document. The UI should use this to show status badges.
  - `new`: Just uploaded.
  - `processing`: A playbook or blind extraction is in progress.
  - `processed`: The last operation completed successfully.
  - `failed`: The last operation failed.
  - `cancelled`: User cancelled a long-running operation. **No further actions are allowed on a cancelled document, except for viewing and downloading.**
- **`global_key_values`**: The master set of key-value pairs for this document. This data is aggregated from all playbook runs and can be modified by the AI co-pilot. This is the primary data display for the user.
- **`playbook_runs`**: An array containing a complete, auditable history of every playbook ever run on this document. The UI must render this as a timeline or log.
- **`blind_extraction_results`**: The output from the "Process Blindly" ad-hoc AI extraction.

---

## 3. Core Document Lifecycle APIs (v5.1)

These are the primary endpoints for the main user workflow.

### **Create a New Document Record**
- **Endpoint:** `POST /api/v1/documents`
- **Description:** Called when a file is first uploaded. Creates the initial document record in the new Document Store.
- **Request Body:**
  ```json
  {
    "document_id": "doc_generated_by_ui",
    "original_file_path": "/path/where/file/is/stored"
  }
  ```

### **Get Document State**
- **Endpoint:** `GET /api/v1/documents/<document_id>`
- **Description:** The most important read endpoint. Fetches the complete Document Object described in Section 2.

### **Run a Playbook on a Document**
- **Endpoint:** `POST /api/v1/documents/<document_id>/run_playbook`
- **Description:** Triggers a specific, published playbook to run against the document. The API will return the fully updated Document Object upon completion.
- **Request Body:**
  ```json
  {
    "playbook_id": "invoice_processing_v2",
    "category_id": "invoices"
  }
  ```

### **Process Document Blindly**
- **Endpoint:** `POST /api/v1/documents/<document_id>/process_blindly`
- **Description:** Triggers the general-purpose AI to extract all possible key-value pairs.
- **Request Body (Requires Document Text):**
  ```json
  {
    "text": "The full text content of the document."
  }
  ```

### **Cancel a Document (NEW)**
- **Endpoint:** `POST /api/v1/documents/<document_id>/cancel`
- **Description:** Sets the document's status to "cancelled". This is an irreversible action. Once a document is cancelled, no further processing or AI interaction is allowed.
- **Request Body:** None

---

## 4. The Document AI Co-pilot API (v5.1)

This API powers the new conversational interface for interacting with a document's data.

### **Ask a Question or Give a Command**
- **Endpoint:** `POST /api/v1/documents/<document_id>/ask`
- **Description:** Sends the user's natural language input from the chat panel to the AI.
- **Request Body:**
  ```json
  { "prompt": "What is the invoice number?" }
  ```
  ```json
  { "prompt": "Change the customer_name to 'Global Corp'" }
  ```

### **Handling AI Responses: CRITICAL**
The UI **must** be able to handle two distinct types of responses from the `/ask` endpoint:

1.  **A Direct Answer:** The AI is simply providing information.
    - **Response:**
      ```json
      { "answer": "The value for 'invoice_number' is 'INV-2023-001'." }
      ```
    - **UI Action:** Display the answer in the chat window.

2.  **A Proposed Update:** The AI is asking for permission to modify data.
    - **Response:**
      ```json
      {
        "action": "propose_update",
        "update_details": {
          "scope": "global_key_values",
          "key": "customer_name",
          "new_value": "Global Corp"
        },
        "confirmation_prompt": "Are you sure you want to update the global value 'customer_name' to 'Global Corp'?"
      }
      ```
    - **UI Action:**
        1.  Display the `confirmation_prompt` in the chat window.
        2.  Present the user with "Confirm" and "Cancel" buttons.
        3.  If the user clicks "Confirm", the UI **must** then call the `PUT /api/v1/documents/<document_id>/global_key_values` endpoint.

### **Confirm an AI-Proposed Update**
- **Endpoint:** `PUT /api/v1/documents/<document_id>/global_key_values`
- **Description:** This endpoint is called **only** after a user confirms a proposed update from the AI. It safely applies the change to the document's data.
- **Request Body:** The `update_details` object from the AI's proposal.
  ```json
  {
    "key": "customer_name",
    "new_value": "Global Corp"
  }
  ```

---

## 5. UI Functional Requirements (v5.1)

### 5.1. Main View: Document List
- The application's default view should be a list/table of all documents.
- Columns should include: Document ID, Status (with a visual badge), and Last Updated.
- Each item must be clickable, navigating the user to the Document Detail View.

### 5.2. Document Detail View: The Single Pane of Glass
This is the core screen of the application. It must be assembled using data from the `GET /api/v1/documents/<document_id>` call. It must contain the following components:

- **Header:**
  - Document ID.
  - Current Status (e.g., "Processed", "Failed", "Cancelled").
  - Action Buttons: **"Run Playbook"**, **"Process Blindly"**, and **"Cancel"**.
- **Document Viewer:**
  - A component to view the original document (e.g., PDF.js or an iframe).
  - A "Download Original" button.
- **Global Key-Values Panel:**
  - A clearly formatted display of all key-value pairs in the `global_key_values` object.
- **Processing History Panel:**
  - A timeline or log view of all `playbook_runs`.
  - Each run should be collapsible and show its status (success/failure).
  - Expanding a run reveals its `steps`. Expanding a step reveals its specific `output`.
- **Blind Extraction Panel:**
  - A display for the `blind_extraction_results`.
- **AI Co-pilot Panel:**
  - A chat interface for interacting with the document via the `/ask` endpoint.
  - It must correctly handle the "answer" vs. "propose update" flows as described in Section 4.

### 5.3. Cancelled State UI Behavior (NEW)
- When the UI loads a document and its status is `cancelled`:
  - ALL action buttons must be disabled, including "Run Playbook", "Process Blindly", "Cancel", and the "send" button in the AI Co-pilot chat.
  - An informative, read-only message should be displayed prominently (e.g., "This document has been cancelled and no further actions can be taken.").
  - The user MUST still be able to view all data and use the "Download Original" button.
