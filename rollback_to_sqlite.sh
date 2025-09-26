#!/bin/bash

# Rollback Script - Revert from MongoDB to SQLite
set -e

echo "🔄 Quiz Partner - MongoDB to SQLite Rollback"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_color() {
    echo -e "${1}${2}${NC}"
}

print_color $YELLOW "⚠️  This will rollback your application to use SQLite instead of MongoDB"
print_color $YELLOW "⚠️  Make sure you have your SQLite backup before proceeding!"

# Confirmation
read -p "Are you sure you want to rollback to SQLite? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_color $BLUE "Rollback cancelled."
    exit 0
fi

print_color $BLUE "🔄 Starting rollback process..."

# Check for backup files
if [ ! -f "app_sqlite_backup.py" ]; then
    print_color $RED "❌ SQLite app backup not found (app_sqlite_backup.py)"
    print_color $YELLOW "💡 You may need to restore from your original app.py manually"
    exit 1
fi

# Restore original app.py
print_color $YELLOW "📄 Restoring SQLite version of app.py..."
cp app.py app_mongodb_backup.py
cp app_sqlite_backup.py app.py
print_color $GREEN "✅ app.py restored to SQLite version"

# Restore templates if backup exists
if [ -f "templates/index_sqlite_backup.html" ]; then
    print_color $YELLOW "📄 Restoring SQLite templates..."
    cp templates/index.html templates/index_mongodb_backup.html
    cp templates/index_sqlite_backup.html templates/index.html
    print_color $GREEN "✅ Templates restored to SQLite version"
fi

# Find most recent SQLite backup
SQLITE_BACKUP=$(ls -t Crime_platform_backup_*.db 2>/dev/null | head -n1)

if [ ! -z "$SQLITE_BACKUP" ] && [ -f "$SQLITE_BACKUP" ]; then
    print_color $YELLOW "📄 Found SQLite backup: $SQLITE_BACKUP"
    read -p "Restore this backup? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$SQLITE_BACKUP" Crime_platform.db
        print_color $GREEN "✅ SQLite database restored from backup"
    fi
else
    print_color $YELLOW "⚠️  No SQLite backup found. You may need to restore manually."
fi

# Update .env file to remove MongoDB settings
if [ -f ".env" ]; then
    print_color $YELLOW "⚙️ Updating environment configuration..."
    
    # Create new .env without MongoDB settings
    cat > .env << EOF
# Environment Configuration
SECRET_KEY=$(grep SECRET_KEY .env | cut -d'=' -f2-)
FLASK_ENV=development
FLASK_DEBUG=1

# SQLite Configuration (restored)
DATABASE_URL=sqlite:///Crime_platform.db

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216

# Server Configuration
PORT=5001
EOF
    
    print_color $GREEN "✅ Environment configuration updated for SQLite"
fi

print_color $GREEN "🎉 Rollback Complete!"
echo ""
print_color $BLUE "📋 What was done:"
echo "  ✅ Restored SQLite version of app.py"
echo "  ✅ MongoDB version backed up as app_mongodb_backup.py"
if [ -f "templates/index_sqlite_backup.html" ]; then
echo "  ✅ Restored SQLite templates"
fi
if [ ! -z "$SQLITE_BACKUP" ] && [ -f "Crime_platform.db" ]; then
echo "  ✅ Restored SQLite database from backup"
fi
echo "  ✅ Updated environment configuration"
echo ""
print_color $YELLOW "🚀 Next Steps:"
echo "1. Start the application: python app.py"
echo "2. Visit: http://localhost:5001"
echo "3. Verify all your data is present"
echo ""
print_color $BLUE "💡 Note: Your MongoDB data is still safe in the cloud"
print_color $BLUE "💡 You can switch back to MongoDB by running setup_mongodb.sh again"