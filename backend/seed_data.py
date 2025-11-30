#!/usr/bin/env python3
"""
Seed initial data to MongoDB
- Admin user
- SignalWire configuration
- SignalWire phone numbers
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

from config.mongodb_init import db, init_db
from services.mongodb_service import MongoDBService
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_admin_user():
    """Create admin user"""
    try:
        # Check if admin already exists
        existing_admin = await db.users.find_one({"email": "admin@callbot.com"})
        if existing_admin:
            logger.info("✅ Admin user already exists")
            return existing_admin['uid']
        
        # Create admin user
        admin_data = await MongoDBService.create_user(
            email="admin@callbot.com",
            password="admin123",
            username="Admin",
            role="admin",
            balance=1000.0
        )
        
        logger.info(f"✅ Admin user created: {admin_data['email']}")
        return admin_data['uid']
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        return None

async def seed_signalwire_config():
    """Seed SignalWire configuration from PROJECT_HANDOFF.md"""
    try:
        config_data = {
            "project_id": "bf825aef-aa0a-402f-a908-2d1c54733518",
            "space_url": "marauang-rauang.signalwire.com",
            "token": "PTf3a107d98daf47a94fee499d736507ec38b7281a3a375b66"
        }
        
        await MongoDBService.set_provider_config('signalwire', config_data)
        logger.info("✅ SignalWire configuration saved")
    except Exception as e:
        logger.error(f"❌ Error saving SignalWire config: {e}")

async def seed_signalwire_numbers():
    """Seed SignalWire phone numbers"""
    numbers = [
        "+12106749012",
        "+14232594719",
        "+18882676520",
        "+18142934760",
        "+18336596004",
        "+17023567895",
        "+15012229881",
        "+12019792184"
    ]
    
    added_count = 0
    for number in numbers:
        try:
            # Check if number already exists
            existing = await db.signalwire_numbers.find_one({"phone_number": number})
            if existing:
                logger.info(f"⏭️  Number already exists: {number}")
                continue
            
            success = await MongoDBService.add_signalwire_number(number)
            if success:
                added_count += 1
                logger.info(f"✅ Added number: {number}")
        except Exception as e:
            logger.error(f"❌ Error adding number {number}: {e}")
    
    logger.info(f"✅ Added {added_count} new SignalWire numbers")

async def seed_telegram_config():
    """Seed Telegram bot configuration"""
    try:
        config_data = {
            "bot_token": "8179370597:AAHPl3T3lixwxukN0Y0_wcrgVXZRjB19wOQ",
            "channel_id": "-1003442553402"
        }
        
        await MongoDBService.set_provider_config('telegram', config_data)
        logger.info("✅ Telegram configuration saved")
    except Exception as e:
        logger.error(f"❌ Error saving Telegram config: {e}")

async def main():
    """Main seeding function"""
    logger.info("🌱 Starting database seeding...")
    
    try:
        # Initialize database indexes
        await init_db()
        logger.info("✅ Database indexes initialized")
        
        # Seed data
        admin_uid = await seed_admin_user()
        await seed_signalwire_config()
        await seed_signalwire_numbers()
        await seed_telegram_config()
        
        logger.info("\n✅ Database seeding completed successfully!")
        logger.info(f"\n📝 Admin Login:")
        logger.info(f"   Email: admin@callbot.com")
        logger.info(f"   Password: admin123")
        logger.info(f"   Balance: $1000")
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
