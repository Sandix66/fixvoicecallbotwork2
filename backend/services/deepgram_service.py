from deepgram import DeepgramClient, SpeakOptions
import os
import logging
import httpx
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class DeepgramService:
    def __init__(self):
        self.api_key = os.getenv('DEEPGRAM_API_KEY')
        if not self.api_key:
            logger.warning("Deepgram API key not configured")
            self.client = None
        else:
            self.client = DeepgramClient(self.api_key)
        
        # Temporary storage for audio files
        self.audio_dir = "/tmp/deepgram_audio"
        os.makedirs(self.audio_dir, exist_ok=True)
    
    async def text_to_speech(self, text: str, voice: str) -> str:
        """
        Convert text to speech using Deepgram and return audio file URL
        
        Args:
            text: The text to synthesize
            voice: Deepgram voice model (e.g., 'aura-2-stella-en')
        
        Returns:
            URL to the generated audio file
        """
        if not self.client:
            raise Exception("Deepgram client not initialized - API key missing")
        
        try:
            logger.info(f"Generating Deepgram TTS: voice={voice}, text_length={len(text)}")
            
            # Configure speech options
            options = SpeakOptions(
                model=voice,
            )
            
            # Generate speech
            response = self.client.speak.v("1").save(
                os.path.join(self.audio_dir, f"temp_{uuid.uuid4()}.mp3"),
                {"text": text},
                options
            )
            
            # Get audio data
            audio_data = response
            
            # Save to file
            audio_id = str(uuid.uuid4())
            filename = os.path.join(self.audio_dir, f"{audio_id}.mp3")
            
            # Write audio to file
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            # Return accessible URL
            backend_url = os.getenv('BACKEND_URL', 'https://lanjutkan-ini.preview.emergentagent.com')
            audio_url = f"{backend_url}/api/audio/deepgram/{audio_id}.mp3"
            
            logger.info(f"✅ Deepgram TTS generated: {audio_url}")
            return audio_url
            
        except Exception as e:
            logger.error(f"Error generating Deepgram TTS: {e}")
            raise
    
    def is_deepgram_voice(self, voice: str) -> bool:
        """Check if voice is a Deepgram voice"""
        return voice.startswith('aura-') or voice.startswith('aura-2-')
    
    def get_audio_file(self, audio_id: str) -> bytes:
        """Get audio file by ID"""
        filename = os.path.join(self.audio_dir, f"{audio_id}.mp3")
        
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Audio file not found: {audio_id}")
        
        with open(filename, 'rb') as f:
            return f.read()
