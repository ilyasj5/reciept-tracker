import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import functions_framework
from google.cloud import vision
from google.cloud import firestore
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel
from flask import jsonify


# Initialize clients
vision_client = vision.ImageAnnotatorClient()
db = firestore.Client()
storage_client = storage.Client()


@functions_framework.http
def process_receipt(request):
    """
    HTTP Cloud Function to process receipt images.
    Triggered when a new receipt is uploaded to Cloud Storage.
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json:
            return jsonify({'error': 'Invalid request'}), 400

        image_url = request_json.get('imageUrl')
        user_id = request_json.get('userId')

        if not image_url or not user_id:
            return jsonify({'error': 'Missing imageUrl or userId'}), 400

        # Extract text from receipt using Cloud Vision API
        extracted_text = extract_text_from_image(image_url)

        # Parse receipt data
        receipt_data = parse_receipt_text(extracted_text)

        # Categorize expense using Vertex AI
        category = categorize_expense(
            receipt_data.get('merchant_name', ''),
            receipt_data.get('line_items', [])
        )

        # Prepare receipt document
        receipt_doc = {
            'userId': user_id,
            'merchantName': receipt_data.get('merchant_name', 'Unknown'),
            'date': receipt_data.get('date', datetime.now().isoformat()),
            'totalAmount': receipt_data.get('total_amount', 0.0),
            'category': category,
            'lineItems': receipt_data.get('line_items', []),
            'imageUrl': image_url,
            'rawText': extracted_text,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
        }

        # Save to Firestore
        doc_ref = db.collection('receipts').add(receipt_doc)

        # Update budget tracking
        update_budget_spending(user_id, category, receipt_data.get('total_amount', 0.0))

        return jsonify({
            'success': True,
            'receiptId': doc_ref[1].id,
            'data': receipt_doc
        }), 200

    except Exception as e:
        print(f'Error processing receipt: {str(e)}')
        return jsonify({'error': str(e)}), 500


def extract_text_from_image(image_url: str) -> str:
    """
    Extract text from receipt image using Cloud Vision API.
    """
    try:
        # Create Image object from URL
        image = vision.Image()
        image.source.image_uri = image_url

        # Perform text detection
        response = vision_client.text_detection(image=image)
        texts = response.text_annotations

        if response.error.message:
            raise Exception(f'Vision API error: {response.error.message}')

        # Return full text
        if texts:
            return texts[0].description
        return ''

    except Exception as e:
        print(f'Error extracting text: {str(e)}')
        raise


def parse_receipt_text(text: str) -> Dict:
    """
    Parse extracted text to identify key receipt information.
    """
    lines = text.split('\n')
    receipt_data = {
        'merchant_name': '',
        'date': None,
        'total_amount': 0.0,
        'line_items': []
    }

    # Extract merchant name (usually first line)
    if lines:
        receipt_data['merchant_name'] = lines[0].strip()

    # Extract date
    date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
    for line in lines:
        date_match = re.search(date_pattern, line)
        if date_match:
            receipt_data['date'] = date_match.group(0)
            break

    # Extract total amount
    total_patterns = [
        r'total[:\s]*\$?(\d+\.\d{2})',
        r'amount[:\s]*\$?(\d+\.\d{2})',
        r'balance[:\s]*\$?(\d+\.\d{2})',
    ]

    for pattern in total_patterns:
        for line in lines:
            match = re.search(pattern, line.lower())
            if match:
                receipt_data['total_amount'] = float(match.group(1))
                break
        if receipt_data['total_amount'] > 0:
            break

    # Extract line items (simplified)
    item_pattern = r'(.+?)\s+\$?(\d+\.\d{2})'
    for line in lines:
        match = re.search(item_pattern, line)
        if match and 'total' not in line.lower():
            try:
                item_name = match.group(1).strip()
                item_price = float(match.group(2))
                receipt_data['line_items'].append({
                    'description': item_name,
                    'quantity': 1,
                    'price': item_price,
                    'amount': item_price
                })
            except ValueError:
                continue

    return receipt_data


def categorize_expense(merchant_name: str, line_items: List[Dict]) -> str:
    """
    Categorize expense using Vertex AI Gemini.
    Falls back to rule-based categorization if AI fails.
    """
    try:
        # Initialize Vertex AI
        project_id = os.environ.get('GCP_PROJECT')
        location = os.environ.get('GCP_REGION', 'us-central1')

        vertexai.init(project=project_id, location=location)
        model = GenerativeModel('gemini-pro')

        # Create prompt
        items_text = ', '.join([item.get('description', '') for item in line_items[:5]])
        prompt = f"""
        Categorize this expense into ONE of these categories:
        - Food & Dining
        - Groceries
        - Transportation
        - Entertainment
        - Shopping
        - Healthcare
        - Utilities
        - Travel
        - Other

        Merchant: {merchant_name}
        Items: {items_text}

        Respond with ONLY the category name, nothing else.
        """

        response = model.generate_content(prompt)
        category = response.text.strip()

        # Validate category
        valid_categories = [
            'Food & Dining', 'Groceries', 'Transportation', 'Entertainment',
            'Shopping', 'Healthcare', 'Utilities', 'Travel', 'Other'
        ]

        if category in valid_categories:
            return category

    except Exception as e:
        print(f'Vertex AI categorization failed: {str(e)}')

    # Fallback to rule-based categorization
    return rule_based_categorization(merchant_name, line_items)


def rule_based_categorization(merchant_name: str, line_items: List[Dict]) -> str:
    """
    Simple rule-based categorization as fallback.
    """
    merchant_lower = merchant_name.lower()

    # Food & Dining keywords
    if any(word in merchant_lower for word in ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'sushi']):
        return 'Food & Dining'

    # Groceries keywords
    if any(word in merchant_lower for word in ['market', 'grocery', 'supermarket', 'whole foods', 'trader']):
        return 'Groceries'

    # Transportation keywords
    if any(word in merchant_lower for word in ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'parking']):
        return 'Transportation'

    # Entertainment keywords
    if any(word in merchant_lower for word in ['cinema', 'theater', 'movie', 'game', 'concert']):
        return 'Entertainment'

    # Shopping keywords
    if any(word in merchant_lower for word in ['store', 'shop', 'mall', 'amazon', 'target', 'walmart']):
        return 'Shopping'

    # Healthcare keywords
    if any(word in merchant_lower for word in ['pharmacy', 'hospital', 'clinic', 'medical', 'doctor']):
        return 'Healthcare'

    # Utilities keywords
    if any(word in merchant_lower for word in ['electric', 'water', 'internet', 'phone', 'utility']):
        return 'Utilities'

    # Travel keywords
    if any(word in merchant_lower for word in ['hotel', 'airline', 'flight', 'travel', 'airbnb']):
        return 'Travel'

    return 'Other'


def update_budget_spending(user_id: str, category: str, amount: float):
    """
    Update budget tracking for the user and category.
    """
    try:
        # Query for existing budget
        budgets_ref = db.collection('budgets')
        query = budgets_ref.where('userId', '==', user_id).where('category', '==', category)
        results = query.get()

        if results:
            # Update existing budget
            for doc in results:
                budget_ref = db.collection('budgets').document(doc.id)
                budget_ref.update({
                    'currentSpending': firestore.Increment(amount),
                    'updatedAt': firestore.SERVER_TIMESTAMP
                })
        else:
            # Create new budget with default limit
            db.collection('budgets').add({
                'userId': user_id,
                'category': category,
                'monthlyLimit': 1000.0,  # Default limit
                'currentSpending': amount,
                'alertThreshold': 80,  # Alert at 80%
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })

    except Exception as e:
        print(f'Error updating budget: {str(e)}')


@functions_framework.cloud_event
def on_receipt_upload(cloud_event):
    """
    Triggered by Cloud Storage when a new receipt is uploaded.
    Background Cloud Function.
    """
    try:
        data = cloud_event.data

        bucket_name = data['bucket']
        file_name = data['name']

        # Only process files in receipts/ folder
        if not file_name.startswith('receipts/'):
            return

        # Extract user ID from path: receipts/{userId}/{filename}
        path_parts = file_name.split('/')
        if len(path_parts) < 3:
            return

        user_id = path_parts[1]

        # Get public URL
        image_url = f'https://storage.googleapis.com/{bucket_name}/{file_name}'

        # Process the receipt
        extracted_text = extract_text_from_image(image_url)
        receipt_data = parse_receipt_text(extracted_text)
        category = categorize_expense(
            receipt_data.get('merchant_name', ''),
            receipt_data.get('line_items', [])
        )

        # Save to Firestore
        receipt_doc = {
            'userId': user_id,
            'merchantName': receipt_data.get('merchant_name', 'Unknown'),
            'date': receipt_data.get('date', datetime.now().isoformat()),
            'totalAmount': receipt_data.get('total_amount', 0.0),
            'category': category,
            'lineItems': receipt_data.get('line_items', []),
            'imageUrl': image_url,
            'rawText': extracted_text,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
        }

        db.collection('receipts').add(receipt_doc)
        update_budget_spending(user_id, category, receipt_data.get('total_amount', 0.0))

        print(f'Successfully processed receipt: {file_name}')

    except Exception as e:
        print(f'Error in on_receipt_upload: {str(e)}')
