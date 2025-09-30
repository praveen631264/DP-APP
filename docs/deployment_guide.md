# Deployment Guide

This guide provides instructions for deploying the IntelliDocs application to a production-like environment. It covers setting up the required services (MongoDB, Redis), configuring environment variables, and running the Flask application and Celery workers.

## 1. Prerequisites

-   Python 3.10+
-   Docker and Docker Compose
-   An account with an AI service provider (e.g., OpenAI) and an API key.

## 2. Local Deployment using Docker Compose

For a simple and reproducible setup, we recommend using Docker Compose. A `docker-compose.yml` file is provided at the root of the project to orchestrate all the necessary services.

### Services:

*   **`mongo`**: A MongoDB instance for the database.
*   **`redis`**: A Redis instance for the Celery message broker.
*   **`api`**: The Flask web application.
*   **`worker`**: The Celery worker for background processing.

### Steps:

1.  **Create an Environment File**:
    Create a `.env` file in the project root. This file will hold all your configuration variables. Start by copying the contents of `.env.example`:

    ```bash
    cp .env.example .env
    ```

2.  **Configure Environment Variables**:
    Open the `.env` file and fill in the required values:

    ```ini
    # Flask Settings
    SECRET_KEY="a_very_secret_and_complex_key_change_me"

    # Database and Broker URLs (for Docker Compose)
    MONGO_URI="mongodb://mongo:27017/intellidocs"
    CELERY_BROKER_URL="redis://redis:6379/0"
    CELERY_RESULT_BACKEND="redis://redis:6379/0"

    # AI Service Configuration
    # Replace with your actual key and desired model
    OPENAI_API_KEY="your_openai_api_key_here"
    LLM_MODEL_NAME="gpt-3.5-turbo-1106"

    # Embedding Model (leave as default unless you have a specific need)
    EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
    VECTOR_DIMENSION=384
    ```

3.  **Build and Run the Services**:
    From the project root, run the following command:

    ```bash
    docker-compose up --build
    ```

    This command will:
    *   Build the Docker images for the `api` and `worker` services.
    *   Pull the official `mongo` and `redis` images.
    *   Start all four containers and connect them on a shared network.

4.  **Accessing the Application**:
    *   The Flask API will be available at `http://localhost:5000`.
    *   You can check the health of the API by navigating to `http://localhost:5000/api/health`.

5.  **Setting up the Vector Index in MongoDB**:
    After the services are running, you need to create the vector search index in MongoDB. A JavaScript helper script is provided in `docs/mongo_setup.js`.

    *   **Connect to the MongoDB Container**:
        ```bash
        docker exec -it <your_mongo_container_name_or_id> mongosh
        ```

    *   **Run the Script**: Copy the content of `docs/mongo_setup.js` and paste it into the `mongosh` prompt. This will create the index on the `documents` collection.

## 3. Manual Deployment (Without Docker)

### Step 1: Set up MongoDB and Redis

Ensure you have running instances of MongoDB and Redis. Note their connection URIs.

### Step 2: Install Dependencies

Create and activate a virtual environment, then install the required Python packages.

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Export the same environment variables as listed in the Docker section, but adjust the `MONGO_URI` and `CELERY_BROKER_URL` to point to your manually started services (e.g., `mongodb://localhost:27017/intellidocs`).

```bash
export SECRET_KEY="your_secret_key"
export MONGO_URI="mongodb://localhost:27017/intellidocs"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export OPENAI_API_KEY="your_openai_api_key"
# ... and so on
```

### Step 4: Run the Application and Worker

*   **Run the Flask App**:
    In one terminal, run:
    ```bash
    flask run
    ```

*   **Run the Celery Worker**:
    In a separate terminal, run:
    ```bash
    celery -A run.celery worker --loglevel=info
    ```

### Step 5: Create the Vector Index

Connect to your MongoDB instance using `mongosh` and run the script from `docs/mongo_setup.js` as described in the Docker section.
