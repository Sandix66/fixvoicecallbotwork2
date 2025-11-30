import os
import httpx
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class InfobipService:
    """Infobip Voice API Service for regular calls"""
    
    def __init__(self):
        self.api_key = os.getenv('INFOBIP_API_KEY')
        self.base_url = os.getenv('INFOBIP_BASE_URL', 'https://api.infobip.com')
        
        if not self.api_key:
            logger.warning("Infobip API key not configured")
    
    async def make_call(
        self,
        from_number: str,
        to_number: str,
        callback_url: str,
        status_callback_url: str,
        record: bool = True
    ) -> Optional[Dict]:
        """
        Initiate voice call via Infobip Voice API
        
        Args:
            from_number: Caller ID (from number)
            to_number: Destination number
            callback_url: URL for voice instructions (TwiML-like)
            status_callback_url: URL for status updates
            record: Enable call recording
            
        Returns:
            Call response dict or None if failed
        """
        try:
            headers = {
                'Authorization': f'App {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Infobip Voice API proper structure
            payload = {
                'endpoint': {
                    'type': 'PHONE',
                    'phoneNumber': to_number
                },
                'from': from_number,
                'scenario': {
                    'name': 'VoiceCall',
                    'script': [
                        {
                            'goto': {
                                'url': callback_url
                            }
                        }
                    ]
                },
                'notifyUrl': status_callback_url,
                'notifyContentType': 'application/json',
                'recording': {
                    'recordingType': 'AUDIO' if record else 'NONE'
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/calls/1/calls",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"Infobip call initiated: {data.get('callId')}")
                    return {
                        'call_id': data.get('callId'),
                        'status': data.get('status'),
                        'provider': 'infobip'
                    }
                else:
                    error_data = response.json() if response.text else {}
                    logger.error(f"Infobip API error: {error_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error making Infobip call: {e}")
            return None
    
    async def hangup_call(self, call_id: str) -> bool:
        """Terminate an active call"""
        try:
            headers = {
                'Authorization': f'App {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/calls/1/calls/{call_id}/hangup",
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"Infobip call {call_id} terminated")
                    return True
                else:
                    logger.error(f"Failed to hangup Infobip call: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error hanging up Infobip call: {e}")
            return False
