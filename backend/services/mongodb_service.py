from config.mongodb_init import db
from datetime import datetime, timezone
from passlib.context import CryptContext
import uuid
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MongoDBService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    async def create_user(email: str, password: str, username: str, role: str = "user", balance: float = 0.0):
        """Create new user in MongoDB"""
        try:
            # Check if user already exists
            existing_user = await db.users.find_one({"email": email})
            if existing_user:
                raise ValueError("User with this email already exists")
            
            user_id = str(uuid.uuid4())
            user_data = {
                'uid': user_id,
                'email': email,
                'username': username,
                'password_hash': MongoDBService.hash_password(password),
                'role': role,
                'balance': balance,
                'device_id': None,
                'telegram_id': None,
                'can_use_spoofing': False,  # Default: no spoofing permission
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.users.insert_one(user_data)
            
            # Remove password_hash from response
            user_data.pop('password_hash', None)
            user_data.pop('_id', None)
            return user_data
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    @staticmethod
    async def get_user_by_email(email: str):
        """Get user by email"""
        user = await db.users.find_one({"email": email})
        if user:
            user.pop('_id', None)
        return user
    
    @staticmethod
    async def get_user(uid: str):
        """Get user by UID"""
        user = await db.users.find_one({"uid": uid})
        if user:
            user.pop('_id', None)
            user.pop('password_hash', None)
        return user
    
    @staticmethod
    async def update_user_balance(uid: str, amount: float):
        """Update user balance"""
        result = await db.users.update_one(
            {"uid": uid},
            {"$set": {"balance": amount}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_device_id(uid: str, device_id: str):
        """Update user device ID"""
        result = await db.users.update_one(
            {"uid": uid},
            {"$set": {"device_id": device_id}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def link_telegram(uid: str, telegram_id: str):
        """Link Telegram account to user"""
        result = await db.users.update_one(
            {"uid": uid},
            {"$set": {"telegram_id": telegram_id}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def get_all_users():
        """Get all users (admin only)"""
        cursor = db.users.find({})
        users = []
        async for doc in cursor:
            doc.pop('_id', None)
            doc.pop('password_hash', None)
            users.append(doc)
        return users
    
    @staticmethod
    async def delete_user(uid: str):
        """Delete user from MongoDB"""
        try:
            result = await db.users.delete_one({"uid": uid})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise
    
    @staticmethod
    async def update_user(uid: str, update_data: dict):
        """Update user fields"""
        try:
            # Remove fields that shouldn't be updated directly
            update_data.pop('uid', None)
            update_data.pop('_id', None)
            update_data.pop('created_at', None)
            
            # Hash password if provided
            if 'password' in update_data:
                update_data['password_hash'] = MongoDBService.hash_password(update_data.pop('password'))
            
            result = await db.users.update_one(
                {"uid": uid},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    # Call Management
    @staticmethod
    async def create_call_log(call_data: dict):
        """Create call log in MongoDB"""
        call_id = str(uuid.uuid4())
        call_data['call_id'] = call_id
        call_data['created_at'] = datetime.now(timezone.utc).isoformat()
        call_data['events'] = call_data.get('events', [])
        
        await db.calls.insert_one(call_data)
        call_data.pop('_id', None)
        return call_data
    
    @staticmethod
    async def get_call(call_id: str):
        """Get call by ID"""
        call = await db.calls.find_one({"call_id": call_id})
        if call:
            call.pop('_id', None)
        return call
    
    @staticmethod
    async def update_call_status(call_id: str, status: str):
        """Update call status"""
        result = await db.calls.update_one(
            {"call_id": call_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_call_events(call_id: str, event: dict):
        """Add event to call log"""
        event['time'] = datetime.now(timezone.utc).isoformat()
        result = await db.calls.update_one(
            {"call_id": call_id},
            {"$push": {"events": event}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_call_field(call_id: str, field: str, value):
        """Update specific call field"""
        result = await db.calls.update_one(
            {"call_id": call_id},
            {"$set": {field: value}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_call_data(call_id: str, update_data: dict):
        """Update multiple call fields"""
        result = await db.calls.update_one(
            {"call_id": call_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def get_user_calls(user_id: str, limit: int = 100):
        """Get user call history"""
        cursor = db.calls.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        calls = []
        async for doc in cursor:
            doc.pop('_id', None)
            calls.append(doc)
        return calls
    
    @staticmethod
    async def get_all_calls(limit: int = 100):
        """Get all calls (admin only)"""
        cursor = db.calls.find({}).sort("created_at", -1).limit(limit)
        calls = []
        async for doc in cursor:
            doc.pop('_id', None)
            calls.append(doc)
        return calls
    
    # SignalWire Numbers
    @staticmethod
    async def get_signalwire_numbers():
        """Get all SignalWire numbers"""
        cursor = db.signalwire_numbers.find({})
        numbers = []
        async for doc in cursor:
            doc.pop('_id', None)
            numbers.append(doc)
        return numbers
    
    @staticmethod
    async def get_available_numbers():
        """Get available SignalWire numbers (not assigned)"""
        cursor = db.signalwire_numbers.find({"assigned_to_user_id": None, "is_active": True})
        numbers = []
        async for doc in cursor:
            doc.pop('_id', None)
            numbers.append(doc)
        return numbers
    
    @staticmethod
    async def assign_number(phone_number: str, user_id: str):
        """Assign number to user"""
        result = await db.signalwire_numbers.update_one(
            {"phone_number": phone_number},
            {"$set": {"assigned_to_user_id": user_id}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def add_signalwire_number(phone_number: str):
        """Add new SignalWire number"""
        try:
            existing = await db.signalwire_numbers.find_one({"phone_number": phone_number})
            if existing:
                return False
            
            await db.signalwire_numbers.insert_one({
                "phone_number": phone_number,
                "assigned_to_user_id": None,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding number: {e}")
            return False
    
    # Payments
    @staticmethod
    async def create_payment(user_id: str, amount: float, method: str):
        """Create payment record"""
        payment_id = str(uuid.uuid4())
        payment_data = {
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'method': method,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.payments.insert_one(payment_data)
        payment_data.pop('_id', None)
        return payment_data
    
    @staticmethod
    async def get_payment(payment_id: str):
        """Get payment by ID"""
        payment = await db.payments.find_one({"payment_id": payment_id})
        if payment:
            payment.pop('_id', None)
        return payment
    
    @staticmethod
    async def update_payment_status(payment_id: str, status: str):
        """Update payment status"""
        result = await db.payments.update_one(
            {"payment_id": payment_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def get_user_payments(user_id: str):
        """Get user payments"""
        cursor = db.payments.find({"user_id": user_id}).sort("created_at", -1)
        payments = []
        async for doc in cursor:
            doc.pop('_id', None)
            payments.append(doc)
        return payments
    
    # Provider Config
    @staticmethod
    async def get_provider_config(provider_name: str):
        """Get provider configuration"""
        config = await db.provider_config.find_one({"provider_name": provider_name})
        if config:
            config.pop('_id', None)
        return config
    
    @staticmethod
    async def set_provider_config(provider_name: str, config_data: dict):
        """Set or update provider configuration"""
        config_data['provider_name'] = provider_name
        config_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db.provider_config.update_one(
            {"provider_name": provider_name},
            {"$set": config_data},
            upsert=True
        )
        return True
