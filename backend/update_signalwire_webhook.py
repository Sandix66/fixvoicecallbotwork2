#!/usr/bin/env python3
"""
Update webhook URLs for SignalWire phone numbers
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.signalwire_service import SignalWireService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_webhooks():
    """Update webhooks for all SignalWire phone numbers"""
    try:
        signalwire = SignalWireService()
        
        # Webhook URLs
        webhook_base = "https://piddly-tenable-frederic.ngrok-free.dev"
        voice_url = f"{webhook_base}/signalwire-webhook.php"
        status_callback = f"{webhook_base}/signalwire-status.php"
        
        logger.info("🔄 Fetching phone numbers from SignalWire...")
        
        # Get all phone numbers
        phone_numbers = await signalwire.list_phone_numbers()
        
        if not phone_numbers:
            logger.warning("⚠️  No phone numbers found in SignalWire account")
            return
        
        logger.info(f"📱 Found {len(phone_numbers)} phone number(s)")
        
        # Update webhook for each number
        for phone in phone_numbers:
            phone_number = phone.get('phone_number')
            phone_sid = phone.get('sid')
            
            logger.info(f"\n🔄 Updating webhook for {phone_number}...")
            
            success = await signalwire.update_phone_webhook(
                phone_number_sid=phone_sid,
                voice_url=voice_url,
                status_callback_url=status_callback
            )
            
            if success:
                logger.info(f"✅ Webhook updated for {phone_number}")
                logger.info(f"   Voice URL: {voice_url}")
                logger.info(f"   Status Callback: {status_callback}")
            else:
                logger.error(f"❌ Failed to update webhook for {phone_number}")
        
        logger.info("\n✅ Webhook update process completed!")
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(update_webhooks())
