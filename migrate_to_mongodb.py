#!/usr/bin/env python3
"""
SQLite to MongoDB Atlas Migration Script
Migrates Quiz Partner data from SQLite to MongoDB Atlas
"""

import sqlite3
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import json
from bson import ObjectId
import argparse

class DatabaseMigrator:
    def __init__(self, sqlite_path, mongodb_uri, database_name):
        self.sqlite_path = sqlite_path
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.mongo_client = None
        self.mongo_db = None
        
    def connect_mongodb(self):
        """Connect to MongoDB Atlas"""
        try:
            print("🔗 Connecting to MongoDB Atlas...")
            self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[self.database_name]
            print("✅ Successfully connected to MongoDB Atlas!")
            return True
        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error connecting to MongoDB: {e}")
            return False
    
    def connect_sqlite(self):
        """Connect to SQLite database"""
        try:
            if not os.path.exists(self.sqlite_path):
                print(f"❌ SQLite database not found: {self.sqlite_path}")
                return None
            
            print(f"🔗 Connecting to SQLite database: {self.sqlite_path}")
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            print("✅ Successfully connected to SQLite!")
            return conn
        except Exception as e:
            print(f"❌ Failed to connect to SQLite: {e}")
            return None
    
    def get_sqlite_data(self, conn):
        """Extract data from SQLite database"""
        try:
            print("📊 Extracting data from SQLite...")
            
            # Get modules
            modules_cursor = conn.execute("SELECT * FROM modules ORDER BY id")
            modules = [dict(row) for row in modules_cursor.fetchall()]
            
            # Get questions
            questions_cursor = conn.execute("SELECT * FROM questions ORDER BY id")
            questions = [dict(row) for row in questions_cursor.fetchall()]
            
            print(f"📦 Found {len(modules)} modules and {len(questions)} questions")
            return modules, questions
            
        except Exception as e:
            print(f"❌ Error extracting SQLite data: {e}")
            return None, None
    
    def create_mongodb_collections(self):
        """Create MongoDB collections with indexes"""
        try:
            print("🏗️ Setting up MongoDB collections...")
            
            # Create collections
            modules_collection = self.mongo_db.modules
            questions_collection = self.mongo_db.questions
            
            # Create indexes for better performance
            print("📊 Creating indexes...")
            
            # Modules indexes
            modules_collection.create_index("name", unique=True)
            modules_collection.create_index("created_at")
            
            # Questions indexes
            questions_collection.create_index("module_id")
            questions_collection.create_index("name")
            questions_collection.create_index("created_at")
            questions_collection.create_index([("module_id", 1), ("created_at", -1)])
            
            print("✅ Collections and indexes created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating MongoDB collections: {e}")
            return False
    
    def migrate_modules(self, modules):
        """Migrate modules to MongoDB"""
        try:
            print("📦 Migrating modules...")
            modules_collection = self.mongo_db.modules
            
            # Clear existing data if any
            modules_collection.delete_many({})
            
            # Create mapping from old ID to new ObjectId
            id_mapping = {}
            
            for module in modules:
                old_id = module['id']
                
                # Create MongoDB document
                mongo_doc = {
                    'name': module['name'],
                    'created_at': module['created_at'],
                    'migrated_from_sqlite_id': old_id,
                    'migration_timestamp': datetime.utcnow()
                }
                
                try:
                    result = modules_collection.insert_one(mongo_doc)
                    id_mapping[old_id] = result.inserted_id
                    print(f"  ✅ Migrated module: {module['name']}")
                    
                except DuplicateKeyError:
                    print(f"  ⚠️ Duplicate module name: {module['name']} - skipping")
                    
            print(f"✅ Successfully migrated {len(id_mapping)} modules")
            return id_mapping
            
        except Exception as e:
            print(f"❌ Error migrating modules: {e}")
            return None
    
    def migrate_questions(self, questions, module_id_mapping):
        """Migrate questions to MongoDB"""
        try:
            print("❓ Migrating questions...")
            questions_collection = self.mongo_db.questions
            
            # Clear existing data if any
            questions_collection.delete_many({})
            
            migrated_count = 0
            skipped_count = 0
            
            for question in questions:
                old_module_id = question['module_id']
                
                # Check if module exists in mapping
                if old_module_id not in module_id_mapping:
                    print(f"  ⚠️ Skipping question - module ID {old_module_id} not found")
                    skipped_count += 1
                    continue
                
                # Create MongoDB document
                mongo_doc = {
                    'module_id': module_id_mapping[old_module_id],
                    'name': question['name'],
                    'image_path': question['image_path'],
                    'answer': question['answer'],
                    'created_at': question['created_at'],
                    'migrated_from_sqlite_id': question['id'],
                    'migration_timestamp': datetime.utcnow()
                }
                
                try:
                    questions_collection.insert_one(mongo_doc)
                    migrated_count += 1
                    print(f"  ✅ Migrated question: {question['name']}")
                    
                except Exception as e:
                    print(f"  ❌ Error migrating question {question['name']}: {e}")
                    skipped_count += 1
            
            print(f"✅ Successfully migrated {migrated_count} questions")
            if skipped_count > 0:
                print(f"⚠️ Skipped {skipped_count} questions due to errors")
                
            return migrated_count
            
        except Exception as e:
            print(f"❌ Error migrating questions: {e}")
            return 0
    
    def verify_migration(self, original_modules_count, original_questions_count):
        """Verify the migration was successful"""
        try:
            print("🔍 Verifying migration...")
            
            # Count documents in MongoDB
            modules_count = self.mongo_db.modules.count_documents({})
            questions_count = self.mongo_db.questions.count_documents({})
            
            print(f"📊 Migration Summary:")
            print(f"  Original modules: {original_modules_count}")
            print(f"  Migrated modules: {modules_count}")
            print(f"  Original questions: {original_questions_count}")
            print(f"  Migrated questions: {questions_count}")
            
            # Check if migration was complete
            if modules_count >= original_modules_count and questions_count >= original_questions_count:
                print("✅ Migration verification successful!")
                return True
            else:
                print("⚠️ Migration may be incomplete - some data was not migrated")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying migration: {e}")
            return False
    
    def create_backup_info(self, modules, questions):
        """Create a backup info file"""
        try:
            backup_info = {
                'migration_timestamp': datetime.utcnow().isoformat(),
                'sqlite_path': self.sqlite_path,
                'mongodb_uri': self.mongodb_uri.split('@')[1] if '@' in self.mongodb_uri else 'hidden',
                'database_name': self.database_name,
                'original_modules_count': len(modules),
                'original_questions_count': len(questions),
                'status': 'completed'
            }
            
            backup_file = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            print(f"📋 Migration info saved to: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Error creating backup info: {e}")
            return None
    
    def migrate(self):
        """Main migration process"""
        print("🚀 Starting SQLite to MongoDB migration...")
        print("=" * 50)
        
        # Connect to databases
        if not self.connect_mongodb():
            return False
        
        sqlite_conn = self.connect_sqlite()
        if not sqlite_conn:
            return False
        
        try:
            # Extract SQLite data
            modules, questions = self.get_sqlite_data(sqlite_conn)
            if modules is None or questions is None:
                return False
            
            # Create backup info
            self.create_backup_info(modules, questions)
            
            # Setup MongoDB collections
            if not self.create_mongodb_collections():
                return False
            
            # Migrate data
            module_id_mapping = self.migrate_modules(modules)
            if not module_id_mapping:
                return False
            
            migrated_questions = self.migrate_questions(questions, module_id_mapping)
            if migrated_questions == 0 and len(questions) > 0:
                return False
            
            # Verify migration
            success = self.verify_migration(len(modules), len(questions))
            
            if success:
                print("\n🎉 Migration completed successfully!")
                print("💡 Next steps:")
                print("  1. Update your application to use MongoDB")
                print("  2. Test the application thoroughly")
                print("  3. Keep SQLite backup until you're confident")
            else:
                print("\n⚠️ Migration completed with warnings")
                
            return success
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
            
        finally:
            sqlite_conn.close()
            if self.mongo_client:
                self.mongo_client.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate Quiz Partner from SQLite to MongoDB Atlas')
    parser.add_argument('--mongodb-uri', required=True, help='MongoDB Atlas connection string')
    parser.add_argument('--database-name', default='quiz_partner', help='MongoDB database name (default: quiz_partner)')
    parser.add_argument('--sqlite-path', default='Crime_platform.db', help='SQLite database path (default: Crime_platform.db)')
    
    args = parser.parse_args()
    
    print("🎯 Quiz Partner - SQLite to MongoDB Migration Tool")
    print("=" * 60)
    
    # Validate inputs
    if not args.mongodb_uri:
        print("❌ MongoDB URI is required!")
        sys.exit(1)
    
    # Create migrator and run migration
    migrator = DatabaseMigrator(
        sqlite_path=args.sqlite_path,
        mongodb_uri=args.mongodb_uri,
        database_name=args.database_name
    )
    
    success = migrator.migrate()
    
    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()