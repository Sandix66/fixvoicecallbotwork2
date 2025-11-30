#!/usr/bin/env python3
"""
Add existing Firebase Auth user to Firestore
"""
from config.firebase_init import db
from firebase_admin import auth
from datetime import datetime

def add_to_firestore():
    email = "admin@callbot.com"
    
    try:
        # Get user from Firebase Auth
        user = auth.get_user_by_email(email)
        uid = user.uid
        
        print(f"✅ Found Firebase Auth user: {uid}")
        
        # Check if already exists in Firestore
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            print("⚠️  User already exists in Firestore")
            print(f"Data: {user_doc.to_dict()}")
            return
        
        # Create user document in Firestore
        user_data = {
            'email': email,
            'username': 'Admin',
            'role': 'admin',
            'balance': 1000.0,
            'device_id': None,
            'telegram_id': None,
            'created_at': datetime.utcnow().isoformat()
        }
        
        user_ref.set(user_data)
        print(f"✅ Firestore user document created")
        
        print(f"\n🎉 Admin user setup complete!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: admin123")
        print(f"💰 Initial Balance: $1000.00")
        print(f"\nℹ️  You can now login at:")
        print(f"   https://callbot-research.preview.emergentagent.com")
        
    except auth.UserNotFoundError:
        print(f"❌ User not found in Firebase Auth")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_to_firestore()
