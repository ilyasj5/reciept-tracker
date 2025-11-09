# Architecture Documentation

## System Architecture

The AI Expense Tracker is built as a cloud-native, serverless application using Google Cloud Platform services.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                   (Next.js + React + Tailwind)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ├─► Firebase Authentication
                         │   (Google Sign-In, Email/Password)
                         │
                         ├─► Firebase Hosting
                         │   (Static site hosting)
                         │
                         └─► Cloud Firestore
                             (Real-time database)
                             │
                             ├── /users/{userId}
                             ├── /receipts/{receiptId}
                             └── /budgets/{budgetId}

┌─────────────────────────────────────────────────────────────────┐
│                        Receipt Upload Flow                       │
└─────────────────────────────────────────────────────────────────┘

1. User uploads receipt image
   │
   ├─► Cloud Storage (receipts/{userId}/{filename})
   │   │
   │   └─► Cloud Function Trigger (on_receipt_upload)
   │       │
   │       ├─► Cloud Vision API
   │       │   └─► Text extraction (OCR)
   │       │
   │       ├─► Vertex AI (Gemini)
   │       │   └─► Expense categorization
   │       │
   │       └─► Cloud Firestore
   │           └─► Store receipt data


┌─────────────────────────────────────────────────────────────────┐
│                    Weekly Email Summary Flow                     │
└─────────────────────────────────────────────────────────────────┘

Cloud Scheduler (Every Monday 9 AM)
   │
   └─► Cloud Function (send_weekly_summary)
       │
       ├─► Cloud Firestore
       │   └─► Query receipts from last 7 days
       │
       └─► SendGrid API
           └─► Send email to users
```

## Component Details

### Frontend (Next.js)

**Technology Stack**:
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Zustand (state management)
- Recharts (data visualization)

**Key Components**:
- `Login.tsx`: Authentication UI
- `Dashboard.tsx`: Main application container
- `ReceiptUpload.tsx`: Drag-and-drop receipt upload
- `ReceiptList.tsx`: Display recent receipts
- `SpendingChart.tsx`: Category spending visualization
- `BudgetAlerts.tsx`: Budget threshold notifications

**State Management**:
```typescript
interface Store {
  receipts: Receipt[]
  budgets: Budget[]
  spendingSummary: SpendingSummary | null
  loading: boolean
  error: string | null
}
```

### Backend (Cloud Functions)

#### Receipt Processing Function

**Trigger**: HTTP / Storage Event
**Runtime**: Python 3.11
**Entry Point**: `process_receipt`, `on_receipt_upload`

**Flow**:
1. Receive image URL or storage event
2. Call Cloud Vision API for text extraction
3. Parse text to extract:
   - Merchant name
   - Date
   - Total amount
   - Line items
4. Categorize expense using Vertex AI
5. Store in Firestore
6. Update budget tracking

**Key Functions**:
- `extract_text_from_image()`: OCR processing
- `parse_receipt_text()`: Data extraction
- `categorize_expense()`: AI categorization
- `rule_based_categorization()`: Fallback logic
- `update_budget_spending()`: Budget tracking

#### Email Service Function

**Trigger**: Cloud Scheduler (Weekly)
**Runtime**: Python 3.11
**Entry Point**: `send_weekly_summary`

**Flow**:
1. Query all users from Firestore
2. For each user:
   - Calculate spending for last 7 days
   - Generate category breakdown
   - Create HTML email
   - Send via SendGrid

### Database (Cloud Firestore)

#### Collections

**users**:
```typescript
{
  id: string (auto-generated)
  email: string
  displayName: string
  photoURL: string
  createdAt: Timestamp
  settings: {
    emailNotifications: boolean
    currency: string
  }
}
```

**receipts**:
```typescript
{
  id: string (auto-generated)
  userId: string (indexed)
  merchantName: string
  date: string
  totalAmount: number
  category: string (indexed)
  lineItems: Array<{
    description: string
    quantity: number
    price: number
    amount: number
  }>
  imageUrl: string
  rawText: string
  createdAt: Timestamp (indexed)
  updatedAt: Timestamp
}
```

**budgets**:
```typescript
{
  id: string (auto-generated)
  userId: string (indexed)
  category: string (indexed)
  monthlyLimit: number
  currentSpending: number
  alertThreshold: number (percentage)
  createdAt: Timestamp
  updatedAt: Timestamp
}
```

#### Indexes

1. `receipts` by `userId` + `createdAt` (descending)
2. `receipts` by `userId` + `category` + `createdAt` (descending)
3. `budgets` by `userId` + `category`

### Storage (Cloud Storage)

**Bucket Structure**:
```
{project-id}.appspot.com/
└── receipts/
    └── {userId}/
        └── {timestamp}_{filename}
```

**Access Control**:
- User-specific folders
- Authenticated read/write only
- 10MB file size limit
- Image files only

### APIs and Services

#### Cloud Vision API

**Usage**: Text detection on receipt images

**Request**:
```python
image = vision.Image()
image.source.image_uri = image_url
response = vision_client.text_detection(image=image)
```

**Response**: Extracted text with bounding boxes

#### Vertex AI (Gemini)

**Usage**: Expense categorization

**Prompt**:
```
Categorize this expense into ONE of these categories:
- Food & Dining
- Groceries
- Transportation
...

Merchant: {merchant_name}
Items: {items_text}

Respond with ONLY the category name.
```

**Model**: `gemini-pro`

### Security

#### Authentication
- Firebase Authentication
- JWT tokens for API calls
- Session management

#### Authorization
- Firestore security rules
- User-scoped data access
- Service account for Cloud Functions

#### Data Protection
- HTTPS only
- Encrypted at rest (GCP default)
- Encrypted in transit
- No sensitive data in logs

### Scalability

**Horizontal Scaling**:
- Cloud Functions auto-scale
- Firestore scales automatically
- Cloud Storage handles any load

**Performance Optimization**:
- Firestore indexes for fast queries
- Image compression
- CDN for static assets (Firebase Hosting)
- Connection pooling

**Cost Optimization**:
- Pay-per-use pricing
- Free tiers for most services
- Lazy loading in frontend
- Efficient queries

### Monitoring and Logging

**Cloud Functions Logs**:
```bash
gcloud functions logs read process_receipt
gcloud functions logs read send_weekly_summary
```

**Firestore Metrics**:
- Document reads/writes
- Query performance
- Index usage

**Error Tracking**:
- Cloud Functions error logs
- Frontend error boundaries
- User feedback mechanism

### Disaster Recovery

**Backup Strategy**:
- Firestore automatic backups
- Cloud Storage versioning
- Code version control (Git)

**Recovery Procedures**:
1. Restore Firestore from backup
2. Redeploy Cloud Functions
3. Restore Storage bucket

### Future Architecture Improvements

1. **Caching Layer**: Redis for frequently accessed data
2. **Message Queue**: Pub/Sub for async processing
3. **Load Balancer**: For multiple regions
4. **CDN**: Cloud CDN for global performance
5. **Monitoring**: Cloud Monitoring + Alerting
6. **Data Warehouse**: BigQuery for analytics
