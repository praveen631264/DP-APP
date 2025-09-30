#!/bin/bash

# =============================================================================
# Local Development Startup Script
# =============================================================================
# This script is for starting the application on your local machine. 
# It simplifies the startup process by using docker-compose for background
# services and providing clear instructions for the application components.
# =============================================================================

echo "Starting Application for Local Development..."

# --- Step 1: Start Background Services with Docker Compose ---
echo "--> Starting Kafka, and Zookeeper using docker-compose..."

docker-compose up -d kafka

if [ $? -ne 0 ]; then
    echo "Error: docker-compose failed to start." >&2
    echo "Please ensure Docker is running and docker-compose is installed." >&2
    exit 1
fi

echo "--> Background services started successfully."

# --- Step 2: Instructions for Celery Worker & Flask Server ---
echo ""
echo "--- Your Action Required ---"
echo "Please open TWO new terminal windows/tabs to start the application components:"

echo ""
echo "1. In the FIRST new terminal, start the Celery Worker:"
echo "   --------------------------------------------------"
echo "   source .venv/bin/activate"
echo "   celery -A app.celery_worker.celery_app worker --loglevel=info"

echo ""
echo "2. In the SECOND new terminal, start the Flask Web Server:"
echo "   ---------------------------------------------------"
echo "   ./devserver.sh"

echo ""
echo "Once both services are running, the Flask API will be available at http://localhost:5000"
echo "You can stop the background services at any time by running: docker-compose down"
