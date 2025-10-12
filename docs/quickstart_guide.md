
# **Project Quickstart & API Guide**

## **1. Overview**

This document provides a comprehensive guide for developers and users of the Unified Business Intelligence & Automation Platform. The platform is designed to ingest, analyze, automate, and unlock insights from business documents through a powerful, multi-layered AI architecture.

## **2. Core Architecture**

The system is built on three pillars:

*   **Intelligent Ingestion & Management:** A Redis-backed, asynchronous system for uploading and categorizing documents.
*   **Customizable Automation Playbooks:** A Celery-based workflow engine that executes multi-step, prompt-driven automations.
*   **Conversational Intelligence Engine:** A Retrieval-Augmented Generation (RAG) pipeline using ChromaDB for asking natural language questions of your documents.

## **3. End-to-End Workflow: The Journey of a Document**

Here is the step-by-step process for using the platform:

1.  **Upload a Document:** A user sends a `POST` request to `/api/v1/upload` with a file.
    *   The system saves the file, creates a metadata record in Redis with `status: pending`, and instantly returns a `doc_id`.
    *   A background task (`pre_analyze_document_task`) is triggered to analyze the document and add a `suggested_category` to its record in Redis.

2.  **Verify the Category (Human-in-the-Loop):** A user (or frontend application) retrieves the document's metadata, views the `suggested_category`, and confirms or corrects it.
    *   Send a `POST` request to `/api/v1/document/{doc_id}/categorize` with a JSON body: `{"category": "Vendor Invoice"}`.
    *   The document's `status` in Redis is updated to `categorized`.

3.  **Execute Automation:** The user triggers the main processing pipeline.
    *   Send a `POST` request to `/api/v1/document/{doc_id}/process`.
    *   This queues the master orchestrator task (`execute_playbook_task`).
    *   The task runs the entire playbook associated with the category (e.g., "Vendor Invoice"), storing the results in Redis for auditing.
    *   Upon completion, it automatically triggers the final RAG indexing task (`process_document_task`).

4.  **Query the Knowledge Base:** Once indexed, the document is part of the conversational knowledge base.
    *   Send a `POST` request to `/api/v1/ai/rag_query` with a JSON body: `{"query": "What was the total amount for invoice INV-12345?"}`.
    *   The AI will use the indexed content to find and synthesize an answer.

## **4. API Endpoint Reference**

### Document Management

*   `POST /api/v1/upload`
    *   **Action:** Uploads a new document.
    *   **Body:** `multipart/form-data` with a `file` part.
    *   **Returns (202):** `{"message": "...", "doc_id": "..."}`

*   `GET /api/v1/documents`
    *   **Action:** Lists all documents. Supports filtering by status.
    *   **Query Params:** `?status=pending` (optional)
    *   **Returns (200):** A JSON array of document metadata objects.

*   `GET /api/v1/document/{doc_id}`
    *   **Action:** Retrieves detailed metadata for a single document, including `task_status` and `playbook_results` if available.
    *   **Returns (200):** A JSON object with the document's full metadata.

*   `POST /api/v1/document/{doc_id}/categorize`
    *   **Action:** Sets or overrides the document's category.
    *   **Body:** `{"category": "Employment Agreement"}`
    *   **Returns (200):** Confirmation message.

### Processing & Automation

*   `POST /api/v1/document/{doc_id}/process`
    *   **Action:** Triggers the full playbook and indexing pipeline for a categorized document.
    *   **Returns (202):** Confirmation that the process has been queued.

### Conversational AI

*   `POST /api/v1/ai/rag_query`
    *   **Action:** Asks a question to the entire indexed knowledge base.
    *   **Body:** `{"query": "Your question here"}`
    *   **Returns (200):** `{"answer": "...", "source_documents": [...]}`

## **5. Extending the System: Adding New Playbooks**

To add a new automation workflow (e.g., for "Purchase Orders"), simply edit the `playbooks.py` file:

1.  Add a new entry to 