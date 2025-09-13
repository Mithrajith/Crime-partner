#!/bin/bash

# Crime Partner - Development Startup Script
echo "🎯 Starting Crime Partner in Development Mode..."

# Activate virtual environment
source .venv/bin/activate

# Start the application with Flask development server
echo "🔧 Starting Crime Partner on http://localhost:5000"
echo "🐛 Debug mode enabled"
echo "⏹️  Press Ctrl+C to stop"

python app.py
