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
                    
                    # Write MP3 audio to remote file
                    with sftp.file(remote_mp3_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    sftp.chmod(remote_mp3_path, 0o644)
                    
                    # Convert MP3 to WAV using sox (Asterisk compatible)
                    convert_cmd = f"sox {remote_mp3_path} -r 8000 -c 1 -b 16 {remote_wav_path}"
                    stdin, stdout, stderr = ssh_client.exec_command(convert_cmd)
                    convert_error = stderr.read().decode()
                    
                    if convert_error and 'FAIL' in convert_error:
                        logger.error(f"Sox conversion failed: {convert_error}")
                        raise Exception(f"Failed to convert {step_name} to WAV")
                    
                    # Verify WAV file created
                    try:
                        wav_stat = sftp.stat(remote_wav_path)
                        logger.info(f"✅ Converted {step_name}: MP3 ({len(audio_bytes)}b) → WAV ({wav_stat.st_size}b)")
                    except:
                        raise Exception(f"WAV file not found after conversion: {remote_wav_path}")
                    
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
            
            # Generate call file with audio playback
            # CRITICAL: Extension MUST be target_number (not call_id)!
            call_file_content = f"""Channel: SIP/infobip-trunk/{target_number}
CallerID: {spoofed_caller_id}
MaxRetries: 0
WaitTime: 30
Context: spoofing-outbound
Extension: {target_number}
Priority: 1
SetVar: SPOOFED_NUMBER={spoofed_caller_id}
SetVar: CALL_ID={call_id}
SetVar: AUDIO_STEP1={audio_paths.get('step_1', '') if audio_paths else ''}
SetVar: AUDIO_STEP2={audio_paths.get('step_2', '') if audio_paths else ''}
SetVar: AUDIO_STEP3={audio_paths.get('step_3', '') if audio_paths else ''}
SetVar: AUDIO_ACCEPTED={audio_paths.get('accepted', '') if audio_paths else ''}
SetVar: AUDIO_REJECTED={audio_paths.get('rejected', '') if audio_paths else ''}
SetVar: STATUS_URL={status_url}
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
