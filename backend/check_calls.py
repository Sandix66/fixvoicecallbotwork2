#!/usr/bin/env python3
"""
Check calls in Firestore
"""
from config.firebase_init import db

def check_calls():
    print("📊 Checking Calls in Firestore\n")
    
    calls_ref = db.collection('calls').limit(10).stream()
    
    calls = []
    for doc in calls_ref:
        call_data = doc.to_dict()
        call_data['call_id'] = doc.id
        calls.append(call_data)
    
    if not calls:
        print("⚠️  No calls found in database")
        return
    
    print(f"✅ Found {len(calls)} calls:\n")
    
    for i, call in enumerate(calls, 1):
        print(f"{'='*60}")
        print(f"Call #{i}")
        print(f"  Call ID: {call.get('call_id')}")
        print(f"  User ID: {call.get('user_id')}")
        print(f"  From: {call.get('from_number')}")
        print(f"  To: {call.get('to_number')}")
        print(f"  Service: {call.get('service_name')}")
        print(f"  Status: {call.get('status')}")
        print(f"  Created: {call.get('created_at')}")
        print(f"  Events: {len(call.get('events', []))} events")
        
        if call.get('events'):
            print(f"  Last Event: {call['events'][-1]}")

if __name__ == "__main__":
    check_calls()
