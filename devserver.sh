#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/app.log"

# --- Setup ---
# Create log directory and clear log file for the new session.
mkdir -p $LOG_DIR
> $LOG_FILE
echo "Log file initialized at $LOG_FILE"

# --- Cleanup function ---
cleanup() {
    echo -e "\nShutting down background services (Redis, Celery, Flask)..."
    # This command finds and terminates all processes that were started by this script.
    # The double dollar sign ($$) is the process ID (PID) of the script itself.
    pkill -P $$
    echo "Shutdown complete."
}

# Trap the EXIT signal. This ensures that the cleanup function is called 
# when the script is terminated, for example, by pressing Ctrl+C.
trap cleanup EXIT

# --- Activate Virtual Environment ---
echo "Activating Python virtual environment..."
source .venv/bin/activate

# --- Start Background Services ---
echo "Starting Redis, Celery, and Flask server in the background..."

# Start Redis and redirect its output to the log file.
# The final '&' runs the command as a background process.
redis-server >> $LOG_FILE 2>&1 &

# Wait a moment for Redis to initialize
sleep 2

# Start Celery workers and redirect their output to the log file.
celery -A main.celery worker --loglevel=info -Q processing >> $LOG_FILE 2>&1 &
celery -A main.celery worker --loglevel=info -Q dead_letter >> $LOG_FILE 2>&1 &

# Start the Flask development server and redirect its output.
flask --app main:app run --host=0.0.0.0 --port=8080 >> $LOG_FILE 2>&1 &

# --- Tail Logs --- 
echo "Tailing logs. Press Ctrl+C to stop all services."
# The 'tail -f' command runs in the foreground. When you press Ctrl+C to stop it,
# the script's EXIT trap is triggered, calling the cleanup function.
tail -f $LOG_FILE
