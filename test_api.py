#!/usr/bin/env python3
"""
Comprehensive API testing script for The Plugs authentication flow.
Tests all 5 authentication endpoints with proper error handling.
"""
import requests
import json
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials
TEST_EMAIL = "test@yopmail.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NEW_PASSWORD = "NewTestPassword456!"

class APITester:
    """API testing class for authentication flow."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "ThePlugs-API-Tester/1.0"
        })
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        try:
            response = self.session.get(f"{API_BASE}/health/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status Code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_login(self) -> Dict[str, Any]:
        """Test login endpoint."""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            response = self.session.post(f"{API_BASE}/auth/login", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Login", True, f"User: {data['user']['email']}")
                return data
            else:
                self.log_test("Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
        except Exception as e:
            self.log_test("Login", False, f"Error: {str(e)}")
            return {}
    
    def test_reset_password(self) -> bool:
        """Test reset password endpoint."""
        try:
            payload = {"email": TEST_EMAIL}
            response = self.session.post(f"{API_BASE}/auth/reset-password", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Reset Password", True, f"Message: {data.get('message')}")
                return True
            else:
                self.log_test("Reset Password", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Reset Password", False, f"Error: {str(e)}")
            return False
    
    def test_send_otp(self) -> bool:
        """Test send OTP endpoint."""
        try:
            payload = {"email": TEST_EMAIL}
            response = self.session.post(f"{API_BASE}/auth/send-otp", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Send OTP", True, f"Message: {data.get('message')}")
                return True
            else:
                self.log_test("Send OTP", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Send OTP", False, f"Error: {str(e)}")
            return False
    
    def test_verify_otp(self, otp_code: str = "123456") -> Dict[str, Any]:
        """Test verify OTP endpoint."""
        try:
            payload = {
                "email": TEST_EMAIL,
                "otp_code": otp_code
            }
            response = self.session.post(f"{API_BASE}/auth/verify-otp", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Verify OTP", True, f"Message: {data.get('message')}")
                return data
            else:
                self.log_test("Verify OTP", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
        except Exception as e:
            self.log_test("Verify OTP", False, f"Error: {str(e)}")
            return {}
    
    def test_change_password(self, token: str) -> bool:
        """Test change password endpoint."""
        try:
            payload = {
                "email": TEST_EMAIL,
                "new_password": TEST_NEW_PASSWORD,
                "token": token
            }
            response = self.session.post(f"{API_BASE}/auth/change-password", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Change Password", True, f"Message: {data.get('message')}")
                return True
            else:
                self.log_test("Change Password", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Change Password", False, f"Error: {str(e)}")
            return False
    
    def test_login_with_new_password(self) -> bool:
        """Test login with new password."""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_NEW_PASSWORD
            }
            response = self.session.post(f"{API_BASE}/auth/login", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Login with New Password", True, f"User: {data['user']['email']}")
                return True
            else:
                self.log_test("Login with New Password", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login with New Password", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_login(self) -> bool:
        """Test login with invalid credentials."""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": "WrongPassword"
            }
            response = self.session.post(f"{API_BASE}/auth/login", json=payload)
            
            if response.status_code == 401:
                self.log_test("Invalid Login", True, "Correctly rejected invalid credentials")
                return True
            else:
                self.log_test("Invalid Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid Login", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_otp(self) -> bool:
        """Test verify OTP with invalid code."""
        try:
            payload = {
                "email": TEST_EMAIL,
                "otp_code": "999999"
            }
            response = self.session.post(f"{API_BASE}/auth/verify-otp", json=payload)
            
            if response.status_code == 400:
                self.log_test("Invalid OTP", True, "Correctly rejected invalid OTP")
                return True
            else:
                self.log_test("Invalid OTP", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid OTP", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting The Plugs API Tests")
        print("=" * 50)
        
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        self.test_health_check()
        
        # Test 2: Login with valid credentials
        print("\n2. Testing Login...")
        login_data = self.test_login()
        
        # Test 3: Invalid login
        print("\n3. Testing Invalid Login...")
        self.test_invalid_login()
        
        # Test 4: Reset Password
        print("\n4. Testing Reset Password...")
        self.test_reset_password()
        
        # Test 5: Send OTP
        print("\n5. Testing Send OTP...")
        self.test_send_otp()
        
        # Test 6: Invalid OTP
        print("\n6. Testing Invalid OTP...")
        self.test_invalid_otp()
        
        # Test 7: Verify OTP (Note: This will fail in real scenario without actual OTP)
        print("\n7. Testing Verify OTP...")
        print("    Note: This test uses a dummy OTP and will likely fail")
        verify_data = self.test_verify_otp("123456")
        
        # Test 8: Change Password (if OTP verification succeeded)
        if verify_data and "token" in verify_data:
            print("\n8. Testing Change Password...")
            self.test_change_password(verify_data["token"])
            
            # Test 9: Login with new password
            print("\n9. Testing Login with New Password...")
            self.test_login_with_new_password()
        else:
            print("\n8. Skipping Change Password (no valid token)")
            print("\n9. Skipping Login with New Password (no valid token)")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! API is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the details above.")
        
        return passed == total

def main():
    """Main function to run API tests."""
    tester = APITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
