#!/bin/bash

# This script will build and run the Docker containers for the Django project

# Step 1: Build the Docker images
echo "Building Docker images..."
docker-compose build

# Step 2: Run the Docker containers
echo "Starting Docker containers..."
docker-compose up

# Optional: To run migrations automatically after the containers are up
# Uncomment the following line if you want to run migrations automatically
# echo "Running migrations..."
# docker-compose exec web python manage.py migrate

# Optional: To run tests automatically after the containers are up
# Uncomment the following line if you want to run tests automatically
# echo "Running tests..."
# docker-compose exec web python manage.py test
