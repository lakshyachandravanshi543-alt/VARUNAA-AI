# Use the official Python image
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Command to run on container start
# 1 worker, multiple threads because the backend requires a shared internal simulation memory state.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
