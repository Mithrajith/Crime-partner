#!/bin/bash

# Quiz Partner - Secure Installation Script

echo "🔧 Setting up Quiz Partner with Security Improvements..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install updated requirements
echo "📥 Installing updated dependencies..."
pip install -r requirements_updated.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env
    echo "🔑 Please edit .env file with your secure settings!"
fi

# Set secure permissions on uploads directory
echo "🔒 Setting secure permissions..."
chmod 755 uploads/
chmod 644 uploads/*

echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit .env file with your secure SECRET_KEY"
echo "2. Review SECURITY_IMPROVEMENTS.md for remaining issues"
echo "3. Run: python app.py"
echo ""
echo "🚨 Remember to:"
echo "- Change SECRET_KEY in .env file"
echo "- Set FLASK_DEBUG=0 for production"
echo "- Implement user authentication before deployment"