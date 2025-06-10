#!/usr/bin/env python3
"""
Rate Limiting Verification Test for DockerDeployer
Tests Redis-based rate limiting functionality across critical endpoints
"""

import requests
import time
import json
from typing import Dict, List, Tuple
import concurrent.futures
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_auth_token() -> str:
    """Get JWT authentication token."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "AdminPassword123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def get_container_id() -> str:
    """Get a running container ID for testing."""
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}}", "--filter", "status=running"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
        return None
    except Exception as e:
        print(f"❌ Error getting container ID: {e}")
        return None

def test_rate_limit_endpoint(endpoint: str, headers: Dict[str, str], 
                           expected_limit: int, test_duration: int = 60) -> Tuple[bool, Dict]:
    """
    Test rate limiting for a specific endpoint.
    
    Args:
        endpoint: API endpoint to test
        headers: Request headers (including auth)
        expected_limit: Expected requests per minute
        test_duration: Test duration in seconds
    
    Returns:
        Tuple of (success, results_dict)
    """
    print(f"🚦 Testing rate limit for {endpoint}")
    print(f"   Expected limit: {expected_limit}/minute")
    
    results = {
        "endpoint": endpoint,
        "expected_limit": expected_limit,
        "requests_sent": 0,
        "successful_requests": 0,
        "rate_limited_requests": 0,
        "first_rate_limit_at": None,
        "rate_limit_headers": {},
        "test_passed": False
    }
    
    start_time = time.time()
    
    # Send requests rapidly to trigger rate limiting
    while time.time() - start_time < test_duration:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            results["requests_sent"] += 1
            
            # Check for rate limit headers
            if "X-RateLimit-Limit" in response.headers:
                results["rate_limit_headers"] = {
                    "limit": response.headers.get("X-RateLimit-Limit"),
                    "remaining": response.headers.get("X-RateLimit-Remaining"),
                    "reset": response.headers.get("X-RateLimit-Reset")
                }
            
            if response.status_code == 200:
                results["successful_requests"] += 1
            elif response.status_code == 429:  # Too Many Requests
                results["rate_limited_requests"] += 1
                if results["first_rate_limit_at"] is None:
                    results["first_rate_limit_at"] = results["requests_sent"]
                print(f"   ⚠️  Rate limited after {results['requests_sent']} requests")
                break
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️  Request timeout")
            break
        except Exception as e:
            print(f"   ❌ Request error: {e}")
            break
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    # Evaluate results
    if results["rate_limited_requests"] > 0:
        actual_limit = results["first_rate_limit_at"] - 1
        tolerance = expected_limit * 0.2  # 20% tolerance
        
        if abs(actual_limit - expected_limit) <= tolerance:
            results["test_passed"] = True
            print(f"   ✅ Rate limiting working: {actual_limit} requests before limit")
        else:
            print(f"   ⚠️  Rate limit mismatch: expected ~{expected_limit}, got {actual_limit}")
    else:
        print(f"   ❌ No rate limiting detected after {results['requests_sent']} requests")
    
    return results["test_passed"], results

def test_redis_connectivity() -> bool:
    """Test Redis connectivity."""
    print("🔗 Testing Redis connectivity...")
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "dockerdeployer-redis", "redis-cli", "ping"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "PONG" in result.stdout:
            print("   ✅ Redis is accessible")
            return True
        else:
            print("   ❌ Redis ping failed")
            return False
    except Exception as e:
        print(f"   ❌ Redis connectivity error: {e}")
        return False

def test_concurrent_requests(endpoint: str, headers: Dict[str, str], 
                           concurrent_users: int = 5) -> Tuple[bool, Dict]:
    """Test rate limiting with concurrent requests."""
    print(f"🔄 Testing concurrent rate limiting for {endpoint}")
    print(f"   Concurrent users: {concurrent_users}")
    
    def make_request(user_id: int) -> Dict:
        """Make a single request."""
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            return {
                "user_id": user_id,
                "status_code": response.status_code,
                "rate_limited": response.status_code == 429,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {
                "user_id": user_id,
                "error": str(e),
                "rate_limited": False
            }
    
    # Send concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_request, i) for i in range(concurrent_users * 10)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    total_requests = len(results)
    rate_limited_count = sum(1 for r in results if r.get("rate_limited", False))
    successful_count = sum(1 for r in results if r.get("status_code") == 200)
    
    print(f"   Total requests: {total_requests}")
    print(f"   Successful: {successful_count}")
    print(f"   Rate limited: {rate_limited_count}")
    
    # Test passes if some requests were rate limited (showing it's working)
    test_passed = rate_limited_count > 0
    
    if test_passed:
        print("   ✅ Concurrent rate limiting working")
    else:
        print("   ⚠️  No rate limiting detected in concurrent test")
    
    return test_passed, {
        "total_requests": total_requests,
        "successful": successful_count,
        "rate_limited": rate_limited_count,
        "test_passed": test_passed
    }

def main():
    """Run comprehensive rate limiting tests."""
    print("🚦 DockerDeployer Rate Limiting Verification")
    print("=" * 50)
    
    # Test Redis connectivity first
    if not test_redis_connectivity():
        print("❌ CRITICAL: Redis not accessible - rate limiting may not work")
        return 1
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ CRITICAL: Cannot authenticate - cannot test rate limiting")
        return 1
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get container ID for stats testing
    container_id = get_container_id()
    if not container_id:
        print("❌ WARNING: No running containers found - skipping container stats test")
        container_endpoints = []
    else:
        container_endpoints = [
            (f"/api/containers/{container_id}/stats", 60),  # Current limit is 60/minute
        ]
    
    # Define endpoints to test with their expected limits
    endpoints_to_test = [
        ("/api/containers", 100),  # General API limit
        ("/auth/me", 100),  # General API limit
    ] + container_endpoints
    
    print(f"\n📋 Testing {len(endpoints_to_test)} endpoints...")
    
    test_results = []
    overall_success = True
    
    for endpoint, expected_limit in endpoints_to_test:
        print(f"\n{'='*30}")
        success, results = test_rate_limit_endpoint(endpoint, headers, expected_limit, 30)
        test_results.append(results)
        
        if not success:
            overall_success = False
    
    # Test concurrent requests
    if container_id:
        print(f"\n{'='*30}")
        concurrent_success, concurrent_results = test_concurrent_requests(
            f"/api/containers/{container_id}/stats", headers
        )
        if not concurrent_success:
            overall_success = False
    
    # Summary
    print(f"\n📊 Rate Limiting Test Summary")
    print("=" * 30)
    
    for result in test_results:
        status = "✅ PASS" if result["test_passed"] else "❌ FAIL"
        print(f"{status} {result['endpoint']}: {result['requests_sent']} requests sent")
        if result["rate_limit_headers"]:
            headers_info = result["rate_limit_headers"]
            print(f"     Rate limit headers: {headers_info['limit']}/{headers_info['remaining']}")
    
    if overall_success:
        print("\n🎉 PASS: Rate limiting is working correctly")
        return 0
    else:
        print("\n❌ FAIL: Rate limiting issues detected")
        return 1

if __name__ == "__main__":
    exit(main())
