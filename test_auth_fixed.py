#!/usr/bin/env python3
"""
Test script to verify DockerDeployer authentication is working.
"""

import requests
import json

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test backend health endpoint."""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_frontend_health():
    """Test frontend accessibility."""
    print("🔍 Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
        return False

def test_admin_login():
    """Test admin login."""
    print("🔍 Testing admin login...")
    try:
        login_data = {
            "username": "admin",
            "password": "AdminPassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ Admin login successful")
                print(f"   Token: {data['access_token'][:50]}...")
                return data["access_token"]
            else:
                print("❌ Admin login failed: No access token in response")
                return None
        else:
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None

def test_user_registration():
    """Test user registration."""
    print("🔍 Testing user registration...")
    try:
        register_data = {
            "username": "testuser_auth_test",
            "email": "testuser_auth_test@example.com",
            "password": "TestPassword123",
            "full_name": "Test User Auth Test"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            print("✅ User registration successful")
            print(f"   User ID: {data.get('id')}, Username: {data.get('username')}")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ User registration working (user already exists)")
            return True
        else:
            print(f"❌ User registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ User registration error: {e}")
        return False

def test_protected_endpoint(token):
    """Test accessing a protected endpoint."""
    print("🔍 Testing protected endpoint access...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/containers", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Protected endpoint access successful")
            return True
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint access error: {e}")
        return False

def main():
    """Run all authentication tests."""
    print("🚀 DockerDeployer Authentication Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Backend Health
    if test_backend_health():
        tests_passed += 1
    
    # Test 2: Frontend Health
    if test_frontend_health():
        tests_passed += 1
    
    # Test 3: User Registration
    if test_user_registration():
        tests_passed += 1
    
    # Test 4: Admin Login
    token = test_admin_login()
    if token:
        tests_passed += 1
        
        # Test 5: Protected Endpoint (only if login successful)
        if test_protected_endpoint(token):
            tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Authentication is working correctly.")
        print("\n📋 Admin Credentials:")
        print("   Username: admin")
        print("   Password: AdminPassword123")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())
