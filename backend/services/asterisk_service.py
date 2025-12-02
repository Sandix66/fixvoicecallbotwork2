import paramiko
import os
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class AsteriskService:
    def __init__(self):
        # VPS Credentials from context
        self.host = "139.59.241.253"
        self.username = "root"
        self.password = os.getenv('ASTERISK_VPS_PASSWORD', 'Pekanbaru236@Nasya')
        self.port = 22
        
        # Asterisk paths
        self.call_files_dir = "/var/spool/asterisk/outgoing"
        self.temp_dir = "/tmp/asterisk_calls"
    
    def _create_ssh_client(self):
        """Create SSH client connection to VPS"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=10
            )
            return client
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            raise
    
    async def make_spoofed_call(
        self,
        target_number: str,
        spoofed_caller_id: str,
        call_id: str,
        webhook_url: str = None
    ) -> bool:
        """
        Make spoofed call via Asterisk call file with webhook callback
        
        Args:
            target_number: Destination number (e.g., +19564952857)
            spoofed_caller_id: Custom caller ID to display (e.g., +15551234567)
            call_id: Unique call identifier
            webhook_url: URL to call for TwiML/voice instructions
        
        Returns:
            True if call file created successfully
        """
        try:
            logger.info(f"📞 Creating spoofed call via Asterisk")
            logger.info(f"   Target: {target_number}")
            logger.info(f"   Spoofed ID: {spoofed_caller_id}")
            logger.info(f"   Call ID: {call_id}")
            logger.info(f"   Webhook: {webhook_url}")
            
            # Generate call file content with webhook application
            # CRITICAL: CallerID must be NUMBER ONLY (no caller name)
            # Use AGI or custom application to fetch TwiML from webhook
            
            if webhook_url:
                # With webhook - fetch TwiML and execute
                call_file_content = f"""Channel: SIP/infobip-trunk/{target_number}
CallerID: {spoofed_caller_id}
MaxRetries: 0
WaitTime: 30
Context: webhook-outbound
Extension: {call_id}
Priority: 1
SetVar: SPOOFED_NUMBER={spoofed_caller_id}
SetVar: CALL_ID={call_id}
SetVar: WEBHOOK_URL={webhook_url}
Archive: yes
"""
            else:
                # Without webhook - simple dial (will be silent)
                call_file_content = f"""Channel: SIP/infobip-trunk/{target_number}
CallerID: {spoofed_caller_id}
MaxRetries: 0
WaitTime: 30
Context: outbound
Extension: {target_number}
Priority: 1
SetVar: SPOOFED_NUMBER={spoofed_caller_id}
SetVar: CALL_ID={call_id}
Archive: yes
"""
            
            # Create unique temporary filename
            temp_filename = f"call_{call_id}_{uuid.uuid4().hex[:8]}.call"
            final_filename = f"call_{call_id}.call"
            
            # SSH to VPS and create call file
            ssh_client = self._create_ssh_client()
            
            try:
                # Create temp file content
                sftp = ssh_client.open_sftp()
                
                # Write call file to /tmp first (to avoid Asterisk picking up incomplete file)
                temp_path = f"/tmp/{temp_filename}"
                with sftp.file(temp_path, 'w') as f:
                    f.write(call_file_content)
                
                # Set proper permissions
                sftp.chmod(temp_path, 0o644)
                
                # Move to outgoing directory (atomic operation)
                stdin, stdout, stderr = ssh_client.exec_command(
                    f"mv {temp_path} {self.call_files_dir}/{final_filename}"
                )
                
                # Check for errors
                error_output = stderr.read().decode()
                if error_output:
                    logger.error(f"Error moving call file: {error_output}")
                    raise Exception(error_output)
                
                logger.info(f"✅ Call file created: {self.call_files_dir}/{final_filename}")
                
                sftp.close()
                
                return True
                
            finally:
                ssh_client.close()
        
        except Exception as e:
            logger.error(f"❌ Error creating spoofed call: {e}")
            raise
    
    async def check_asterisk_status(self) -> dict:
        """Check Asterisk and SIP trunk status"""
        try:
            ssh_client = self._create_ssh_client()
            
            try:
                # Check SIP peer status
                stdin, stdout, stderr = ssh_client.exec_command(
                    "asterisk -rx 'sip show peers' | grep infobip"
                )
                sip_status = stdout.read().decode().strip()
                
                # Check active channels
                stdin, stdout, stderr = ssh_client.exec_command(
                    "asterisk -rx 'core show channels' | grep 'active call'"
                )
                active_channels = stdout.read().decode().strip()
                
                return {
                    "asterisk_running": True,
                    "sip_trunk_status": sip_status,
                    "active_channels": active_channels
                }
            
            finally:
                ssh_client.close()
                
        except Exception as e:
            logger.error(f"Error checking Asterisk status: {e}")
            return {
                "asterisk_running": False,
                "error": str(e)
            }
