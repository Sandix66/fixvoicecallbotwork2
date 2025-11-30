from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt_service import JWTService
from services.mongodb_service import MongoDBService
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = JWTService.verify_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        uid = payload.get('sub')
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user from MongoDB
        user_data = await MongoDBService.get_user(uid)
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user_data
    except HTTPException:
        raise
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