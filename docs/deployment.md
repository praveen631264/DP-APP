# Deployment Guide

This guide provides instructions for deploying the application to a production environment. The entire stack, including the AI models, is designed to be self-hosted.

## 1. Prerequisites

- A server with Docker and Docker Compose installed.
- A self-hosted MongoDB instance (or MongoDB Atlas if you prefer).
- A separate server or a dedicated GPU machine to run the [Ollama](https://ollama.com/) service.

## 2. Ollama Server Setup

The most robust deployment involves running the Ollama LLM service on its own dedicated hardware, ideally with a powerful GPU, separate from the main application server.

1.  **Install Ollama:** On your dedicated AI server, follow the official instructions to [install Ollama for Linux](https://github.com/ollama/ollama/blob/main/docs/linux.md).

2.  **Download the Model:** Pull the `phi3:mini` model.
    ```bash
    ollama pull phi3:mini
    ```

3.  **Expose Ollama to the Network:** By default, Ollama only listens on `127.0.0.1`. You must configure it to be accessible from your application server. 
    - **Option 1 (Systemd):** If you're using systemd, edit the service file:
      ```bash
      sudo systemctl edit ollama.service
      ```
      And add the following lines to expose it on all network interfaces:
      ```ini
      [Service]
      Environment="OLLAMA_HOST=0.0.0.0"
      ```
    - **Option 2 (Environment Variable):** Alternatively, set the environment variable `OLLAMA_HOST=0.0.0.0` before starting the Ollama service.

4.  **Restart and Verify:** Restart the Ollama service (`sudo systemctl restart ollama`) and ensure it's running and accessible from your application server (e.g., via `curl http://<ollama-server-ip>:11434`).

## 3. Application Server Configuration

On your main application server, create a `.env` file in the root of the project with the following environment variables:

```
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=a_very_secret_key # Change this to a random string

# MongoDB Configuration
MONGO_URI=your_mongodb_connection_string

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# --- Local AI Model Configuration ---
# URL to your separately hosted Ollama instance.
OLLAMA_BASE_URL=http://<your-ollama-server-ip>:11434

# The embeddings model runs locally inside the Docker container.
EMBEDDINGS_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# The chat/extraction model to use from your Ollama server.
CHAT_MODEL_NAME=phi3:mini
```

## 4. Build and Run with Docker Compose

From the root of the project, run the following command to build and start the services in the background:

```bash
docker-compose up --build -d
```

This will start the following services:

- `web`: The Flask application, served by Gunicorn.
- `worker`: The Celery worker for background processing.
- `redis`: The Redis message broker for Celery.

## 5. Database Initialization

The first time you deploy, you may need to create the vector search index in your MongoDB database. Run the following command:

```bash
docker-compose exec web python -c "from app import create_app; from app.database import init_db; app, _ = create_app(); init_db(app)"
```
