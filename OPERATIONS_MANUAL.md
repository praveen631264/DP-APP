# Developer Onboarding & Operations Manual

Welcome to the AI-Powered Document Management API project. This document is the single source of truth for understanding the project's architecture and how to operate it in both local development and cloud production environments.

---

## 1. High-Level Architecture

The project is a containerized Flask application stack designed for robust document processing and management. It is architected to run in two distinct, but compatible, environments.

- **Application Layer:** Python (Flask) & Celery
- **AI Model Serving:** Ollama
- **Database:** MongoDB
- **Task Queue / Cache:** Redis
- **Containerization:** Docker
- **Cloud Deployment:** Terraform & Google Cloud Platform

---

## 2. Local Development Environment

This environment runs the entire application stack on your local machine using Docker Desktop. It is designed for day-to-day coding, feature development, and debugging.

### 2.1. Infrastructure & How It Works

- **Orchestration:** `docker-compose.yml` defines all services.
- **Startup Script:** `./deploy-local.sh` is the single command to start the environment.
- **Networking:** A private Docker network named `app-network` is created. All services (flask, mongo, etc.) communicate privately within this network. Only the Nginx service on port `80` is exposed to your host machine.
- **Secret Management:** Secrets are **ephemeral and generated on-the-fly**. The `deploy-local.sh` script generates a secure, random password for MongoDB for each session and injects it as an environment variable into the containers. **No secrets are ever stored on disk.**
- **Data Persistence:** Data for MongoDB and Ollama is persisted on your local disk in the `./data` directory. This means your data survives between `docker-compose up` and `down` cycles.

### 2.2. How to Run

1.  **Prerequisite:** Ensure Docker Desktop is installed and running.
2.  Run the following command from the project root:
    ```bash
    ./deploy-local.sh
    ```

### 2.3. Developer Operations (Accessing Services)

#### Accessing Logs

- **Combined Logs:** The terminal running `./deploy-local.sh` shows a live, combined stream of logs from all services.
- **Specific Logs:** In a new terminal, use `docker-compose logs -f <service_name>`. Example:
    ```bash
    # Follow logs for the Flask app in real-time
    docker-compose logs -f flask-app
    
    # Follow logs for the database
    docker-compose logs -f mongo
    ```

#### Accessing the Database (MongoDB)

1.  When you run `./deploy-local.sh`, the session's randomly generated password will be printed to the console.
2.  Use any database GUI (like MongoDB Compass or DBeaver).
3.  Create a new connection with these details:
    - **Host:** `localhost`
    - **Port:** `27017`
    - **Username:** `admin`
    - **Password:** *Paste the password from your terminal.*

#### Accessing a Server Shell

To get a command prompt inside a running container:

```bash
# Get a shell inside the main Flask app container
docker-compose exec flask-app /bin/bash

# Get a shell inside the Celery worker container
docker-compose exec celery-worker /bin/bash
```

---

## 3. Cloud Production Environment

This environment deploys the application to a scalable, secure, and fully-managed production environment on Google Cloud Platform (GCP). All infrastructure is defined as code using Terraform.

### 3.1. Infrastructure & How It Works

- **Location:** All files are in the `gcp_deployment/` directory.
- **Orchestration:** Terraform (`main.tf`, `variables.tf`) provisions all cloud resources.
- **Networking:** A private **Virtual Private Cloud (VPC)** isolates all resources. Services communicate over this private network using a **VPC Connector**. No service can be accessed directly from the public internet except for the main API.
- **Secret Management:** All secrets (database passwords, API keys) are stored securely in **Google Secret Manager**. Terraform retrieves these secrets and injects them into the Cloud Run environment at runtime.
- **Compute:**
    - `flask-app`: A public-facing **Cloud Run** service that runs the main API.
    - `celery-worker`: An **internal-only Cloud Run** service that is not exposed to the internet.
- **Database:**
    - **MongoDB Atlas:** Hosted externally, but configured with **VPC Peering** to only accept connections from within our private GCP VPC.
    - **Memorystore (Redis):** A fully managed Redis instance that lives exclusively inside our private VPC.
- **CI/CD:** **Cloud Build** automatically fetches your code, builds the Docker image, and pushes it to the Google Artifact Registry whenever you deploy.

### 3.2. How to Deploy

1.  **Prerequisites:** Install the `gcloud` CLI and Terraform. Authenticate with your Google Cloud account.
2.  **First-Time Setup:** Follow the instructions in `gcp_deployment/README.md` to create your `terraform.tfvars` file with your project ID and secrets.
3.  Run the following command from the project root:
    ```bash
    ./deploy-cloud.sh
    ```
    This script automates running `terraform init` and `terraform apply`.

### 3.3. Developer Operations (Accessing Services)

#### Accessing Logs

All logs are automatically sent to **Google Cloud Logging**.

1.  Open the Google Cloud Console.
2.  Navigate to **Logging > Logs Explorer**.
3.  Filter logs by **Resource > Cloud Run Revision** and select your services (`flask-app`, `celery-worker`). You can search and create alerts here.

#### Accessing the Database (MongoDB)

Access is locked down by default. You must temporarily whitelist your computer's IP address.

1.  Find your public IP address (e.g., from `whatismyip.com`).
2.  In the **MongoDB Atlas UI**, go to **Network Access**.
3.  Click **Add IP Address** and add your current IP with a description like "Temp dev access".
4.  Use your database client to connect using the production connection string from Atlas.
5.  **CRITICAL SECURITY STEP:** When you are finished, **DELETE the IP address** you added from the Network Access list.

#### Accessing the Server / Infrastructure

Direct SSH is not possible with serverless. Operations are performed via Google Cloud tools:

- **Google Cloud Console:** A web UI for viewing and managing all resources.
- **Google Cloud Shell:** A pre-authenticated terminal in your browser for running `gcloud` or `terraform` commands against your live environment.

---

## 4. Summary: Local vs. Cloud

| Feature           | Local Environment (Docker)                                    | Cloud Environment (GCP & Terraform)                                       |
|-------------------|---------------------------------------------------------------|---------------------------------------------------------------------------|
| **Startup**       | `./deploy-local.sh`                                           | `./deploy-cloud.sh`                                                       |
| **Networking**    | Private Docker Bridge Network                                 | Private Google VPC with VPC Peering                                       |
| **Secrets**       | In-memory, generated on-the-fly by startup script             | Google Secret Manager                                                     |
| **Data Storage**  | Local disk (`./data` folder)                                  | MongoDB Atlas & Google Memorystore                                        |
| **Log Access**    | `docker-compose logs`                                         | Google Cloud Logging (Logs Explorer)                                      |
| **DB Access**     | Direct connection to `localhost:27017` with session password    | Temporarily whitelist IP in Atlas UI                                      |
| **Infra Changes** | Edit `docker-compose.yml`                                     | Edit Terraform files in `gcp_deployment/` and run `./deploy-cloud.sh`   |

