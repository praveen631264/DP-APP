# Quickstart Guide

This guide provides a fast track to getting the IntelliDocs application up and running on your local machine for development and testing purposes.

## Prerequisites

*   **Python 3.10+**: Ensure you have a modern version of Python installed.
*   **Docker & Docker Compose**: This is the recommended method for running the required services (MongoDB, Redis) with minimal setup.
*   **AI Provider API Key**: You need an API key from an AI service provider like OpenAI to use the document analysis features.

## 1. Clone the Repository

```bash
git clone <repository_url>
cd intellidocs
```

## 2. Set Up Environment Variables

Configuration is managed via a `.env` file. A sample is provided in the project root.

1.  **Copy the Example**:

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file**:
    Open the new `.env` file and update the following variables:

    *   `SECRET_KEY`: Change this to a long, random string for security.
    *   `OPENAI_API_KEY`: **This is mandatory**. Paste your API key here.

    The other variables (`MONGO_URI`, `CELERY_BROKER_URL`, etc.) are pre-configured to work with the Docker Compose setup. You don't need to change them.

## 3. Launch Services with Docker Compose

From the project root directory, run:

```bash
docker-compose up --build
```

This command will:
-   Build the Docker images for the Flask API (`api`) and the Celery worker (`worker`).
-   Download and start `mongo` and `redis` containers.
-   Start all services and connect them.

Your environment is now running! The API is accessible at `http://localhost:5000`.

## 4. Set Up the Database Vector Index

To enable semantic search, you need to create a vector index in MongoDB. This is a one-time setup step.

1.  **Find your MongoDB container name**:

    ```bash
    docker ps
    ```
    Look for the container using the `mongo` image (e.g., `intellidocs-mongo-1`).

2.  **Connect to the MongoDB shell**:

    ```bash
    docker exec -it <your_mongo_container_name> mongosh
    ```

3.  **Run the setup script**: The script `docs/mongo_setup.js` contains the command to create the index. Copy its contents and paste them into the `mongosh` prompt. Press Enter.

    You should see `"ok": 1`, confirming the index was created.

## 5. Test the Application

Your application is ready to use. You can interact with it via any API client (like Postman, Insomnia, or cURL).

### Example: Upload a Document

Use `curl` to upload a file. This example uses a simple text file.

1.  **Create a test file**:

    ```bash
    echo "This is a test invoice for Acme Corp for the amount of $500." > test.txt
    ```

2.  **Send the upload request**:

    ```bash
    curl -X POST -F "file=@test.txt" http://localhost:5000/api/documents/upload
    ```

### Example: Check Document Status

After uploading, you will get a response with a `document_id`. You can use this ID to check the processing status.

```bash
curl http://localhost:5000/api/documents/<your_document_id>
```

Initially, the status will be `PENDING` or `PROCESSING`. After a few seconds, it should change to `COMPLETED`, and you will see the extracted `kvps` and `category`.

### Example: Perform a Semantic Search

Once a document is processed, you can search for it based on its content.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"query": "Acme invoice"}' http://localhost:5000/api/documents/search
```

This will return a list of documents semantically related to your query.
