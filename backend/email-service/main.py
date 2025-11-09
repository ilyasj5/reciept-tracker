import os
from datetime import datetime, timedelta
from typing import Dict, List
import functions_framework
from google.cloud import firestore
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import jsonify


# Initialize Firestore client
db = firestore.Client()


@functions_framework.http
def send_weekly_summary(request):
    """
    HTTP Cloud Function to send weekly spending summaries.
    Triggered by Cloud Scheduler every week.
    """
    try:
        # Get all users
        users_ref = db.collection('users')
        users = users_ref.get()

        sent_count = 0
        for user_doc in users:
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            user_email = user_data.get('email')

            if not user_email:
                continue

            # Generate weekly summary
            summary = generate_weekly_summary(user_id)

            # Send email
            if summary and send_email(user_email, summary):
                sent_count += 1

        return jsonify({
            'success': True,
            'emailsSent': sent_count
        }), 200

    except Exception as e:
        print(f'Error sending weekly summaries: {str(e)}')
        return jsonify({'error': str(e)}), 500


def generate_weekly_summary(user_id: str) -> Dict:
    """
    Generate weekly spending summary for a user.
    """
    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Query receipts from last week
        receipts_ref = db.collection('receipts')
        query = receipts_ref.where('userId', '==', user_id).where(
            'createdAt', '>=', start_date
        ).where('createdAt', '<=', end_date)

        receipts = query.get()

        if not receipts:
            return None

        # Calculate statistics
        total_spending = 0.0
        category_spending = {}
        transaction_count = 0

        for receipt_doc in receipts:
            receipt = receipt_doc.to_dict()
            amount = receipt.get('totalAmount', 0.0)
            category = receipt.get('category', 'Other')

            total_spending += amount
            transaction_count += 1

            if category in category_spending:
                category_spending[category]['amount'] += amount
                category_spending[category]['count'] += 1
            else:
                category_spending[category] = {
                    'amount': amount,
                    'count': 1
                }

        # Sort categories by spending
        sorted_categories = sorted(
            category_spending.items(),
            key=lambda x: x[1]['amount'],
            reverse=True
        )

        return {
            'total_spending': total_spending,
            'transaction_count': transaction_count,
            'category_breakdown': sorted_categories,
            'period': {
                'start': start_date.strftime('%B %d, %Y'),
                'end': end_date.strftime('%B %d, %Y')
            }
        }

    except Exception as e:
        print(f'Error generating summary: {str(e)}')
        return None


def send_email(to_email: str, summary: Dict) -> bool:
    """
    Send email using SendGrid.
    """
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            print('SendGrid API key not configured')
            return False

        # Create email content
        subject = f"Your Weekly Spending Summary - ${summary['total_spending']:.2f}"

        # Build HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f7fafc; padding: 30px; }}
                .summary-card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .total {{ font-size: 36px; font-weight: bold; color: #667eea; }}
                .category {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }}
                .category:last-child {{ border-bottom: none; }}
                .category-name {{ font-weight: 600; }}
                .category-amount {{ color: #667eea; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #718096; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Weekly Spending Summary</h1>
                    <p>{summary['period']['start']} - {summary['period']['end']}</p>
                </div>
                <div class="content">
                    <div class="summary-card">
                        <h2>Total Spending</h2>
                        <div class="total">${summary['total_spending']:.2f}</div>
                        <p>{summary['transaction_count']} transactions this week</p>
                    </div>

                    <div class="summary-card">
                        <h2>Spending by Category</h2>
        """

        # Add category breakdown
        for category, data in summary['category_breakdown']:
            percentage = (data['amount'] / summary['total_spending']) * 100
            html_content += f"""
                        <div class="category">
                            <span class="category-name">{category}</span>
                            <span class="category-amount">${data['amount']:.2f} ({percentage:.1f}%)</span>
                        </div>
            """

        html_content += """
                    </div>

                    <div class="summary-card">
                        <h3>Keep tracking your expenses!</h3>
                        <p>Visit your dashboard to see detailed analytics and set budget goals.</p>
                        <a href="https://your-app-url.com" style="display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 10px;">View Dashboard</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated email from AI Expense Tracker</p>
                    <p>To stop receiving these emails, update your preferences in settings</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create and send email
        message = Mail(
            from_email=Email('noreply@expense-tracker.com'),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content('text/html', html_content)
        )

        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)

        print(f'Email sent to {to_email}: {response.status_code}')
        return response.status_code == 202

    except Exception as e:
        print(f'Error sending email: {str(e)}')
        return False


@functions_framework.http
def test_email(request):
    """
    Test endpoint for email functionality.
    """
    try:
        request_json = request.get_json(silent=True)
        if not request_json or 'email' not in request_json:
            return jsonify({'error': 'Email required'}), 400

        test_summary = {
            'total_spending': 567.89,
            'transaction_count': 15,
            'category_breakdown': [
                ('Groceries', {'amount': 234.50, 'count': 5}),
                ('Food & Dining', {'amount': 189.30, 'count': 6}),
                ('Transportation', {'amount': 89.09, 'count': 3}),
                ('Entertainment', {'amount': 55.00, 'count': 1}),
            ],
            'period': {
                'start': 'November 2, 2025',
                'end': 'November 9, 2025'
            }
        }

        success = send_email(request_json['email'], test_summary)

        return jsonify({
            'success': success,
            'message': 'Test email sent' if success else 'Failed to send email'
        }), 200 if success else 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
