#!/usr/bin/env python3
"""
Security Testing Script for DockerDeployer Production Readiness
Tests critical security vulnerabilities that must be fixed before deployment.
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_PAYLOADS = [
    {
        "name": "Script Tag XSS",
        "payload": {
            "username": "<script>alert('xss')</script>",
            "email": "test@test.com",
            "full_name": "Test User",
            "password": "TestPassword123"
        },
        "expected_status": 400
    },
    {
        "name": "Iframe XSS",
        "payload": {
            "username": "testuser",
            "email": "test@test.com", 
            "full_name": "<iframe src='javascript:alert(1)'></iframe>",
            "password": "TestPassword123"
        },
        "expected_status": 400
    },
    {
        "name": "Event Handler XSS",
        "payload": {
            "username": "testuser",
            "email": "test@test.com",
            "full_name": "Test onclick=alert('xss') User",
            "password": "TestPassword123"
        },
        "expected_status": 400
    },
    {
        "name": "JavaScript Protocol XSS",
        "payload": {
            "username": "testuser",
            "email": "javascript:alert('xss')@test.com",
            "full_name": "Test User",
            "password": "TestPassword123"
        },
        "expected_status": 400
    },
    {
        "name": "Valid Registration",
        "payload": {
            "username": "validuser123",
            "email": "valid@test.com",
            "full_name": "Valid User",
            "password": "TestPassword123"
        },
        "expected_status": 201
    }
]

def test_xss_protection():
    """Test XSS input validation on registration endpoint."""
    print("🔒 Testing XSS Protection...")
    
    results = []
    for test_case in TEST_PAYLOADS:
        print(f"  Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            status_match = response.status_code == test_case["expected_status"]
            
            if status_match:
                print(f"    ✅ PASS - Status: {response.status_code}")
                results.append(True)
            else:
                print(f"    ❌ FAIL - Expected: {test_case['expected_status']}, Got: {response.status_code}")
                print(f"    Response: {response.text[:200]}...")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"    ❌ ERROR - Request failed: {e}")
            results.append(False)
    
    return all(results)

def test_cors_configuration():
    """Test CORS configuration with malicious origins."""
    print("🌐 Testing CORS Configuration...")
    
    malicious_origins = [
        "http://malicious-site.com",
        "https://evil.example.com",
        "http://localhost:9999"
    ]
    
    results = []
    for origin in malicious_origins:
        print(f"  Testing origin: {origin}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/health",
                headers={"Origin": origin},
                timeout=10
            )
            
            # Check if wildcard CORS is present (security issue)
            cors_header = response.headers.get("access-control-allow-origin", "")
            
            if cors_header == "*":
                print(f"    ❌ FAIL - Wildcard CORS detected: {cors_header}")
                results.append(False)
            elif cors_header == origin:
                print(f"    ❌ FAIL - Malicious origin allowed: {cors_header}")
                results.append(False)
            else:
                print(f"    ✅ PASS - Origin properly restricted")
                results.append(True)
                
        except requests.exceptions.RequestException as e:
            print(f"    ❌ ERROR - Request failed: {e}")
            results.append(False)
    
    return all(results)

def test_rate_limiting():
    """Test rate limiting enforcement."""
    print("⏱️  Testing Rate Limiting...")
    
    # Make rapid requests to trigger rate limiting
    print("  Making 15 rapid requests...")
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(15):
        try:
            response = requests.get(
                f"{BASE_URL}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"    Rate limited on request {i+1}")
                
        except requests.exceptions.RequestException as e:
            print(f"    Request {i+1} failed: {e}")
    
    print(f"  Results: {success_count} successful, {rate_limited_count} rate limited")
    
    # Rate limiting should kick in after some requests
    if rate_limited_count > 0:
        print("    ✅ PASS - Rate limiting is working")
        return True
    else:
        print("    ❌ FAIL - No rate limiting detected")
        return False

def test_security_headers():
    """Test presence of security headers."""
    print("🛡️  Testing Security Headers...")
    
    required_headers = [
        "content-security-policy",
        "x-frame-options", 
        "x-content-type-options"
    ]
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        results = []
        for header in required_headers:
            if header in headers:
                print(f"    ✅ {header}: {headers[header][:50]}...")
                results.append(True)
            else:
                print(f"    ❌ Missing header: {header}")
                results.append(False)
        
        return all(results)
        
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - Request failed: {e}")
        return False

def test_templates_api():
    """Test templates API availability."""
    print("📋 Testing Templates API...")
    
    try:
        # This will fail without auth, but should not return 404
        response = requests.get(f"{BASE_URL}/api/templates", timeout=10)
        
        if response.status_code == 404:
            print("    ❌ FAIL - Templates API returns 404 (volume mount issue)")
            return False
        elif response.status_code == 401:
            print("    ✅ PASS - Templates API accessible (returns 401 auth required)")
            return True
        else:
            print(f"    ✅ PASS - Templates API responds with status {response.status_code}")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ ERROR - Request failed: {e}")
        return False

def main():
    """Run all security tests."""
    print("🚀 DockerDeployer Security Testing Suite")
    print("=" * 50)
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    tests = [
        ("XSS Protection", test_xss_protection),
        ("CORS Configuration", test_cors_configuration), 
        ("Rate Limiting", test_rate_limiting),
        ("Security Headers", test_security_headers),
        ("Templates API", test_templates_api)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 30)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SECURITY TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SECURITY TESTS PASSED - Ready for deployment!")
        sys.exit(0)
    else:
        print("🚨 SECURITY ISSUES DETECTED - DO NOT DEPLOY!")
        sys.exit(1)

if __name__ == "__main__":
    main()
