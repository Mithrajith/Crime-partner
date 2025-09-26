#!/bin/bash

# MongoDB Migration and Setup Script for Quiz Partner
set -e

echo "🎯 Quiz Partner - MongoDB Migration Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Check if MongoDB URI is provided
if [ -z "$1" ]; then
    print_color $RED "❌ Error: MongoDB URI is required!"
    echo ""
    echo "Usage: ./setup_mongodb.sh 'mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority'"
    echo ""
    echo "📝 How to get MongoDB Atlas URI:"
    echo "1. Go to https://cloud.mongodb.com/"
    echo "2. Create/login to your account"
    echo "3. Create a new cluster (free tier available)"
    echo "4. Click 'Connect' -> 'Connect your application'"
    echo "5. Copy the connection string"
    echo "6. Replace <password> with your actual password"
    exit 1
fi

MONGODB_URI="$1"
DATABASE_NAME="${2:-quiz_partner}"

print_color $BLUE "🔧 Setting up Quiz Partner with MongoDB Atlas..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_color $YELLOW "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
print_color $YELLOW "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install updated requirements
print_color $YELLOW "📥 Installing dependencies with MongoDB support..."
pip install -r requirements_updated.txt

# Create .env file
print_color $YELLOW "⚙️ Creating environment configuration..."
cat > .env << EOF
# Environment Configuration
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=development
FLASK_DEBUG=1

# MongoDB Configuration
MONGODB_URI=${MONGODB_URI}
DATABASE_NAME=${DATABASE_NAME}

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216

# Server Configuration
PORT=5001
EOF

print_color $GREEN "✅ Environment file created with secure secret key!"

# Make migration script executable
chmod +x migrate_to_mongodb.py

# Check if SQLite database exists
if [ -f "Crime_platform.db" ]; then
    print_color $YELLOW "🗄️ SQLite database found. Starting migration..."
    
    # Run migration
    python3 migrate_to_mongodb.py --mongodb-uri "$MONGODB_URI" --database-name "$DATABASE_NAME"
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Migration completed successfully!"
        
        # Backup original SQLite database
        BACKUP_FILE="Crime_platform_backup_$(date +%Y%m%d_%H%M%S).db"
        cp Crime_platform.db "$BACKUP_FILE"
        print_color $YELLOW "💾 SQLite database backed up as: $BACKUP_FILE"
        
        # Replace app.py with MongoDB version
        if [ -f "app.py" ]; then
            cp app.py "app_sqlite_backup.py"
            cp app_mongodb.py app.py
            print_color $GREEN "✅ Application updated to use MongoDB!"
            print_color $YELLOW "💾 Original app.py backed up as: app_sqlite_backup.py"
        fi
        
        # Update templates if needed
        if [ -f "templates/index_mongodb.html" ]; then
            cp templates/index.html templates/index_sqlite_backup.html
            cp templates/index_mongodb.html templates/index.html
            print_color $GREEN "✅ Templates updated for MongoDB!"
        fi
        
    else
        print_color $RED "❌ Migration failed! Please check the error messages above."
        exit 1
    fi
else
    print_color $YELLOW "⚠️ No SQLite database found. Setting up fresh MongoDB application..."
    
    # Test MongoDB connection
    python3 -c "
from pymongo import MongoClient
import sys
try:
    client = MongoClient('$MONGODB_URI', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB connection successful!')
    client.close()
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        # Replace app.py with MongoDB version
        if [ -f "app.py" ]; then
            cp app.py "app_sqlite_backup.py"
            cp app_mongodb.py app.py
            print_color $GREEN "✅ Application configured for MongoDB!"
        fi
        
        # Update templates if needed
        if [ -f "templates/index_mongodb.html" ]; then
            cp templates/index.html templates/index_sqlite_backup.html 2>/dev/null || true
            cp templates/index_mongodb.html templates/index.html
            print_color $GREEN "✅ Templates updated for MongoDB!"
        fi
    else
        print_color $RED "❌ Cannot connect to MongoDB. Please check your connection string."
        exit 1
    fi
fi

# Set secure permissions
print_color $YELLOW "🔒 Setting secure permissions..."
chmod 755 uploads/ 2>/dev/null || true
chmod 644 uploads/* 2>/dev/null || true

print_color $GREEN "🎉 Setup Complete!"
echo ""
print_color $BLUE "📋 Summary:"
echo "  ✅ MongoDB dependencies installed"
echo "  ✅ Environment configured with secure settings"
echo "  ✅ Application updated to use MongoDB"
if [ -f "Crime_platform.db" ]; then
echo "  ✅ SQLite data migrated to MongoDB"
echo "  ✅ SQLite database backed up"
fi
echo ""
print_color $YELLOW "🚀 Next Steps:"
echo "1. Start the application: python app.py"
echo "2. Visit: http://localhost:5001"
echo "3. Test all functionality thoroughly"
echo "4. Keep SQLite backups until you're confident"
echo ""
print_color $BLUE "💡 Useful Commands:"
echo "  • Test MongoDB connection: python -c \"from pymongo import MongoClient; print('OK' if MongoClient('$MONGODB_URI').admin.command('ping') else 'FAIL')\""
echo "  • View migration logs: ls -la migration_backup_*.json"
echo "  • Rollback to SQLite: cp app_sqlite_backup.py app.py"
echo ""
print_color $GREEN "✨ Your Quiz Partner is now running on MongoDB Atlas!"