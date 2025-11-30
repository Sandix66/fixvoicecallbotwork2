#!/usr/bin/env python3
"""
CallBot Research System Backend API Tests
Testing JWT Authentication, MongoDB operations, and API endpoints
Focus: Bug investigation for data persistence issues
"""

import requests
import sys
import json
from datetime import datetime

class CallBotAPITester:
    def __init__(self, base_url="https://lanjutkan-ini.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user = None
        self.test_call_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success and response.get('status') == 'healthy'

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )
        return success and 'CallBot Research API' in response.get('message', '')

    def test_admin_login(self):
        """Test admin login with seeded credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "admin@callbot.com",
                "password": "admin123"
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.admin_user = response.get('user', {})
            print(f"   Admin UID: {self.admin_user.get('uid')}")
            print(f"   Admin Role: {self.admin_user.get('role')}")
            print(f"   Admin Balance: ${self.admin_user.get('balance')}")
            return True
        return False

    def test_token_verification(self):
        """Test JWT token verification"""
        if not self.token:
            print("❌ No token available for verification")
            return False
            
        success, response = self.run_test(
            "Token Verification",
            "GET",
            "auth/verify",
            200
        )
        return success and response.get('valid') == True

    def test_user_profile(self):
        """Test user profile retrieval"""
        if not self.token:
            print("❌ No token available for profile test")
            return False
            
        success, response = self.run_test(
            "User Profile",
            "GET",
            "users/profile",
            200
        )
        return success and response.get('uid') == self.admin_user.get('uid')

    def test_signalwire_numbers(self):
        """Test SignalWire numbers endpoint"""
        if not self.token:
            print("❌ No token available for SignalWire test")
            return False
            
        success, response = self.run_test(
            "Available SignalWire Numbers",
            "GET",
            "admin/signalwire/numbers/available",
            200
        )
        
        if success:
            numbers = response if isinstance(response, list) else []
            print(f"   Available numbers: {len(numbers)}")
            for num in numbers[:3]:  # Show first 3
                print(f"   - {num.get('phone_number', 'N/A')}")
            return len(numbers) > 0
        return False

    def test_signalwire_config(self):
        """Test SignalWire configuration retrieval"""
        if not self.token:
            print("❌ No token available for SignalWire config test")
            return False
            
        success, response = self.run_test(
            "SignalWire Configuration",
            "GET",
            "admin/signalwire/credentials",
            200
        )
        
        if success:
            config = response
            print(f"   Project ID: {config.get('project_id', 'N/A')[:10]}...")
            print(f"   Space URL: {config.get('space_url', 'N/A')}")
            return 'project_id' in config and 'space_url' in config
        return False

    def test_all_users(self):
        """Test get all users (admin only)"""
        if not self.token:
            print("❌ No token available for users test")
            return False
            
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "users/all",
            200
        )
        
        if success:
            users = response if isinstance(response, list) else []
            print(f"   Total users: {len(users)}")
            admin_found = any(user.get('role') == 'admin' for user in users)
            print(f"   Admin user found: {admin_found}")
            return len(users) > 0 and admin_found
        return False

    def test_unauthorized_access(self):
        """Test unauthorized access without token"""
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthorized Access Test",
            "GET",
            "users/profile",
            403  # Should return 403 Not authenticated
        )
        
        # Restore token
        self.token = temp_token
        return success  # Success means we got the expected 403

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Invalid Login Test",
            "POST",
            "auth/login",
            401,
            data={
                "email": "admin@callbot.com",
                "password": "wrongpassword"
            }
        )
        return success  # Success means we got the expected 401

    def test_create_call(self):
        """Test call creation and data persistence"""
        if not self.token:
            print("❌ No token available for call creation test")
            return False
            
        call_data = {
            "from_number": "+12078865862",
            "to_number": "+1234567890",
            "recipient_name": "John Doe",
            "service_name": "TestBank",
            "call_type": "otp",
            "provider": "signalwire",
            "language": "en-US",
            "tts_voice": "Aurora",
            "step_1_message": "Hello {name}, this is {service}",
            "step_2_message": "Your verification code is {digit}",
            "step_3_message": "Press 1 to confirm",
            "accepted_message": "Thank you for confirming",
            "rejected_message": "Request cancelled",
            "digits": 123456
        }
        
        success, response = self.run_test(
            "Create Call",
            "POST",
            "calls/start",
            200,
            data=call_data
        )
        
        if success and 'call_id' in response:
            self.test_call_id = response['call_id']
            print(f"   Call ID: {self.test_call_id}")
            print(f"   Status: {response.get('status')}")
            print(f"   From: {response.get('from_number')}")
            print(f"   To: {response.get('to_number')}")
            
            # Verify all fields are saved correctly
            fields_ok = (
                response.get('recipient_name') == call_data['recipient_name'] and
                response.get('service_name') == call_data['service_name'] and
                response.get('call_type') == call_data['call_type']
            )
            
            if not fields_ok:
                print("   ⚠️  WARNING: Some call fields may not be saved correctly")
                return False
            
            return True
        return False

    def test_get_call_details(self):
        """Test retrieving specific call details"""
        if not self.token or not self.test_call_id:
            print("❌ No token or call_id available for call details test")
            return False
            
        success, response = self.run_test(
            "Get Call Details",
            "GET",
            f"calls/{self.test_call_id}",
            200
        )
        
        if success:
            print(f"   Call ID: {response.get('call_id')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Recipient: {response.get('recipient_name')}")
            print(f"   Service: {response.get('service_name')}")
            print(f"   Events: {len(response.get('events', []))}")
            
            # Verify data persistence
            if response.get('call_id') != self.test_call_id:
                print("   ❌ Call ID mismatch!")
                return False
            
            return True
        return False

    def test_call_history(self):
        """Test call history retrieval"""
        if not self.token:
            print("❌ No token available for call history test")
            return False
            
        success, response = self.run_test(
            "Get Call History",
            "GET",
            "calls/history",
            200
        )
        
        if success:
            calls = response if isinstance(response, list) else []
            print(f"   Total calls in history: {len(calls)}")
            
            if len(calls) > 0:
                # Check if our test call is in history
                test_call_found = any(call.get('call_id') == self.test_call_id for call in calls)
                print(f"   Test call found in history: {test_call_found}")
                
                # Show first call details
                first_call = calls[0]
                print(f"   Latest call: {first_call.get('call_id')}")
                print(f"   Status: {first_call.get('status')}")
                print(f"   Created: {first_call.get('created_at')}")
                
                return test_call_found
            else:
                print("   ⚠️  WARNING: No calls found in history!")
                return False
        return False

    def test_database_persistence(self):
        """Test if data persists in database"""
        if not self.token or not self.test_call_id:
            print("❌ No token or call_id available for persistence test")
            return False
        
        print(f"\n🔍 Testing Database Persistence...")
        print(f"   Retrieving call {self.test_call_id} again...")
        
        # Get call details again to verify persistence
        success, response = self.run_test(
            "Verify Data Persistence",
            "GET",
            f"calls/{self.test_call_id}",
            200
        )
        
        if success:
            # Check all critical fields
            critical_fields = ['call_id', 'user_id', 'from_number', 'to_number', 
                             'recipient_name', 'service_name', 'status', 'created_at']
            
            missing_fields = [field for field in critical_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            
            print(f"   ✅ All critical fields present")
            return True
        
        return False

    def test_user_data_persistence(self):
        """Test if user data persists correctly"""
        if not self.token:
            print("❌ No token available for user persistence test")
            return False
        
        print(f"\n🔍 Testing User Data Persistence...")
        
        # Get profile multiple times to verify consistency
        success1, response1 = self.run_test(
            "Get Profile (1st time)",
            "GET",
            "users/profile",
            200
        )
        
        if not success1:
            return False
        
        # Get profile again
        success2, response2 = self.run_test(
            "Get Profile (2nd time)",
            "GET",
            "users/profile",
            200
        )
        
        if not success2:
            return False
        
        # Compare responses
        if response1.get('uid') != response2.get('uid'):
            print("   ❌ User ID mismatch between requests!")
            return False
        
        if response1.get('balance') != response2.get('balance'):
            print("   ❌ Balance mismatch between requests!")
            return False
        
        print(f"   ✅ User data consistent across requests")
        return True

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting CallBot Analytics Backend API Tests")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n📡 CONNECTIVITY TESTS")
        self.test_health_check()
        self.test_root_endpoint()
        
        # Authentication tests
        print("\n🔐 AUTHENTICATION TESTS")
        self.test_invalid_login()
        self.test_admin_login()
        self.test_token_verification()
        self.test_unauthorized_access()
        
        # User management tests
        print("\n👤 USER MANAGEMENT TESTS")
        self.test_user_profile()
        self.test_all_users()
        
        # SignalWire integration tests
        print("\n📞 SIGNALWIRE INTEGRATION TESTS")
        self.test_signalwire_config()
        self.test_signalwire_numbers()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test function"""
    tester = CallBotAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())