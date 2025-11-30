from fastapi import APIRouter, HTTPException, Depends
from models.schemas import PaymentInitiate, PaymentResponse
from services.mongodb_service import MongoDBService
from utils.auth_middleware import verify_token, verify_admin
from datetime import datetime, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(payment_data: PaymentInitiate, current_user: dict = Depends(verify_token)):
    """Initiate a payment (Mock for research)"""
    try:
        # Create payment with mock details
        payment = await MongoDBService.create_payment(
            user_id=current_user['uid'],
            amount=payment_data.amount,
            method=payment_data.method
        )
        
        # Add mock payment details
        if payment_data.method == 'usdt':
            payment['qr_code_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=TRC20:TMockAddressForResearch123456789:{payment_data.amount}"
            payment['transaction_hash'] = None
        else:
            payment['bank_details'] = {
                'bank_name': 'Research Bank (Mock)',
                'account_number': '1234567890',
                'account_name': 'CallBot Research',
                'reference': payment['payment_id']
            }
        
        return PaymentResponse(**payment)
    
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate payment")

@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(current_user: dict = Depends(verify_token)):
    """Get payment history"""
    payments = await MongoDBService.get_user_payments(current_user['uid'])
    return [PaymentResponse(**payment) for payment in payments]

@router.post("/{payment_id}/verify")
async def verify_payment(payment_id: str, current_user: dict = Depends(verify_admin)):
    """Verify and complete payment (Admin only - Mock)"""
    try:
        payment = await MongoDBService.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Update payment status
        await MongoDBService.update_payment_status(payment_id, 'completed')
        
        # Update user balance
        user = await MongoDBService.get_user(payment['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_balance = user['balance'] + payment['amount']
        await MongoDBService.update_user_balance(payment['user_id'], new_balance)
        
        return {"message": "Payment verified and balance updated", "new_balance": new_balance}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")