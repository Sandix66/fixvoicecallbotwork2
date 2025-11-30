from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from config.firebase_init import db
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify Firebase ID token"""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        
        # Get user from Firestore
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        user_data['uid'] = uid
        
        return user_data
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def verify_admin(user: dict = Depends(verify_token)):
    """Verify user has admin role"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def verify_device(device_id: str, user: dict = Depends(verify_token)):
    """Verify device restriction"""
    stored_device = user.get('device_id')
    
    if stored_device and stored_device != device_id:
        raise HTTPException(
            status_code=403, 
            detail="This account is already logged in on another device"
        )
    
    return user