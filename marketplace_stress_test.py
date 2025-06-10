#!/usr/bin/env python3
"""
Stress testing script for Template Marketplace to test system limits.

This script pushes the system beyond normal operating conditions to identify:
- Maximum concurrent user capacity
- Rate limiting effectiveness under extreme load
- System recovery after overload
- Memory and resource exhaustion points

Usage:
    # Run stress test with high user count
    locust -f marketplace_stress_test.py --host=http://localhost:8000 -u 200 -r 20 -t 600s --headless

    # Run with gradual ramp-up
    locust -f marketplace_stress_test.py --host=http://localhost:8000 -u 500 -r 10 -t 1800s --headless
"""

import random
import time
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class AggressiveBrowsingUser(HttpUser):
    """
    Aggressive browsing user that makes rapid requests to test rate limiting.
    """
    
    weight = 60
    wait_time = between(0.1, 0.5)  # Very short wait times for stress testing
    
    def on_start(self):
        """Login and prepare for aggressive testing."""
        self.login_user()
        self.request_count = 0
        self.rate_limited_count = 0
    
    def login_user(self):
        """Login as test user."""
        user_id = random.randint(5, 99)
        login_data = {
            "username": f"testuser{user_id:04d}",
            "password": "testpassword123"
        }
        
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            self.client.headers.update({
                "Authorization": f"Bearer {token_data.get('access_token', '')}"
            })
    
    @task(50)
    def rapid_template_browsing(self):
        """Make rapid template browsing requests to test rate limits."""
        self.request_count += 1
        
        params = {
            "page": random.randint(1, 20),
            "per_page": random.choice([10, 20, 50, 100]),
            "sort_by": random.choice(["created_at", "rating_avg", "downloads"]),
        }
        
        with self.client.get("/api/marketplace/templates", params=params,
                           catch_response=True, name="Rapid Browse") as response:
            if response.status_code == 429:  # Rate limited
                self.rate_limited_count += 1
                response.success()  # Expected behavior
                print(f"✅ Rate limit triggered after {self.request_count} requests")
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(30)
    def rapid_template_details(self):
        """Rapidly request template details."""
        template_id = random.randint(1, 1000)
        
        with self.client.get(f"/api/marketplace/templates/{template_id}",
                           catch_response=True, name="Rapid Details") as response:
            if response.status_code == 429:
                self.rate_limited_count += 1
                response.success()
            elif response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(20)
    def rapid_search_requests(self):
        """Make rapid search requests with complex queries."""
        search_terms = ["nginx", "database", "web", "api", "cache", "monitoring", "docker", "kubernetes"]
        
        params = {
            "query": random.choice(search_terms),
            "category_id": random.randint(1, 10),
            "min_rating": random.choice([1.0, 2.0, 3.0, 4.0]),
            "page": random.randint(1, 50),
            "per_page": 100  # Large page size for stress
        }
        
        with self.client.get("/api/marketplace/templates", params=params,
                           catch_response=True, name="Rapid Search") as response:
            if response.status_code == 429:
                self.rate_limited_count += 1
                response.success()
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")


class AggressiveContributorUser(HttpUser):
    """
    Aggressive contributor that rapidly creates templates to test submission limits.
    """
    
    weight = 30
    wait_time = between(0.2, 1.0)
    
    def on_start(self):
        """Login and prepare for aggressive template creation."""
        self.login_user()
        self.creation_count = 0
        self.rate_limited_count = 0
    
    def login_user(self):
        """Login as contributor."""
        user_id = random.randint(10, 99)
        login_data = {
            "username": f"testuser{user_id:04d}",
            "password": "testpassword123"
        }
        
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            self.client.headers.update({
                "Authorization": f"Bearer {token_data.get('access_token', '')}"
            })
    
    @task(70)
    def rapid_template_creation(self):
        """Rapidly create templates to test rate limiting."""
        self.creation_count += 1
        
        docker_compose = f"""version: '3.8'
services:
  stress_test_{self.creation_count}:
    image: nginx:alpine
    ports:
      - "{8000 + self.creation_count}:80"
    environment:
      - STRESS_TEST=true
      - CREATION_TIME={time.time()}
"""
        
        template_data = {
            "name": f"Stress Test Template {self.creation_count} - {time.time()}",
            "description": f"Stress testing template #{self.creation_count} created for load testing purposes. This template tests the system's ability to handle rapid template submissions.",
            "category_id": random.randint(1, 10),
            "version": f"1.0.{self.creation_count}",
            "docker_compose_yaml": docker_compose,
            "tags": ["stress-test", "load-test", f"batch-{self.creation_count // 10}"]
        }
        
        with self.client.post("/api/marketplace/templates", json=template_data,
                            catch_response=True, name="Rapid Create") as response:
            if response.status_code == 429:  # Rate limited
                self.rate_limited_count += 1
                response.success()
                print(f"✅ Template creation rate limited after {self.creation_count} attempts")
            elif response.status_code == 201:
                response.success()
                print(f"📝 Created template #{self.creation_count}")
            else:
                response.failure(f"Creation failed: {response.status_code}")
    
    @task(30)
    def rapid_review_submission(self):
        """Rapidly submit reviews to test rate limiting."""
        template_id = random.randint(1, 800)
        
        review_data = {
            "rating": random.randint(1, 5),
            "comment": f"Stress test review #{random.randint(1, 1000)} - {time.time()}"
        }
        
        with self.client.post(f"/api/marketplace/templates/{template_id}/reviews",
                            json=review_data, catch_response=True, name="Rapid Review") as response:
            if response.status_code == 429:
                self.rate_limited_count += 1
                response.success()
            elif response.status_code in [201, 409]:  # 409 = already reviewed
                response.success()
            else:
                response.failure(f"Review failed: {response.status_code}")


class AggressiveAdminUser(HttpUser):
    """
    Aggressive admin user testing admin endpoint limits.
    """
    
    weight = 10
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Login as admin."""
        self.login_admin()
        self.admin_requests = 0
    
    def login_admin(self):
        """Login as admin user."""
        admin_id = random.randint(0, 4)
        login_data = {
            "username": f"testuser{admin_id:04d}",
            "password": "testpassword123"
        }
        
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            self.client.headers.update({
                "Authorization": f"Bearer {token_data.get('access_token', '')}"
            })
    
    @task(50)
    def rapid_pending_checks(self):
        """Rapidly check pending templates."""
        self.admin_requests += 1
        
        with self.client.get("/api/marketplace/admin/pending",
                           catch_response=True, name="Rapid Admin Pending") as response:
            if response.status_code == 429:
                response.success()
                print(f"✅ Admin rate limit triggered after {self.admin_requests} requests")
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin pending failed: {response.status_code}")
    
    @task(30)
    def rapid_stats_requests(self):
        """Rapidly request marketplace statistics."""
        with self.client.get("/api/marketplace/admin/stats",
                           catch_response=True, name="Rapid Admin Stats") as response:
            if response.status_code == 429:
                response.success()
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin stats failed: {response.status_code}")
    
    @task(20)
    def rapid_approvals(self):
        """Rapidly approve/reject templates."""
        template_id = random.randint(801, 1000)  # Pending templates
        
        approval_data = {
            "approved": random.choice([True, False]),
            "admin_notes": f"Stress test decision #{self.admin_requests}"
        }
        
        with self.client.post(f"/api/marketplace/admin/templates/{template_id}/approve",
                            json=approval_data, catch_response=True, name="Rapid Approval") as response:
            if response.status_code == 429:
                response.success()
            elif response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Approval failed: {response.status_code}")


# Performance monitoring for stress testing
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Monitor stress test performance."""
    if response_time > 500:  # Very slow requests
        print(f"🚨 VERY SLOW REQUEST: {name} took {response_time:.0f}ms")
    elif response_time > 200:
        print(f"⚠️ Slow request: {name} took {response_time:.0f}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize stress testing."""
    print("🚨 Starting Template Marketplace STRESS Testing")
    print("⚡ This test pushes the system beyond normal limits")
    print("🎯 Stress Test Objectives:")
    print("  - Test rate limiting effectiveness")
    print("  - Find maximum concurrent user capacity")
    print("  - Validate system recovery after overload")
    print("  - Identify resource exhaustion points")
    print("⚠️ Monitor system resources during this test!")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize stress testing."""
    print("✅ Template Marketplace Stress Testing Completed")
    print("📊 Analyze results for:")
    print("  - Rate limiting effectiveness")
    print("  - System stability under extreme load")
    print("  - Resource usage patterns")
    print("  - Recovery time after overload")
