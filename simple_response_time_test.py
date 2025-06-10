#!/usr/bin/env python3
"""
Simple API Response Time Test for Template Marketplace.

This script validates API response times using basic HTTP requests
and confirms the performance monitoring middleware is working.
"""

import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import json


def test_endpoint_response_time(url, timeout=5):
    """Test a single endpoint and extract performance metrics."""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        # Calculate our own response time
        measured_time = (end_time - start_time) * 1000
        
        # Extract performance headers from middleware
        perf_header = response.headers.get('x-response-time', 'Not present')
        threshold_header = response.headers.get('x-performance-threshold', 'Not present')
        
        # Parse middleware response time if present
        middleware_time = None
        if perf_header != 'Not present' and 'ms' in perf_header:
            try:
                middleware_time = float(perf_header.replace('ms', ''))
            except:
                pass
        
        return {
            "url": url,
            "status_code": response.status_code,
            "measured_time_ms": round(measured_time, 2),
            "middleware_time_ms": middleware_time,
            "performance_header": perf_header,
            "threshold_header": threshold_header,
            "success": True
        }
        
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }


def run_concurrent_test(url, num_requests=50, max_workers=10):
    """Run concurrent requests to test performance under load."""
    print(f"🔥 Testing {url} with {num_requests} requests ({max_workers} concurrent)")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        futures = [executor.submit(test_endpoint_response_time, url) for _ in range(num_requests)]
        
        # Collect results
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    # Analyze results
    successful_results = [r for r in results if r.get('success')]
    failed_results = [r for r in results if not r.get('success')]
    
    if successful_results:
        # Get response times (prefer middleware times if available)
        response_times = []
        for r in successful_results:
            if r.get('middleware_time_ms') is not None:
                response_times.append(r['middleware_time_ms'])
            else:
                response_times.append(r['measured_time_ms'])
        
        if response_times:
            analysis = {
                "url": url,
                "total_requests": num_requests,
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": (len(successful_results) / num_requests) * 100,
                "response_times": {
                    "min": round(min(response_times), 2),
                    "max": round(max(response_times), 2),
                    "avg": round(statistics.mean(response_times), 2),
                    "median": round(statistics.median(response_times), 2)
                },
                "performance_analysis": {
                    "under_200ms": len([t for t in response_times if t < 200]),
                    "under_200ms_percentage": round((len([t for t in response_times if t < 200]) / len(response_times)) * 100, 2),
                    "over_200ms": len([t for t in response_times if t >= 200])
                },
                "middleware_working": any(r.get('middleware_time_ms') is not None for r in successful_results)
            }
            
            return analysis
    
    return {
        "url": url,
        "error": "No successful requests",
        "total_requests": num_requests,
        "failed_requests": len(failed_results)
    }


def main():
    """Main function to run API response time validation."""
    print("🚀 API Response Time Validation")
    print("=" * 50)
    print("🎯 Target: <200ms response time")
    print("📊 Testing with concurrent requests")
    print("")
    
    base_url = "http://localhost:8000"
    
    # Test endpoints that should be available
    test_endpoints = [
        "/docs",
        "/openapi.json",
        "/health"
    ]
    
    all_results = []
    
    for endpoint in test_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing {endpoint}...")
        
        # Run concurrent test
        result = run_concurrent_test(url, num_requests=50, max_workers=10)
        all_results.append(result)
        
        # Display results
        if not result.get('error'):
            avg_time = result['response_times']['avg']
            success_rate = result['success_rate']
            under_200ms = result['performance_analysis']['under_200ms_percentage']
            middleware_working = result['middleware_working']
            
            status = "✅ PASS" if avg_time < 200 and under_200ms >= 95 else "❌ FAIL"
            middleware_status = "✅" if middleware_working else "❌"
            
            print(f"  {status} Average: {avg_time}ms")
            print(f"  📈 Success Rate: {success_rate:.1f}%")
            print(f"  🎯 <200ms: {under_200ms:.1f}%")
            print(f"  🔧 Middleware: {middleware_status}")
        else:
            print(f"  ❌ FAILED: {result.get('error')}")
        
        print("")
    
    # Overall assessment
    print("📊 OVERALL ASSESSMENT")
    print("=" * 30)
    
    successful_tests = [r for r in all_results if not r.get('error')]
    total_tests = len(all_results)
    
    if successful_tests:
        # Calculate overall metrics
        all_avg_times = [r['response_times']['avg'] for r in successful_tests]
        all_success_rates = [r['success_rate'] for r in successful_tests]
        all_under_200ms = [r['performance_analysis']['under_200ms_percentage'] for r in successful_tests]
        middleware_working_count = len([r for r in successful_tests if r.get('middleware_working')])
        
        overall_avg_time = statistics.mean(all_avg_times)
        overall_success_rate = statistics.mean(all_success_rates)
        overall_under_200ms = statistics.mean(all_under_200ms)
        
        print(f"Tests Completed: {len(successful_tests)}/{total_tests}")
        print(f"Average Response Time: {overall_avg_time:.2f}ms")
        print(f"Average Success Rate: {overall_success_rate:.1f}%")
        print(f"Requests <200ms: {overall_under_200ms:.1f}%")
        print(f"Middleware Working: {middleware_working_count}/{len(successful_tests)} endpoints")
        
        # Determine overall status
        if (overall_avg_time < 200 and 
            overall_under_200ms >= 95 and 
            overall_success_rate >= 95 and
            middleware_working_count >= len(successful_tests) * 0.8):
            
            overall_status = "✅ EXCELLENT"
            recommendation = "API response times meet production requirements"
        elif (overall_avg_time < 300 and 
              overall_under_200ms >= 80 and 
              overall_success_rate >= 90):
            
            overall_status = "⚠️ ACCEPTABLE"
            recommendation = "Performance is acceptable but monitor closely"
        else:
            overall_status = "❌ NEEDS IMPROVEMENT"
            recommendation = "Optimization required before production deployment"
        
        print(f"\n🏆 Overall Status: {overall_status}")
        print(f"💡 Recommendation: {recommendation}")
        
        # Save detailed results
        timestamp = int(time.time())
        filename = f"api_response_validation_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "overall_status": overall_status,
            "overall_metrics": {
                "avg_response_time": overall_avg_time,
                "success_rate": overall_success_rate,
                "under_200ms_percentage": overall_under_200ms,
                "middleware_working_count": middleware_working_count
            },
            "recommendation": recommendation,
            "detailed_results": all_results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {filename}")
        
        # Return appropriate exit code
        if overall_status == "✅ EXCELLENT":
            return 0
        elif overall_status == "⚠️ ACCEPTABLE":
            return 0
        else:
            return 1
    else:
        print("❌ No successful tests completed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
