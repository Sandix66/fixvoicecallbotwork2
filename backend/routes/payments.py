from fastapi import APIRouter, HTTPException, Depends
from models.schemas import PaymentInitiate, PaymentResponse
from config.firebase_init import db
from utils.auth_middleware import verify_token, verify_admin
from datetime import datetime
from typing import List
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(payment_data: PaymentInitiate, current_user: dict = Depends(verify_token)):
    """Initiate a payment (Mock for research)"""
    try:
        payment_id = str(uuid.uuid4())
        
        payment_doc = {
            'payment_id': payment_id,
            'user_id': current_user['uid'],
            'amount': payment_data.amount,
            'method': payment_data.method,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Mock payment details
        if payment_data.method == 'usdt':
            payment_doc['qr_code_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=TRC20:TMockAddressForResearch123456789:{payment_data.amount}"
            payment_doc['transaction_hash'] = None
        else:
            payment_doc['bank_details'] = {
                'bank_name': 'Research Bank (Mock)',
                'account_number': '1234567890',
                'account_name': 'CallBot Research',
                'reference': payment_id
            }
        
        # Save to Firestore
        db.collection('payments').document(payment_id).set(payment_doc)
        
        return PaymentResponse(**payment_doc)
    
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate payment")

@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(current_user: dict = Depends(verify_token)):
    """Get payment history"""
    payments_ref = db.collection('payments').where('user_id', '==', current_user['uid']).order_by('created_at', direction='DESCENDING')
    docs = payments_ref.stream()
    
    payments = []
    for doc in docs:
        payment_data = doc.to_dict()
        payments.append(PaymentResponse(**payment_data))
    
    return payments

@router.post("/{payment_id}/verify")
async def verify_payment(payment_id: str, current_user: dict = Depends(verify_admin)):
    """Verify and complete payment (Admin only - Mock)"""
    try:
        payment_ref = db.collection('payments').document(payment_id)
        payment_doc = payment_ref.get()
        
        if not payment_doc.exists:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        payment_data = payment_doc.to_dict()
        
        # Update payment status
        payment_ref.update({'status': 'completed'})
        
        # Update user balance
        from services.firebase_service import FirebaseService
        user = await FirebaseService.get_user(payment_data['user_id'])
        new_balance = user['balance'] + payment_data['amount']
        await FirebaseService.update_user_balance(payment_data['user_id'], new_balance)
        
        return {"message": "Payment verified and balance updated", "new_balance": new_balance}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")