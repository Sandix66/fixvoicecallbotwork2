#!/usr/bin/env python3
"""
Test SignalWire API Connection
"""
import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_signalwire():
    project_id = os.getenv('SIGNALWIRE_PROJECT_ID')
    token = os.getenv('SIGNALWIRE_TOKEN')
    space_url = os.getenv('SIGNALWIRE_SPACE_URL')
    
    print("🧪 Testing SignalWire Configuration\n")
    print(f"Project ID: {project_id}")
    print(f"Space URL: {space_url}")
    print(f"Token: {token[:10]}...{token[-4:]}\n")
    
    base_url = f"https://{space_url}"
    
    # Test 1: Check account
    print("📋 Test 1: Checking Account...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/laml/2010-04-01/Accounts/{project_id}.json",
                auth=(project_id, token),
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ Account check: SUCCESS")
                data = response.json()
                print(f"   Account Status: {data.get('status')}")
            else:
                print(f"❌ Account check: FAILED")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Account check: ERROR - {e}")
    
    # Test 2: List available numbers
    print(f"\n📞 Test 2: Listing Available Phone Numbers...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/laml/2010-04-01/Accounts/{project_id}/IncomingPhoneNumbers.json",
                auth=(project_id, token),
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                numbers = data.get('incoming_phone_numbers', [])
                print(f"✅ Found {len(numbers)} phone numbers:")
                for num in numbers[:5]:  # Show first 5
                    print(f"   - {num.get('phone_number')} (SID: {num.get('sid')})")
            else:
                print(f"❌ List numbers: FAILED")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ List numbers: ERROR - {e}")
    
    # Test 3: Try to make a test call
    print(f"\n📲 Test 3: Testing Call Initiation (Dry Run)...")
    test_from = "+12106749012"  # Use one of our numbers
    test_to = "+1234567890"     # Dummy number
    
    print(f"   From: {test_from}")
    print(f"   To: {test_to}")
    print(f"   Callback: https://lanjutkan-ini.preview.emergentagent.com/api/webhooks/signalwire/test")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/laml/2010-04-01/Accounts/{project_id}/Calls.json",
                auth=(project_id, token),
                data={
                    'From': test_from,
                    'To': test_to,
                    'Url': 'https://lanjutkan-ini.preview.emergentagent.com/api/webhooks/signalwire/test',
                    'StatusCallback': 'https://lanjutkan-ini.preview.emergentagent.com/api/webhooks/signalwire/test/status'
                },
                timeout=10.0
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Call initiated successfully!")
                print(f"   Call SID: {data.get('sid')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Direction: {data.get('direction')}")
            elif response.status_code == 400:
                print(f"⚠️  Call failed (expected for test)")
                error_data = response.json()
                print(f"   Error: {error_data}")
            else:
                print(f"❌ Call failed")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Call test: ERROR - {e}")
    
    print(f"\n{'='*50}")
    print("🏁 Test Complete")

if __name__ == "__main__":
    asyncio.run(test_signalwire())
