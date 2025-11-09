#!/bin/bash

# AI Expense Tracker Deployment Script
# This script deploys the entire application to GCP

set -e

echo "🚀 Starting deployment of AI Expense Tracker..."

# Check if required environment variables are set
if [ -z "$GCP_PROJECT" ]; then
    echo "❌ Error: GCP_PROJECT environment variable is not set"
    exit 1
fi

# Set the project
gcloud config set project $GCP_PROJECT

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Deploy to Firebase Hosting
echo "🌐 Deploying to Firebase Hosting..."
firebase deploy --only hosting

# Deploy Firestore rules and indexes
echo "🔒 Deploying Firestore rules and indexes..."
firebase deploy --only firestore

# Deploy Storage rules
echo "📦 Deploying Storage rules..."
firebase deploy --only storage

# Deploy Cloud Functions
echo "☁️  Deploying Cloud Functions..."

# Deploy receipt processing function
gcloud functions deploy process_receipt \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --entry-point process_receipt \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,GCP_REGION=us-central1 \
  --source backend/functions

# Deploy storage trigger function
gcloud functions deploy on_receipt_upload \
  --runtime python311 \
  --trigger-event google.storage.object.finalize \
  --trigger-resource ${GCP_PROJECT}.appspot.com \
  --region us-central1 \
  --entry-point on_receipt_upload \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,GCP_REGION=us-central1 \
  --source backend/functions

# Deploy email function
if [ -n "$SENDGRID_API_KEY" ]; then
    gcloud functions deploy send_weekly_summary \
      --runtime python311 \
      --trigger-http \
      --allow-unauthenticated \
      --region us-central1 \
      --entry-point send_weekly_summary \
      --set-env-vars SENDGRID_API_KEY=$SENDGRID_API_KEY \
      --source backend/email-service

    echo "📧 Setting up Cloud Scheduler..."
    gcloud scheduler jobs create http weekly-expense-summary \
      --location us-central1 \
      --schedule "0 9 * * 1" \
      --uri "https://us-central1-${GCP_PROJECT}.cloudfunctions.net/send_weekly_summary" \
      --http-method GET \
      --time-zone "America/New_York" \
      --description "Send weekly expense summaries every Monday at 9 AM" \
      || echo "Scheduler job already exists"
else
    echo "⚠️  Warning: SENDGRID_API_KEY not set, skipping email function deployment"
fi

echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Your app is now live at:"
echo "   https://${GCP_PROJECT}.web.app"
echo ""
echo "📝 Next steps:"
echo "   1. Configure Firebase Authentication"
echo "   2. Test receipt upload functionality"
echo "   3. Set up budget alerts"
