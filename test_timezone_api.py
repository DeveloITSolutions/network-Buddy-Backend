#!/usr/bin/env python3
"""
Test script for timezone API endpoints.
"""
import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test user ID (we'll get this from login)
TEST_EMAIL = "test51214@yopmail.com"
TEST_PASSWORD = "TestPassword123!"

def test_timezone_endpoints():
    """Test timezone-related API endpoints."""
    print("🌍 Testing Timezone API Endpoints")
    print("=" * 50)
    
    # Test 1: Get available timezones
    print("\n1. Testing Get Timezones...")
    try:
        response = requests.get(f"{API_BASE}/auth/timezones")
        if response.status_code == 200:
            data = response.json()
            print("✅ Get Timezones - SUCCESS")
            print(f"   Common timezones: {len(data['common_timezones'])}")
            print(f"   Grouped regions: {len(data['grouped_timezones'])}")
            
            # Show some examples
            print("   Sample common timezones:")
            for tz in data['common_timezones'][:5]:
                print(f"     - {tz['label']}")
        else:
            print(f"❌ Get Timezones - FAILED: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Get Timezones - ERROR: {e}")
    
    # Test 2: Login to get user ID
    print("\n2. Testing Login to get User ID...")
    try:
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            user_id = data['user']['id']
            print(f"✅ Login - SUCCESS")
            print(f"   User ID: {user_id}")
            print(f"   Current timezone: {data['user']['timezone']}")
        else:
            print(f"❌ Login - FAILED: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login - ERROR: {e}")
        return
    
    # Test 3: Update timezone to America/New_York
    print("\n3. Testing Update Timezone to America/New_York...")
    try:
        timezone_data = {
            "timezone": "America/New_York"
        }
        response = requests.put(f"{API_BASE}/auth/timezone/{user_id}", json=timezone_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Update Timezone - SUCCESS")
            print(f"   New timezone: {data['timezone']}")
            print(f"   UTC offset: {data['utc_offset']}")
            print(f"   Message: {data['message']}")
        else:
            print(f"❌ Update Timezone - FAILED: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Update Timezone - ERROR: {e}")
    
    # Test 4: Update timezone to Europe/London
    print("\n4. Testing Update Timezone to Europe/London...")
    try:
        timezone_data = {
            "timezone": "Europe/London"
        }
        response = requests.put(f"{API_BASE}/auth/timezone/{user_id}", json=timezone_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Update Timezone - SUCCESS")
            print(f"   New timezone: {data['timezone']}")
            print(f"   UTC offset: {data['utc_offset']}")
            print(f"   Message: {data['message']}")
        else:
            print(f"❌ Update Timezone - FAILED: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Update Timezone - ERROR: {e}")
    
    # Test 5: Test invalid timezone
    print("\n5. Testing Invalid Timezone...")
    try:
        timezone_data = {
            "timezone": "Invalid/Timezone"
        }
        response = requests.put(f"{API_BASE}/auth/timezone/{user_id}", json=timezone_data)
        if response.status_code == 400:
            print("✅ Invalid Timezone - SUCCESS (correctly rejected)")
            print(f"   Error: {response.json()['detail']}")
        else:
            print(f"❌ Invalid Timezone - FAILED: Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid Timezone - ERROR: {e}")
    
    # Test 6: Test with non-existent user ID
    print("\n6. Testing Non-existent User ID...")
    try:
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        timezone_data = {
            "timezone": "Asia/Tokyo"
        }
        response = requests.put(f"{API_BASE}/auth/timezone/{fake_user_id}", json=timezone_data)
        if response.status_code == 404:
            print("✅ Non-existent User - SUCCESS (correctly rejected)")
            print(f"   Error: {response.json()['detail']}")
        else:
            print(f"❌ Non-existent User - FAILED: Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"❌ Non-existent User - ERROR: {e}")
    
    # Test 7: Verify timezone was updated by logging in again
    print("\n7. Verifying Timezone Update...")
    try:
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Login Verification - SUCCESS")
            print(f"   Current timezone: {data['user']['timezone']}")
            if data['user']['timezone'] == "Europe/London":
                print("   ✅ Timezone successfully updated to Europe/London")
            else:
                print(f"   ⚠️  Expected Europe/London, got {data['user']['timezone']}")
        else:
            print(f"❌ Login Verification - FAILED: {response.status_code}")
    except Exception as e:
        print(f"❌ Login Verification - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Timezone API Testing Complete!")

if __name__ == "__main__":
    test_timezone_endpoints()
