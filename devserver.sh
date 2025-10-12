
#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Activate the virtual environment
source .venv/bin/activate

# Start the Flask development server.
# We will pipe the output to the `app.log` file while also printing it to the console.
echo "Starting Flask server... Logs will be written to app.log"
python main.py | tee app.log
