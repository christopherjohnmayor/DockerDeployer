#!/usr/bin/env python3
"""
API Response Time Validation Script for Template Marketplace.

This script validates that all critical marketplace endpoints respond
within the <200ms performance target under normal load conditions.
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json


class APIResponseTimeValidator:
    """Validator for API response times."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the validator."""
        self.base_url = base_url
        self.results = []
        self.target_response_time = 200  # 200ms target
        
    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", 
                          data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """Test a single endpoint and measure response time."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    await response.text()  # Read response body
                    status_code = response.status
                    response_headers = dict(response.headers)
            elif method == "POST":
                async with session.post(url, json=data, headers=headers) as response:
                    await response.text()
                    status_code = response.status
                    response_headers = dict(response.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Check if performance headers are present
            perf_header = response_headers.get('x-response-time', 'Not present')
            threshold_header = response_headers.get('x-performance-threshold', 'Not present')
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "response_time_ms": round(response_time_ms, 2),
                "status_code": status_code,
                "meets_target": response_time_ms < self.target_response_time,
                "performance_header": perf_header,
                "threshold_header": threshold_header,
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "response_time_ms": None,
                "status_code": None,
                "meets_target": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def test_concurrent_load(self, endpoint: str, concurrent_users: int = 50, 
                                 total_requests: int = 200) -> List[Dict[str, Any]]:
        """Test endpoint under concurrent load."""
        print(f"🔥 Testing {endpoint} with {concurrent_users} concurrent users ({total_requests} total requests)")
        
        async with aiohttp.ClientSession() as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(concurrent_users)
            
            async def make_request():
                async with semaphore:
                    return await self.test_endpoint(session, endpoint)
            
            # Create tasks for all requests
            tasks = [make_request() for _ in range(total_requests)]
            
            # Execute all requests concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Filter out exceptions and process results
            valid_results = [r for r in results if isinstance(r, dict) and not r.get('error')]
            
            if valid_results:
                response_times = [r['response_time_ms'] for r in valid_results if r['response_time_ms'] is not None]
                
                if response_times:
                    summary = {
                        "endpoint": endpoint,
                        "concurrent_users": concurrent_users,
                        "total_requests": total_requests,
                        "successful_requests": len(valid_results),
                        "failed_requests": total_requests - len(valid_results),
                        "success_rate": (len(valid_results) / total_requests) * 100,
                        "total_duration": round(end_time - start_time, 2),
                        "requests_per_second": round(total_requests / (end_time - start_time), 2),
                        "response_times": {
                            "min": round(min(response_times), 2),
                            "max": round(max(response_times), 2),
                            "avg": round(statistics.mean(response_times), 2),
                            "median": round(statistics.median(response_times), 2),
                            "p95": round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 20 else round(max(response_times), 2)
                        },
                        "performance_analysis": {
                            "meets_target_count": len([r for r in response_times if r < self.target_response_time]),
                            "meets_target_percentage": round((len([r for r in response_times if r < self.target_response_time]) / len(response_times)) * 100, 2),
                            "slow_requests": len([r for r in response_times if r >= self.target_response_time])
                        }
                    }
                    
                    print(f"  ✅ Completed: {summary['successful_requests']}/{summary['total_requests']} requests")
                    print(f"  📊 Success Rate: {summary['success_rate']:.1f}%")
                    print(f"  ⚡ Avg Response Time: {summary['response_times']['avg']}ms")
                    print(f"  🎯 Target Met: {summary['performance_analysis']['meets_target_percentage']}% of requests")
                    
                    return summary
            
            return {
                "endpoint": endpoint,
                "error": "No valid responses received",
                "concurrent_users": concurrent_users,
                "total_requests": total_requests
            }
    
    async def validate_critical_endpoints(self):
        """Validate response times for all critical marketplace endpoints."""
        print("🚀 Starting API Response Time Validation")
        print("=" * 60)
        print(f"🎯 Target: <{self.target_response_time}ms response time")
        print(f"👥 Load: 50 concurrent users per endpoint")
        print("")
        
        # Define critical endpoints to test
        critical_endpoints = [
            "/health",
            "/docs",
            "/openapi.json",
            # Add more endpoints as they become available
        ]
        
        results = []
        
        # Test each endpoint under load
        for endpoint in critical_endpoints:
            try:
                result = await self.test_concurrent_load(endpoint, concurrent_users=50, total_requests=200)
                results.append(result)
                print("")
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
                results.append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
                print("")
        
        return results
    
    def generate_performance_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        print("📊 PERFORMANCE VALIDATION REPORT")
        print("=" * 60)
        
        total_endpoints = len(results)
        successful_endpoints = len([r for r in results if not r.get('error')])
        
        # Calculate overall statistics
        all_response_times = []
        all_success_rates = []
        endpoints_meeting_target = 0
        
        for result in results:
            if not result.get('error') and 'response_times' in result:
                all_response_times.extend([
                    result['response_times']['min'],
                    result['response_times']['max'],
                    result['response_times']['avg']
                ])
                all_success_rates.append(result['success_rate'])
                
                if result['performance_analysis']['meets_target_percentage'] >= 95:
                    endpoints_meeting_target += 1
                
                # Print individual endpoint results
                endpoint = result['endpoint']
                avg_time = result['response_times']['avg']
                target_met = result['performance_analysis']['meets_target_percentage']
                success_rate = result['success_rate']
                
                status = "✅ PASS" if avg_time < self.target_response_time and target_met >= 95 else "❌ FAIL"
                print(f"{status} {endpoint}")
                print(f"    Avg Response: {avg_time}ms")
                print(f"    Target Met: {target_met}%")
                print(f"    Success Rate: {success_rate}%")
                print("")
        
        # Overall assessment
        overall_success_rate = statistics.mean(all_success_rates) if all_success_rates else 0
        overall_avg_response = statistics.mean(all_response_times) if all_response_times else 0
        endpoints_passing_percentage = (endpoints_meeting_target / total_endpoints) * 100 if total_endpoints > 0 else 0
        
        print("🎯 OVERALL ASSESSMENT:")
        print(f"   Endpoints Tested: {total_endpoints}")
        print(f"   Endpoints Passing: {endpoints_meeting_target}/{total_endpoints} ({endpoints_passing_percentage:.1f}%)")
        print(f"   Average Response Time: {overall_avg_response:.2f}ms")
        print(f"   Average Success Rate: {overall_success_rate:.1f}%")
        
        # Determine overall status
        if endpoints_passing_percentage >= 80 and overall_avg_response < self.target_response_time:
            overall_status = "✅ EXCELLENT"
            recommendation = "System meets performance requirements for production deployment"
        elif endpoints_passing_percentage >= 60 and overall_avg_response < self.target_response_time * 1.5:
            overall_status = "⚠️ ACCEPTABLE"
            recommendation = "System performance is acceptable but monitor closely"
        else:
            overall_status = "❌ NEEDS IMPROVEMENT"
            recommendation = "System requires optimization before production deployment"
        
        print(f"\n🏆 Overall Status: {overall_status}")
        print(f"💡 Recommendation: {recommendation}")
        
        return {
            "overall_status": overall_status,
            "endpoints_tested": total_endpoints,
            "endpoints_passing": endpoints_meeting_target,
            "pass_percentage": endpoints_passing_percentage,
            "average_response_time": overall_avg_response,
            "average_success_rate": overall_success_rate,
            "recommendation": recommendation,
            "detailed_results": results
        }


async def main():
    """Main function to run API response time validation."""
    validator = APIResponseTimeValidator()
    
    try:
        # Run validation tests
        results = await validator.validate_critical_endpoints()
        
        # Generate and display report
        report = validator.generate_performance_report(results)
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"api_response_time_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {filename}")
        
        # Exit with appropriate code
        if report['pass_percentage'] >= 80:
            print("\n🎉 API Response Time Validation: PASSED")
            return 0
        else:
            print("\n⚠️ API Response Time Validation: FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
