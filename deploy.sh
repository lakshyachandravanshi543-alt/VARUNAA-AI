#!/bin/bash

# Ensure we are using the correct project
gcloud config set project test121-493806

echo "Building the Docker image..."
gcloud builds submit --tag gcr.io/test121-493806/water-quality-ai

echo "Deploying to Google Cloud Run..."
gcloud run deploy water-quality-ai \
    --image gcr.io/test121-493806/water-quality-ai \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --concurrency 8 \
    --port 8080

echo "Deployment Complete!"
