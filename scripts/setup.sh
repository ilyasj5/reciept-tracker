#!/bin/bash

# AI Expense Tracker Setup Script
# This script sets up the local development environment

set -e

echo "🛠️  Setting up AI Expense Tracker development environment..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or later."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

# Check if gcloud is installed (warning only)
if ! command -v gcloud &> /dev/null; then
    echo "⚠️  Warning: gcloud not found in PATH. If you have it installed, you may need to:"
    echo "   - Add gcloud to your PATH"
    echo "   - Run: source ~/.bashrc or source ~/.zshrc"
    echo "   - Or install from: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "Continuing setup..."
else
    echo "✓ Google Cloud SDK found"
fi

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "📦 Installing Firebase CLI..."
    npm install -g firebase-tools
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend/functions
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

cd backend/email-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your configuration values"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "📝 Creating frontend/.env.local file from template..."
    cp frontend/.env.local.example frontend/.env.local
    echo "⚠️  Please edit frontend/.env.local and add your Firebase configuration"
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env and frontend/.env.local with your configuration"
echo "   2. Initialize Firebase: firebase login && firebase init"
echo "   3. Deploy infrastructure: cd terraform && terraform init && terraform apply"
echo "   4. Start development server: npm run dev"
echo ""
echo "📚 For detailed instructions, see README.md"
