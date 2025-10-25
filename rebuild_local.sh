#!/bin/bash

# =============================================================================
# Local Development Rebuild Script
# =============================================================================
# This script forces a rebuild of the Docker images and then restarts the
# services.
#
# Usage:
#   ./rebuild_local.sh        # Rebuilds all services
#   ./rebuild_local.sh ui     # Rebuilds only the 'ui' service
#   ./rebuild_local.sh api    # Rebuilds only the 'api' and 'worker' services
# =============================================================================

SERVICE_TO_REBUILD=$1

if [ -z "$SERVICE_TO_REBUILD" ]; then
    echo "Rebuilding all services and restarting..."
    # This command will force a rebuild of all services with a 'build' section
    docker-compose build --no-cache && docker-compose up -d
elif [ "$SERVICE_TO_REBUILD" = "api" ]; then
    echo "Rebuilding the 'api' and 'worker' services and restarting..."
    # Rebuild and restart both api and worker as they share a build context
    docker-compose up --build -d api worker
else
    echo "Rebuilding the '$SERVICE_TO_REBUILD' service and restarting..."
    docker-compose up --build -d "$SERVICE_TO_REBUILD"
fi

if [ $? -eq 0 ]; then
    echo "--> Rebuild and restart process initiated successfully."
fi