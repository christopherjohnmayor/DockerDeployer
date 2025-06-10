#!/usr/bin/env python3
"""
Script to insert default template categories.
"""

import sys
import os
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.database import engine

def insert_default_categories():
    """Insert default template categories."""
    
    default_categories = [
        {"name": "Web Servers", "description": "Web server stacks like NGINX, Apache, and reverse proxies", "icon": "web", "sort_order": 1},
        {"name": "Databases", "description": "Database systems including MySQL, PostgreSQL, MongoDB, Redis", "icon": "database", "sort_order": 2},
        {"name": "Development Tools", "description": "Development environments, IDEs, and build tools", "icon": "code", "sort_order": 3},
        {"name": "Monitoring", "description": "Monitoring and observability tools like Grafana, Prometheus", "icon": "chart", "sort_order": 4},
        {"name": "CI/CD", "description": "Continuous integration and deployment pipelines", "icon": "pipeline", "sort_order": 5},
        {"name": "E-commerce", "description": "E-commerce platforms and shopping cart solutions", "icon": "shopping", "sort_order": 6},
        {"name": "CMS", "description": "Content management systems like WordPress, Drupal", "icon": "edit", "sort_order": 7},
        {"name": "Analytics", "description": "Analytics and data processing tools", "icon": "analytics", "sort_order": 8},
        {"name": "Security", "description": "Security tools and services", "icon": "shield", "sort_order": 9},
        {"name": "Networking", "description": "Network tools and services", "icon": "network", "sort_order": 10},
    ]

    insert_sql = """
    INSERT OR IGNORE INTO template_categories (name, description, icon, sort_order)
    VALUES (:name, :description, :icon, :sort_order);
    """

    with engine.connect() as connection:
        for category in default_categories:
            connection.execute(text(insert_sql), category)
        connection.commit()

    print("✅ Default template categories inserted successfully")

if __name__ == "__main__":
    insert_default_categories()
