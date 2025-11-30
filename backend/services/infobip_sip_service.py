import os
import httpx
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class InfobipSIPService:
    """Infobip SIP Trunking Service for Caller ID Spoofing"""
    
    def __init__(self):
        self.api_key = os.getenv('INFOBIP_API_KEY')
        self.sip_trunk_id = os.getenv('INFOBIP_SIP_TRUNK_ID')
        self.base_url = os.getenv('INFOBIP_BASE_URL', 'https://api.infobip.com')
        
        if not self.api_key or not self.sip_trunk_id:
            logger.warning("Infobip SIP credentials not configured")
    
    async def make_spoofed_call(
        self,
        from_number: str,
        to_number: str,
        from_display_name: str,
        spoofed_caller_id: str,
        callback_url: str,
        status_callback_url: str,
        record: bool = True
    ) -> Optional[Dict]:
        """
        Initiate spoofed voice call via Infobip SIP Trunking
        
        Args:
            from_number: Actual originating number (SIP trunk)
            to_number: Destination number
            from_display_name: Display name shown to recipient
            spoofed_caller_id: Spoofed caller ID number shown
            callback_url: URL for voice instructions
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
            
            # Simplified Infobip Voice API call
            # Using WebRTC/Voice API v1 format
            payload = {
                'from': spoofed_caller_id,
                'to': to_number,
                'connectTimeout': 30,
                'recording': {
                    'recordingType': 'AUDIO'
                }
            }
            
            logger.info(f"Making Infobip call with payload: {payload}")
            logger.info(f"Headers: Authorization: App {self.api_key[:20]}...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try WebRTC endpoint first
                response = await client.post(
                    f"{self.base_url}/webrtc/1/calls",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"Infobip SIP spoofed call initiated: {data.get('callId')}")
                    logger.info(f"Spoofed Caller ID: {spoofed_caller_id}, Display: {from_display_name}")
                    return {
                        'call_id': data.get('callId'),
                        'status': data.get('status'),
                        'provider': 'infobip_sip',
                        'spoofed_caller_id': spoofed_caller_id,
                        'from_display_name': from_display_name
                    }
                else:
                    error_data = response.json() if response.text else {}
                    logger.error(f"Infobip SIP API error: {error_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error making Infobip SIP call: {e}")
            return None
    
    async def hangup_call(self, call_id: str) -> bool:
        """Terminate an active SIP call"""
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
                    logger.info(f"Infobip SIP call {call_id} terminated")
                    return True
                else:
                    logger.error(f"Failed to hangup Infobip SIP call: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error hanging up Infobip SIP call: {e}")
            return False
