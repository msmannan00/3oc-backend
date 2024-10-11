#!/bin/bash
docker-compose down

echo "Building Docker images..."
docker-compose build

# Step 2: Run the Docker containers
echo "Starting Docker containers..."
docker-compose up
