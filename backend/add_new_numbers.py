import asyncio
from config.mongodb_init import db, connect_db, close_db
from datetime import datetime, timezone

async def add_numbers():
    """Add new SignalWire numbers to database"""
    await connect_db()
    
    new_numbers = [
        "+17122177408",
        "+18663909702",
        "+18336525008",
        "+18889397693",
        "+14122844537",
        "+12192296664",
        "+19083791512",
        "+18077983095",
        "+12078865909"
    ]
    
    added_count = 0
    skipped_count = 0
    
    for number in new_numbers:
        # Check if number already exists
        existing = await db.signalwire_numbers.find_one({"phone_number": number})
        
        if existing:
            print(f"⚠️  {number} - Already exists, skipping")
            skipped_count += 1
        else:
            # Add new number
            number_data = {
                "phone_number": number,
                "assigned_to_user_id": None,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.signalwire_numbers.insert_one(number_data)
            print(f"✅ {number} - Added successfully")
            added_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Added: {added_count} numbers")
    print(f"   ⚠️  Skipped: {skipped_count} numbers (already exist)")
    
    # Show total numbers
    total = await db.signalwire_numbers.count_documents({})
    print(f"   📱 Total numbers in database: {total}")
    
    await close_db()

if __name__ == "__main__":
    asyncio.run(add_numbers())
