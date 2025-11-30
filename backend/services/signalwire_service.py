from signalwire.voice_response import VoiceResponse, Say
import httpx
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalWireService:
    def __init__(self):
        self.project_id = os.getenv('SIGNALWIRE_PROJECT_ID')
        self.token = os.getenv('SIGNALWIRE_TOKEN')
        self.space_url = os.getenv('SIGNALWIRE_SPACE_URL')
        self.base_url = f"https://{self.space_url}"
    
    async def make_call(self, from_number: str, to_number: str, callback_url: str, status_callback_url: str = None):
        """Initiate a call using SignalWire API"""
        try:
            call_data = {
                'From': from_number,
                'To': to_number,
                'Url': callback_url,
                'StatusCallback': status_callback_url or callback_url,
                'Record': 'true',
                'MachineDetection': 'Enable'  # Simple AMD detection
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/laml/2010-04-01/Accounts/{self.project_id}/Calls.json",
                    auth=(self.project_id, self.token),
                    data=call_data
                )
                
                if response.status_code == 201:
                    call_data = response.json()
                    return call_data
                else:
                    logger.error(f"SignalWire API error: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error making call: {e}")
            return None
    
    def generate_twiml_greeting(self, message: str, voice: str = "Chirp-HD-0"):
        """Generate TwiML for greeting message"""
        response = VoiceResponse()
        response.say(message, voice=voice, language='en-US')
        response.pause(length=2)
        return str(response)
    
    def generate_twiml_gather(self, message: str, action_url: str, num_digits: int = 6, voice: str = "Chirp-HD-0"):
        """Generate TwiML for gathering DTMF input"""
        response = VoiceResponse()
        gather = response.gather(
            num_digits=num_digits,
            action=action_url,
            method='POST',
            timeout=10
        )
        gather.say(message, voice=voice, language='en-US')
        return str(response)
    
    def generate_twiml_response(self, message: str, voice: str = "Chirp-HD-0", hangup: bool = True):
        """Generate TwiML response message"""
        response = VoiceResponse()
        response.say(message, voice=voice, language='en-US')
        if hangup:
            response.hangup()
        return str(response)
    
    async def get_recording(self, recording_sid: str):
        """Get recording URL from SignalWire"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/laml/2010-04-01/Accounts/{self.project_id}/Recordings/{recording_sid}.json",
                    auth=(self.project_id, self.token)
                )
                
                if response.status_code == 200:
                    recording_data = response.json()
                    return recording_data.get('uri')
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching recording: {e}")
            return None
    
    async def hangup_call(self, call_sid: str):
        """Terminate/hangup an active call"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/laml/2010-04-01/Accounts/{self.project_id}/Calls/{call_sid}.json",
                    auth=(self.project_id, self.token),
                    data={'Status': 'completed'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Call {call_sid} terminated successfully")
                    return True
                else:
                    logger.error(f"Failed to terminate call: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error terminating call: {e}")
            return False