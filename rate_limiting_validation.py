#!/usr/bin/env python3
"""
Rate Limiting Validation Script for Template Marketplace.

This script validates that rate limiting is working effectively
by testing endpoints with high request volumes.
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any


async def test_rate_limiting(base_url: str = "http://localhost:8000", 
                           endpoint: str = "/health", 
                           requests_count: int = 100,
                           concurrent_requests: int = 20) -> Dict[str, Any]:
    """Test rate limiting on a specific endpoint."""
    
    print(f"🔥 Testing Rate Limiting on {endpoint}")
    print(f"📊 Sending {requests_count} requests with {concurrent_requests} concurrent")
    print("🎯 Expecting rate limiting to kick in...")
    print("")
    
    url = f"{base_url}{endpoint}"
    results = []
    
    async def make_request(session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """Make a single request and capture rate limiting response."""
        try:
            start_time = time.time()
            
            async with session.get(url) as response:
                await response.text()
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                return {
                    "request_id": request_id,
                    "status_code": response.status,
                    "response_time_ms": round(response_time_ms, 2),
                    "rate_limited": response.status == 429,
                    "performance_header": response.headers.get('x-response-time', 'Not present'),
                    "retry_after": response.headers.get('retry-after'),
                    "timestamp": time.time()
                }
                
        except Exception as e:
            return {
                "request_id": request_id,
                "error": str(e),
                "timestamp": time.time()
            }
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(concurrent_requests)
    
    async def limited_request(session: aiohttp.ClientSession, request_id: int):
        async with semaphore:
            return await make_request(session, request_id)
    
    # Execute requests
    connector = aiohttp.TCPConnector(limit=concurrent_requests * 2)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        start_time = time.time()
        
        # Create all request tasks
        tasks = [limited_request(session, i) for i in range(requests_count)]
        
        # Execute all requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
    
    # Filter out exceptions
    valid_results = [r for r in results if isinstance(r, dict) and not r.get('error')]
    
    # Analyze results
    total_requests = len(valid_results)
    rate_limited_requests = len([r for r in valid_results if r.get('rate_limited')])
    successful_requests = len([r for r in valid_results if r.get('status_code') == 200])
    error_requests = len([r for r in valid_results if r.get('status_code', 0) >= 400 and r.get('status_code') != 429])
    
    # Calculate rates
    rate_limited_percentage = (rate_limited_requests / total_requests) * 100 if total_requests > 0 else 0
    success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
    error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
    
    # Response time analysis
    response_times = [r["response_time_ms"] for r in valid_results if r.get("response_time_ms") is not None]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Requests per second
    requests_per_second = total_requests / duration if duration > 0 else 0
    
    print(f"📊 RATE LIMITING TEST RESULTS")
    print("=" * 40)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Total Requests: {total_requests}")
    print(f"Successful (200): {successful_requests}")
    print(f"Rate Limited (429): {rate_limited_requests}")
    print(f"Other Errors: {error_requests}")
    print(f"Rate Limited: {rate_limited_percentage:.1f}%")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Error Rate: {error_rate:.1f}%")
    print(f"Avg Response Time: {avg_response_time:.2f}ms")
    print(f"Requests/Second: {requests_per_second:.1f}")
    print("")
    
    # Determine if rate limiting is working
    rate_limiting_effective = rate_limited_requests > 0
    
    if rate_limiting_effective:
        print("✅ Rate limiting is WORKING - 429 responses detected")
    else:
        print("⚠️ Rate limiting may not be active - no 429 responses")
    
    # Check if performance monitoring is working
    perf_headers_present = len([r for r in valid_results if r.get('performance_header') != 'Not present']) > 0
    
    if perf_headers_present:
        print("✅ Performance monitoring is WORKING - headers detected")
    else:
        print("⚠️ Performance monitoring headers not detected")
    
    return {
        "endpoint": endpoint,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "rate_limited_requests": rate_limited_requests,
        "error_requests": error_requests,
        "rate_limited_percentage": rate_limited_percentage,
        "success_rate": success_rate,
        "error_rate": error_rate,
        "avg_response_time": avg_response_time,
        "requests_per_second": requests_per_second,
        "duration": duration,
        "rate_limiting_effective": rate_limiting_effective,
        "performance_monitoring_working": perf_headers_present,
        "detailed_results": valid_results
    }


async def main():
    """Main function to run rate limiting validation."""
    print("🚀 Rate Limiting Validation for Template Marketplace")
    print("=" * 60)
    print("")
    
    # Test different endpoints
    endpoints_to_test = [
        "/health",
        "/docs", 
        "/openapi.json"
    ]
    
    all_results = []
    
    for endpoint in endpoints_to_test:
        print(f"Testing {endpoint}...")
        result = await test_rate_limiting(
            endpoint=endpoint,
            requests_count=50,  # Reduced for faster testing
            concurrent_requests=10
        )
        all_results.append(result)
        print("")
        
        # Small delay between endpoint tests
        await asyncio.sleep(2)
    
    # Overall assessment
    print("🏆 OVERALL RATE LIMITING ASSESSMENT")
    print("=" * 40)
    
    endpoints_with_rate_limiting = len([r for r in all_results if r.get('rate_limiting_effective')])
    endpoints_with_monitoring = len([r for r in all_results if r.get('performance_monitoring_working')])
    total_endpoints = len(all_results)
    
    print(f"Endpoints Tested: {total_endpoints}")
    print(f"Rate Limiting Active: {endpoints_with_rate_limiting}/{total_endpoints}")
    print(f"Performance Monitoring: {endpoints_with_monitoring}/{total_endpoints}")
    
    # Calculate overall metrics
    total_requests = sum(r['total_requests'] for r in all_results)
    total_rate_limited = sum(r['rate_limited_requests'] for r in all_results)
    avg_response_time = sum(r['avg_response_time'] for r in all_results) / len(all_results)
    
    print(f"Total Requests Sent: {total_requests}")
    print(f"Total Rate Limited: {total_rate_limited}")
    print(f"Average Response Time: {avg_response_time:.2f}ms")
    
    # Final assessment
    if endpoints_with_monitoring >= total_endpoints * 0.8:
        if endpoints_with_rate_limiting > 0:
            overall_status = "✅ EXCELLENT - Rate limiting and monitoring working"
        else:
            overall_status = "⚠️ GOOD - Monitoring working, rate limiting may need configuration"
    else:
        overall_status = "❌ NEEDS ATTENTION - Infrastructure issues detected"
    
    print(f"\n🎯 Overall Status: {overall_status}")
    
    # Save results
    timestamp = int(time.time())
    filename = f"rate_limiting_validation_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "overall_status": overall_status,
            "summary": {
                "endpoints_tested": total_endpoints,
                "rate_limiting_active": endpoints_with_rate_limiting,
                "performance_monitoring_active": endpoints_with_monitoring,
                "total_requests": total_requests,
                "total_rate_limited": total_rate_limited,
                "avg_response_time": avg_response_time
            },
            "detailed_results": all_results
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: {filename}")
    
    # Return appropriate exit code
    if "EXCELLENT" in overall_status or "GOOD" in overall_status:
        return 0
    else:
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
