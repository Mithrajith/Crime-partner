#!/bin/bash

# Quiz Partner - Production Startup Script with MongoDB
set -e

echo "🎯 Starting Quiz Partner with Gunicorn and MongoDB"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_color() {
    echo -e "${1}${2}${NC}"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_color $YELLOW "⚠️ .env file not found. Please create one with your MongoDB credentials."
    echo ""
    echo "Example .env file:"
    echo "MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
    echo "DATABASE_NAME=quiz_partner"
    echo "SECRET_KEY=your-secret-key"
    echo "PORT=5001"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

print_color $BLUE "🔧 Configuration:"
echo "  • Port: ${PORT:-5001}"
echo "  • Database: ${DATABASE_NAME:-quiz_partner}"
echo "  • MongoDB URI: ${MONGODB_URI:0:60}..."

# Test MongoDB connection
print_color $YELLOW "🔍 Testing MongoDB connection..."
.venv/bin/python -c "
import os
from pymongo import MongoClient
try:
    client = MongoClient(os.environ.get('MONGODB_URI'), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB connection successful!')
    client.close()
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    print_color $YELLOW "💡 Please check your MongoDB Atlas connection string and network access."
    exit 1
fi

print_color $GREEN "🚀 Starting Gunicorn server..."

# Start Gunicorn with our configuration
exec .venv/bin/gunicorn \
    --config gunicorn.conf.py \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app