#!/bin/bash
# This script is used to start Docker containers using docker-compose.
# Ensure the script is run from the directory containing the docker-compose.yml file

# Try to free up port 5672 for RabbitMQ
if sudo fuser -k 5672/tcp ; then
    echo "Killed process on port 5672"
fi

if docker compose up ; then
  echo "Restarting user-service..."
  docker compose restart user-service
  echo "Docker containers started successfully."
else
  echo "Stopping local PostgreSQL..."
  sudo systemctl stop postgresql@14-main
  docker compose up
fi

