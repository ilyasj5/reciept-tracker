# AI-Powered Expense Tracker

A full-stack, cloud-native expense tracking application that leverages Google Cloud Platform services to automatically scan and categorize receipts using AI.

## Features

- **AI-Powered Receipt Scanning**: Upload receipt images and automatically extract merchant name, date, amount, and line items using Cloud Vision API
- **Smart Categorization**: Expenses are intelligently categorized using Vertex AI (Gemini) with fallback to rule-based categorization
- **Real-time Dashboard**: View spending analytics, monthly trends with charts, and budget alerts
- **Budget Management**: Set budget limits by category and receive alerts when approaching limits
- **Weekly Email Summaries**: Automated weekly spending reports delivered via SendGrid
- **Secure Authentication**: Firebase Authentication with Google Sign-In and email/password
- **Cloud-Native Architecture**: Fully serverless deployment on Google Cloud Platform

## Architecture

### Frontend
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Charts**: Recharts
- **Hosting**: Firebase Hosting
- **Language**: TypeScript

### Backend
- **Cloud Functions**: Python 3.11
  - Receipt processing with Cloud Vision API
  - Expense categorization with Vertex AI
  - Weekly email summaries with SendGrid
- **Database**: Cloud Firestore (NoSQL)
- **Storage**: Cloud Storage for receipt images
- **Authentication**: Firebase Authentication
- **Scheduling**: Cloud Scheduler for automated emails
- **CI/CD**: Cloud Build

### Google Cloud Services Used
- Cloud Vision API (OCR)
- Vertex AI (Gemini for categorization)
- Cloud Functions
- Cloud Firestore
- Cloud Storage
- Cloud Scheduler
- Cloud Build
- Firebase Hosting
- Firebase Authentication

## Project Structure

```
reciept-tracker/
├── frontend/                  # Next.js frontend application
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   ├── components/       # React components
│   │   ├── lib/              # Firebase configuration
│   │   ├── store/            # Zustand state management
│   │   └── types/            # TypeScript types
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── backend/
│   ├── functions/            # Cloud Functions for receipt processing
│   │   ├── main.py
│   │   └── requirements.txt
│   └── email-service/        # Cloud Functions for email summaries
│       ├── main.py
│       └── requirements.txt
├── terraform/                # Infrastructure as Code
│   ├── main.tf
│   └── terraform.tfvars.example
├── scripts/                  # Deployment scripts
│   ├── setup.sh
│   └── deploy.sh
├── firebase.json            # Firebase configuration
├── firestore.rules          # Firestore security rules
├── firestore.indexes.json   # Firestore indexes
├── storage.rules            # Cloud Storage security rules
├── cloudbuild.yaml          # Cloud Build CI/CD configuration
└── README.md
```

## Prerequisites

- **Node.js** 18 or later
- **Python** 3.11 or later
- **Google Cloud SDK** (gcloud CLI)
- **Firebase CLI**
- **Terraform** (optional, for infrastructure deployment)
- **GCP Project** with billing enabled
- **SendGrid Account** (for email functionality)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd reciept-tracker
```

### 2. Run Setup Script

```bash
./scripts/setup.sh
```

This script will:
- Install Node.js and Python dependencies
- Create environment files from templates
- Set up Python virtual environments

### 3. Configure Environment Variables

#### Frontend Configuration

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

#### Backend Configuration

Edit `.env`:

```env
GCP_PROJECT=your-gcp-project-id
GCP_REGION=us-central1
SENDGRID_API_KEY=your_sendgrid_api_key
```

### 4. Initialize Firebase

```bash
# Login to Firebase
firebase login

# Initialize Firebase project
firebase init

# Select:
# - Hosting
# - Firestore
# - Storage
```

### 5. Deploy Infrastructure with Terraform (Optional)

```bash
cd terraform

# Copy and edit terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the infrastructure
terraform apply
```

This will:
- Enable required GCP APIs
- Create Firestore database
- Create Cloud Storage bucket
- Set up Cloud Scheduler
- Configure IAM permissions

### 6. Deploy the Application

```bash
# Set environment variables
export GCP_PROJECT=your-gcp-project-id
export SENDGRID_API_KEY=your-sendgrid-api-key

# Run deployment script
./scripts/deploy.sh
```

Or deploy manually:

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
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --entry-point process_receipt \
  --source backend/functions

gcloud functions deploy on_receipt_upload \
  --runtime python311 \
  --trigger-event google.storage.object.finalize \
  --trigger-resource ${GCP_PROJECT}.appspot.com \
  --region us-central1 \
  --entry-point on_receipt_upload \
  --source backend/functions

gcloud functions deploy send_weekly_summary \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --entry-point send_weekly_summary \
  --source backend/email-service
```

## Development

### Run Frontend Locally

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000`

### Test Cloud Functions Locally

```bash
cd backend/functions
source venv/bin/activate
functions-framework --target=process_receipt --debug
```

### Run Tests

```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend/functions
python -m pytest
```

## Usage

### 1. Sign Up / Sign In

- Navigate to the application URL
- Sign in with Google or create an account with email/password

### 2. Upload Receipt

- Click on "Upload Receipt" tab
- Drag and drop or select a receipt image (PNG, JPG, JPEG, GIF)
- Wait for AI processing to complete
- Receipt data will appear in your dashboard

### 3. View Dashboard

- See recent receipts
- View spending by category (pie chart)
- Monitor budget alerts

### 4. Set Budgets

- Go to Settings
- Set monthly budget limits by category
- Configure alert thresholds (e.g., alert at 80% of limit)

### 5. Receive Weekly Summaries

- Automatically receive email summaries every Monday at 9 AM
- Contains total spending, category breakdown, and transaction count

## API Endpoints

### Receipt Processing

**Endpoint**: `https://us-central1-{project-id}.cloudfunctions.net/process_receipt`

**Method**: POST

**Body**:
```json
{
  "imageUrl": "https://storage.googleapis.com/...",
  "userId": "user123"
}
```

**Response**:
```json
{
  "success": true,
  "receiptId": "receipt123",
  "data": {
    "merchantName": "Starbucks",
    "date": "2025-11-09",
    "totalAmount": 12.50,
    "category": "Food & Dining",
    "lineItems": [...]
  }
}
```

### Weekly Email Summary

**Endpoint**: `https://us-central1-{project-id}.cloudfunctions.net/send_weekly_summary`

**Method**: GET

**Response**:
```json
{
  "success": true,
  "emailsSent": 15
}
```

## Security

### Firestore Rules

- Users can only read/write their own data
- All queries are filtered by userId
- Authenticated access required for all operations

### Storage Rules

- Users can only access receipts in their own folder
- Maximum file size: 10MB
- Only image files allowed
- Authenticated upload required

### Cloud Functions

- API endpoints are protected
- User authentication verified before processing
- Environment variables for sensitive data
- Service account with minimal required permissions

## Cost Estimation

### Monthly Costs (Approximate)

For 1,000 receipts/month:

- **Cloud Vision API**: ~$1.50
- **Vertex AI (Gemini)**: ~$2.00
- **Cloud Functions**: ~$0.50
- **Firestore**: ~$1.00
- **Cloud Storage**: ~$0.50
- **Firebase Hosting**: Free tier
- **SendGrid**: Free tier (up to 100 emails/day)

**Total**: ~$5.50/month

Costs scale with usage. Most GCP services have generous free tiers.

## Troubleshooting

### Receipt Upload Fails

- Check Cloud Storage bucket permissions
- Verify Cloud Function is deployed
- Check Cloud Vision API is enabled
- Review Cloud Function logs: `gcloud functions logs read process_receipt`

### Authentication Issues

- Verify Firebase configuration in `.env.local`
- Check Firebase Authentication is enabled in console
- Enable Google Sign-In provider if using Google auth

### Email Not Sending

- Verify SendGrid API key is set
- Check Cloud Scheduler job is active
- Review email function logs: `gcloud functions logs read send_weekly_summary`

### Deployment Errors

- Ensure all required APIs are enabled
- Check IAM permissions for Cloud Build service account
- Verify billing is enabled on GCP project

## CI/CD Pipeline

The project includes Cloud Build configuration for automated deployment:

1. Push code to main branch
2. Cloud Build triggers automatically
3. Builds frontend
4. Deploys to Firebase Hosting
5. Deploys Cloud Functions
6. Updates Firestore rules

### Trigger Cloud Build Manually

```bash
gcloud builds submit --config cloudbuild.yaml
```

## Performance Optimization

- Receipt images are automatically compressed
- Firestore indexes optimize common queries
- Cloud Functions use cold start optimization
- Frontend uses Next.js image optimization
- Caching headers for static assets

## Future Enhancements

- [ ] Mobile app (React Native)
- [ ] Receipt export to CSV/PDF
- [ ] Multi-currency support
- [ ] Receipt sharing between users
- [ ] Advanced analytics dashboard
- [ ] Integration with accounting software
- [ ] Recurring expense detection
- [ ] Tax category classification
- [ ] Receipt duplicate detection
- [ ] Voice-activated receipt entry

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: [Link to docs]
- Email: support@example.com

## Acknowledgments

- Google Cloud Platform for cloud services
- Firebase for authentication and hosting
- SendGrid for email delivery
- Anthropic Claude for AI assistance

---

Built with ❤️ using Google Cloud Platform
