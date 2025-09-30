#!/bin/bash

# =============================================================================
# Local Development Startup Script
# =============================================================================
# This script is for starting the application on your local machine. 
# It assumes you have already run the one-time setup (creating a virtual 
# environment and installing dependencies).
#
# It will start the three required services in separate terminal windows.
# =============================================================================

echo "Starting Application for Local Development..."

# --- Step 1: Start Kafka ---
# Kafka requires two services: Zookeeper and the Kafka Broker.
# IMPORTANT: You must have Kafka installed. The paths below might need to be
# adjusted to match your Kafka installation directory.

echo "
--- Terminal 1: Starting Kafka ---
This script can't automatically open new terminal windows for you.
Please open TWO NEW TERMINAL TABS/WINDOWS and run the following commands:

1. In the FIRST new terminal, start Zookeeper:
   (Adjust the path to your Kafka installation)
   bin/zookeeper-server-start.sh config/zookeeper.properties

2. In the SECOND new terminal, start the Kafka Broker:
   (Adjust the path to your Kafka installation)
   bin/kafka-server-start.sh config/server.properties

Press [Enter] here after you have started both Kafka services...
"
read

# --- Step 2: Start the Celery Worker ---
echo "
--- Terminal 2: Starting Celery Worker ---
Now, open a THIRD new terminal and run these commands:

1. Activate the virtual environment:
   source .venv/bin/activate

2. Start the Celery worker:
   celery -A app.celery_worker.celery_app worker --loglevel=info

Press [Enter] here after you have started the Celery worker...
"
read

# --- Step 3: Start the Flask Web Server ---
echo "
--- Terminal 3: Starting Flask Web Server ---
Finally, this script will now start the Flask development server in this window.
"

./devserver.sh

echo "Application has been started. The Flask API is available at http://localhost:5000"
