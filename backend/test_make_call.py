#!/usr/bin/env python3
"""
Test make call directly
"""
import asyncio
from services.signalwire_service import SignalWireService
import os
from dotenv import load_dotenv

load_dotenv()

async def test_call():
    sw = SignalWireService()
    
    print("🧪 Testing Call Initiation\n")
    
    from_number = "+12106749012"  # One of our numbers
    to_number = "+14089105678"    # Test number
    
    webhook_main = os.getenv('WEBHOOK_MAIN')
    webhook_status = os.getenv('WEBHOOK_STATUS')
    
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"Webhook: {webhook_main}")
    print(f"Status: {webhook_status}\n")
    
    # Add call_id to webhooks
    call_id = "test_call_123"
    callback_url = f"{webhook_main}?call_id={call_id}"
    status_callback = f"{webhook_status}?call_id={call_id}"
    
    print(f"Callback URL: {callback_url}")
    print(f"Status URL: {status_callback}\n")
    
    try:
        result = await sw.make_call(
            from_number=from_number,
            to_number=to_number,
            callback_url=callback_url,
            status_callback_url=status_callback
        )
        
        if result:
            print("✅ Call initiated successfully!")
            print(f"   Call SID: {result.get('sid')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Direction: {result.get('direction')}")
        else:
            print("❌ Call failed - no response from SignalWire")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_call())
