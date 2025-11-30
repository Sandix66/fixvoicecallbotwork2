from fastapi import APIRouter, HTTPException, Depends
from models.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse
from services.mongodb_service import MongoDBService
from services.jwt_service import JWTService
from utils.auth_middleware import verify_token, verify_admin
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, current_user: dict = Depends(verify_admin)):
    """Register new user (Admin only)"""
    try:
        user = await MongoDBService.create_user(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
            role=user_data.role
        )
        return UserResponse(**user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login with email and password"""
    try:
        # Get user by email
        user = await MongoDBService.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not MongoDBService.verify_password(login_data.password, user.get('password_hash', '')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check device restriction
        if login_data.device_id:
            stored_device = user.get('device_id')
            if stored_device and stored_device != login_data.device_id:
                raise HTTPException(
                    status_code=403,
                    detail="This account is already logged in on another device"
                )
            # Update device ID
            await MongoDBService.update_device_id(user['uid'], login_data.device_id)
        
        # Create JWT token
        token = JWTService.create_user_token(
            uid=user['uid'],
            email=user['email'],
            role=user['role']
        )
        
        # Remove password_hash from response
        user.pop('password_hash', None)
        
        return LoginResponse(
            token=token,
            user=UserResponse(**user)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/verify")
async def verify_token_endpoint(current_user: dict = Depends(verify_token)):
    """Verify token validity"""
    return {"valid": True, "user": UserResponse(**current_user)}