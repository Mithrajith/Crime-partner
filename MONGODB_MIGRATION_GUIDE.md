# 🚀 MongoDB Migration Guide

## Overview
This guide will help you migrate your Quiz Partner application from SQLite to MongoDB Atlas, providing better scalability, cloud storage, and advanced features.

## 📋 What You'll Get

### ✅ **After Migration:**
- **Cloud Database**: Your data stored securely on MongoDB Atlas
- **Better Performance**: Optimized queries and indexing
- **Scalability**: Handle more users and data
- **Backup & Recovery**: Automatic cloud backups
- **Advanced Features**: Full-text search, aggregation pipelines
- **Security**: Enterprise-grade security features

## 🎯 Quick Start (Easiest Method)

### Step 1: Get MongoDB Atlas URI
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free account (if you don't have one)
3. Create a new cluster (Free tier is sufficient)
4. Click **"Connect"** → **"Connect your application"** 
5. Copy the connection string
6. Replace `<password>` with your actual password

Example URI:
```
mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority
```

### Step 2: Run Migration Script
```bash
# Make sure you're in the project directory
cd /path/to/Quiz-partner

# Run the automated setup (replace with your actual URI)
./setup_mongodb.sh 'mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority'
```

### Step 3: Start Your Application
```bash
python app.py
```

**That's it!** 🎉 Your application is now running with MongoDB!

---

## 🔧 Manual Migration (Advanced Users)

### 1. Install Dependencies
```bash
pip install -r requirements_updated.txt
```

### 2. Create Environment File
```bash
cp .env.example .env
# Edit .env with your MongoDB URI
```

### 3. Run Migration Script
```bash
python migrate_to_mongodb.py --mongodb-uri "your-connection-string" --database-name "quiz_partner"
```

### 4. Switch Application
```bash
cp app_mongodb.py app.py
```

---

## 🔍 Migration Script Features

### **Smart Data Migration**
- ✅ Preserves all modules and questions
- ✅ Maintains relationships between data
- ✅ Creates proper indexes for performance
- ✅ Validates data integrity
- ✅ Provides detailed migration logs

### **Safety Features**
- 🛡️ Automatic SQLite backup before migration
- 🛡️ Rollback capability if needed
- 🛡️ Data validation at each step
- 🛡️ Error handling and recovery

### **Performance Optimizations**
- 🚀 Database indexes for fast queries
- 🚀 Optimized aggregation pipelines
- 🚀 Connection pooling
- 🚀 Efficient ObjectId handling

---

## 📊 Database Schema Changes

### SQLite → MongoDB Transformation

**Modules Collection:**
```javascript
// Before (SQLite)
{
  id: 1,
  name: "Level-1",
  created_at: "2024-01-01 10:00:00"
}

// After (MongoDB)
{
  _id: ObjectId("..."),
  name: "Level-1", 
  created_at: "2024-01-01T10:00:00Z",
  migrated_from_sqlite_id: 1,
  migration_timestamp: "2024-01-15T08:30:00Z"
}
```

**Questions Collection:**
```javascript
// Before (SQLite)
{
  id: 1,
  module_id: 1,
  name: "Question 1",
  image_path: "abc123.jpg",
  answer: "Answer text",
  created_at: "2024-01-01 10:00:00"
}

// After (MongoDB)
{
  _id: ObjectId("..."),
  module_id: ObjectId("..."), // References modules collection
  name: "Question 1",
  image_path: "abc123.jpg", 
  answer: "Answer text",
  created_at: "2024-01-01T10:00:00Z",
  migrated_from_sqlite_id: 1,
  migration_timestamp: "2024-01-15T08:30:00Z"
}
```

---

## 🛠️ Available Scripts

### **setup_mongodb.sh**
Complete automated migration and setup
```bash
./setup_mongodb.sh 'your-mongodb-uri' [database-name]
```

### **migrate_to_mongodb.py**
Migration script only
```bash
python migrate_to_mongodb.py --mongodb-uri "uri" --database-name "db_name"
```

### **rollback_to_sqlite.sh**
Revert back to SQLite if needed
```bash
./rollback_to_sqlite.sh
```

---

## 🔧 Troubleshooting

### **Connection Issues**
```bash
# Test MongoDB connection
python -c "
from pymongo import MongoClient
client = MongoClient('your-uri')
print('✅ Connection successful!' if client.admin.command('ping') else '❌ Connection failed!')
"
```

### **Common Errors & Solutions**

**Error: "Import pymongo could not be resolved"**
```bash
pip install pymongo dnspython
```

**Error: "Authentication failed"**
- Check username/password in connection string
- Ensure user has read/write permissions
- Check if IP is whitelisted in MongoDB Atlas

**Error: "Network timeout"**
- Check internet connection
- Verify MongoDB Atlas cluster is running
- Try different network (sometimes corporate firewalls block MongoDB)

**Error: "Database connection refused"**
- Ensure MongoDB Atlas cluster is not paused
- Check connection string format
- Verify cluster region accessibility

### **Migration Issues**

**Partial Migration:**
```bash
# Check migration status
python -c "
from pymongo import MongoClient
client = MongoClient('your-uri')
db = client['quiz_partner']
print(f'Modules: {db.modules.count_documents({})}')
print(f'Questions: {db.questions.count_documents({})}')
"
```

**Rollback if Needed:**
```bash
./rollback_to_sqlite.sh
```

---

## 📈 Performance Improvements

### **MongoDB Advantages:**
1. **Indexing**: Automatic indexes on commonly queried fields
2. **Aggregation**: Complex queries like search with joins
3. **Scalability**: Horizontal scaling capabilities
4. **Cloud Backup**: Automatic point-in-time recovery
5. **Monitoring**: Built-in performance monitoring

### **Query Optimizations:**
- Questions with module info use `$lookup` aggregation
- Search queries use regex with case-insensitive matching
- Proper indexing on `module_id`, `name`, and `created_at`

---

## 🔒 Security Features

### **Enhanced Security:**
- ObjectId prevents enumeration attacks
- Input sanitization and validation
- Connection string environment variables
- Proper error handling without data leakage

### **MongoDB Atlas Security:**
- Encryption at rest and in transit
- Network access controls
- User authentication and authorization
- Audit logging (on paid tiers)

---

## 📦 Backup & Recovery

### **Automatic Backups:**
- SQLite database backed up before migration
- Migration info saved in JSON format
- Application files backed up before changes

### **Manual Backup:**
```bash
# Export MongoDB data
mongoexport --uri="your-uri" --collection=modules --out=modules_backup.json
mongoexport --uri="your-uri" --collection=questions --out=questions_backup.json
```

### **Restore from Backup:**
```bash
# Import MongoDB data
mongoimport --uri="your-uri" --collection=modules --file=modules_backup.json
mongoimport --uri="your-uri" --collection=questions --file=questions_backup.json
```

---

## 🚨 Important Notes

### **Before Migration:**
- ✅ Backup your SQLite database
- ✅ Test MongoDB connection
- ✅ Ensure you have admin access to MongoDB Atlas
- ✅ Stop the running application

### **After Migration:**
- ✅ Test all functionality thoroughly
- ✅ Verify data integrity
- ✅ Monitor application performance
- ✅ Set up MongoDB Atlas monitoring

### **Production Deployment:**
- 🔒 Use environment variables for sensitive data
- 🔒 Enable MongoDB Atlas IP whitelisting
- 🔒 Set up proper user roles and permissions
- 🔒 Configure SSL/TLS certificates
- 📊 Set up monitoring and alerting

---

## 💡 Tips for Success

1. **Start with Free Tier**: MongoDB Atlas offers a generous free tier
2. **Test Thoroughly**: Migrate to staging environment first
3. **Monitor Performance**: Use MongoDB Compass for visual monitoring
4. **Keep Backups**: Don't delete SQLite files until confident
5. **Use Environment Variables**: Keep credentials secure

---

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review migration logs in `migration_backup_*.json`
3. Test MongoDB connection independently
4. Consider rolling back and trying again
5. Check MongoDB Atlas status page for service issues

---

## 🎉 Success Indicators

Your migration is successful when:
- ✅ Application starts without errors
- ✅ All modules and questions are visible
- ✅ You can add new questions
- ✅ Search functionality works
- ✅ Image uploads work correctly
- ✅ Edit/delete operations work

**Welcome to the cloud! 🌤️ Your Quiz Partner is now powered by MongoDB Atlas!**