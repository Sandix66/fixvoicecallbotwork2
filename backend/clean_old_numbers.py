#!/usr/bin/env python3
"""
Clean old SignalWire numbers and keep only the new one
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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_numbers():
    """Delete all old numbers and keep only the new one"""
    try:
        # New number to keep
        new_number = "+12078865862"
        
        logger.info("🗑️  Deleting all old SignalWire numbers...")
        
        # Delete ALL numbers
        result = await db.signalwire_numbers.delete_many({})
        logger.info(f"✅ Deleted {result.deleted_count} old numbers")
        
        # Add only the new number
        logger.info(f"➕ Adding new number: {new_number}")
        await db.signalwire_numbers.insert_one({
            "phone_number": new_number,
            "assigned_to_user_id": None,
            "is_active": True,
            "created_at": "2025-11-30T00:00:00+00:00"
        })
        
        logger.info(f"✅ Successfully added {new_number}")
        
        # Verify
        count = await db.signalwire_numbers.count_documents({})
        logger.info(f"\n📊 Total numbers in database: {count}")
        
        # List all numbers
        cursor = db.signalwire_numbers.find({})
        async for num in cursor:
            logger.info(f"   - {num['phone_number']}")
        
    except Exception as e:
        logger.error(f"❌ Cleaning failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(clean_numbers())
