# System Architecture

This document outlines the architecture of the intelligent document processing system. The system is designed to be a scalable, resilient, and maintainable platform for uploading, analyzing, and managing documents.

## Core Components

The architecture is composed of four main components:

1.  **Flask Web Application**: The primary user interface for uploading and viewing documents. It serves the frontend, handles user authentication, and provides RESTful APIs.

2.  **Celery Distributed Task Queue**: Handles all long-running and resource-intensive tasks, most notably document processing and AI analysis. Using a task queue prevents the web application from becoming unresponsive during heavy operations.

3.  **MongoDB Database**: The central data store for the application. It leverages GridFS for large file storage and houses collections for document metadata, audit trails, and vector embeddings.

4.  **AI Service (LLM)**: An external or self-hosted Large Language Model (LLM) responsible for extracting key-value pairs (KVPs) and categorizing documents from their text content.

## Architectural Diagram

```mermaid
graph TD
    subgraph User Interaction
        A[User] -->|Uploads Document via UI/API| B(Flask Web App)
    end

    subgraph Backend Services
        B -->|1. Stores File in GridFS| C(MongoDB)
        B -->|2. Creates Task in Redis| D(Redis Broker)
        D -->|3. Fetches Task| E(Celery Worker)
    end

    subgraph Data Processing
        E -->|4. Retrieves File from GridFS| C
        E -->|5. Extracts Text| F(Text Extraction Module)
        F -->|6. Sends Text to AI| G(AI Service / LLM)
        G -->|7. Returns Analysis (KVPs, Category)| E
        E -->|8. Creates Vector Embeddings| H(Sentence Transformer)
        E -->|9. Stores Metadata, KVPs, & Embeddings| C
    end

    subgraph Data Retrieval
        B -->|Queries for docs, search, stats| C
    end
```

## Detailed Component Breakdown

### 1. Flask Web Application

*   **Role**: Serves as the main entry point for users and API clients.
*   **Responsibilities**:
    *   Handling HTTP requests for file uploads, document retrieval, search, and dashboard statistics.
    *   Serving the frontend UI (if applicable).
    *   Enqueuing document processing tasks onto the Celery queue.
    *   Validating user input.
*   **Key Libraries**: Flask, Werkzeug, Flask-CORS.

### 2. Celery & Redis

*   **Role**: Manages background task execution.
*   **Responsibilities**:
    *   **Celery Worker**: Executes the document processing pipeline asynchronously. This includes text extraction, calling the AI service, generating embeddings, and updating the database.
    *   **Redis**: Acts as the message broker, holding the queue of tasks for Celery workers to consume.
*   **Key Libraries**: Celery, Redis.

### 3. MongoDB

*   **Role**: The primary, multi-faceted data store.
*   **Structure**:
    *   **`fs.files` & `fs.chunks` (GridFS)**: Stores the raw binary content of the uploaded documents, allowing for files larger than the 16MB BSON limit.
    *   **`documents` Collection**: Stores metadata for each document, including filename, content type, status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`), extracted key-value pairs, and the document category.
    *   **`documents_audit` Collection**: Provides a full audit trail for each document, logging every status change and action. This supports traceability and debugging.
    *   **`documents` Vector Index**: A MongoDB Vector Search index is built on the `embedding` field. This enables efficient and scalable semantic search over the document content.
*   **Key Libraries**: Pymongo, GridFS.

### 4. AI Integration

*   **Role**: Provides the core intelligence for document analysis.
*   **Implementation**: The `app.utils.doc_utils.get_kvps_and_category` function orchestrates the call to an external LLM.
*   **Process**:
    1.  The extracted text is formatted into a structured prompt.
    2.  The prompt is sent to the configured LLM (e.g., OpenAI GPT, Google Gemini, Anthropic Claude).
    3.  The LLM is instructed to return a JSON object containing the `category` and `kvps`.
    4.  The system parses this JSON response and stores it in the `documents` collection.
*   **Key Libraries**: Langchain, Sentence-Transformers (for embeddings).

## Data Flow: Document Upload

1.  **Upload**: A user uploads a file via the Flask API endpoint (`/api/documents/upload`).
2.  **Initial Storage**: The Flask application saves the file directly to MongoDB GridFS and creates a preliminary record in the `documents` collection with a `PENDING` status. An initial `PENDING` entry is also made in the `documents_audit` collection.
3.  **Task Queuing**: The Flask app dispatches a new task to the Celery queue via Redis, passing the `document_id`.
4.  **Worker Pickup**: A Celery worker picks up the task from the queue.
5.  **Processing State**: The worker immediately updates the document's status to `PROCESSING` in both the `documents` and `documents_audit` collections.
6.  **Text Extraction**: The worker retrieves the file from GridFS and extracts its text content using libraries like PyPDF2, python-docx, etc.
7.  **AI Analysis**: The extracted text is sent to the configured LLM for categorization and KVP extraction.
8.  **Embedding Generation**: The worker uses a Sentence Transformer model to generate a vector embedding of the document's text.
9.  **Final Update**: The worker updates the document record with the extracted KVPs, category, embedding, and sets the status to `COMPLETED`.
10. **Auditing**: A final `COMPLETED` entry is logged in the `documents_audit` collection.

## Key Design Principles

*   **Decoupling**: The web server is decoupled from the heavy processing logic. This ensures the user experience is snappy and the system can handle bursts of uploads without crashing.
*   **Scalability**: The Celery workers can be scaled horizontally (by running more worker processes) to handle increased load.
*   **Resilience**: If the AI service or a text extraction step fails, the task is marked as `FAILED` in the database, and the failure is logged. The system does not crash, and the issue can be diagnosed from the audit trail.
*   **Configurability**: Key settings like model names, database URIs, and vector dimensions are managed in a central configuration file, making the application adaptable to different environments.
*   **Data Integrity**: The use of a dedicated audit collection ensures a complete history of every document is preserved. The soft-delete feature prevents accidental data loss.
