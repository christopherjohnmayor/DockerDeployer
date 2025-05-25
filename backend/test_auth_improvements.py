#!/usr/bin/env python3
"""
Test script for authentication improvements.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

import json

import requests

BASE_URL = "http://localhost:8000"


def test_login_with_email():
    """Test login with email instead of username."""
    print("Testing login with email...")

    # First, let's register a test user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ Test user registered successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✓ Test user already exists")
        else:
            print(f"✗ Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return False

    # Test login with username
    login_data = {"username": "testuser", "password": "TestPassword123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✓ Login with username successful")
        else:
            print(
                f"✗ Login with username failed: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        print(f"✗ Login with username error: {e}")
        return False

    # Test login with email
    login_data = {
        "username": "test@example.com",  # Using email in username field
        "password": "TestPassword123",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✓ Login with email successful")
            return True
        else:
            print(
                f"✗ Login with email failed: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        print(f"✗ Login with email error: {e}")
        return False


def test_password_reset_flow():
    """Test password reset functionality."""
    print("\nTesting password reset flow...")

    # Test password reset request
    reset_request_data = {"email": "test@example.com"}

    try:
        response = requests.post(
            f"{BASE_URL}/auth/password-reset-request", json=reset_request_data
        )
        if response.status_code == 200:
            print("✓ Password reset request successful")
        else:
            print(
                f"✗ Password reset request failed: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        print(f"✗ Password reset request error: {e}")
        return False

    # Note: In a real scenario, we would get the token from email
    # For testing, we'll just verify the endpoint exists
    print("✓ Password reset endpoints are accessible")
    return True


def test_user_management_endpoints():
    """Test user management endpoints (admin only)."""
    print("\nTesting user management endpoints...")

    # First, login as admin (we need to create an admin user first)
    # For now, just test that the endpoints exist and require authentication

    try:
        response = requests.get(f"{BASE_URL}/auth/admin/users")
        if response.status_code == 401:
            print("✓ User management endpoints require authentication")
            return True
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ User management endpoint error: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing DockerDeployer Authentication Improvements")
    print("=" * 50)

    tests = [
        test_login_with_email,
        test_password_reset_flow,
        test_user_management_endpoints,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
