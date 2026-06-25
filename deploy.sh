#!/bin/bash

# Ensure we are using the correct project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: No GCP project set."
  echo "Run: gcloud config set project YOUR_ID"
  exit 1
fi

echo "Building the Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/water-quality-ai

echo "Deploying to Google Cloud Run..."
gcloud run deploy water-quality-ai \
    --image gcr.io/$PROJECT_ID/water-quality-ai \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --concurrency 8 \
    --port 8080

echo "Deployment Complete!"
