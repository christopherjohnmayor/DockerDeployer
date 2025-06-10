#!/usr/bin/env python3
"""
Comprehensive performance test runner for Template Marketplace.

This script orchestrates all performance testing scenarios:
1. Basic API response time validation
2. Load testing with realistic user scenarios
3. Stress testing for system limits
4. Rate limiting validation
5. Database performance testing

Usage:
    python run_performance_tests.py --test-type all
    python run_performance_tests.py --test-type load --users 100 --duration 300
    python run_performance_tests.py --test-type stress --users 200 --duration 600
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

import requests


class PerformanceTestRunner:
    """Main class for running marketplace performance tests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the test runner."""
        self.base_url = base_url
        self.results = {
            "test_run_id": f"perf_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": {}
        }
        
    def check_server_health(self) -> bool:
        """Check if the marketplace server is running and healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Server is healthy and ready for testing")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def authenticate_test_user(self) -> str:
        """Authenticate a test user and return access token."""
        try:
            login_data = {
                "username": "testuser0010",
                "password": "testpassword123"
            }
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json().get("access_token")
                print("✅ Test user authenticated successfully")
                return token
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return ""
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return ""
    
    def run_basic_response_time_test(self) -> Dict[str, Any]:
        """Run basic API response time validation."""
        print("\n🚀 Running Basic API Response Time Tests")
        print("=" * 50)
        
        token = self.authenticate_test_user()
        if not token:
            return {"status": "failed", "error": "Authentication failed"}
        
        headers = {"Authorization": f"Bearer {token}"}
        endpoints = [
            ("/api/marketplace/templates", "Browse Templates"),
            ("/api/marketplace/templates/1", "Template Details"),
            ("/api/marketplace/categories", "Browse Categories"),
            ("/api/marketplace/stats", "Marketplace Stats"),
            ("/api/marketplace/my-templates", "My Templates")
        ]
        
        results = {}
        total_passed = 0
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                result = {
                    "response_time_ms": round(response_time_ms, 2),
                    "status_code": response.status_code,
                    "passed": response_time_ms < 200 and response.status_code in [200, 404]
                }
                
                results[name] = result
                
                if result["passed"]:
                    print(f"✅ {name}: {result['response_time_ms']}ms")
                    total_passed += 1
                else:
                    print(f"❌ {name}: {result['response_time_ms']}ms (FAILED)")
                    
            except Exception as e:
                results[name] = {"error": str(e), "passed": False}
                print(f"❌ {name}: Error - {e}")
        
        summary = {
            "total_tests": len(endpoints),
            "passed": total_passed,
            "success_rate": (total_passed / len(endpoints)) * 100,
            "results": results
        }
        
        print(f"\n📊 Summary: {total_passed}/{len(endpoints)} tests passed ({summary['success_rate']:.1f}%)")
        return summary
    
    def run_locust_test(self, test_file: str, users: int, spawn_rate: int, duration: int, test_name: str) -> Dict[str, Any]:
        """Run a Locust load test."""
        print(f"\n🔥 Running {test_name}")
        print("=" * 50)
        print(f"Users: {users}, Spawn Rate: {spawn_rate}/sec, Duration: {duration}s")
        
        # Create results directory
        results_dir = "performance_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate unique filename for this test
        timestamp = int(time.time())
        csv_file = f"{results_dir}/{test_name.lower().replace(' ', '_')}_{timestamp}.csv"
        html_file = f"{results_dir}/{test_name.lower().replace(' ', '_')}_{timestamp}.html"
        
        # Build Locust command
        cmd = [
            "locust",
            "-f", test_file,
            "--host", self.base_url,
            "-u", str(users),
            "-r", str(spawn_rate),
            "-t", f"{duration}s",
            "--headless",
            "--csv", csv_file.replace('.csv', ''),
            "--html", html_file
        ]
        
        try:
            print(f"🚀 Starting Locust test: {' '.join(cmd)}")
            start_time = time.time()
            
            # Run Locust test
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 60)
            
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # Parse results from output
            output_lines = result.stdout.split('\n')
            stats = self._parse_locust_output(output_lines)
            
            test_result = {
                "status": "completed" if result.returncode == 0 else "failed",
                "duration": round(actual_duration, 2),
                "users": users,
                "spawn_rate": spawn_rate,
                "csv_file": csv_file,
                "html_file": html_file,
                "stats": stats,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print(f"✅ {test_name} completed successfully")
                if stats:
                    print(f"📈 Average Response Time: {stats.get('avg_response_time', 'N/A')}ms")
                    print(f"📈 Failure Rate: {stats.get('failure_rate', 'N/A')}%")
            else:
                print(f"❌ {test_name} failed with return code {result.returncode}")
                print(f"Error: {result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} timed out after {duration + 60} seconds")
            return {"status": "timeout", "duration": duration + 60}
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _parse_locust_output(self, output_lines: List[str]) -> Dict[str, Any]:
        """Parse Locust output to extract performance statistics."""
        stats = {}
        
        for line in output_lines:
            if "Aggregated" in line and "ms" in line:
                # Parse aggregated statistics line
                parts = line.split()
                try:
                    # Extract response time statistics
                    for i, part in enumerate(parts):
                        if part.endswith("ms"):
                            if "avg" not in stats:
                                stats["avg_response_time"] = float(part.replace("ms", ""))
                            elif "min" not in stats:
                                stats["min_response_time"] = float(part.replace("ms", ""))
                            elif "max" not in stats:
                                stats["max_response_time"] = float(part.replace("ms", ""))
                except (ValueError, IndexError):
                    continue
            
            elif "failures" in line.lower() and "%" in line:
                # Parse failure rate
                try:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            stats["failure_rate"] = float(part.replace("%", ""))
                            break
                except (ValueError, IndexError):
                    continue
        
        return stats
    
    def run_all_tests(self, users: int = 100, duration: int = 300) -> Dict[str, Any]:
        """Run all performance tests."""
        print("🎯 Starting Comprehensive Performance Testing")
        print("=" * 60)
        
        # Check server health
        if not self.check_server_health():
            return {"status": "failed", "error": "Server health check failed"}
        
        # Run basic response time tests
        self.results["tests"]["basic_response_time"] = self.run_basic_response_time_test()
        
        # Run load tests
        load_tests = [
            ("marketplace_locust.py", users, 10, duration, "Realistic Load Test"),
            ("marketplace_stress_test.py", users * 2, 20, duration // 2, "Stress Test")
        ]
        
        for test_file, test_users, spawn_rate, test_duration, test_name in load_tests:
            if os.path.exists(test_file):
                self.results["tests"][test_name.lower().replace(" ", "_")] = self.run_locust_test(
                    test_file, test_users, spawn_rate, test_duration, test_name
                )
            else:
                print(f"⚠️ Test file {test_file} not found, skipping {test_name}")
        
        # Generate summary
        self._generate_test_summary()
        
        return self.results
    
    def _generate_test_summary(self):
        """Generate a comprehensive test summary."""
        print("\n📊 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_result in self.results["tests"].items():
            total_tests += 1
            
            if test_result.get("status") == "completed" or test_result.get("success_rate", 0) > 95:
                passed_tests += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            print(f"{status} {test_name.replace('_', ' ').title()}")
            
            # Print key metrics
            if "response_time_ms" in test_result:
                print(f"    Response Time: {test_result['response_time_ms']}ms")
            if "success_rate" in test_result:
                print(f"    Success Rate: {test_result['success_rate']:.1f}%")
            if "stats" in test_result and test_result["stats"]:
                stats = test_result["stats"]
                if "avg_response_time" in stats:
                    print(f"    Avg Response Time: {stats['avg_response_time']}ms")
                if "failure_rate" in stats:
                    print(f"    Failure Rate: {stats['failure_rate']}%")
        
        overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 90:
            print("🎉 EXCELLENT: System meets performance requirements!")
        elif overall_success_rate >= 75:
            print("⚠️ GOOD: System performance is acceptable with minor issues")
        else:
            print("🚨 POOR: System requires performance optimization")
        
        # Save results to file
        results_file = f"performance_results/test_summary_{self.results['test_run_id']}.json"
        os.makedirs("performance_results", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")


def main():
    """Main function to run performance tests."""
    parser = argparse.ArgumentParser(description="Template Marketplace Performance Testing")
    parser.add_argument("--test-type", choices=["all", "basic", "load", "stress"], 
                       default="all", help="Type of test to run")
    parser.add_argument("--users", type=int, default=100, 
                       help="Number of concurrent users for load testing")
    parser.add_argument("--duration", type=int, default=300, 
                       help="Test duration in seconds")
    parser.add_argument("--host", default="http://localhost:8000", 
                       help="Base URL of the marketplace API")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = PerformanceTestRunner(args.host)
    
    try:
        if args.test_type == "all":
            results = runner.run_all_tests(args.users, args.duration)
        elif args.test_type == "basic":
            results = {"tests": {"basic": runner.run_basic_response_time_test()}}
        elif args.test_type == "load":
            results = {"tests": {"load": runner.run_locust_test(
                "marketplace_locust.py", args.users, 10, args.duration, "Load Test"
            )}}
        elif args.test_type == "stress":
            results = {"tests": {"stress": runner.run_locust_test(
                "marketplace_stress_test.py", args.users, 20, args.duration, "Stress Test"
            )}}
        
        # Exit with appropriate code
        if any(test.get("status") == "failed" for test in results.get("tests", {}).values()):
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⏹️ Performance testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Performance testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
