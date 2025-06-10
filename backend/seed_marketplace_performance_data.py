#!/usr/bin/env python3
"""
Database seeding script for Template Marketplace performance testing.

This script creates production-scale test data:
- 1000+ marketplace templates
- 5000+ template reviews
- 100+ test users
- Realistic data distribution for performance testing

Usage:
    python seed_marketplace_performance_data.py
"""

import asyncio
import random
import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import get_db, engine
from app.db.models import (
    User,
    MarketplaceTemplate,
    TemplateCategory,
    TemplateReview,
    TemplateVersion,
    TemplateStatus,
    UserRole
)
from app.auth.jwt import get_password_hash


class MarketplaceDataSeeder:
    """Seeder class for marketplace performance test data."""
    
    def __init__(self):
        """Initialize the seeder."""
        self.db = next(get_db())
        self.users = []
        self.categories = []
        self.templates = []
        
        # Sample Docker Compose templates for variety
        self.docker_compose_templates = [
            """version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
""",
            """version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
""",
            """version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
volumes:
  redis_data:
""",
            """version: '3.8'
services:
  mongodb:
    image: mongo:4.4
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongo_data:/data/db
volumes:
  mongo_data:
""",
            """version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: myapp
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
volumes:
  mysql_data:
"""
        ]
        
        # Sample template names and descriptions
        self.template_names = [
            "NGINX Load Balancer", "PostgreSQL Database", "Redis Cache", "MongoDB NoSQL",
            "MySQL Database", "Elasticsearch Search", "RabbitMQ Message Queue", "Apache Kafka",
            "Node.js API Server", "Python Flask App", "Django Web App", "React Frontend",
            "Vue.js SPA", "Angular Application", "WordPress CMS", "Drupal CMS",
            "Jenkins CI/CD", "GitLab Runner", "Prometheus Monitoring", "Grafana Dashboard",
            "ELK Stack", "LAMP Stack", "MEAN Stack", "LEMP Stack",
            "Microservice Template", "API Gateway", "Service Mesh", "Container Registry"
        ]
        
        self.descriptions = [
            "High-performance web server and reverse proxy solution",
            "Robust relational database for enterprise applications",
            "In-memory data structure store for caching and sessions",
            "Document-oriented NoSQL database for modern applications",
            "Popular open-source relational database management system",
            "Distributed search and analytics engine",
            "Reliable message broker for distributed systems",
            "Distributed streaming platform for real-time data",
            "Scalable server-side JavaScript runtime environment",
            "Lightweight Python web framework for rapid development",
            "High-level Python web framework for complex applications",
            "Modern JavaScript library for building user interfaces",
            "Progressive JavaScript framework for building UIs",
            "Platform for building mobile and desktop web applications",
            "Popular content management system for websites",
            "Open-source content management framework",
            "Automation server for continuous integration and deployment",
            "CI/CD runner for GitLab projects",
            "Systems monitoring and alerting toolkit",
            "Analytics and interactive visualization platform",
            "Centralized logging solution with Elasticsearch, Logstash, and Kibana",
            "Complete web development stack with Linux, Apache, MySQL, PHP",
            "Full-stack JavaScript solution with MongoDB, Express, Angular, Node.js",
            "High-performance web stack with Linux, Nginx, MySQL, PHP",
            "Template for building scalable microservices architecture",
            "Centralized entry point for managing API requests",
            "Infrastructure layer for service-to-service communication",
            "Private Docker registry for container image management"
        ]
        
        self.tags_pool = [
            "web-server", "database", "cache", "nosql", "sql", "search", "messaging",
            "streaming", "javascript", "python", "php", "cms", "ci-cd", "monitoring",
            "logging", "microservices", "api", "frontend", "backend", "full-stack",
            "development", "production", "scalable", "high-performance", "enterprise",
            "open-source", "container", "docker", "kubernetes", "cloud-native"
        ]

    def create_test_users(self, count: int = 100) -> List[User]:
        """Create test users for performance testing."""
        print(f"Creating {count} test users...")
        
        users = []
        for i in range(count):
            user = User(
                username=f"testuser{i:04d}",
                email=f"testuser{i:04d}@example.com",
                hashed_password=get_password_hash("testpassword123"),
                is_active=True,
                role=UserRole.ADMIN if i < 5 else UserRole.USER,  # First 5 users are admins
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            users.append(user)
            self.db.add(user)
        
        self.db.commit()
        
        # Refresh to get IDs
        for user in users:
            self.db.refresh(user)
        
        self.users = users
        print(f"✅ Created {len(users)} test users")
        return users

    def create_marketplace_templates(self, count: int = 1000) -> List[MarketplaceTemplate]:
        """Create marketplace templates for performance testing."""
        print(f"Creating {count} marketplace templates...")
        
        # Get existing categories
        categories = self.db.query(TemplateCategory).all()
        if not categories:
            print("❌ No categories found. Please run category seeding first.")
            return []
        
        templates = []
        for i in range(count):
            # Select random template data
            name_idx = i % len(self.template_names)
            desc_idx = i % len(self.descriptions)
            compose_idx = i % len(self.docker_compose_templates)
            
            # Generate unique name
            template_name = f"{self.template_names[name_idx]} v{random.randint(1, 5)}.{random.randint(0, 9)}"
            if i >= len(self.template_names):
                template_name += f" #{i // len(self.template_names) + 1}"
            
            # Random tags (2-5 tags per template)
            num_tags = random.randint(2, 5)
            tags = random.sample(self.tags_pool, num_tags)
            
            # Random status distribution: 80% approved, 15% pending, 5% rejected
            status_rand = random.random()
            if status_rand < 0.8:
                status = TemplateStatus.APPROVED
                approved_by = random.choice(self.users[:5]).id  # Admin user
                approved_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            elif status_rand < 0.95:
                status = TemplateStatus.PENDING
                approved_by = None
                approved_at = None
            else:
                status = TemplateStatus.REJECTED
                approved_by = random.choice(self.users[:5]).id
                approved_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            
            template = MarketplaceTemplate(
                name=template_name,
                description=self.descriptions[desc_idx] + f" (Performance test template #{i})",
                author_id=random.choice(self.users).id,
                category_id=random.choice(categories).id,
                version=f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                docker_compose_yaml=self.docker_compose_templates[compose_idx],
                tags=tags,
                status=status,
                downloads=random.randint(0, 5000) if status == TemplateStatus.APPROVED else 0,
                rating_avg=round(random.uniform(1.0, 5.0), 2) if status == TemplateStatus.APPROVED else 0.0,
                rating_count=random.randint(0, 500) if status == TemplateStatus.APPROVED else 0,
                approved_by=approved_by,
                approved_at=approved_at,
                rejection_reason="Does not meet quality standards" if status == TemplateStatus.REJECTED else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 180)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            
            templates.append(template)
            self.db.add(template)
            
            # Commit in batches to avoid memory issues
            if (i + 1) % 100 == 0:
                self.db.commit()
                print(f"  Committed batch {(i + 1) // 100}")
        
        self.db.commit()
        
        # Refresh to get IDs
        for template in templates:
            self.db.refresh(template)
        
        self.templates = templates
        print(f"✅ Created {len(templates)} marketplace templates")
        return templates

    def create_template_reviews(self, count: int = 5000) -> List[TemplateReview]:
        """Create template reviews for performance testing."""
        print(f"Creating {count} template reviews...")

        # Only create reviews for approved templates
        approved_templates = [t for t in self.templates if t.status == TemplateStatus.APPROVED]
        if not approved_templates:
            print("❌ No approved templates found for reviews")
            return []

        reviews = []
        review_comments = [
            "Excellent template, works perfectly!",
            "Great starting point for my project.",
            "Easy to use and well documented.",
            "Could use some improvements but overall good.",
            "Perfect for development environments.",
            "Production-ready and reliable.",
            "Simple setup, exactly what I needed.",
            "Well-structured and follows best practices.",
            "Good performance and stability.",
            "Highly recommended for beginners.",
            "Professional quality template.",
            "Saves a lot of time in setup.",
            "Clean and efficient implementation.",
            "Works as advertised, no issues.",
            "Great for learning Docker concepts."
        ]

        # Track created combinations to avoid duplicates
        created_combinations = set()
        attempts = 0
        max_attempts = count * 3  # Allow more attempts to reach target count

        while len(reviews) < count and attempts < max_attempts:
            template = random.choice(approved_templates)
            user = random.choice(self.users)
            combination = (template.id, user.id)

            # Skip if combination already exists
            if combination in created_combinations:
                attempts += 1
                continue

            created_combinations.add(combination)

            review = TemplateReview(
                template_id=template.id,
                user_id=user.id,
                rating=random.randint(1, 5),
                comment=random.choice(review_comments) if random.random() > 0.2 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )

            reviews.append(review)
            self.db.add(review)
            attempts += 1

            # Commit in batches
            if len(reviews) % 500 == 0:
                self.db.commit()
                print(f"  Committed batch {len(reviews) // 500}")

        self.db.commit()
        print(f"✅ Created {len(reviews)} template reviews (attempted {attempts} combinations)")
        return reviews

    def update_template_ratings(self):
        """Update template rating averages based on reviews."""
        print("Updating template rating averages...")
        
        for template in self.templates:
            reviews = self.db.query(TemplateReview).filter(
                TemplateReview.template_id == template.id
            ).all()
            
            if reviews:
                total_rating = sum(review.rating for review in reviews)
                template.rating_avg = round(total_rating / len(reviews), 2)
                template.rating_count = len(reviews)
        
        self.db.commit()
        print("✅ Updated template rating averages")

    def create_template_versions(self):
        """Create version history for templates."""
        print("Creating template version history...")
        
        versions = []
        for template in self.templates:
            # Create 1-3 versions per template
            num_versions = random.randint(1, 3)
            
            for v in range(num_versions):
                version = TemplateVersion(
                    template_id=template.id,
                    version_number=f"{template.version}.{v}",
                    docker_compose_yaml=template.docker_compose_yaml,
                    changelog=f"Version {template.version}.{v} - Performance improvements and bug fixes",
                    created_at=template.created_at + timedelta(days=v * 30)
                )
                versions.append(version)
                self.db.add(version)
        
        self.db.commit()
        print(f"✅ Created {len(versions)} template versions")

    def clear_test_data(self):
        """Clear existing test data."""
        print("🧹 Clearing existing test data...")

        try:
            # Delete in reverse order of dependencies
            self.db.query(TemplateVersion).delete()
            self.db.query(TemplateReview).delete()
            self.db.query(MarketplaceTemplate).delete()

            # Delete test users (keep admin and existing real users)
            test_users = self.db.query(User).filter(User.username.like("testuser%")).all()
            for user in test_users:
                self.db.delete(user)

            self.db.commit()
            print(f"✅ Cleared test data")

        except Exception as e:
            print(f"⚠️ Warning during cleanup: {e}")
            self.db.rollback()

    def seed_all_data(self):
        """Seed all performance test data."""
        print("🚀 Starting marketplace performance data seeding...")

        try:
            # Clear existing test data first
            self.clear_test_data()

            # Create test users
            self.create_test_users(100)

            # Create marketplace templates
            self.create_marketplace_templates(1000)

            # Create template reviews
            self.create_template_reviews(5000)

            # Update template ratings
            self.update_template_ratings()

            # Create template versions
            self.create_template_versions()

            print("\n✅ Performance data seeding completed successfully!")
            print(f"📊 Summary:")
            print(f"  - Users: {len(self.users)}")
            print(f"  - Templates: {len(self.templates)}")
            print(f"  - Reviews: {self.db.query(TemplateReview).count()}")
            print(f"  - Versions: {self.db.query(TemplateVersion).count()}")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            self.db.rollback()
            raise
        finally:
            self.db.close()


def main():
    """Main function to run the seeding script."""
    seeder = MarketplaceDataSeeder()
    seeder.seed_all_data()


if __name__ == "__main__":
    main()
