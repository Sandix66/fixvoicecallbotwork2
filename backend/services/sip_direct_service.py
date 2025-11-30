import os
import asyncio
import logging
from typing import Optional, Dict
import socket

logger = logging.getLogger(__name__)

class SIPDirectService:
    """
    Direct SIP calling service for Infobip (IP-based authentication)
    No API key required - uses SIP INVITE directly
    """
    
    def __init__(self):
        self.sip_domain = os.getenv('INFOBIP_SIP_DOMAIN', '81.23.254.103')
        self.sip_port = int(os.getenv('INFOBIP_SIP_PORT', '5061'))
        self.sip_transport = os.getenv('INFOBIP_SIP_TRANSPORT', 'TLS')
        
        if not self.sip_domain:
            logger.warning("SIP domain not configured")
    
    def generate_sip_invite(
        self,
        from_number: str,
        to_number: str,
        from_display_name: str,
        spoofed_caller_id: str,
        call_id: str
    ) -> str:
        """
        Generate SIP INVITE message for spoofed call
        
        Args:
            from_number: Actual trunk number
            to_number: Destination number
            from_display_name: Display name shown to recipient
            spoofed_caller_id: Spoofed caller ID number
            call_id: Unique call identifier
            
        Returns:
            SIP INVITE message string
        """
        # SIP INVITE with custom FROM header for spoofing
        sip_invite = f"""INVITE sip:{to_number}@{self.sip_domain}:{self.sip_port} SIP/2.0
Via: SIP/2.0/{self.sip_transport} {socket.gethostbyname(socket.gethostname())}:{self.sip_port};branch=z9hG4bK{call_id}
Max-Forwards: 70
From: "{from_display_name}" <sip:{spoofed_caller_id}@{self.sip_domain}>;tag={call_id}-from
To: <sip:{to_number}@{self.sip_domain}>
Call-ID: {call_id}@callbot
CSeq: 1 INVITE
Contact: <sip:{from_number}@{socket.gethostbyname(socket.gethostname())}:{self.sip_port};transport={self.sip_transport.lower()}>
Content-Type: application/sdp
Content-Length: 0

"""
        return sip_invite
    
    async def make_spoofed_call(
        self,
        from_number: str,
        to_number: str,
        from_display_name: str,
        spoofed_caller_id: str,
        call_id: str
    ) -> Optional[Dict]:
        """
        Initiate spoofed call via direct SIP connection
        
        This uses RAW SIP protocol without API key
        Authentication is done via IP whitelist
        
        Args:
            from_number: Actual SIP trunk number
            to_number: Destination number
            from_display_name: Name displayed to recipient
            spoofed_caller_id: Number displayed to recipient
            call_id: Unique call ID
            
        Returns:
            Dict with call info or None if failed
        """
        try:
            logger.info(f"Initiating SIP spoofed call: {spoofed_caller_id} -> {to_number}")
            logger.info(f"SIP Target: {self.sip_domain}:{self.sip_port} ({self.sip_transport})")
            logger.info(f"Display Name: {from_display_name}")
            
            # Generate SIP INVITE message
            sip_invite = self.generate_sip_invite(
                from_number=from_number,
                to_number=to_number,
                from_display_name=from_display_name,
                spoofed_caller_id=spoofed_caller_id,
                call_id=call_id
            )
            
            # For now, log the SIP message
            # In production, this would use actual SIP library (pjsua2, FreeSWITCH, etc)
            logger.info(f"SIP INVITE generated:\n{sip_invite}")
            
            # TODO: Send SIP INVITE via socket or SIP library
            # This requires:
            # 1. TLS connection to 81.23.254.103:5061
            # 2. Send SIP INVITE
            # 3. Handle SIP responses (100 Trying, 180 Ringing, 200 OK)
            # 4. Handle SDP negotiation for audio
            # 5. Handle RTP stream for voice/TTS
            
            return {
                'call_id': call_id,
                'status': 'initiated',
                'provider': 'sip_direct',
                'sip_domain': self.sip_domain,
                'spoofed_caller_id': spoofed_caller_id,
                'from_display_name': from_display_name,
                'method': 'direct_sip'
            }
            
        except Exception as e:
            logger.error(f"Error making SIP spoofed call: {e}")
            return None
    
    def get_sip_config(self) -> Dict:
        """Get current SIP configuration"""
        return {
            'sip_domain': self.sip_domain,
            'sip_port': self.sip_port,
            'transport': self.sip_transport,
            'auth_method': 'IP-based (no credentials)',
            'source_ip': socket.gethostbyname(socket.gethostname())
        }
