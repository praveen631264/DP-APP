#!/bin/bash
# This script generates ephemeral secrets and starts the local development environment.

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command to the terminal before executing it (for debugging).
set -x

echo "--- SCRIPT START ---"

echo "Generating ephemeral secrets for this session..."

# Generate random, secure strings for secrets
MONGO_PASS=$(openssl rand -hex 16)
FLASK_KEY=$(openssl rand -hex 32)

echo "--- SECRETS GENERATED (will be exported) ---"

# Export the variables to make them available to Docker Compose
export MONGO_PASSWORD="${MONGO_PASS}"
export FLASK_SECRET_KEY="${FLASK_KEY}"

echo "--- VERIFYING EXPORTED ENVIRONMENT VARIABLES ---"
# This command will print the environment variables. We should see our secrets here.
printenv | grep MONGO_PASSWORD
printenv | grep FLASK_SECRET_KEY
echo "------------------------------------------------"

# Inform the user what the password is for this session for manual connection.
echo "INFO: The MongoDB Password for this session is: ${MONGO_PASSWORD}"

# Ensure the data directories exist
mkdir -p data/mongo
mkdir -p data/ollama

# Start the services. Docker Compose automatically picks up exported variables.
echo "--- RUNNING DOCKER COMPOSE ---"
docker-compose up --build

# Unset the variables after docker-compose exits
unset MONGO_PASSWORD
unset FLASK_SECRET_KEY

# Turn off debugging flags when the script is done.
set +x
set +e
