from config.firebase_init import db, get_firebase_auth
from firebase_admin import auth
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FirebaseService:
    @staticmethod
    async def create_user_with_email(email: str, password: str, username: str, role: str = "user"):
        """Create user with Firebase Auth and Firestore"""
        try:
            # Create Firebase Auth user
            user = auth.create_user(
                email=email,
                password=password,
                display_name=username
            )
            
            # Create user document in Firestore
            user_data = {
                'email': email,
                'username': username,
                'role': role,
                'balance': 0.0,
                'device_id': None,
                'telegram_id': None,
                'created_at': datetime.utcnow().isoformat()
            }
            
            db.collection('users').document(user.uid).set(user_data)
            
            return {"uid": user.uid, **user_data}
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    @staticmethod
    async def get_user(uid: str):
        """Get user from Firestore"""
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
        
        user_data = user_doc.to_dict()
        user_data['uid'] = uid
        return user_data
    
    @staticmethod
    async def update_user_balance(uid: str, amount: float):
        """Update user balance"""
        user_ref = db.collection('users').document(uid)
        user_ref.update({'balance': amount})
        return True
    
    @staticmethod
    async def update_device_id(uid: str, device_id: str):
        """Update user device ID"""
        user_ref = db.collection('users').document(uid)
        user_ref.update({'device_id': device_id})
        return True
    
    @staticmethod
    async def link_telegram(uid: str, telegram_id: str):
        """Link Telegram account to user"""
        user_ref = db.collection('users').document(uid)
        user_ref.update({'telegram_id': telegram_id})
        return True
    
    @staticmethod
    async def get_all_users():
        """Get all users (admin only)"""
        users_ref = db.collection('users')
        docs = users_ref.stream()
        
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data['uid'] = doc.id
            users.append(user_data)
        
        return users
    
    @staticmethod
    async def delete_user(uid: str):
        """Delete user from Auth and Firestore"""
        try:
            # Delete from Firebase Auth
            auth.delete_user(uid)
            
            # Delete from Firestore
            db.collection('users').document(uid).delete()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise
    
    @staticmethod
    async def create_call_log(call_data: dict):
        """Create call log in Firestore"""
        call_ref = db.collection('calls').document()
        call_data['call_id'] = call_ref.id
        call_data['created_at'] = datetime.utcnow().isoformat()
        call_data['events'] = []
        call_ref.set(call_data)
        return call_data
    
    @staticmethod
    async def update_call_events(call_id: str, event: dict):
        """Add event to call log"""
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if call_doc.exists:
            events = call_doc.to_dict().get('events', [])
            events.append(event)
            call_ref.update({'events': events})
        
        return True
    
    @staticmethod
    async def get_user_calls(user_id: str):
        """Get user call history"""
        # Temporary: Remove order_by to avoid index requirement
        calls_ref = db.collection('calls').where('user_id', '==', user_id).limit(100)
        docs = calls_ref.stream()
        
        calls = []
        for doc in docs:
            call_data = doc.to_dict()
            calls.append(call_data)
        
        # Sort in Python instead
        calls.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return calls
    
    @staticmethod
    async def get_all_calls():
        """Get all calls (admin only)"""
        calls_ref = db.collection('calls').order_by('created_at', direction='DESCENDING')
        docs = calls_ref.stream()
        
        calls = []
        for doc in docs:
            call_data = doc.to_dict()
            calls.append(call_data)
        
        return calls