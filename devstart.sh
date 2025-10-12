
#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Cleanup function ---
cleanup() {
    echo -e "\nShutting down all services..."
    pkill -P $$
    echo "Shutdown complete."
}

# Trap the EXIT signal to ensure cleanup runs on script termination
trap cleanup EXIT

# Activate the virtual environment
source .venv/bin/activate

# --- Start Services ---

# Clear the log file for a new session
> app.log

# Start the Flask server in the background and log its output
echo "Starting Flask server in the background..."
./devserver.sh & # This runs the simplified devserver script

# Wait a moment for the server to initialize
sleep 3

# Start the monitoring agent in the background and log its output
echo "Starting the Bugger Monitoring Agent in the background..."
python monitoring_agent.py >> app.log 2>&1 &

# --- Tail Logs --- 
echo "Tailing logs from app.log. Press Ctrl+C to stop all services."
tail -f app.log
