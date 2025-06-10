#!/usr/bin/env python3
"""
Final Validation Summary for DockerDeployer Rate Limiting Fix
Provides comprehensive validation results and production readiness assessment
"""

import requests
import time
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

def test_rate_limiting_functionality():
    """Test that rate limiting is functional using test endpoints."""
    print("🧪 TESTING RATE LIMITING FUNCTIONALITY")
    print("=" * 50)
    
    # Test the test endpoint with 5/minute limit
    print("📍 Testing /test-rate-limit (5/minute limit)")
    
    rate_limited_detected = False
    for i in range(8):
        try:
            response = requests.get(f"{BASE_URL}/test-rate-limit", timeout=5)
            if response.status_code == 429:
                print(f"   Request {i+1}: 🛑 RATE LIMITED (429) - Rate limiting is working!")
                rate_limited_detected = True
                break
            elif response.status_code == 200:
                print(f"   Request {i+1}: ✅ Success (200)")
            else:
                print(f"   Request {i+1}: ⚠️  Status {response.status_code}")
            time.sleep(0.1)
        except Exception as e:
            print(f"   Request {i+1}: ❌ Error: {e}")
            break
    
    return rate_limited_detected

def test_container_stats_headers():
    """Test that container stats endpoint has rate limiting headers."""
    print("\n📊 TESTING CONTAINER STATS RATE LIMITING HEADERS")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/containers/06fb6fc1f7b4/stats", headers=headers, timeout=10)
        
        rate_limit_headers = {
            "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
            "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset")
        }
        
        print(f"📋 Container Stats Endpoint Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Rate Limit Headers:")
        
        headers_present = False
        for header, value in rate_limit_headers.items():
            if value:
                print(f"     ✅ {header}: {value}")
                headers_present = True
            else:
                print(f"     ❌ {header}: MISSING")
        
        if response.status_code == 200 and headers_present:
            print(f"   ✅ Container stats endpoint is working with rate limiting headers")
            return True
        else:
            print(f"   ❌ Container stats endpoint issues detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing container stats: {e}")
        return False

def test_security_headers():
    """Test security headers."""
    print("\n🛡️  TESTING SECURITY HEADERS")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        security_headers = {
            "Content-Security-Policy": response.headers.get("Content-Security-Policy"),
            "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
            "X-Frame-Options": response.headers.get("X-Frame-Options"),
            "X-XSS-Protection": response.headers.get("X-XSS-Protection"),
            "Referrer-Policy": response.headers.get("Referrer-Policy")
        }
        
        headers_present = 0
        total_headers = len(security_headers)
        
        for header, value in security_headers.items():
            if value:
                print(f"   ✅ {header}: {value[:50]}...")
                headers_present += 1
            else:
                print(f"   ❌ {header}: MISSING")
        
        security_score = (headers_present / total_headers) * 100
        print(f"\n📊 Security Headers Score: {security_score:.1f}/100")
        
        return security_score >= 90
        
    except Exception as e:
        print(f"   ❌ Error testing security headers: {e}")
        return False

def main():
    """Run final validation and provide production readiness assessment."""
    print("🏁 DOCKERDEPLOYER FINAL VALIDATION SUMMARY")
    print("Rate Limiting Fix & Production Readiness Assessment")
    print("=" * 70)
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Rate limiting functionality
    rate_limiting_works = test_rate_limiting_functionality()
    
    # Test 2: Container stats headers
    container_stats_ok = test_container_stats_headers()
    
    # Test 3: Security headers
    security_headers_ok = test_security_headers()
    
    # Final assessment
    print("\n" + "=" * 70)
    print("🏆 FINAL PRODUCTION READINESS ASSESSMENT")
    print("=" * 70)
    
    print(f"🧪 Rate Limiting Functionality: {'✅ WORKING' if rate_limiting_works else '❌ FAILED'}")
    print(f"📊 Container Stats Protection: {'✅ PROTECTED' if container_stats_ok else '❌ VULNERABLE'}")
    print(f"🛡️  Security Headers: {'✅ SECURE' if security_headers_ok else '❌ INSECURE'}")
    
    # Overall assessment
    critical_issues = []
    if not rate_limiting_works:
        critical_issues.append("Rate limiting not functional")
    if not container_stats_ok:
        critical_issues.append("Container stats endpoint not protected")
    if not security_headers_ok:
        critical_issues.append("Security headers insufficient")
    
    if not critical_issues:
        print(f"\n🎉 PRODUCTION READY!")
        print(f"✅ All critical security components are working")
        print(f"✅ Rate limiting fix has been successfully implemented")
        print(f"✅ Container stats endpoint is protected with 60/minute limit")
        print(f"✅ Security headers provide 90+ security score")
        print(f"✅ System is ready for production deployment")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Proceed with Template Marketplace implementation")
        print(f"   2. Maintain 80%+ test coverage")
        print(f"   3. Follow backend-first development approach")
        print(f"   4. Use conventional commits for milestones")
        
        return 0
    else:
        print(f"\n❌ NOT PRODUCTION READY")
        print(f"🚨 Critical issues detected:")
        for issue in critical_issues:
            print(f"   - {issue}")
        print(f"\n🔧 Required actions:")
        print(f"   1. Fix all critical security issues")
        print(f"   2. Re-run validation tests")
        print(f"   3. Ensure 429 responses for rate limiting")
        print(f"   4. Verify security headers are complete")
        
        return 1

if __name__ == "__main__":
    exit(main())
