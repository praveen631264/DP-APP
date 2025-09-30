#!/bin/bash

# =============================================================================
# Cloud Deployment Guide Script (Google Cloud)
# =============================================================================
# This is NOT an executable script, but a step-by-step guide with the 
# commands needed to deploy the application to Google Cloud Run. 
#
# It assumes:
#   - You have `gcloud` CLI installed and authenticated.
#   - You have Docker installed.
#   - You have a Google Cloud project.
#   - You have created Dockerfiles for both the Flask app and Celery worker.
# =============================================================================

# --- Configuration ---
# Replace these with your actual Google Cloud project details.

export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export AR_HOSTNAME="${REGION}-docker.pkg.dev"
export REPO_NAME="doc-processing-repo" # Name for your Artifact Registry repo

# Names for your two Cloud Run services
export FLASK_APP_SERVICE_NAME="doc-processor-web"
export CELERY_WORKER_SERVICE_NAME="doc-processor-worker"

# --- One-Time Setup on Google Cloud ---

# 1. Set your project context
# gcloud config set project ${PROJECT_ID}

# 2. Enable required APIs
# gcloud services enable run.googleapis.com
# gcloud services enable artifactregistry.googleapis.com
# gcloud services enable cloudbuild.googleapis.com

# 3. Create an Artifact Registry repository to store your Docker images
# gcloud artifacts repositories create ${REPO_NAME} \
#     --repository-format=docker \
#     --location=${REGION} \
#     --description="Docker repository for document processing app"

# 4. Configure Docker to authenticate with Artifact Registry
# gcloud auth configure-docker ${AR_HOSTNAME}

# --- Deployment Workflow ---
# Run these steps each time you want to deploy a new version.

# Step 1: Build the Docker Image using Cloud Build
# This command builds the image in the cloud, which is faster and more secure.
# It assumes you have a Dockerfile in your root directory.
echo "Building the Docker image using Google Cloud Build..."
# gcloud builds submit --tag "${AR_HOSTNAME}/${PROJECT_ID}/${REPO_NAME}/${FLASK_APP_SERVICE_NAME}:latest"

# Step 2: Deploy the Flask App to Cloud Run
# This command creates or updates the web-facing service.
echo "Deploying the Flask application to Cloud Run..."
# gcloud run deploy ${FLASK_APP_SERVICE_NAME} \
#   --image "${AR_HOSTNAME}/${PROJECT_ID}/${REPO_NAME}/${FLASK_APP_SERVICE_NAME}:latest" \
#   --platform managed \
#   --region ${REGION} \
#   --allow-unauthenticated \ # Makes the service public
#   # Important: You must provide the connection details for your Kafka broker.
#   # For cloud deployments, a managed service like Confluent Cloud or Amazon MSK is recommended.
#   # Ensure your Cloud Run service can connect to the broker (VPC connectors may be required).
#   --set-env-vars="CELERY_BROKER_URL=kafka://your-kafka-broker:9092,OTHER_VAR=value" 


# --- IMPORTANT NOTES for CELERY WORKER ---
#
# Deploying a Celery worker to a serverless, scale-to-zero environment like
# Cloud Run requires special considerations.
#
# Option A: Run as a separate Cloud Run service
# This is simpler but has a key limitation: the worker will shut down if it has
# no incoming requests, which means it won't be listening for Kafka messages.
# This is ONLY suitable if you trigger the worker via an HTTP push from Kafka.
#
# gcloud run deploy ${CELERY_WORKER_SERVICE_NAME} \
#   --image "path_to_your_celery_worker_image" \
#   --platform managed \
#   --region ${REGION} \
#   --no-allow-unauthenticated \ # Internal service, not public
#   --set-env-vars="CELERY_BROKER_URL=kafka://your-kafka-broker:9092"
#
# Option B: Use Google Kubernetes Engine (GKE) or a Compute Engine VM (More Robust)
# For a traditional, long-running Celery worker that constantly listens to a
# Kafka queue, a better approach is to deploy its container to GKE or a managed
# VM group. This ensures the service is always on.


echo "
Cloud Deployment Guide:

This script contains the commented-out commands to deploy to 