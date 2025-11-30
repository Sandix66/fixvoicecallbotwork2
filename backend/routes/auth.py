from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import auth
from models.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse
from services.firebase_service import FirebaseService
from utils.auth_middleware import verify_token, verify_admin
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, current_user: dict = Depends(verify_admin)):
    """Register new user (Admin only)"""
    try:
        user = await FirebaseService.create_user_with_email(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
            role=user_data.role
        )
        return user
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login with email and password"""
    try:
        # Verify email and password using Firebase Auth REST API
        import httpx
        firebase_api_key = "AIzaSyBTMOOZHr-ywMJuEtZriUb_rvK9gSCMRyU"  # From frontend config
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}",
                json={
                    "email": login_data.email,
                    "password": login_data.password,
                    "returnSecureToken": True
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            result = response.json()
            id_token = result['idToken']
            uid = result['localId']
        
        # Get user data
        user = await FirebaseService.get_user(uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update device ID if provided
        if login_data.device_id:
            if user.get('device_id') and user.get('device_id') != login_data.device_id:
                raise HTTPException(
                    status_code=403,
                    detail="This account is already logged in on another device"
                )
            await FirebaseService.update_device_id(uid, login_data.device_id)
        
        return LoginResponse(
            token=id_token,
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