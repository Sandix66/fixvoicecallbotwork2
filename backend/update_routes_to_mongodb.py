#!/usr/bin/env python3
"""
Script to update all route files from Firebase to MongoDB
"""

import os
import re

def update_file_content(file_path):
    """Update a single file to use MongoDB instead of Firebase"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace Firebase imports with MongoDB imports
    content = re.sub(
        r'from firebase_admin import auth',
        'from services.mongodb_service import MongoDBService',
        content
    )
    
    content = re.sub(
        r'from services\.firebase_service import FirebaseService',
        'from services.mongodb_service import MongoDBService',
        content
    )
    
    content = re.sub(
        r'from config\.firebase_init import db',
        'from config.mongodb_init import db',
        content
    )
    
    content = re.sub(
        r'from google\.cloud import firestore',
        '',
        content
    )
    
    # Replace FirebaseService calls with MongoDBService
    content = content.replace('FirebaseService.', 'MongoDBService.')
    
    # Replace Firestore operations with MongoDB operations
    # db.collection('users').document(uid) -> db.users.find_one({"uid": uid})
    content = re.sub(
        r'db\.collection\([\'"](\w+)[\'"]\)\.document\(([^)]+)\)\.get\(\)',
        r'await db.\1.find_one({"_id": \2})',
        content
    )
    
    content = re.sub(
        r'db\.collection\([\'"](\w+)[\'"]\)\.document\(([^)]+)\)\.update\(([^)]+)\)',
        r'await db.\1.update_one({"_id": \2}, {"$set": \3})',
        content
    )
    
    content = re.sub(
        r'db\.collection\([\'"](\w+)[\'"]\)\.document\(([^)]+)\)\.delete\(\)',
        r'await db.\1.delete_one({"_id": \2})',
        content
    )
    
    content = re.sub(
        r'db\.collection\([\'"](\w+)[\'"]\)\.document\(([^)]+)\)\.set\(([^)]+)\)',
        r'await db.\1.insert_one(\3)',
        content
    )
    
    # Remove firestore.SERVER_TIMESTAMP references
    content = content.replace('firestore.SERVER_TIMESTAMP', 'datetime.now(timezone.utc).isoformat()')
    
    # Add necessary imports if not present
    if 'from datetime import datetime' not in content and 'datetime.' in content:
        content = 'from datetime import datetime, timezone\n' + content
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated: {file_path}")
        return True
    else:
        print(f"⏭️  Skipped (no changes): {file_path}")
        return False

def main():
    """Update all route files"""
    routes_dir = '/app/backend/routes'
    route_files = [
        'users.py',
        'calls.py',
        'admin.py',
        'webhooks.py',
        'payments.py'
    ]
    
    print("🔄 Updating route files from Firebase to MongoDB...\n")
    
    updated_count = 0
    for filename in route_files:
        file_path = os.path.join(routes_dir, filename)
        if os.path.exists(file_path):
            if update_file_content(file_path):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n✅ Updated {updated_count} files")

if __name__ == '__main__':
    main()
