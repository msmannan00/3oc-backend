# Use Python 3.12 as the base image
FROM python:3.12

# Set the working directory in the container
WORKDIR /user/src/app

# Copy the current directory contents into the container
COPY . .

# Ensure all packages are up-to-date, including certifi, and install dependencies from requirements.txt
RUN pip install --upgrade pip certifi && \
    pip install --no-cache-dir -r requirements.txt

# Expose the application on port 8000
EXPOSE 8000

# Define the command to run the application
CMD ["python", "run.py"]
