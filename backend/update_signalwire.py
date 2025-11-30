#!/usr/bin/env python3
"""
Update SignalWire credentials and phone numbers in MongoDB
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

from config.mongodb_init import db
from services.mongodb_service import MongoDBService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_signalwire():
    """Update SignalWire configuration and phone numbers"""
    try:
        # 1. Update SignalWire credentials
        logger.info("🔄 Updating SignalWire credentials...")
        config_data = {
            "project_id": "35bf55a6-45f6-40f2-bedf-81cb805ff311",
            "space_url": "catherine.signalwire.com",
            "token": "PT8acd9ae620bd53e2156bd370d821a60afd81459f4c17e796"
        }
        
        await MongoDBService.set_provider_config('signalwire', config_data)
        logger.info("✅ SignalWire credentials updated")
        
        # 2. Delete all old phone numbers
        logger.info("🗑️  Deleting old phone numbers...")
        result = await db.signalwire_numbers.delete_many({})
        logger.info(f"✅ Deleted {result.deleted_count} old phone numbers")
        
        # 3. Add new phone number
        logger.info("➕ Adding new phone number...")
        new_number = "+12078865862"
        success = await MongoDBService.add_signalwire_number(new_number)
        
        if success:
            logger.info(f"✅ Added new phone number: {new_number}")
        else:
            logger.warning(f"⚠️  Phone number already exists: {new_number}")
        
        logger.info("\n✅ SignalWire update completed successfully!")
        logger.info(f"\n📝 New Configuration:")
        logger.info(f"   Project ID: 35bf55a6-45f6-40f2-bedf-81cb805ff311")
        logger.info(f"   Space URL: catherine.signalwire.com")
        logger.info(f"   Phone Number: +12078865862")
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(update_signalwire())
