from fastapi import APIRouter, HTTPException, Depends
from models.schemas import SignalWireNumber, SignalWireCredentials
from services.mongodb_service import MongoDBService
from utils.auth_middleware import verify_admin
from typing import List
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/signalwire/numbers")
async def add_signalwire_number(number: SignalWireNumber, current_user: dict = Depends(verify_admin)):
    """Add SignalWire phone number"""
    try:
        success = await MongoDBService.add_signalwire_number(number.phone_number)
        if not success:
            raise HTTPException(status_code=400, detail="Number already exists")
        return {"message": "Phone number added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding number: {e}")
        raise HTTPException(status_code=500, detail="Failed to add number")

@router.get("/signalwire/numbers", response_model=List[SignalWireNumber])
async def get_signalwire_numbers(current_user: dict = Depends(verify_admin)):
    """Get all SignalWire numbers"""
    numbers = await MongoDBService.get_signalwire_numbers()
    return [SignalWireNumber(**number) for number in numbers]

@router.delete("/signalwire/numbers/{phone_number}")
async def delete_signalwire_number(phone_number: str, current_user: dict = Depends(verify_admin)):
    """Delete SignalWire number"""
    from config.mongodb_init import db
    result = await db.signalwire_numbers.delete_one({"phone_number": phone_number})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Number not found")
    return {"message": "Number deleted successfully"}

@router.put("/signalwire/credentials")
async def update_signalwire_credentials(credentials: SignalWireCredentials, current_user: dict = Depends(verify_admin)):
    """Update SignalWire credentials"""
    try:
        await MongoDBService.set_provider_config('signalwire', credentials.model_dump())
        return {"message": "Credentials updated successfully"}
    except Exception as e:
        logger.error(f"Error updating credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to update credentials")

@router.get("/signalwire/credentials")
async def get_signalwire_credentials(current_user: dict = Depends(verify_admin)):
    """Get SignalWire credentials (masked)"""
    config = await MongoDBService.get_provider_config('signalwire')
    
    if not config:
        return {
            "project_id": os.getenv('SIGNALWIRE_PROJECT_ID', ''),
            "space_url": os.getenv('SIGNALWIRE_SPACE_URL', ''),
            "token": "****" + os.getenv('SIGNALWIRE_TOKEN', '')[-4:] if os.getenv('SIGNALWIRE_TOKEN') else ''
        }
    
    # Mask token
    if 'token' in config:
        config['token'] = "****" + config['token'][-4:]
    
    return config

@router.get("/signalwire/numbers/available")
async def get_available_numbers():
    """Get available SignalWire numbers (public endpoint for users)"""
    numbers = await MongoDBService.get_available_numbers()
    return [{'phone_number': num['phone_number']} for num in numbers]