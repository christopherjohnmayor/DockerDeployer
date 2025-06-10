#!/usr/bin/env python3
"""
Test script to verify rate limiting functionality.
"""

import requests
import time
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_ENDPOINT = "/api/containers/stats/test-container"
RATE_LIMIT = 60  # 60 requests per minute
TEST_REQUESTS = 70  # Send more than the limit

def get_auth_token():
    """Get authentication token for testing."""
    login_data = {
        "username": "admin",
        "password": "AdminPassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_rate_limiting():
    """Test rate limiting on container stats endpoint."""
    print("Testing Rate Limiting Implementation")
    print("=" * 50)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔑 Authentication successful")
    print(f"📊 Testing endpoint: {TEST_ENDPOINT}")
    print(f"⚡ Rate limit: {RATE_LIMIT} requests/minute")
    print(f"🚀 Sending {TEST_REQUESTS} requests...")
    print()
    
    success_count = 0
    rate_limited_count = 0
    error_count = 0
    
    start_time = time.time()
    
    for i in range(1, TEST_REQUESTS + 1):
        try:
            response = requests.get(f"{BASE_URL}{TEST_ENDPOINT}", headers=headers)
            
            # Check for rate limiting headers
            rate_limit_headers = {
                "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
                "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
                "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset"),
                "Retry-After": response.headers.get("Retry-After")
            }
            
            if response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i:2d}: ⛔ RATE LIMITED (429) - Headers: {rate_limit_headers}")
            elif response.status_code == 200:
                success_count += 1
                print(f"Request {i:2d}: ✅ SUCCESS (200) - Remaining: {rate_limit_headers.get('X-RateLimit-Remaining', 'N/A')}")
            elif response.status_code == 404:
                success_count += 1  # Expected for non-existent container
                print(f"Request {i:2d}: ✅ SUCCESS (404 - Expected) - Remaining: {rate_limit_headers.get('X-RateLimit-Remaining', 'N/A')}")
            else:
                error_count += 1
                print(f"Request {i:2d}: ❌ ERROR ({response.status_code}) - {response.text[:100]}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
            
        except Exception as e:
            error_count += 1
            print(f"Request {i:2d}: ❌ EXCEPTION - {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print()
    print("Test Results")
    print("=" * 50)
    print(f"📊 Total requests: {TEST_REQUESTS}")
    print(f"✅ Successful requests: {success_count}")
    print(f"⛔ Rate limited requests: {rate_limited_count}")
    print(f"❌ Error requests: {error_count}")
    print(f"⏱️  Total duration: {duration:.2f} seconds")
    print(f"🚀 Requests per second: {TEST_REQUESTS/duration:.2f}")
    print()
    
    # Evaluate results
    if rate_limited_count > 0:
        print("🎉 RATE LIMITING IS WORKING!")
        print(f"   - {rate_limited_count} requests were properly rate limited")
        print(f"   - Rate limiting kicked in after ~{success_count} requests")
        return True
    else:
        print("❌ RATE LIMITING IS NOT WORKING!")
        print(f"   - All {success_count} requests succeeded")
        print(f"   - No 429 status codes received")
        print(f"   - Expected rate limiting after {RATE_LIMIT} requests")
        return False

def test_rate_limit_headers():
    """Test if rate limiting headers are present in responses."""
    print("\nTesting Rate Limit Headers")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}{TEST_ENDPOINT}", headers=headers)
        
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset"
        ]
        
        print("Response Headers:")
        for header in rate_limit_headers:
            value = response.headers.get(header)
            status = "✅" if value else "❌"
            print(f"  {status} {header}: {value or 'MISSING'}")
        
        # Check if any rate limiting headers are present
        has_headers = any(response.headers.get(h) for h in rate_limit_headers)
        
        if has_headers:
            print("\n✅ Rate limiting headers are present")
            return True
        else:
            print("\n❌ Rate limiting headers are missing")
            return False
            
    except Exception as e:
        print(f"❌ Error testing headers: {e}")
        return False

if __name__ == "__main__":
    print("DockerDeployer Rate Limiting Test")
    print("=" * 50)
    print()
    
    # Test 1: Check for rate limiting headers
    headers_working = test_rate_limit_headers()
    
    # Test 2: Test actual rate limiting
    rate_limiting_working = test_rate_limiting()
    
    print("\nFinal Assessment")
    print("=" * 50)
    
    if headers_working and rate_limiting_working:
        print("🎉 RATE LIMITING IS FULLY FUNCTIONAL")
        sys.exit(0)
    elif rate_limiting_working:
        print("⚠️  RATE LIMITING WORKS BUT HEADERS ARE MISSING")
        sys.exit(1)
    elif headers_working:
        print("⚠️  HEADERS PRESENT BUT RATE LIMITING NOT ENFORCED")
        sys.exit(1)
    else:
        print("❌ RATE LIMITING IS COMPLETELY BROKEN")
        sys.exit(1)
