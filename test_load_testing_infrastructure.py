#!/usr/bin/env python3
"""
Test script to validate load testing infrastructure without authentication.

This script tests the load testing framework itself and validates that
all components are working correctly.
"""

import os
import subprocess
import sys
import time
import requests


def test_server_connectivity():
    """Test basic server connectivity."""
    print("🔗 Testing server connectivity...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is reachable and healthy")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False


def test_locust_installation():
    """Test if Locust is properly installed."""
    print("\n🐛 Testing Locust installation...")
    
    try:
        result = subprocess.run(["locust", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Locust is installed: {version}")
            return True
        else:
            print("❌ Locust is not properly installed")
            return False
    except FileNotFoundError:
        print("❌ Locust command not found")
        return False


def test_load_testing_files():
    """Test if all load testing files exist."""
    print("\n📁 Testing load testing files...")
    
    required_files = [
        "marketplace_locust.py",
        "marketplace_stress_test.py",
        "marketplace_performance_test.sh",
        "run_performance_tests.py",
        "performance-requirements.txt"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist


def test_simple_locust_run():
    """Test a simple Locust run without authentication."""
    print("\n🔥 Testing simple Locust execution...")
    
    # Create a minimal test file
    simple_test_content = '''
from locust import HttpUser, task, between

class SimpleTestUser(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def test_health_endpoint(self):
        self.client.get("/health")
'''
    
    # Write test file
    with open("simple_test.py", "w") as f:
        f.write(simple_test_content)
    
    try:
        # Run a very short Locust test
        cmd = [
            "locust",
            "-f", "simple_test.py",
            "--host", "http://localhost:8000",
            "-u", "5",
            "-r", "2",
            "-t", "10s",
            "--headless"
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Simple Locust test completed successfully")
            print("📊 Sample output:")
            # Print last few lines of output
            output_lines = result.stdout.split('\n')
            for line in output_lines[-5:]:
                if line.strip():
                    print(f"    {line}")
            return True
        else:
            print(f"❌ Locust test failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Locust test timed out")
        return False
    except Exception as e:
        print(f"❌ Locust test error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists("simple_test.py"):
            os.remove("simple_test.py")


def test_performance_test_runner():
    """Test the performance test runner script."""
    print("\n🏃 Testing performance test runner...")
    
    try:
        # Test help command
        result = subprocess.run([sys.executable, "run_performance_tests.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Template Marketplace Performance Testing" in result.stdout:
            print("✅ Performance test runner is working")
            return True
        else:
            print("❌ Performance test runner has issues")
            print(f"Output: {result.stdout}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Performance test runner error: {e}")
        return False


def test_shell_script_permissions():
    """Test if shell scripts have proper permissions."""
    print("\n🔐 Testing shell script permissions...")
    
    shell_scripts = ["marketplace_performance_test.sh"]
    all_executable = True
    
    for script in shell_scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"✅ {script} is executable")
            else:
                print(f"❌ {script} is not executable")
                all_executable = False
        else:
            print(f"⚠️ {script} not found")
    
    return all_executable


def main():
    """Run all infrastructure tests."""
    print("🧪 LOAD TESTING INFRASTRUCTURE VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Server Connectivity", test_server_connectivity),
        ("Locust Installation", test_locust_installation),
        ("Load Testing Files", test_load_testing_files),
        ("Shell Script Permissions", test_shell_script_permissions),
        ("Simple Locust Run", test_simple_locust_run),
        ("Performance Test Runner", test_performance_test_runner),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n📊 INFRASTRUCTURE TEST SUMMARY")
    print("=" * 40)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All infrastructure tests passed!")
        print("✅ Load testing infrastructure is ready for performance testing")
        return True
    else:
        print("⚠️ Some infrastructure tests failed")
        print("🔧 Please fix the issues before running performance tests")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
