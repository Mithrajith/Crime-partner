#!/bin/bash

# Quiz Partner - Development Startup Script
echo "🎯 Starting Quiz Partner in Development Mode..."

# Activate virtual environment
source .venv/bin/activate

# Start the application with Flask development server
echo "🔧 Starting Quiz Partner on http://localhost:5000"
echo "🐛 Debug mode enabled"
echo "⏹️  Press Ctrl+C to stop"

python app.py
