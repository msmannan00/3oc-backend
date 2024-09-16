# Use Python 3.11 slim-buster as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install system dependencies (if needed) and Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && \
    pip install --upgrade pip certifi && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y build-essential gcc libpq-dev && \
    apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Expose the application on port 8000
EXPOSE 8000

# Define the command to run the application
CMD ["python", "run.py"]
