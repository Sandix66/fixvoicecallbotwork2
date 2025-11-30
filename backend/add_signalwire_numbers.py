#!/usr/bin/env python3
"""
Add SignalWire numbers to Firestore
"""
from config.firebase_init import db
from datetime import datetime

def add_signalwire_numbers():
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
    
    print("🔢 Adding SignalWire numbers to Firestore...\n")
    
    for number in numbers:
        try:
            # Check if number already exists
            existing = db.collection('signalwire_numbers').where('phone_number', '==', number).limit(1).get()
            
            if len(list(existing)) > 0:
                print(f"⚠️  {number} already exists, skipping...")
                continue
            
            # Add new number
            number_data = {
                'phone_number': number,
                'assigned_to_user_id': None,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            number_ref = db.collection('signalwire_numbers').document()
            number_ref.set(number_data)
            
            print(f"✅ Added: {number}")
            
        except Exception as e:
            print(f"❌ Error adding {number}: {e}")
    
    print(f"\n🎉 SignalWire numbers added successfully!")
    print(f"📊 Total numbers in database:")
    
    # Show all numbers
    all_numbers = db.collection('signalwire_numbers').stream()
    count = 0
    for doc in all_numbers:
        data = doc.to_dict()
        count += 1
        status = "🟢 Active" if data.get('is_active') else "🔴 Inactive"
        print(f"   {count}. {data['phone_number']} - {status}")
    
    print(f"\n✨ Total: {count} numbers available")

if __name__ == "__main__":
    add_signalwire_numbers()
