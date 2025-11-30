from fastapi import APIRouter, HTTPException, Depends
from models.schemas import SignalWireNumber, SignalWireCredentials
from config.firebase_init import db
from google.cloud import firestore
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
        number_ref = db.collection('signalwire_numbers').document()
        number_data = number.model_dump()
        number_data['created_at'] = firestore.SERVER_TIMESTAMP
        number_ref.set(number_data)
        return {"message": "Phone number added successfully", "id": number_ref.id}
    except Exception as e:
        logger.error(f"Error adding number: {e}")
        raise HTTPException(status_code=500, detail="Failed to add number")

@router.get("/signalwire/numbers", response_model=List[SignalWireNumber])
async def get_signalwire_numbers(current_user: dict = Depends(verify_admin)):
    """Get all SignalWire numbers"""
    numbers_ref = db.collection('signalwire_numbers')
    docs = numbers_ref.stream()
    
    numbers = []
    for doc in docs:
        number_data = doc.to_dict()
        numbers.append(SignalWireNumber(**number_data))
    
    return numbers

@router.delete("/signalwire/numbers/{number_id}")
async def delete_signalwire_number(number_id: str, current_user: dict = Depends(verify_admin)):
    """Delete SignalWire number"""
    db.collection('signalwire_numbers').document(number_id).delete()
    return {"message": "Number deleted successfully"}

@router.put("/signalwire/credentials")
async def update_signalwire_credentials(credentials: SignalWireCredentials, current_user: dict = Depends(verify_admin)):
    """Update SignalWire credentials"""
    try:
        cred_ref = db.collection('signalwire_credentials').document('default')
        cred_data = credentials.model_dump()
        cred_data['updated_at'] = firestore.SERVER_TIMESTAMP
        cred_ref.set(cred_data)
        return {"message": "Credentials updated successfully"}
    except Exception as e:
        logger.error(f"Error updating credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to update credentials")

@router.get("/signalwire/credentials")
async def get_signalwire_credentials(current_user: dict = Depends(verify_admin)):
    """Get SignalWire credentials (masked)"""
    cred_ref = db.collection('signalwire_credentials').document('default')
    cred_doc = cred_ref.get()
    
    if not cred_doc.exists:
        return {
            "project_id": os.getenv('SIGNALWIRE_PROJECT_ID', ''),
            "space_url": os.getenv('SIGNALWIRE_SPACE_URL', ''),
            "token": "****" + os.getenv('SIGNALWIRE_TOKEN', '')[-4:] if os.getenv('SIGNALWIRE_TOKEN') else ''
        }
    
    cred_data = cred_doc.to_dict()
    # Mask token
    if 'token' in cred_data:
        cred_data['token'] = "****" + cred_data['token'][-4:]
    
    return cred_data

@router.get("/signalwire/numbers/available")
async def get_available_numbers():
    """Get available SignalWire numbers (public endpoint for users)"""
    numbers_ref = db.collection('signalwire_numbers').where('is_active', '==', True)
    docs = numbers_ref.stream()
    
    numbers = []
    for doc in docs:
        number_data = doc.to_dict()
        numbers.append({
            'id': doc.id,
            'phone_number': number_data.get('phone_number')
        })
    
    return numbers