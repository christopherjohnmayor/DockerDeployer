#!/usr/bin/env python3
"""
Quick test to validate the container stats endpoint rate limiting fix.
"""

import requests
import time

def test_container_stats_rate_limiting():
    """Test if the container stats endpoint is now rate limited."""
    print("Testing Container Stats Endpoint Rate Limiting Fix")
    print("=" * 50)
    
    try:
        # Get auth token
        login_data = {"username": "admin", "password": "AdminPassword123"}
        response = requests.post("http://localhost:8000/auth/login", json=login_data, timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Authentication successful")
        print("🔍 Testing container stats endpoint...")
        
        # Test the endpoint with multiple requests
        success_count = 0
        rate_limited = False
        
        for i in range(10):  # Test with 10 requests
            try:
                response = requests.get(
                    "http://localhost:8000/api/containers/test-container/stats", 
                    headers=headers, 
                    timeout=5
                )
                
                # Check for rate limiting headers
                limit_header = response.headers.get("X-RateLimit-Limit")
                remaining_header = response.headers.get("X-RateLimit-Remaining")
                
                if response.status_code == 429:
                    print(f"Request {i+1}: ⛔ RATE LIMITED (429)")
                    print(f"  Headers: Limit={limit_header}, Remaining={remaining_header}")
                    rate_limited = True
                    break
                elif response.status_code in [200, 404]:  # 404 expected for non-existent container
                    success_count += 1
                    print(f"Request {i+1}: ✅ SUCCESS ({response.status_code}) - Remaining: {remaining_header}")
                else:
                    print(f"Request {i+1}: ❓ UNEXPECTED ({response.status_code})")
                
                time.sleep(0.1)  # Small delay
                
            except requests.exceptions.Timeout:
                print(f"Request {i+1}: ⏰ TIMEOUT")
                break
            except Exception as e:
                print(f"Request {i+1}: ❌ ERROR - {e}")
                break
        
        # Evaluate results
        print(f"\nResults:")
        print(f"  ✅ Successful requests: {success_count}")
        print(f"  ⛔ Rate limited: {'YES' if rate_limited else 'NO'}")
        
        if rate_limited:
            print(f"\n🎉 SUCCESS: Container stats endpoint rate limiting is WORKING!")
            print(f"✅ Production deployment security requirement is MET!")
            return True
        else:
            print(f"\n❌ FAILURE: Container stats endpoint rate limiting is still BROKEN!")
            print(f"🚫 Production deployment security requirement is NOT MET!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_container_stats_rate_limiting()
    exit(0 if success else 1)
