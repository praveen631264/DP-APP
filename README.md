# AI-Powered Document Management API

This project is a sophisticated, AI-powered Flask API for managing and understanding documents. It is designed with two distinct deployment targets: local development with Docker Compose and a fully-managed, scalable production environment on Google Cloud.

***

## 1. Local Development (with Docker Compose)

Use this method to run the entire application stack on your local machine using Docker Desktop. This is ideal for development, testing, and running the application offline.

### Prerequisites

- **Docker and Docker Compose:** Ensure you have Docker Desktop installed and running.

### How to Run

To build the Docker images and start all services (Flask, Celery, Nginx, MongoDB, Redis, and Ollama), run the following command from the project root directory:

```bash
./deploy-local.sh
```

This script simply executes `docker-compose up --build`.

- The Nginx reverse proxy will be accessible at `http://localhost:80`.
- Your application data for MongoDB and Ollama will be persisted in the `./data` directory.

To stop the services, press `Ctrl+C` in the terminal, then run `docker-compose down`.

***

## 2. Cloud Deployment (with Terraform & Google Cloud)

Use this method to deploy the application to a production-ready, scalable environment on Google Cloud. This workflow pushes your code to the cloud, where it is built and deployed to managed services.

### Prerequisites

- A Google Cloud Account, Terraform, and the `gcloud` SDK installed.
- A MongoDB Atlas cluster.

### How to Deploy

All configuration and instructions for the cloud deployment are contained within the `gcp_deployment` folder.

To initiate the deployment, run the following command from the project root directory:

```bash
./deploy-cloud.sh
```

This script will guide you through the process:
1.  It will change into the `gcp_deployment` directory.
2.  It will run `terraform init` to prepare your configuration.
3.  It will run `terraform apply`, which will prompt you to confirm the deployment after showing you the plan.

**Note:** Before running the script for the first time, you must follow the setup instructions in `gcp_deployment/README.md` to configure your project ID and secrets.

Once complete, Terraform will output the public URL of your application.
