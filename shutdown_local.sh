#!/bin/bash

# =============================================================================
# Local Development Shutdown Script
# =============================================================================
# This script stops all application services that were started with
# docker-compose.
# =============================================================================

echo "Stopping all application services..."

docker-compose down

echo "--> All services stopped successfully."
