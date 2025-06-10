#!/usr/bin/env python3
"""
Critical Rate Limiting Validation Script
Validates that the 60/minute container stats endpoint rate limiting fix is working correctly
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

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

def validate_container_stats_rate_limiting() -> Dict:
    """
    CRITICAL: Validate that container stats endpoint has 60/minute rate limiting.
    This is the security vulnerability that was just fixed.
    """
    print("🚨 CRITICAL VALIDATION: Container Stats Rate Limiting")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return {"success": False, "error": "Authentication failed"}
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get container ID
    container_id = get_container_id()
    if not container_id:
        return {"success": False, "error": "No running containers found"}
    
    endpoint = f"/api/containers/{container_id}/stats"
    print(f"🎯 Testing endpoint: {endpoint}")
    print(f"📊 Expected limit: 60 requests/minute")
    print(f"🚀 Sending rapid requests to trigger rate limiting...")
    
    results = {
        "endpoint": endpoint,
        "expected_limit": 60,
        "requests_sent": 0,
        "successful_requests": 0,
        "rate_limited_requests": 0,
        "first_rate_limit_at": None,
        "rate_limit_headers": {},
        "validation_passed": False,
        "security_vulnerability_fixed": False
    }
    
    start_time = time.time()
    
    # Send requests rapidly to trigger rate limiting
    for i in range(70):  # Send more than the limit to ensure we hit it
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            results["requests_sent"] += 1
            
            # Capture rate limit headers
            if "X-RateLimit-Limit" in response.headers:
                results["rate_limit_headers"] = {
                    "limit": response.headers.get("X-RateLimit-Limit"),
                    "remaining": response.headers.get("X-RateLimit-Remaining"),
                    "reset": response.headers.get("X-RateLimit-Reset")
                }
            
            if response.status_code == 200 or response.status_code == 404:
                results["successful_requests"] += 1
                print(f"Request {i+1:2d}: ✅ SUCCESS ({response.status_code}) - Remaining: {results['rate_limit_headers'].get('remaining', 'N/A')}")
            elif response.status_code == 429:  # Too Many Requests - THIS IS WHAT WE WANT
                results["rate_limited_requests"] += 1
                if results["first_rate_limit_at"] is None:
                    results["first_rate_limit_at"] = results["requests_sent"]
                print(f"Request {i+1:2d}: 🛑 RATE LIMITED (429) - SECURITY FIX WORKING!")
                print(f"                Rate limit headers: {results['rate_limit_headers']}")
                break
            else:
                print(f"Request {i+1:2d}: ⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"Request {i+1:2d}: ❌ Error: {e}")
            break
        
        # Small delay to avoid overwhelming
        time.sleep(0.05)
    
    # Evaluate results - CRITICAL SECURITY CHECK
    if results["rate_limited_requests"] > 0:
        actual_limit = results["first_rate_limit_at"] - 1
        tolerance = 60 * 0.2  # 20% tolerance (48-72 requests acceptable)
        
        if 48 <= actual_limit <= 72:  # Within tolerance of 60/minute
            results["validation_passed"] = True
            results["security_vulnerability_fixed"] = True
            print(f"\n🎉 SECURITY FIX VALIDATED!")
            print(f"   ✅ Rate limiting triggered after {actual_limit} requests")
            print(f"   ✅ Expected ~60/minute, got {actual_limit} (within tolerance)")
            print(f"   ✅ Container stats endpoint is now protected")
        else:
            print(f"\n⚠️  RATE LIMIT MISMATCH:")
            print(f"   Expected: ~60 requests/minute")
            print(f"   Actual: {actual_limit} requests before limit")
            print(f"   Status: Rate limiting working but limit may be incorrect")
    else:
        print(f"\n❌ CRITICAL SECURITY ISSUE:")
        print(f"   No rate limiting detected after {results['requests_sent']} requests")
        print(f"   Container stats endpoint is NOT protected")
        print(f"   Security vulnerability still exists!")
    
    return results

def validate_all_endpoints_rate_limiting() -> Dict:
    """Validate rate limiting across all critical endpoints."""
    print("\n🔍 COMPREHENSIVE ENDPOINT VALIDATION")
    print("=" * 40)
    
    token = get_auth_token()
    if not token:
        return {"success": False, "error": "Authentication failed"}
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test endpoints with their expected limits
    endpoints_to_test = [
        ("/api/containers", 100, "General API"),
        ("/auth/me", 100, "Auth API"),
        ("/health", None, "Health Check (no auth)")  # No rate limit expected
    ]
    
    results = {"endpoints": [], "all_passed": True}
    
    for endpoint, expected_limit, description in endpoints_to_test:
        print(f"\n📍 Testing {description}: {endpoint}")
        
        if endpoint == "/health":
            test_headers = None  # No auth for health check
        else:
            test_headers = headers
        
        endpoint_result = test_endpoint_rate_limiting(endpoint, test_headers, expected_limit)
        results["endpoints"].append(endpoint_result)
        
        if expected_limit and not endpoint_result.get("rate_limiting_working", False):
            results["all_passed"] = False
    
    return results

def test_endpoint_rate_limiting(endpoint: str, headers: Dict, expected_limit: int) -> Dict:
    """Test rate limiting for a specific endpoint."""
    if expected_limit is None:
        print(f"   ⏭️  Skipping rate limit test (no limit expected)")
        return {"endpoint": endpoint, "skipped": True}
    
    print(f"   🎯 Expected limit: {expected_limit}/minute")
    
    result = {
        "endpoint": endpoint,
        "expected_limit": expected_limit,
        "requests_sent": 0,
        "rate_limited": False,
        "rate_limiting_working": False
    }
    
    # Send requests to test rate limiting
    for i in range(min(expected_limit + 10, 50)):  # Don't overwhelm
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            result["requests_sent"] += 1
            
            if response.status_code == 429:
                result["rate_limited"] = True
                result["rate_limiting_working"] = True
                print(f"   ✅ Rate limiting triggered after {result['requests_sent']} requests")
                break
            elif response.status_code in [200, 404]:
                continue
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                break
                
        except Exception as e:
            print(f"   ❌ Request error: {e}")
            break
        
        time.sleep(0.05)
    
    if not result["rate_limited"]:
        print(f"   ⚠️  No rate limiting detected after {result['requests_sent']} requests")
    
    return result

def main():
    """Run critical rate limiting validation."""
    print("🚨 CRITICAL SECURITY VALIDATION")
    print("DockerDeployer Rate Limiting Fix Verification")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    
    # STEP 1: Critical container stats validation
    container_stats_result = validate_container_stats_rate_limiting()
    
    # STEP 2: Comprehensive endpoint validation
    all_endpoints_result = validate_all_endpoints_rate_limiting()
    
    # STEP 3: Final assessment
    print("\n" + "=" * 60)
    print("🏁 FINAL SECURITY VALIDATION RESULTS")
    print("=" * 60)
    
    if container_stats_result.get("security_vulnerability_fixed", False):
        print("✅ CRITICAL: Container stats rate limiting FIXED")
        print("✅ Security vulnerability has been resolved")
    else:
        print("❌ CRITICAL: Container stats rate limiting FAILED")
        print("❌ Security vulnerability still exists")
    
    if all_endpoints_result.get("all_passed", False):
        print("✅ All endpoints have proper rate limiting")
    else:
        print("⚠️  Some endpoints may have rate limiting issues")
    
    # Overall assessment
    overall_success = (
        container_stats_result.get("security_vulnerability_fixed", False) and
        all_endpoints_result.get("all_passed", False)
    )
    
    if overall_success:
        print("\n🎉 PRODUCTION READY: Rate limiting security fix validated")
        print("✅ System is secure and ready for deployment")
        return 0
    else:
        print("\n❌ NOT PRODUCTION READY: Security issues detected")
        print("🚨 Do not deploy until rate limiting is fixed")
        return 1

if __name__ == "__main__":
    exit(main())
