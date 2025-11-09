# Deployment Guide

Complete guide for deploying the AI Expense Tracker to Google Cloud Platform.

## Prerequisites Checklist

- [ ] Google Cloud Platform account with billing enabled
- [ ] GCP Project created
- [ ] Firebase project linked to GCP project
- [ ] gcloud CLI installed and authenticated
- [ ] Firebase CLI installed
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] SendGrid account (for email functionality)

## Step-by-Step Deployment

### Step 1: GCP Project Setup

```bash
# Set your project ID
export GCP_PROJECT="your-project-id"

# Set the project
gcloud config set project $GCP_PROJECT

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Step 2: Firebase Setup

```bash
# Login to Firebase
firebase login

# Initialize Firebase in your project
firebase init

# Select:
# ✓ Hosting
# ✓ Firestore
# ✓ Storage

# Follow the prompts:
# - Use existing project: Select your GCP project
# - Firestore rules: firestore.rules
# - Firestore indexes: firestore.indexes.json
# - Hosting public directory: frontend/out
# - Storage rules: storage.rules
```

### Step 3: Configure Firebase Authentication

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Navigate to Authentication > Sign-in method
4. Enable the following providers:
   - Email/Password
   - Google
5. Add authorized domains for your app

### Step 4: Get Firebase Configuration

1. Go to Project Settings > General
2. Scroll to "Your apps" section
3. Click on the web app (or add one if none exists)
4. Copy the Firebase configuration

### Step 5: Configure Environment Variables

#### Frontend Environment

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123
```

#### Backend Environment

Set environment variables:

```bash
export GCP_PROJECT="your-project-id"
export GCP_REGION="us-central1"
export SENDGRID_API_KEY="SG.xxx..."
```

### Step 6: Deploy Infrastructure (Terraform)

```bash
cd terraform

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the infrastructure
terraform apply

# Confirm with: yes
```

This creates:
- Firestore database
- Cloud Storage bucket
- Service accounts
- IAM roles
- Cloud Scheduler job

### Step 7: Build Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Verify build
ls -la out/
```

### Step 8: Deploy Frontend to Firebase Hosting

```bash
# Deploy from project root
firebase deploy --only hosting

# Note the hosting URL
# Your app is now live at: https://{project-id}.web.app
```

### Step 9: Deploy Firestore Rules and Indexes

```bash
# Deploy security rules
firebase deploy --only firestore:rules

# Deploy indexes
firebase deploy --only firestore:indexes

# This may take a few minutes to build indexes
```

### Step 10: Deploy Storage Rules

```bash
firebase deploy --only storage
```

### Step 11: Deploy Cloud Functions

#### Receipt Processing Function

```bash
gcloud functions deploy process_receipt \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=backend/functions \
  --entry-point=process_receipt \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars=GCP_PROJECT=$GCP_PROJECT,GCP_REGION=us-central1 \
  --memory=512MB \
  --timeout=120s
```

#### Storage Trigger Function

```bash
gcloud functions deploy on_receipt_upload \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=backend/functions \
  --entry-point=on_receipt_upload \
  --trigger-bucket=${GCP_PROJECT}.appspot.com \
  --set-env-vars=GCP_PROJECT=$GCP_PROJECT,GCP_REGION=us-central1 \
  --memory=512MB \
  --timeout=120s
```

#### Email Service Function

```bash
gcloud functions deploy send_weekly_summary \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=backend/email-service \
  --entry-point=send_weekly_summary \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars=SENDGRID_API_KEY=$SENDGRID_API_KEY \
  --memory=256MB \
  --timeout=60s
```

### Step 12: Set Up Cloud Scheduler

```bash
# Create the scheduler job
gcloud scheduler jobs create http weekly-expense-summary \
  --location=us-central1 \
  --schedule="0 9 * * 1" \
  --uri="https://us-central1-${GCP_PROJECT}.cloudfunctions.net/send_weekly_summary" \
  --http-method=GET \
  --time-zone="America/New_York" \
  --description="Send weekly expense summaries every Monday at 9 AM"

# Verify the job was created
gcloud scheduler jobs list --location=us-central1
```

### Step 13: Verify Deployment

#### Test Frontend

Visit: `https://{project-id}.web.app`

#### Test Authentication

1. Sign up with a new account
2. Verify email confirmation (if enabled)
3. Log in successfully

#### Test Receipt Upload

1. Navigate to Upload Receipt tab
2. Upload a test receipt image
3. Wait for processing
4. Check dashboard for new receipt

#### Test Cloud Functions

```bash
# View function logs
gcloud functions logs read process_receipt --limit=50

# Test receipt processing
curl -X POST \
  https://us-central1-${GCP_PROJECT}.cloudfunctions.net/process_receipt \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "gs://{bucket}/test-receipt.jpg",
    "userId": "test-user-id"
  }'
```

#### Test Email Function

```bash
# Test email
curl -X POST \
  https://us-central1-${GCP_PROJECT}.cloudfunctions.net/test_email \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com"}'
```

## Automated Deployment (Cloud Build)

### Set Up Cloud Build Trigger

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click "Create Trigger"
3. Configure:
   - **Name**: deploy-expense-tracker
   - **Event**: Push to branch
   - **Source**: Connect your repository
   - **Branch**: main
   - **Configuration**: cloudbuild.yaml
4. Add substitution variables:
   - `_SENDGRID_API_KEY`: Your SendGrid API key
5. Save the trigger

### Manual Deployment via Cloud Build

```bash
# Submit build manually
gcloud builds submit --config cloudbuild.yaml

# Monitor build progress
gcloud builds list --limit=5
```

## Environment-Specific Deployments

### Development Environment

```bash
# Use separate Firebase project
firebase use development

# Deploy with development settings
firebase deploy --only hosting
```

### Staging Environment

```bash
firebase use staging
npm run build:staging
firebase deploy
```

### Production Environment

```bash
firebase use production
npm run build:production
firebase deploy
```

## Rollback Procedures

### Rollback Frontend

```bash
# List hosting releases
firebase hosting:releases:list

# Rollback to previous version
firebase hosting:rollback
```

### Rollback Cloud Functions

```bash
# List function versions
gcloud functions list

# Deploy previous version
gcloud functions deploy FUNCTION_NAME --source=PATH_TO_OLD_VERSION
```

### Rollback Firestore Rules

```bash
# Get release history
firebase firestore:releases:list

# Rollback to specific version
firebase firestore:release RELEASE_NAME
```

## Post-Deployment Tasks

### 1. Configure Domain (Optional)

```bash
# Add custom domain in Firebase Console
# Hosting > Add custom domain
# Follow DNS configuration instructions
```

### 2. Set Up Monitoring

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime checks
gcloud monitoring uptime create https-check \
  --resource-type=uptime-url \
  --host=https://${GCP_PROJECT}.web.app
```

### 3. Configure Alerts

1. Go to Cloud Monitoring
2. Create alert policies for:
   - Cloud Function errors
   - High latency
   - Budget thresholds

### 4. Backup Configuration

```bash
# Export Firestore data
gcloud firestore export gs://${GCP_PROJECT}-backups

# Schedule regular backups
gcloud scheduler jobs create http firestore-backup \
  --schedule="0 2 * * *" \
  --uri="https://firestore.googleapis.com/v1/projects/${GCP_PROJECT}/databases/(default):exportDocuments" \
  --message-body='{"outputUriPrefix":"gs://'${GCP_PROJECT}'-backups"}' \
  --oauth-service-account-email="${GCP_PROJECT}@appspot.gserviceaccount.com"
```

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds log BUILD_ID

# Common issues:
# - Missing environment variables
# - Insufficient permissions
# - API not enabled
```

### Function Deployment Fails

```bash
# Check function logs
gcloud functions logs read FUNCTION_NAME

# Common issues:
# - Timeout too short
# - Memory too low
# - Missing dependencies in requirements.txt
```

### Frontend Not Loading

```bash
# Check hosting status
firebase hosting:channel:list

# Redeploy
firebase deploy --only hosting --force
```

## Maintenance

### Update Dependencies

```bash
# Frontend
cd frontend
npm update
npm audit fix

# Backend
cd backend/functions
pip install --upgrade -r requirements.txt
```

### Monitor Costs

```bash
# View billing
gcloud billing accounts list
gcloud billing projects describe $GCP_PROJECT
```

### Scale Functions

```bash
# Increase memory/timeout if needed
gcloud functions deploy FUNCTION_NAME \
  --memory=1024MB \
  --timeout=300s
```

## Security Checklist

- [ ] Firestore rules deployed and tested
- [ ] Storage rules deployed and tested
- [ ] API keys stored as environment variables (not in code)
- [ ] Service account has minimal required permissions
- [ ] HTTPS only (Firebase Hosting default)
- [ ] Authentication enabled and tested
- [ ] CORS configured properly
- [ ] Regular security audits scheduled

## Support

If you encounter issues:

1. Check logs: `gcloud functions logs read FUNCTION_NAME`
2. Review documentation
3. Check GCP Status: https://status.cloud.google.com/
4. Open GitHub issue
