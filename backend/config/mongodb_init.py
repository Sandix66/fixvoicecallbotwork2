from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise ValueError("MONGO_URL environment variable is not set")

client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'callbot_db')]

async def get_database():
    """Get MongoDB database instance"""
    return db

async def init_db():
    """Initialize database with indexes"""
    try:
        # Create indexes for users collection
        await db.users.create_index("email", unique=True)
        await db.users.create_index("device_id")
        
        # Create indexes for calls collection
        await db.calls.create_index([("user_id", 1), ("created_at", -1)])
        await db.calls.create_index("call_id", unique=True)
        
        # Create indexes for signalwire_numbers collection
        await db.signalwire_numbers.create_index("phone_number", unique=True)
        
        # Create indexes for payments collection
        await db.payments.create_index("user_id")
        await db.payments.create_index("payment_id", unique=True)
        
        # Create indexes for provider_config collection
        await db.provider_config.create_index("provider_name", unique=True)
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")

async def close_db():
    """Close MongoDB connection"""
    client.close()
    logger.info("MongoDB connection closed")
