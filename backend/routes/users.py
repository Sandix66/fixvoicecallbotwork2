from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import auth
from models.schemas import UserResponse, UpdateBalance, ChangePassword, LinkTelegram
from services.firebase_service import FirebaseService
from utils.auth_middleware import verify_token, verify_admin
from config.firebase_init import db
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(verify_token)):
    """Get current user profile"""
    return UserResponse(**current_user)

@router.post("/change-password")
async def change_password(data: ChangePassword, current_user: dict = Depends(verify_token)):
    """Change user password"""
    try:
        # Firebase Admin SDK doesn't support password verification
        # In production, use Firebase Auth REST API for this
        auth.update_user(current_user['uid'], password=data.new_password)
        return {"message": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=400, detail="Failed to update password")

@router.put("/{uid}")
async def update_user(uid: str, update_data: dict, current_user: dict = Depends(verify_admin)):
    """Update user profile (Admin only)"""
    try:
        # Update Firebase Auth if email or password changed
        auth_updates = {}
        if 'email' in update_data and update_data['email']:
            auth_updates['email'] = update_data['email']
        if 'password' in update_data and update_data['password']:
            auth_updates['password'] = update_data['password']
        if 'username' in update_data and update_data['username']:
            auth_updates['display_name'] = update_data['username']
        
        if auth_updates:
            auth.update_user(uid, **auth_updates)
        
        # Update Firestore
        firestore_updates = {}
        if 'username' in update_data and update_data['username']:
            firestore_updates['username'] = update_data['username']
        if 'email' in update_data and update_data['email']:
            firestore_updates['email'] = update_data['email']
        
        if firestore_updates:
            user_ref = db.collection('users').document(uid)
            user_ref.update(firestore_updates)
        
        return {"message": "User updated successfully"}
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(status_code=400, detail="Failed to update user")

@router.post("/link-telegram")
async def link_telegram_account(data: LinkTelegram, current_user: dict = Depends(verify_token)):
    """Link Telegram account to user"""
    await FirebaseService.link_telegram(current_user['uid'], data.telegram_id)
    return {"message": "Telegram account linked successfully"}

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(verify_admin)):
    """Get all users (Admin only)"""
    users = await FirebaseService.get_all_users()
    return [UserResponse(**user) for user in users]

@router.put("/{uid}/balance")
async def update_user_balance(uid: str, data: UpdateBalance, current_user: dict = Depends(verify_admin)):
    """Update user balance (Admin only)"""
    await FirebaseService.update_user_balance(uid, data.amount)
    return {"message": "Balance updated successfully"}

@router.delete("/{uid}")
async def delete_user(uid: str, current_user: dict = Depends(verify_admin)):
    """Delete user (Admin only)"""
    await FirebaseService.delete_user(uid)
    return {"message": "User deleted successfully"}