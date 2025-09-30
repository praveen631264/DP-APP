# API Specification

This document provides a comprehensive specification for all RESTful API endpoints available in the application.

## Base URL

All API endpoints are prefixed with `/api/v1`.

---

## 1. Health & Dashboard

### `GET /health`

- **Description:** Checks the health of the service. A standard endpoint for monitoring and uptime checks.
- **Response `200 OK`:**
  ```json
  {
    "status": "ok"
  }
  ```

### `GET /api/v1/dashboard/stats`

- **Description:** Retrieves a collection of aggregated statistics for displaying on a dashboard.
- **Response `200 OK`:** A JSON object containing various metrics, such as:
  ```json
  {
    "total_documents": 150,
    "documents_in_trash": 5,
    "categories_count": 12,
    "average_processing_time_seconds": 45.6
  }
  ```

---

## 2. Document Management

### `POST /api/v1/documents`

- **Description:** Uploads a new document for asynchronous AI processing.
- **Request:** `multipart/form-data` with a single `file` part.
- **Response `202 Accepted`:** The document was successfully received and queued. The body contains the initial document object.
- **Response `400 Bad Request`:** If the `file` part is missing or the file type is not allowed.

### `GET /api/v1/documents`

- **Description:** Fetches a paginated list of documents. Provides filtering by category and for viewing the trash.
- **Query Parameters:**
  - `category` (string, optional): Filter by a specific category name (e.g., "Invoices"). Use `"Uncategorized"` for documents without a category.
  - `include_deleted` (boolean, optional): If `true`, returns only soft-deleted documents (the trash).
  - `page` (int, optional): The page number for pagination. Defaults to `1`.
  - `per_page` (int, optional): The number of documents per page. Defaults to `10`.
- **Response `200 OK`:** A JSON object with pagination details and a list of document objects.

### `GET /api/v1/documents/search`

- **Description:** Searches for documents by filename.
- **Query Parameters:**
  - `q` (string, required): The search term.
- **Response `200 OK`:** A JSON array of matching document objects.

### `GET /api/v1/documents/<doc_id>`

- **Description:** Retrieves the full, detailed metadata for a single document.
- **Response `200 OK`:** The complete document JSON object.
- **Response `404 Not Found`:** If a document with the given `doc_id` does not exist.

### `DELETE /api/v1/documents/<doc_id>`

- **Description:** Moves a document to the trash (soft delete).
- **Response `200 OK`:** `{ "message": "Document moved to trash" }`
- **Response `404 Not Found`:** If the document does not exist.

### `POST /api/v1/documents/<doc_id>/restore`

- **Description:** Restores a soft-deleted document from the trash.
- **Response `200 OK`:** `{ "message": "Document restored successfully" }`
- **Response `404 Not Found`:** If the document is not in the trash.

### `GET /api/v1/documents/<doc_id>/download`

- **Description:** Downloads the original, raw file associated with a document.
- **Response `200 OK`:** The binary file stream.
- **Response `404 Not Found`:** If the document or its underlying file does not exist.

---

## 3. AI & Data Interaction

### `POST /api/v1/documents/<doc_id>/reprocess`

- **Description:** Re-triggers the AI processing pipeline for a document.
- **Response `202 Accepted`:** A success message indicating the document has been re-queued.
- **Response `404 Not Found`:** If the document does not exist.

### `PUT /api/v1/documents/<doc_id>/kvp`

- **Description:** (Human-in-the-Loop) Manually overwrites the entire set of Key-Value Pairs for a document.
- **Request Body (JSON):** A JSON object representing the new set of KVPs.
- **Response `200 OK`:** The updated document object.
- **Response `400 Bad Request`:** If the request body is not a valid JSON object.

### `PUT /api/v1/documents/<doc_id>/recategorize`

- **Description:** (Human-in-the-Loop) Manually changes the category of a document.
- **Request Body (JSON):**
  ```json
  {
    "new_category": "The new category name",
    "explanation": "(Optional) Reason for the change."
  }
  ```
- **Response `200 OK`:** The updated document object.
- **Response `400 Bad Request`:** If `new_category` is missing.
- **Response `404 Not Found`:** If the document does not exist.

### `POST /api/v1/chat`

- **Description:** The main endpoint for the Retrieval-Augmented Generation (RAG) chat feature.
- **Request Body (JSON):**
  ```json
  {
    "query": "What is the total amount for invoice 123?",
    "doc_id": "(Optional) ID of a specific document to focus the chat."
  }
  ```
- **Response `200 OK`:** JSON object with the answer and source documents.

---

## 4. Category Management

### `GET /api/v1/categories`

- **Description:** Fetches a list of all unique document categories.
- **Response `200 OK`:** `{"categories": ["Invoices", "Contracts", ...]}`

### `POST /api/v1/categories`

- **Description:** Creates a new document category.
- **Request Body (JSON):** `{"name": "New Legal Agreements"}`
- **Response `201 Created`:** The newly created category object.
- **Response `409 Conflict`:** If a category with that name already exists.

### `DELETE /api/v1/categories/<category_name>`

- **Description:** Deletes a category. Fails if any documents are still assigned to it.
- **Response `200 OK`:** Success message.
- **Response `404 Not Found`:** If the category does not exist.
- **Response `409 Conflict`:** If the category is still in use.
