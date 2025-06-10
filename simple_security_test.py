#!/usr/bin/env python3
"""
Simple Security Headers Test for DockerDeployer
"""

import requests
import json

def test_security_headers():
    """Test security headers with simple validation."""
    print("🔒 Security Headers Test")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        headers = response.headers
        
        # Required headers
        required = [
            "content-security-policy",
            "x-content-type-options", 
            "x-frame-options",
            "x-xss-protection",
            "permissions-policy",
            "referrer-policy"
        ]
        
        score = 0
        max_score = len(required) * 10
        
        for header in required:
            if header in headers:
                value = headers[header]
                print(f"✅ {header}: Present")
                score += 10
                
                # Validate key values
                if header == "x-content-type-options" and value == "nosniff":
                    score += 5
                elif header == "x-frame-options" and value == "DENY":
                    score += 5
                elif header == "content-security-policy" and "default-src 'self'" in value:
                    score += 5
            else:
                print(f"❌ {header}: Missing")
        
        # Test CORS
        cors_response = requests.get(
            "http://localhost:8000/health",
            headers={"Origin": "https://malicious.com"},
            timeout=5
        )
        
        if "access-control-allow-origin" not in cors_response.headers:
            print("✅ CORS: Malicious origin rejected")
            score += 10
        elif cors_response.headers.get("access-control-allow-origin") != "*":
            print("✅ CORS: No wildcard origin")
            score += 10
        else:
            print("❌ CORS: Wildcard origin detected")
        
        print(f"\nSecurity Score: {score}/{max_score + 10}")
        
        if score >= 80:
            print("🎉 PASS: Good security configuration")
            return True
        else:
            print("⚠️  FAIL: Security improvements needed")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_security_headers()
