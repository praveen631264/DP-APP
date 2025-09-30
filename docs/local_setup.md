# Local Development Setup

This guide explains how to set up the project for local development and testing. The system is designed to run entirely on-premise, using local, open-source AI models.

## 1. Install and Run the Local LLM (Ollama)

This application uses [Ollama](https://ollama.com/) to run and serve the local Large Language Model. You must install it and download the required model before starting the application.

1.  **Install Ollama:** Follow the instructions on the [Ollama website](https://ollama.com/) to download and install it for your operating system (Windows, macOS, or Linux).

2.  **Download the AI Model:** Open your terminal and run the following command to download `phi3:mini`, the recommended model for your hardware.
    ```bash
    ollama pull phi3:mini
    ```

3.  **Keep Ollama Running:** The Ollama application must be running in the background for the application to be able to use the AI model. 

## 2. Project Setup

### Prerequisites

- Python 3.9+
- Pip and Venv
- A local MongoDB instance
- A local Redis instance

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <project_directory>
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the project root. This file is used to store your local configuration. **Do not commit this file.**

    ```
    # Flask Configuration
    FLASK_APP=run.py
    FLASK_ENV=development
    SECRET_KEY=a_local_secret_key

    # MongoDB Configuration (update with your local instance details)
    MONGO_URI=mongodb://localhost:27017/doc_analyzer_db

    # Celery and Redis Configuration (update if Redis is not on localhost)
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/0

    # --- Local AI Model Configuration ---
    # This should point to your locally running Ollama instance.
    OLLAMA_BASE_URL=http://127.0.0.1:11434

    # The embeddings model runs directly in the app.
    EMBEDDINGS_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

    # This is the chat/extraction model served by Ollama.
    CHAT_MODEL_NAME=phi3:mini
    ```

## 3. Running the Application Locally

You need to run two main services: the Flask web server and the Celery worker for background tasks.

1.  **Start the Web Server:**
    Make sure your virtual environment is active (`source .venv/bin/activate`) and then run:
    ```bash
    flask run
    ```
    The application will be running at `http://127.0.0.1:5000`.

2.  **Start the Celery Worker:**
    Open a **new terminal window**, activate the virtual environment, and start the Celery worker.
    ```bash
    # Activate the virtual environment in the new terminal
    source .venv/bin/activate

    # Start the worker
    celery -A run.celery worker --loglevel=info
    ```
    This worker will automatically pick up and execute tasks like document processing when you upload a file.
