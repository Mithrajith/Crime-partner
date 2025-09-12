#!/bin/bash

# Quiz Partner - Production Startup Script
echo "🎯 Starting Quiz Partner in Production Mode..."

# Activate virtual environment
source .venv/bin/activate

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "📦 Installing gunicorn..."
    pip install gunicorn
fi

# Start the application with gunicorn
echo "🚀 Starting Quiz Partner on http://0.0.0.0:8000"
echo "📊 Using 4 worker processes"
echo "⏹️  Press Ctrl+C to stop"

gunicorn app:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile - \
    --error-logfile -
