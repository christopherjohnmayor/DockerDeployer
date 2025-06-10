#!/usr/bin/env python3
"""
Comprehensive load testing script for Template Marketplace using Locust.

This script simulates realistic user scenarios:
- 70% browsing activities (search, view templates, read reviews)
- 20% template submission activities (create, update templates)
- 10% admin operations (approve/reject templates, manage users)

Usage:
    # Install Locust first
    pip install locust

    # Run load testing
    locust -f marketplace_locust.py --host=http://localhost:8000

    # Run with specific user count and spawn rate
    locust -f marketplace_locust.py --host=http://localhost:8000 -u 100 -r 10

    # Run headless mode for CI/CD
    locust -f marketplace_locust.py --host=http://localhost:8000 -u 50 -r 5 -t 300s --headless
"""

import random
import time
from typing import Dict, Any

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class MarketplaceBrowsingUser(HttpUser):
    """
    User class for marketplace browsing activities (70% of traffic).
    Simulates regular users browsing templates, reading reviews, and searching.
    """
    
    weight = 70  # 70% of users will be browsing users
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user session with login."""
        self.login_as_regular_user()
        self.template_ids = list(range(1, 801))  # Approved templates (80% of 1000)
        self.category_ids = list(range(1, 11))  # Available categories
    
    def login_as_regular_user(self):
        """Login as a regular test user."""
        user_id = random.randint(5, 99)  # Regular users (not admins)
        login_data = {
            "username": f"testuser{user_id:04d}",
            "password": "testpassword123"
        }
        
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                # Store auth token for subsequent requests
                token_data = response.json()
                self.client.headers.update({
                    "Authorization": f"Bearer {token_data.get('access_token', '')}"
                })
            else:
                response.failure(f"Login failed: {response.status_code}")
                raise RescheduleTask()
    
    @task(30)
    def browse_templates(self):
        """Browse marketplace templates with various filters."""
        params = {
            "page": random.randint(1, 10),
            "per_page": random.choice([10, 20, 50]),
            "sort_by": random.choice(["created_at", "rating_avg", "downloads", "name"]),
            "sort_order": random.choice(["asc", "desc"])
        }
        
        # Add random filters
        if random.random() < 0.3:  # 30% chance to filter by category
            params["category_id"] = random.choice(self.category_ids)
        
        if random.random() < 0.2:  # 20% chance to filter by rating
            params["min_rating"] = random.choice([3.0, 4.0, 4.5])
        
        if random.random() < 0.4:  # 40% chance to search
            search_terms = ["nginx", "database", "web", "api", "cache", "monitoring"]
            params["query"] = random.choice(search_terms)
        
        with self.client.get("/api/marketplace/templates", params=params, 
                           catch_response=True, name="Browse Templates") as response:
            if response.status_code == 200:
                response.success()
                # Track response time for performance monitoring
                if response.elapsed.total_seconds() > 0.2:  # >200ms
                    print(f"⚠️ Slow browse request: {response.elapsed.total_seconds():.3f}s")
            else:
                response.failure(f"Browse failed: {response.status_code}")
    
    @task(20)
    def view_template_details(self):
        """View detailed information about a specific template."""
        template_id = random.choice(self.template_ids)
        
        with self.client.get(f"/api/marketplace/templates/{template_id}",
                           catch_response=True, name="View Template Details") as response:
            if response.status_code == 200:
                response.success()
                if response.elapsed.total_seconds() > 0.2:
                    print(f"⚠️ Slow template details: {response.elapsed.total_seconds():.3f}s")
            elif response.status_code == 404:
                response.success()  # Expected for some template IDs
            else:
                response.failure(f"Template details failed: {response.status_code}")
    
    @task(15)
    def view_template_reviews(self):
        """View reviews for a template."""
        template_id = random.choice(self.template_ids)
        
        with self.client.get(f"/api/marketplace/templates/{template_id}/reviews",
                           catch_response=True, name="View Template Reviews") as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Reviews failed: {response.status_code}")
    
    @task(10)
    def browse_categories(self):
        """Browse available template categories."""
        with self.client.get("/api/marketplace/categories",
                           catch_response=True, name="Browse Categories") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Categories failed: {response.status_code}")
    
    @task(5)
    def view_marketplace_stats(self):
        """View marketplace statistics."""
        with self.client.get("/api/marketplace/stats",
                           catch_response=True, name="View Marketplace Stats") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Stats failed: {response.status_code}")


class MarketplaceContributorUser(HttpUser):
    """
    User class for template submission activities (20% of traffic).
    Simulates users creating, updating, and managing their templates.
    """
    
    weight = 20  # 20% of users will be contributors
    wait_time = between(2, 5)  # Longer wait time for content creation
    
    def on_start(self):
        """Initialize contributor session."""
        self.login_as_contributor()
        self.my_templates = []
        self.category_ids = list(range(1, 11))
    
    def login_as_contributor(self):
        """Login as a contributor user."""
        user_id = random.randint(10, 99)  # Regular users who contribute
        login_data = {
            "username": f"testuser{user_id:04d}",
            "password": "testpassword123"
        }
        
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                token_data = response.json()
                self.client.headers.update({
                    "Authorization": f"Bearer {token_data.get('access_token', '')}"
                })
            else:
                response.failure(f"Contributor login failed: {response.status_code}")
                raise RescheduleTask()
    
    @task(40)
    def browse_my_templates(self):
        """Browse user's own templates."""
        with self.client.get("/api/marketplace/my-templates",
                           catch_response=True, name="Browse My Templates") as response:
            if response.status_code == 200:
                response.success()
                # Store template IDs for updates
                data = response.json()
                if isinstance(data, dict) and "templates" in data:
                    self.my_templates = [t["id"] for t in data["templates"]]
            else:
                response.failure(f"My templates failed: {response.status_code}")
    
    @task(25)
    def create_template(self):
        """Create a new marketplace template."""
        template_names = [
            "Load Test Template", "Performance Test Stack", "Benchmark Template",
            "Test Environment", "Development Stack", "Monitoring Setup"
        ]
        
        docker_compose = """version: '3.8'
services:
  app:
    image: nginx:alpine
    ports:
      - "80:80"
    environment:
      - ENV=production
    volumes:
      - ./config:/etc/nginx/conf.d
"""
        
        template_data = {
            "name": f"{random.choice(template_names)} {random.randint(1, 1000)}",
            "description": f"Load testing template created at {time.time()}. This template is designed for performance testing scenarios.",
            "category_id": random.choice(self.category_ids),
            "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.0",
            "docker_compose_yaml": docker_compose,
            "tags": random.sample(["test", "performance", "load", "benchmark", "dev"], 3)
        }
        
        with self.client.post("/api/marketplace/templates", json=template_data,
                            catch_response=True, name="Create Template") as response:
            if response.status_code == 201:
                response.success()
                # Add to my templates list
                data = response.json()
                if isinstance(data, dict) and "id" in data:
                    self.my_templates.append(data["id"])
                if response.elapsed.total_seconds() > 0.2:
                    print(f"⚠️ Slow template creation: {response.elapsed.total_seconds():.3f}s")
            else:
                response.failure(f"Template creation failed: {response.status_code}")
    
    @task(20)
    def update_template(self):
        """Update an existing template."""
        if not self.my_templates:
            return
        
        template_id = random.choice(self.my_templates)
        update_data = {
            "description": f"Updated description at {time.time()}. Enhanced for better performance testing.",
            "tags": random.sample(["updated", "improved", "performance", "test", "optimized"], 3)
        }
        
        with self.client.put(f"/api/marketplace/templates/{template_id}", json=update_data,
                           catch_response=True, name="Update Template") as response:
            if response.status_code in [200, 404]:  # 404 if template doesn't exist
                response.success()
            else:
                response.failure(f"Template update failed: {response.status_code}")
    
    @task(15)
    def submit_review(self):
        """Submit a review for a template."""
        template_id = random.randint(1, 800)  # Approved templates
        review_data = {
            "rating": random.randint(3, 5),  # Mostly positive reviews
            "comment": f"Load test review submitted at {time.time()}. Great template for testing!"
        }
        
        with self.client.post(f"/api/marketplace/templates/{template_id}/reviews", 
                            json=review_data, catch_response=True, name="Submit Review") as response:
            if response.status_code in [201, 404, 409]:  # 409 if already reviewed
                response.success()
            else:
                response.failure(f"Review submission failed: {response.status_code}")


class MarketplaceAdminUser(HttpUser):
    """
    User class for admin operations (10% of traffic).
    Simulates admin users managing templates and marketplace operations.
    """
    
    weight = 10  # 10% of users will be admins
    wait_time = between(3, 8)  # Longer wait time for admin operations
    
    def on_start(self):
        """Initialize admin session."""
        self.login_as_admin()
        self.pending_templates = []
    
    def login_as_admin(self):
        """Login as an admin user."""
        admin_id = random.randint(0, 4)  # First 5 users are admins
        login_data = {
            "username": f"testuser{admin_id:04d}",
            "password": "testpassword123"
        }
        
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                token_data = response.json()
                self.client.headers.update({
                    "Authorization": f"Bearer {token_data.get('access_token', '')}"
                })
            else:
                response.failure(f"Admin login failed: {response.status_code}")
                raise RescheduleTask()
    
    @task(40)
    def view_pending_templates(self):
        """View templates pending approval."""
        with self.client.get("/api/marketplace/admin/pending",
                           catch_response=True, name="View Pending Templates") as response:
            if response.status_code == 200:
                response.success()
                # Store pending template IDs
                data = response.json()
                if isinstance(data, dict) and "templates" in data:
                    self.pending_templates = [t["id"] for t in data["templates"]]
                if response.elapsed.total_seconds() > 0.2:
                    print(f"⚠️ Slow admin pending view: {response.elapsed.total_seconds():.3f}s")
            else:
                response.failure(f"Pending templates failed: {response.status_code}")
    
    @task(30)
    def approve_template(self):
        """Approve a pending template."""
        if not self.pending_templates:
            return
        
        template_id = random.choice(self.pending_templates)
        approval_data = {
            "approved": True,
            "admin_notes": f"Approved during load testing at {time.time()}"
        }
        
        with self.client.post(f"/api/marketplace/admin/templates/{template_id}/approve",
                            json=approval_data, catch_response=True, name="Approve Template") as response:
            if response.status_code in [200, 404]:
                response.success()
                # Remove from pending list
                if template_id in self.pending_templates:
                    self.pending_templates.remove(template_id)
            else:
                response.failure(f"Template approval failed: {response.status_code}")
    
    @task(20)
    def view_marketplace_stats(self):
        """View detailed marketplace statistics."""
        with self.client.get("/api/marketplace/admin/stats",
                           catch_response=True, name="View Admin Stats") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin stats failed: {response.status_code}")
    
    @task(10)
    def reject_template(self):
        """Reject a pending template."""
        if not self.pending_templates:
            return
        
        template_id = random.choice(self.pending_templates)
        rejection_data = {
            "approved": False,
            "admin_notes": "Rejected during load testing - does not meet quality standards"
        }
        
        with self.client.post(f"/api/marketplace/admin/templates/{template_id}/approve",
                            json=rejection_data, catch_response=True, name="Reject Template") as response:
            if response.status_code in [200, 404]:
                response.success()
                if template_id in self.pending_templates:
                    self.pending_templates.remove(template_id)
            else:
                response.failure(f"Template rejection failed: {response.status_code}")


# Event handlers for performance monitoring
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Track request performance metrics."""
    if response_time > 200:  # Log slow requests (>200ms)
        print(f"🐌 SLOW REQUEST: {name} took {response_time:.0f}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize performance testing."""
    print("🚀 Starting Template Marketplace Load Testing")
    print("📊 User Distribution:")
    print("  - 70% Browsing Users (search, view templates)")
    print("  - 20% Contributor Users (create, update templates)")
    print("  - 10% Admin Users (approve, manage templates)")
    print("🎯 Performance Targets:")
    print("  - API Response Time: <200ms")
    print("  - Error Rate: <1%")
    print("  - Rate Limiting: Effective protection")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize performance testing."""
    print("✅ Template Marketplace Load Testing Completed")
    print("📈 Check Locust web UI for detailed performance metrics")
