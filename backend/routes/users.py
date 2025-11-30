from fastapi import APIRouter, HTTPException, Depends
from models.schemas import UserResponse, UpdateBalance, ChangePassword, LinkTelegram
from services.mongodb_service import MongoDBService
from utils.auth_middleware import verify_token, verify_admin
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
        # Get current user from MongoDB
        user = await MongoDBService.get_user(current_user['uid'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify old password
        if not MongoDBService.verify_password(data.old_password, user.get('password_hash', '')):
            raise HTTPException(status_code=400, detail="Invalid old password")
        
        # Update password
        await MongoDBService.update_user(current_user['uid'], {'password': data.new_password})
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=400, detail="Failed to update password")

@router.put("/{uid}")
async def update_user(uid: str, update_data: dict, current_user: dict = Depends(verify_admin)):
    """Update user profile (Admin only)"""
    try:
        # Update MongoDB
        await MongoDBService.update_user(uid, update_data)
        return {"message": "User updated successfully"}
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(status_code=400, detail="Failed to update user")

@router.post("/link-telegram")
async def link_telegram_account(data: LinkTelegram, current_user: dict = Depends(verify_token)):
    """Link Telegram account to user"""
    await MongoDBService.link_telegram(current_user['uid'], data.telegram_id)
    return {"message": "Telegram account linked successfully"}

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(verify_admin)):
    """Get all users (Admin only)"""
    users = await MongoDBService.get_all_users()
    return [UserResponse(**user) for user in users]

@router.put("/{uid}/balance")
async def update_user_balance(uid: str, data: UpdateBalance, current_user: dict = Depends(verify_admin)):
    """Update user balance (Admin only)"""
    await MongoDBService.update_user_balance(uid, data.amount)
    return {"message": "Balance updated successfully"}

@router.delete("/{uid}")
async def delete_user(uid: str, current_user: dict = Depends(verify_admin)):
    """Delete user (Admin only)"""
    await MongoDBService.delete_user(uid)
    return {"message": "User deleted successfully"}