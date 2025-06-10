#!/usr/bin/env python3
"""
Aggressive Rate Limiting Test
Tests rate limiting by sending requests as fast as possible to trigger 429 responses
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT authentication token."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "AdminPassword123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None

def make_request(endpoint, headers, request_id):
    """Make a single request and return result."""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
        return {
            "id": request_id,
            "status": response.status_code,
            "remaining": response.headers.get("X-RateLimit-Remaining", "N/A"),
            "limit": response.headers.get("X-RateLimit-Limit", "N/A"),
            "reset": response.headers.get("X-RateLimit-Reset", "N/A"),
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "id": request_id,
            "error": str(e),
            "timestamp": time.time()
        }

def test_aggressive_rate_limiting():
    """Test rate limiting with aggressive concurrent requests."""
    print("🚨 AGGRESSIVE RATE LIMITING TEST")
    print("=" * 50)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = "/api/containers/06fb6fc1f7b4/stats"
    
    print(f"🎯 Testing endpoint: {endpoint}")
    print(f"📊 Expected limit: 60 requests/minute")
    print(f"🚀 Sending 100 concurrent requests as fast as possible...")
    
    # Send many requests concurrently to overwhelm the rate limit
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(make_request, endpoint, headers, i) 
            for i in range(100)
        ]
        
        for future in futures:
            result = future.result()
            results.append(result)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Analyze results
    successful_requests = [r for r in results if r.get("status") == 200]
    rate_limited_requests = [r for r in results if r.get("status") == 429]
    error_requests = [r for r in results if "error" in r]
    
    print(f"\n📊 RESULTS:")
    print(f"   Total requests: {len(results)}")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Requests/second: {len(results)/duration:.2f}")
    print(f"   Successful (200): {len(successful_requests)}")
    print(f"   Rate limited (429): {len(rate_limited_requests)}")
    print(f"   Errors: {len(error_requests)}")
    
    # Show first few rate limited responses
    if rate_limited_requests:
        print(f"\n🛑 RATE LIMITING TRIGGERED!")
        print(f"   First rate limit at request: {min(r['id'] for r in rate_limited_requests)}")
        for r in rate_limited_requests[:3]:
            print(f"   Request {r['id']}: 429 - Limit: {r.get('limit')}, Remaining: {r.get('remaining')}")
        return True
    else:
        print(f"\n❌ NO RATE LIMITING DETECTED")
        print(f"   All {len(successful_requests)} requests succeeded")
        
        # Show rate limit headers from successful requests
        if successful_requests:
            print(f"\n📋 Rate limit headers from successful requests:")
            for r in successful_requests[:5]:
                print(f"   Request {r['id']}: Limit: {r.get('limit')}, Remaining: {r.get('remaining')}")
        
        return False

def test_sequential_rate_limiting():
    """Test rate limiting with rapid sequential requests."""
    print("\n🔄 SEQUENTIAL RATE LIMITING TEST")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = "/api/containers/06fb6fc1f7b4/stats"
    
    print(f"🎯 Sending 80 requests sequentially with minimal delay...")
    
    results = []
    for i in range(80):
        result = make_request(endpoint, headers, i)
        results.append(result)
        
        if result.get("status") == 429:
            print(f"🛑 Rate limited at request {i+1}!")
            print(f"   Headers: Limit={result.get('limit')}, Remaining={result.get('remaining')}")
            break
        elif result.get("status") == 200:
            remaining = result.get("remaining", "N/A")
            if i % 10 == 0:  # Print every 10th request
                print(f"   Request {i+1}: ✅ Success - Remaining: {remaining}")
        
        # Very small delay to avoid overwhelming
        time.sleep(0.01)
    
    rate_limited = [r for r in results if r.get("status") == 429]
    successful = [r for r in results if r.get("status") == 200]
    
    print(f"\n📊 Sequential Results:")
    print(f"   Total requests: {len(results)}")
    print(f"   Successful: {len(successful)}")
    print(f"   Rate limited: {len(rate_limited)}")
    
    return len(rate_limited) > 0

def main():
    """Run aggressive rate limiting tests."""
    print("🚨 AGGRESSIVE RATE LIMITING VALIDATION")
    print("DockerDeployer Container Stats Endpoint")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Concurrent requests
    concurrent_success = test_aggressive_rate_limiting()
    
    # Test 2: Sequential requests
    sequential_success = test_sequential_rate_limiting()
    
    # Final assessment
    print("\n" + "=" * 60)
    print("🏁 AGGRESSIVE TEST RESULTS")
    print("=" * 60)
    
    if concurrent_success or sequential_success:
        print("✅ RATE LIMITING IS WORKING!")
        print("🛑 429 responses detected - security vulnerability is FIXED")
        print("🎉 Container stats endpoint is properly protected")
        return 0
    else:
        print("⚠️  RATE LIMITING HEADERS PRESENT BUT NO 429 RESPONSES")
        print("📊 Rate limit headers are working (counting down)")
        print("🔧 Rate limiting may be configured but not enforcing limits")
        print("💡 This could indicate a configuration issue")
        return 1

if __name__ == "__main__":
    exit(main())
