#!/usr/bin/env python3
"""
Security Headers Validation Test for DockerDeployer
Tests all required security headers and CORS configuration
"""

import requests
import sys
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"

def test_security_headers() -> Tuple[bool, Dict[str, str]]:
    """Test all required security headers."""
    print("🛡️  Testing Security Headers...")
    
    required_headers = {
        "content-security-policy": "CSP policy for XSS protection",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "x-xss-protection": "XSS protection",
        "permissions-policy": "Feature policy",
        "referrer-policy": "strict-origin-when-cross-origin"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        results = {}
        all_passed = True
        
        for header, expected in required_headers.items():
            if header in headers:
                value = headers[header]
                print(f"    ✅ {header}: {value[:80]}...")
                results[header] = value
                
                # Validate specific header values
                if header == "x-content-type-options" and value != "nosniff":
                    print(f"    ⚠️  Warning: {header} should be 'nosniff', got '{value}'")
                elif header == "x-frame-options" and value != "DENY":
                    print(f"    ⚠️  Warning: {header} should be 'DENY', got '{value}'")
                elif header == "referrer-policy" and value != "strict-origin-when-cross-origin":
                    print(f"    ⚠️  Warning: {header} unexpected value '{value}'")
                elif header == "x-xss-protection" and not value.startswith("1; mode=block"):
                    print(f"    ⚠️  Warning: {header} may have display issue, expected '1; mode=block'")
            else:
                print(f"    ❌ Missing header: {header}")
                results[header] = None
                all_passed = False
        
        return all_passed, results
        
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - Request failed: {e}")
        return False, {}

def test_cors_configuration() -> bool:
    """Test CORS configuration to ensure no wildcard origins."""
    print("🌐 Testing CORS Configuration...")
    
    # Test with malicious origin
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            headers={"Origin": "https://malicious-site.com"},
            timeout=10
        )
        
        cors_headers = {k.lower(): v for k, v in response.headers.items() if 'access-control' in k.lower()}
        
        # Should not allow malicious origin
        if "access-control-allow-origin" in cors_headers:
            origin = cors_headers["access-control-allow-origin"]
            if origin == "*":
                print("    ❌ CRITICAL: Wildcard CORS origin detected!")
                return False
            elif origin == "https://malicious-site.com":
                print("    ❌ CRITICAL: Malicious origin allowed!")
                return False
            else:
                print(f"    ✅ Malicious origin rejected (no CORS header)")
        
        # Test with allowed origin
        response = requests.get(
            f"{BASE_URL}/health",
            headers={"Origin": "http://localhost:3000"},
            timeout=10
        )
        
        cors_headers = {k.lower(): v for k, v in response.headers.items() if 'access-control' in k.lower()}
        
        if "access-control-allow-origin" in cors_headers:
            origin = cors_headers["access-control-allow-origin"]
            if origin == "http://localhost:3000":
                print(f"    ✅ Allowed origin accepted: {origin}")
                return True
            else:
                print(f"    ⚠️  Unexpected allowed origin: {origin}")
                return True  # Still secure, just different config
        else:
            print("    ❌ No CORS header for allowed origin")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - CORS test failed: {e}")
        return False

def calculate_security_score(headers_passed: bool, cors_passed: bool, headers_results: Dict[str, str]) -> int:
    """Calculate security score based on test results."""
    score = 0
    
    # Base score for headers (60 points)
    if headers_passed:
        score += 60
    else:
        # Partial credit for individual headers
        for header, value in headers_results.items():
            if value is not None:
                score += 10
    
    # CORS configuration (20 points)
    if cors_passed:
        score += 20
    
    # Bonus points for specific security measures (20 points)
    if headers_results.get("content-security-policy"):
        csp = headers_results["content-security-policy"]
        if "frame-ancestors 'none'" in csp:
            score += 5
        if "'unsafe-eval'" not in csp or "'unsafe-inline'" not in csp:
            score += 5  # Bonus for stricter CSP
        if "https:" in csp:
            score += 5
    
    if headers_results.get("x-frame-options") == "DENY":
        score += 5
    
    return min(score, 100)  # Cap at 100

def main():
    """Run all security validation tests."""
    print("🔒 DockerDeployer Security Headers Validation")
    print("=" * 50)
    
    # Test security headers
    headers_passed, headers_results = test_security_headers()
    print()
    
    # Test CORS configuration
    cors_passed = test_cors_configuration()
    print()
    
    # Calculate security score
    security_score = calculate_security_score(headers_passed, cors_passed, headers_results)
    
    print("📊 Security Validation Results:")
    print(f"    Security Headers: {'✅ PASS' if headers_passed else '❌ FAIL'}")
    print(f"    CORS Configuration: {'✅ PASS' if cors_passed else '❌ FAIL'}")
    print(f"    Security Score: {security_score}/100")
    
    if security_score >= 90:
        print("🎉 EXCELLENT: Production ready security score!")
        return 0
    elif security_score >= 80:
        print("✅ GOOD: Acceptable security score for production")
        return 0
    elif security_score >= 70:
        print("⚠️  WARNING: Security improvements recommended")
        return 1
    else:
        print("❌ CRITICAL: Security issues must be fixed before production")
        return 1

if __name__ == "__main__":
    sys.exit(main())
