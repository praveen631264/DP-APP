#!/bin/bash

# =============================================================================
# On-Premises Deployment Script
# =============================================================================
# This script is designed to run the application in a production-like 
# on-premises environment. It runs the services as background processes.
#
# It assumes:
#   - You are in the project's root directory.
#   - A Python virtual environment exists at ./.venv.
#   - A production Kafka cluster is running and accessible.
# =============================================================================

# --- Configuration ---
# Set these environment variables to match your on-prem setup.

# The publicly accessible URL of your Flask app (e.g., http://192.168.1.50:8000)
export FLASK_APP_URL="http://localhost:8000"

# The address of your Kafka broker (e.g., kafka.your-company.com:9092)
export KAFKA_BROKER_URL="localhost:9092"

# The IP address and port Gunicorn will bind to.
# 0.0.0.0 makes it accessible from other machines on the network.
BIND_ADDRESS="0.0.0.0:8000"

# --- Stop, Start, or Restart --- 

# Function to stop running services
stop_services() {
    echo "Stopping services..."
    # Find and kill the Gunicorn and Celery processes
    pkill -f "gunicorn.*app:create_app()"
    pkill -f "celery.*app.celery_worker"
    echo "Services stopped."
}

# Function to start services
start_services() {
    echo "Starting services in the background..."

    # Activate virtual environment
    source .venv/bin/activate

    # 1. Start Celery Worker in the background
    echo "Starting Celery Worker..."
    nohup celery -A app.celery_worker.celery_app worker --loglevel=info > celery.log 2>&1 &

    # 2. Start Flask App with Gunicorn in the background
    echo "Starting Flask App with Gunicorn..."
    # The -w 4 flag starts 4 worker processes. Adjust based on your server's CPU cores.
    nohup gunicorn -w 4 --bind ${BIND_ADDRESS} "app:create_app()" > gunicorn.log 2>&1 &

    echo "Services started. Check gunicorn.log and celery.log for output."
    echo "API will be available at ${FLASK_APP_URL}"
}

# --- Script Logic ---

if [ "$1" = "start" ]; then
    start_services
elif [ "$1" = "stop" ]; then
    stop_services
elif [ "$1" = "restart" ]; then
    stop_services
    sleep 5 # Give services time to shut down cleanly
    start_services
else
    echo "Usage: ./run_onprem.sh [start|stop|restart]"
    exit 1
fi
