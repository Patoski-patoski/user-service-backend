#!/bin/bash
# This script is used to start Docker containers using docker-compose.
# Ensure the script is run from the directory containing the docker-compose.yml file
if docker compose up ; then
  echo "Docker containers started successfully."
else
  echo "Stopping local PostgreSQL..."
  sudo systemctl stop postgresql@14-main
  docker compose up
fi

