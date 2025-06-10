#!/usr/bin/env python3
"""
Final comprehensive rate limiting test for DockerDeployer.
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "AdminPassword123"}

def get_auth_token():
    """Get authentication token."""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS, timeout=5)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_endpoint_rate_limiting(endpoint, headers=None, limit=60, test_name=""):
    """Test rate limiting for a specific endpoint."""
    print(f"\n=== {test_name} ===")
    print(f"Endpoint: {endpoint}")
    print(f"Expected limit: {limit}/minute")
    
    success_count = 0
    rate_limited_count = 0
    
    # Test with more requests than the limit
    test_requests = min(limit + 10, 20)  # Don't overwhelm the server
    
    for i in range(test_requests):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            
            # Check rate limiting headers
            rate_headers = {
                "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
                "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
            }
            
            if response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i+1:2d}: ⛔ RATE LIMITED (429)")
                break
            elif response.status_code in [200, 404]:  # 404 is expected for non-existent containers
                success_count += 1
                remaining = rate_headers.get("X-RateLimit-Remaining", "N/A")
                print(f"Request {i+1:2d}: ✅ SUCCESS ({response.status_code}) - Remaining: {remaining}")
            else:
                print(f"Request {i+1:2d}: ❓ UNEXPECTED ({response.status_code})")
            
            time.sleep(0.1)  # Small delay
            
        except Exception as e:
            print(f"Request {i+1:2d}: ❌ ERROR - {e}")
            break
    
    # Evaluate results
    print(f"\nResults:")
    print(f"  ✅ Successful requests: {success_count}")
    print(f"  ⛔ Rate limited requests: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print(f"  🎉 RATE LIMITING IS WORKING!")
        return True
    else:
        print(f"  ❌ RATE LIMITING IS NOT WORKING!")
        return False

def main():
    """Run comprehensive rate limiting tests."""
    print("DockerDeployer Final Rate Limiting Test")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different endpoints
    tests = [
        {
            "endpoint": "/test-rate-limit",
            "headers": None,  # No auth required
            "limit": 5,
            "name": "Test Endpoint (No Auth) - @rate_limit_api"
        },
        {
            "endpoint": "/test-rate-limit-metrics", 
            "headers": None,  # No auth required
            "limit": 3,
            "name": "Test Metrics Endpoint (No Auth) - @rate_limit_metrics"
        },
        {
            "endpoint": "/test-rate-limit-auth/test-container",
            "headers": headers,  # Auth required
            "limit": 3,
            "name": "Test Auth Endpoint - @rate_limit_metrics + Auth"
        },
        {
            "endpoint": "/api/containers/test-container/stats",
            "headers": headers,  # Auth required
            "limit": 60,
            "name": "Container Stats Endpoint - @rate_limit_metrics + Auth (CRITICAL)"
        },
    ]
    
    results = []
    
    for test in tests:
        result = test_endpoint_rate_limiting(
            test["endpoint"],
            test["headers"],
            test["limit"],
            test["name"]
        )
        results.append((test["name"], result))
        
        # Wait between tests to avoid interference
        time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    
    working_count = 0
    for name, result in results:
        status = "✅ WORKING" if result else "❌ BROKEN"
        print(f"{status}: {name}")
        if result:
            working_count += 1
    
    print(f"\nOverall: {working_count}/{len(results)} endpoints have working rate limiting")
    
    # Critical assessment
    critical_endpoint_working = results[-1][1]  # Container stats endpoint
    
    if critical_endpoint_working:
        print("\n🎉 SUCCESS: Critical container stats endpoint rate limiting is WORKING!")
        print("✅ Production deployment security requirement is MET!")
        return True
    else:
        print("\n❌ FAILURE: Critical container stats endpoint rate limiting is BROKEN!")
        print("🚫 Production deployment security requirement is NOT MET!")
        print("🔧 Further investigation and fixes required!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
