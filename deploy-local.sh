#!/bin/bash
# This script generates ephemeral secrets and starts the local development environment.

echo "Generating ephemeral secrets for this session..."

# Generate random, secure strings for secrets
# We use openssl for robust random string generation.
export MONGO_PASSWORD=$(openssl rand -hex 16)
export FLASK_SECRET_KEY=$(openssl rand -hex 32)

echo "Secrets generated. Starting local deployment with Docker Compose..."

# Inform the user what the password is for this session, in case they need to connect manually.
echo "-----------------------------------------------------------------"
echo "MongoDB Password for this session: $MONGO_PASSWORD"
echo "-----------------------------------------------------------------"

# Ensure the data directories exist
mkdir -p data/mongo
mkdir -p data/ollama

# Pass the generated secrets to docker-compose and start the services.
docker-compose up --build
