#!/usr/bin/env python3
"""
Create initial admin user for CallBot Research System
"""
import asyncio
import httpx
from config.firebase_init import db
from datetime import datetime

async def create_admin_user():
    email = "admin@callbot.com"
    password = "admin123"
    username = "Admin"
    
    firebase_api_key = "AIzaSyBTMOOZHr-ywMJuEtZriUb_rvK9gSCMRyU"
    
    try:
        # Create user via Firebase Auth REST API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={firebase_api_key}",
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
            )
            
            if response.status_code != 200:
                error_data = response.json()
                if 'error' in error_data and 'EMAIL_EXISTS' in error_data['error'].get('message', ''):
                    print("⚠️  User with this email already exists")
                    return
                else:
                    print(f"❌ Error from Firebase: {error_data}")
                    return
            
            result = response.json()
            uid = result['localId']
        
        print(f"✅ Firebase Auth user created: {uid}")
        
        # Create user document in Firestore
        user_data = {
            'email': email,
            'username': username,
            'role': 'admin',
            'balance': 1000.0,  # Initial balance for testing
            'device_id': None,
            'telegram_id': None,
            'created_at': datetime.utcnow().isoformat()
        }
        
        db.collection('users').document(uid).set(user_data)
        print(f"✅ Firestore user document created")
        
        print(f"\n🎉 Admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"💰 Initial Balance: ${user_data['balance']}")
        print(f"\nℹ️  Use these credentials to login to the system")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
