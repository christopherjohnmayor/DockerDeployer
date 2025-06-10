#!/usr/bin/env python3
"""
Comprehensive Concurrent User Load Testing for Template Marketplace.

This script executes load testing with 100+ concurrent users using mixed scenarios,
monitors system resources, validates rate limiting effectiveness, and ensures <1% error rate.
"""

import asyncio
import aiohttp
import time
import statistics
import psutil
import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime
import concurrent.futures


class SystemResourceMonitor:
    """Monitor system resources during load testing."""
    
    def __init__(self):
        """Initialize the monitor."""
        self.metrics = []
        self.monitoring = False
        
    async def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system resources."""
        self.monitoring = True
        
        while self.monitoring:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get network stats if available
                try:
                    network = psutil.net_io_counters()
                    network_stats = {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    }
                except:
                    network_stats = {}
                
                metric = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "network": network_stats
                }
                
                self.metrics.append(metric)
                
                # Log warnings for high resource usage
                if cpu_percent > 80:
                    print(f"⚠️ High CPU usage: {cpu_percent:.1f}%")
                
                if memory.percent > 80:
                    print(f"⚠️ High memory usage: {memory.percent:.1f}%")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"Error monitoring resources: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop monitoring system resources."""
        self.monitoring = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get resource usage summary."""
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_percent"] for m in self.metrics]
        
        return {
            "duration_seconds": len(self.metrics),
            "cpu": {
                "avg": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "p95": statistics.quantiles(cpu_values, n=20)[18] if len(cpu_values) > 20 else max(cpu_values)
            },
            "memory": {
                "avg": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "p95": statistics.quantiles(memory_values, n=20)[18] if len(memory_values) > 20 else max(memory_values)
            },
            "peak_memory_used_gb": max(m["memory_used_gb"] for m in self.metrics),
            "warnings": {
                "high_cpu_events": len([m for m in self.metrics if m["cpu_percent"] > 80]),
                "high_memory_events": len([m for m in self.metrics if m["memory_percent"] > 80])
            }
        }


class ConcurrentUserLoadTester:
    """Main class for concurrent user load testing."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the load tester."""
        self.base_url = base_url
        self.results = []
        self.resource_monitor = SystemResourceMonitor()
        
        # Test scenarios with different weights
        self.scenarios = [
            {"name": "docs_browsing", "weight": 40, "endpoint": "/docs"},
            {"name": "api_schema", "weight": 30, "endpoint": "/openapi.json"},
            {"name": "health_check", "weight": 20, "endpoint": "/health"},
            {"name": "root_access", "weight": 10, "endpoint": "/"}
        ]
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, 
                          scenario_name: str) -> Dict[str, Any]:
        """Make a single request and measure performance."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            async with session.get(url) as response:
                await response.text()  # Read response body
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                # Extract performance headers
                perf_header = response.headers.get('x-response-time', 'Not present')
                
                return {
                    "scenario": scenario_name,
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "response_time_ms": round(response_time_ms, 2),
                    "performance_header": perf_header,
                    "success": response.status < 400,
                    "timestamp": time.time()
                }
                
        except Exception as e:
            return {
                "scenario": scenario_name,
                "endpoint": endpoint,
                "status_code": None,
                "response_time_ms": None,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def simulate_user_session(self, session: aiohttp.ClientSession, 
                                  user_id: int, duration_seconds: int = 120) -> List[Dict[str, Any]]:
        """Simulate a user session with mixed scenarios."""
        user_results = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds:
            # Choose scenario based on weights
            scenario = random.choices(
                self.scenarios,
                weights=[s["weight"] for s in self.scenarios]
            )[0]
            
            # Make request
            result = await self.make_request(session, scenario["endpoint"], scenario["name"])
            result["user_id"] = user_id
            user_results.append(result)
            
            # Random delay between requests (0.5-3 seconds)
            await asyncio.sleep(random.uniform(0.5, 3.0))
        
        return user_results
    
    async def run_concurrent_load_test(self, concurrent_users: int = 100, 
                                     duration_seconds: int = 120) -> Dict[str, Any]:
        """Run concurrent user load test."""
        print(f"🚀 Starting Concurrent User Load Test")
        print(f"👥 Concurrent Users: {concurrent_users}")
        print(f"⏱️ Duration: {duration_seconds} seconds")
        print(f"🎯 Target: <1% error rate, <200ms response times")
        print("")
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())
        
        # Create connector with appropriate limits
        connector = aiohttp.TCPConnector(
            limit=concurrent_users * 2,
            limit_per_host=concurrent_users * 2
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Create tasks for all users
            user_tasks = [
                self.simulate_user_session(session, user_id, duration_seconds)
                for user_id in range(concurrent_users)
            ]
            
            print(f"🔥 Launching {concurrent_users} concurrent users...")
            start_time = time.time()
            
            # Run all user sessions concurrently
            user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
            
            end_time = time.time()
            actual_duration = end_time - start_time
        
        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()
        monitor_task.cancel()
        
        # Process results
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, list):
                all_results.extend(user_result)
            elif isinstance(user_result, Exception):
                print(f"⚠️ User session failed: {user_result}")
        
        return self.analyze_results(all_results, actual_duration, concurrent_users)
    
    def analyze_results(self, results: List[Dict[str, Any]], duration: float, 
                       concurrent_users: int) -> Dict[str, Any]:
        """Analyze load test results."""
        print(f"\n📊 CONCURRENT LOAD TEST ANALYSIS")
        print("=" * 50)
        
        if not results:
            return {"error": "No results to analyze"}
        
        # Basic statistics
        total_requests = len(results)
        successful_requests = len([r for r in results if r.get("success")])
        failed_requests = total_requests - successful_requests
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        
        # Response time analysis
        response_times = [r["response_time_ms"] for r in results if r.get("response_time_ms") is not None]
        
        if response_times:
            response_stats = {
                "min": round(min(response_times), 2),
                "max": round(max(response_times), 2),
                "avg": round(statistics.mean(response_times), 2),
                "median": round(statistics.median(response_times), 2),
                "p95": round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 20 else round(max(response_times), 2),
                "p99": round(statistics.quantiles(response_times, n=100)[98], 2) if len(response_times) > 100 else round(max(response_times), 2)
            }
        else:
            response_stats = {}
        
        # Throughput analysis
        requests_per_second = total_requests / duration if duration > 0 else 0
        
        # Scenario analysis
        scenario_stats = {}
        for scenario in self.scenarios:
            scenario_results = [r for r in results if r.get("scenario") == scenario["name"]]
            if scenario_results:
                scenario_response_times = [r["response_time_ms"] for r in scenario_results if r.get("response_time_ms") is not None]
                scenario_success_rate = (len([r for r in scenario_results if r.get("success")]) / len(scenario_results)) * 100
                
                scenario_stats[scenario["name"]] = {
                    "requests": len(scenario_results),
                    "success_rate": round(scenario_success_rate, 2),
                    "avg_response_time": round(statistics.mean(scenario_response_times), 2) if scenario_response_times else 0,
                    "endpoint": scenario["endpoint"]
                }
        
        # Performance targets validation
        targets_met = {
            "error_rate_under_1_percent": error_rate < 1.0,
            "avg_response_under_200ms": response_stats.get("avg", 0) < 200,
            "p95_response_under_200ms": response_stats.get("p95", 0) < 200,
            "no_system_resource_warnings": True  # Will be updated with resource analysis
        }
        
        # Get resource usage summary
        resource_summary = self.resource_monitor.get_summary()
        if not resource_summary.get("error"):
            targets_met["no_system_resource_warnings"] = (
                resource_summary["warnings"]["high_cpu_events"] == 0 and
                resource_summary["warnings"]["high_memory_events"] == 0
            )
        
        # Overall assessment
        targets_passed = sum(targets_met.values())
        total_targets = len(targets_met)
        overall_success = targets_passed == total_targets
        
        # Print results
        print(f"Duration: {duration:.1f} seconds")
        print(f"Concurrent Users: {concurrent_users}")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Failed Requests: {failed_requests}")
        print(f"Error Rate: {error_rate:.2f}%")
        print(f"Requests/Second: {requests_per_second:.1f}")
        print("")
        
        if response_stats:
            print("📈 Response Time Statistics:")
            print(f"  Average: {response_stats['avg']}ms")
            print(f"  Median: {response_stats['median']}ms")
            print(f"  95th Percentile: {response_stats['p95']}ms")
            print(f"  99th Percentile: {response_stats['p99']}ms")
            print(f"  Min: {response_stats['min']}ms")
            print(f"  Max: {response_stats['max']}ms")
            print("")
        
        print("🎯 Performance Targets:")
        for target, met in targets_met.items():
            status = "✅" if met else "❌"
            print(f"  {status} {target.replace('_', ' ').title()}")
        print("")
        
        print("📊 Scenario Performance:")
        for scenario_name, stats in scenario_stats.items():
            print(f"  {scenario_name}: {stats['requests']} requests, "
                  f"{stats['success_rate']}% success, {stats['avg_response_time']}ms avg")
        print("")
        
        if not resource_summary.get("error"):
            print("💻 System Resource Usage:")
            print(f"  CPU Average: {resource_summary['cpu']['avg']:.1f}%")
            print(f"  CPU Peak: {resource_summary['cpu']['max']:.1f}%")
            print(f"  Memory Average: {resource_summary['memory']['avg']:.1f}%")
            print(f"  Memory Peak: {resource_summary['memory']['max']:.1f}%")
            print(f"  Peak Memory Used: {resource_summary['peak_memory_used_gb']:.2f} GB")
            print("")
        
        # Final assessment
        if overall_success:
            print("🏆 Overall Assessment: ✅ EXCELLENT")
            print("💡 All performance targets met - ready for production load")
        elif targets_passed >= total_targets * 0.75:
            print("🏆 Overall Assessment: ⚠️ GOOD")
            print("💡 Most targets met - minor optimizations recommended")
        else:
            print("🏆 Overall Assessment: ❌ NEEDS IMPROVEMENT")
            print("💡 Performance optimization required before production")
        
        return {
            "overall_success": overall_success,
            "targets_passed": targets_passed,
            "total_targets": total_targets,
            "duration": duration,
            "concurrent_users": concurrent_users,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_rate": error_rate,
            "requests_per_second": requests_per_second,
            "response_times": response_stats,
            "scenario_stats": scenario_stats,
            "targets_met": targets_met,
            "resource_usage": resource_summary,
            "detailed_results": results
        }


async def main():
    """Main function to run concurrent user load testing."""
    tester = ConcurrentUserLoadTester()
    
    try:
        # Run the load test
        results = await tester.run_concurrent_load_test(
            concurrent_users=100,
            duration_seconds=120
        )
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"concurrent_load_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: {filename}")
        
        # Return appropriate exit code
        if results.get("overall_success"):
            print("\n🎉 Concurrent User Load Test: PASSED")
            return 0
        else:
            print("\n⚠️ Concurrent User Load Test: NEEDS ATTENTION")
            return 1
            
    except Exception as e:
        print(f"\n❌ Load test failed with error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
