# Quick Start Guide

You've already configured your GCP project! Here are the next steps to get your expense tracker running:

## Your Configuration

- **GCP Project**: tracker045
- **Account**: ilyasjaghoori5@gmail.com

## Step 1: Get Firebase Configuration

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (tracker045) or create a Firebase project
3. Go to Project Settings (gear icon) > General
4. Scroll to "Your apps" > Add a web app (or select existing)
5. Copy the Firebase configuration

## Step 2: Configure Environment Variables

Create `frontend/.env.local` with your Firebase config:

```bash
cd frontend
cat > .env.local << 'EOF'
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=tracker045.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=tracker045
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=tracker045.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
EOF
cd ..
```

## Step 3: Install Dependencies

```bash
# Install frontend dependencies
cd frontend
npm install
cd ..

# Optional: Set up Python virtual environments for backend
cd backend/functions
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..
```

## Step 4: Enable Required GCP APIs

```bash
# Make sure you're using the correct project
gcloud config set project tracker045

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Step 5: Initialize Firebase

```bash
# Login to Firebase
firebase login

# Initialize Firebase (select Hosting, Firestore, Storage)
firebase init
```

When prompted:
- Select "Use an existing project" > tracker045
- Hosting public directory: `frontend/out`
- Configure as single-page app: Yes
- Firestore rules: `firestore.rules`
- Firestore indexes: `firestore.indexes.json`
- Storage rules: `storage.rules`

## Step 6: Set Up Firebase Authentication

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select tracker045
3. Go to Authentication > Sign-in method
4. Enable:
   - Email/Password
   - Google

## Step 7: Get SendGrid API Key (Optional for emails)

1. Sign up at [SendGrid](https://sendgrid.com)
2. Create an API key
3. Add to environment:

```bash
export SENDGRID_API_KEY="your_sendgrid_api_key"
```

## Step 8: Run Development Server

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000

## Step 9: Deploy to Production (When Ready)

### Option A: Use Deploy Script

```bash
export GCP_PROJECT=tracker045
export SENDGRID_API_KEY=your_key_here  # optional
./scripts/deploy.sh
```

### Option B: Manual Deployment

```bash
# Build and deploy frontend
cd frontend
npm run build
firebase deploy --only hosting

# Deploy Firestore rules
firebase deploy --only firestore

# Deploy Storage rules
firebase deploy --only storage

# Deploy Cloud Functions
gcloud functions deploy process_receipt \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=backend/functions \
  --entry-point=process_receipt \
  --trigger-http \
  --allow-unauthenticated
```

## Common Issues

### gcloud not in PATH
If gcloud commands don't work, add to your shell profile:

```bash
# For bash
echo 'source ~/google-cloud-sdk/path.bash.inc' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'source ~/google-cloud-sdk/path.zsh.inc' >> ~/.zshrc
source ~/.zshrc
```

### Firebase init fails
Make sure you're logged in:
```bash
firebase logout
firebase login
```

## Need Help?

See the detailed guides:
- `README.md` - Complete documentation
- `docs/DEPLOYMENT.md` - Detailed deployment instructions
- `docs/ARCHITECTURE.md` - System architecture

## Testing the Application

1. Sign up with a test account
2. Upload a test receipt image
3. View the dashboard to see extracted data
4. Check Firestore console to verify data storage
