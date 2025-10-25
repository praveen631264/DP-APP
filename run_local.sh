#!/bin/bash

# =============================================================================
# Local Development Startup Script
# =============================================================================
# This script starts all application services using docker-compose.
# It will start the following services in the background:
# - MongoDB (Database)
# - Redis (Celery Broker)
# - Ollama (AI Model Server)
# - Flask API (Application Server)
# - Celery Worker (Background Task Processor)
#
# To view the logs of the running services, you can use:
# docker-compose logs -f
# =============================================================================

echo "Starting all application services for Local Development..."

docker-compose up -d

if [ $? -ne 0 ]; then
    echo "Error: docker-compose failed to start." >&2
    echo "Please ensure Docker is running and docker-compose is installed." >&2
    exit 1
fi

echo "--> All services started successfully."
echo "--> To force a rebuild of the images, run: ./rebuild_local.sh"
echo "The Flask API will be available at http://localhost:8000"
echo "You can stop the services at any time by running: ./shutdown_local.sh"