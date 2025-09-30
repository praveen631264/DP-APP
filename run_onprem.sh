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
#   - A .env file with the CELERY_BROKER_URL is present.
# =============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Pre-flight Checks ---

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment '.venv' not found." >&2
    echo "Please run the one-time setup to create it." >&2
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Error: Configuration file '.env' not found." >&2
    echo "Please create it and define CELERY_BROKER_URL." >&2
    exit 1
fi

# --- Configuration ---

# The IP address and port Gunicorn will bind to.
# 0.0.0.0 makes it accessible from other machines on the network.
BIND_ADDRESS="0.0.0.0:8000"
FLASK_APP_URL="http://$(hostname -I | awk '{print $1}'):8000" # Auto-detect IP

# Log files
GUNICORN_LOG="gunicorn.log"
CELERY_LOG="celery.log"

# PID files to manage processes
GUNICORN_PID="gunicorn.pid"
CELERY_PID="celery.pid"


# --- Stop, Start, or Restart --- 

# Function to stop running services
stop_services() {
    echo "Stopping services..."
    # Stop Gunicorn
    if [ -f $GUNICORN_PID ]; then
        kill $(cat $GUNICORN_PID)
        rm $GUNICORN_PID
    else
        pkill -f "gunicorn.*app:create_app"
    fi

    # Stop Celery
    if [ -f $CELERY_PID ]; then
        kill $(cat $CELERY_PID)
        rm $CELERY_PID
    else
        pkill -f "celery.*app.celery_worker"
    fi
    echo "Services stopped."
}

# Function to start services
start_services() {
    echo "Starting services in the background..."

    # Activate virtual environment
    source .venv/bin/activate

    # 1. Start Flask App with Gunicorn in the background
    echo "Starting Flask App with Gunicorn..."
    # The -w 4 flag starts 4 worker processes. Adjust based on your server's CPU cores.
    nohup gunicorn -w 4 --bind ${BIND_ADDRESS} --pid ${GUNICORN_PID} "app:create_app()" > ${GUNICORN_LOG} 2>&1 &

    # 2. Start Celery Worker in the background
    echo "Starting Celery Worker..."
    nohup celery -A app.celery_worker.celery_app worker --loglevel=info --pidfile=${CELERY_PID} > ${CELERY_LOG} 2>&1 &

    echo "Services started. Check ${GUNICORN_LOG} and ${CELERY_LOG} for output."
    echo "API will be available at ${FLASK_APP_URL}"
}

# --- Script Logic ---

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2 # Give services time to shut down cleanly
        start_services
        ;;
    *)
        echo "Usage: ./run_onprem.sh [start|stop|restart]"
        exit 1
        ;;
esac
