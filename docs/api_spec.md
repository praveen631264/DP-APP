# API Specification

This document outlines the API endpoints for the application.

## Health Check

### `GET /health`

- **Description:** Checks the health of the service.
- **Response:**
  - `200 OK`: `{"status": "ok"}`

---

## Chat

### `POST /api/v1/chat`

- **Description:** Initiates a chat session, either globally or focused on a specific document.
- **Request Body (JSON):**
  ```json
  {
    "query": "Your chat query",
    "doc_id": "(Optional) The ID of the document to chat with"
  }
  ```
- **Response:**
  - `200 OK`: A JSON object with the chat agent's answer and the source documents it used.
  - `400 Bad Request`: If the `query` is missing.

---

## Documents

### `POST /api/v1/documents`

- **Description:** Uploads a new document for processing.
- **Request Body:** `multipart/form-data` with a `file` part.
- **Response:**
  - `202 Accepted`: If the file is uploaded and queued successfully.
  - `400 Bad Request`: If the file part is missing or the file type is not allowed.

### `GET /api/v1/documents`

- **Description:** Fetches a list of documents. Can be filtered by category or used to view the trash.
- **Query Parameters:**
  - `category` (optional): Filter documents by a specific category name (e.g., "Invoices"). Use "Uncategorized" for documents with no category.
  - `include_deleted` (optional): Set to `true` to list soft-deleted documents (the trash).
- **Response:**
  - `200 OK`: A JSON array of document objects.

### `GET /api/v1/documents/search`

- **Description:** Searches for documents by filename.
- **Query Parameters:**
  - `q`: The search query.
- **Response:**
  - `200 OK`: A JSON array of matching document objects.

### `GET /api/v1/documents/<doc_id>`

- **Description:** Retrieves the detailed metadata for a single document.
- **Response:**
  - `200 OK`: A JSON object containing the document's details.
  - `404 Not Found`: If the document does not exist.

### `DELETE /api/v1/documents/<doc_id>`

- **Description:** Moves a document to the trash (soft delete).
- **Response:**
  - `200 OK`: Success message.
  - `404 Not Found`: If the document does not exist.

### `POST /api/v1/documents/<doc_id>/restore`

- **Description:** Restores a soft-deleted document from the trash.
- **Response:**
  - `200 OK`: Success message.
  - `404 Not Found`: If the document is not in the trash.

### `GET /api/v1/documents/<doc_id>/download`

- **Description:** Downloads the original file for a document.
- **Response:**
  - `200 OK`: The raw file.
  - `404 Not Found`: If the document or file does not exist.

### `PUT /api/v1/documents/<doc_id>/kvp`

- **Description:** Manually overwrites the entire set of Key-Value Pairs for a document. This is typically used for bulk correction from a user interface.
- **Request Body (JSON):**
  ```json
  {
    "new_key_1": "new_value_1",
    "new_key_2": "new_value_2"
  }
  ```
- **Response:**
  - `200 OK`: A success message and the updated document object.
  - `400 Bad Request`: If the request body is not a valid JSON object.
  - `404 Not Found`: If the document does not exist.

### `POST /api/v1/documents/<doc_id>/reprocess`

- **Description:** Re-queues a document for AI processing. This is useful if the initial processing failed.
- **Response:**
  - `202 Accepted`: A success message and the updated document object.
  - `404 Not Found`: If the document does not exist.

---

## Interactive KVP Management (For Chat Interface)

These endpoints are designed to be called by the chat UI to allow users to make precise, audited changes to KVPs.

### `POST /api/v1/documents/<doc_id>/kvp/add`

- **Description:** Adds a single new Key-Value Pair to a document.
- **Request Body (JSON):**
  ```json
  {
    "key": "new_key",
    "value": "new_value"
  }
  ```
- **Response:**
  - `200 OK`: Success message and the updated document.

### `PATCH /api/v1/documents/<doc_id>/kvp/update`

- **Description:** Updates the value of a single existing Key-Value Pair.
- **Request Body (JSON):**
  ```json
  {
    "key": "existing_key",
    "value": "updated_value"
  }
  ```
- **Response:**
  - `200 OK`: Success message and the updated document.
  - `404 Not Found`: If the KVP key does not exist on the document.

### `DELETE /api/v1/documents/<doc_id>/kvp/delete`

- **Description:** Deletes a single Key-Value Pair from a document.
- **Request Body (JSON):**
  ```json
  {
    "key": "key_to_delete"
  }
  ```
- **Response:**
  - `200 OK`: Success message and the updated document.
  - `404 Not Found`: If the KVP key does not exist on the document.

---

## Categories

### `GET /api/v1/categories`

- **Description:** Fetches a list of all unique document categories.
- **Response:**
  - `200 OK`: `{"categories": ["Category1", "Category2", ...]}`

### `POST /api/v1/categories`

- **Description:** Creates a new document category.
- **Request Body (JSON):**
  ```json
  {
    "name": "New Category Name"
  }
  ```
- **Response:**
  - `201 Created`: Success message.
  - `409 Conflict`: If the category already exists.

### `DELETE /api/v1/categories/<category_name>`

- **Description:** Deletes a category. This will fail if any documents are still assigned to this category.
- **Response:**
  - `200 OK`: Success message.
  - `404 Not Found`: If the category does not exist.
  - `409 Conflict`: If the category is still in use.

---

## Dashboard

### `GET /api/v1/dashboard/stats`

- **Description:** Retrieves a collection of statistics for the main dashboard.
- **Response:**
  - `200 OK`: A JSON object containing various dashboard metrics.

---
