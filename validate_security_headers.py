#!/usr/bin/env python3
"""
Security Headers Validation Script
Validates that SecurityHeadersMiddleware is working and provides 90+ security score
"""

import requests
import json
from datetime import datetime
from typing import Dict, List

BASE_URL = "http://localhost:8000"

def test_security_headers() -> Dict:
    """Test security headers on critical endpoints."""
    print("🛡️  SECURITY HEADERS VALIDATION")
    print("=" * 40)
    
    endpoints_to_test = [
        "/health",
        "/api/containers", 
        "/auth/me"
    ]
    
    results = {
        "endpoints_tested": [],
        "security_score": 0,
        "all_headers_present": True,
        "production_ready": False
    }
    
    required_headers = {
        "content-security-policy": 20,
        "x-content-type-options": 15,
        "x-frame-options": 15,
        "x-xss-protection": 15,
        "referrer-policy": 10,
        "permissions-policy": 10
    }
    
    for endpoint in endpoints_to_test:
        print(f"\n📍 Testing {endpoint}")
        
        try:
            # Test without auth first
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            
            endpoint_result = {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "headers_found": {},
                "headers_missing": [],
                "endpoint_score": 0
            }
            
            # Check each required header
            for header_name, points in required_headers.items():
                header_value = response.headers.get(header_name)
                if header_value:
                    endpoint_result["headers_found"][header_name] = header_value
                    endpoint_result["endpoint_score"] += points
                    print(f"   ✅ {header_name}: {header_value[:50]}...")
                else:
                    endpoint_result["headers_missing"].append(header_name)
                    print(f"   ❌ {header_name}: MISSING")
            
            # Check for HSTS (only for HTTPS)
            if response.url.startswith("https://"):
                hsts = response.headers.get("strict-transport-security")
                if hsts:
                    endpoint_result["headers_found"]["strict-transport-security"] = hsts
                    endpoint_result["endpoint_score"] += 15
                    print(f"   ✅ strict-transport-security: {hsts}")
                else:
                    endpoint_result["headers_missing"].append("strict-transport-security")
                    print(f"   ⚠️  strict-transport-security: Not required for HTTP")
            
            results["endpoints_tested"].append(endpoint_result)
            
            if endpoint_result["headers_missing"]:
                results["all_headers_present"] = False
            
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {e}")
            results["endpoints_tested"].append({
                "endpoint": endpoint,
                "error": str(e),
                "endpoint_score": 0
            })
    
    # Calculate overall security score
    if results["endpoints_tested"]:
        avg_score = sum(ep.get("endpoint_score", 0) for ep in results["endpoints_tested"]) / len(results["endpoints_tested"])
        results["security_score"] = min(avg_score, 100)  # Cap at 100
    
    # Determine if production ready (90+ score)
    results["production_ready"] = results["security_score"] >= 90
    
    return results

def test_cors_configuration() -> Dict:
    """Test CORS configuration."""
    print("\n🌐 CORS CONFIGURATION VALIDATION")
    print("=" * 40)
    
    result = {
        "cors_working": False,
        "allowed_origins_restricted": False,
        "production_ready": False
    }
    
    try:
        # Test with allowed origin
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
        
        response = requests.options(f"{BASE_URL}/api/containers", headers=headers, timeout=10)
        
        cors_headers = {
            "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
            "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
            "access-control-allow-headers": response.headers.get("access-control-allow-headers")
        }
        
        print(f"📋 CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"   ✅ {header}: {value}")
            else:
                print(f"   ❌ {header}: MISSING")
        
        # Check if CORS is working
        if cors_headers["access-control-allow-origin"]:
            result["cors_working"] = True
            
            # Check if origins are restricted (not wildcard)
            if cors_headers["access-control-allow-origin"] != "*":
                result["allowed_origins_restricted"] = True
                print("   ✅ Origins properly restricted (no wildcard)")
            else:
                print("   ⚠️  Wildcard origin detected - security risk")
        
        result["production_ready"] = result["cors_working"] and result["allowed_origins_restricted"]
        
    except Exception as e:
        print(f"   ❌ CORS test error: {e}")
    
    return result

def validate_rate_limiting_headers() -> Dict:
    """Validate that rate limiting headers are present."""
    print("\n⏱️  RATE LIMITING HEADERS VALIDATION")
    print("=" * 40)
    
    result = {
        "rate_limit_headers_present": False,
        "headers_found": {},
        "production_ready": False
    }
    
    try:
        # Get auth token
        auth_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "AdminPassword123"},
            timeout=10
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test rate limiting headers on protected endpoint
            response = requests.get(f"{BASE_URL}/api/containers", headers=headers, timeout=10)
            
            rate_limit_headers = {
                "x-ratelimit-limit": response.headers.get("x-ratelimit-limit"),
                "x-ratelimit-remaining": response.headers.get("x-ratelimit-remaining"),
                "x-ratelimit-reset": response.headers.get("x-ratelimit-reset")
            }
            
            print(f"📊 Rate Limiting Headers:")
            for header, value in rate_limit_headers.items():
                if value:
                    result["headers_found"][header] = value
                    print(f"   ✅ {header}: {value}")
                else:
                    print(f"   ❌ {header}: MISSING")
            
            result["rate_limit_headers_present"] = bool(result["headers_found"])
            result["production_ready"] = result["rate_limit_headers_present"]
            
        else:
            print("   ❌ Authentication failed - cannot test rate limiting headers")
    
    except Exception as e:
        print(f"   ❌ Rate limiting headers test error: {e}")
    
    return result

def main():
    """Run comprehensive security validation."""
    print("🔒 COMPREHENSIVE SECURITY VALIDATION")
    print("DockerDeployer Security Configuration Check")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    
    # Test security headers
    headers_result = test_security_headers()
    
    # Test CORS configuration
    cors_result = test_cors_configuration()
    
    # Test rate limiting headers
    rate_limit_result = validate_rate_limiting_headers()
    
    # Final assessment
    print("\n" + "=" * 60)
    print("🏁 SECURITY VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"🛡️  Security Headers Score: {headers_result['security_score']:.1f}/100")
    if headers_result["production_ready"]:
        print("   ✅ Security headers: PRODUCTION READY")
    else:
        print("   ❌ Security headers: NEEDS IMPROVEMENT")
    
    print(f"🌐 CORS Configuration:")
    if cors_result["production_ready"]:
        print("   ✅ CORS: PRODUCTION READY")
    else:
        print("   ❌ CORS: NEEDS IMPROVEMENT")
    
    print(f"⏱️  Rate Limiting Headers:")
    if rate_limit_result["production_ready"]:
        print("   ✅ Rate limiting headers: PRESENT")
    else:
        print("   ❌ Rate limiting headers: MISSING")
    
    # Overall security score
    overall_score = (
        headers_result["security_score"] * 0.6 +  # 60% weight
        (90 if cors_result["production_ready"] else 60) * 0.3 +  # 30% weight
        (90 if rate_limit_result["production_ready"] else 60) * 0.1  # 10% weight
    )
    
    print(f"\n📊 OVERALL SECURITY SCORE: {overall_score:.1f}/100")
    
    if overall_score >= 90:
        print("🎉 EXCELLENT: Production ready security configuration!")
        print("✅ System meets security requirements for deployment")
        return 0
    elif overall_score >= 75:
        print("⚠️  GOOD: Security mostly configured, minor improvements needed")
        print("🔧 Address missing components before production deployment")
        return 1
    else:
        print("❌ POOR: Significant security issues detected")
        print("🚨 Do not deploy until security is properly configured")
        return 2

if __name__ == "__main__":
    exit(main())
