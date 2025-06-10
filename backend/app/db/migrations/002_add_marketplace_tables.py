"""
Migration: Add marketplace template tables

This migration adds the following tables for the Template Marketplace feature:
- template_categories: For organizing templates by category
- marketplace_templates: For storing community-contributed templates
- template_reviews: For user ratings and comments
- template_versions: For version history tracking

Created: 2024-01-XX
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from sqlalchemy import text

# Import from the backend directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.db.database import engine


def upgrade():
    """Apply the migration."""

    # Create template_categories table
    template_categories_sql = """
    CREATE TABLE IF NOT EXISTS template_categories (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        icon VARCHAR(255),
        sort_order INTEGER NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Create marketplace_templates table
    marketplace_templates_sql = """
    CREATE TABLE IF NOT EXISTS marketplace_templates (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
        docker_compose_yaml TEXT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        downloads INTEGER NOT NULL DEFAULT 0,
        rating_avg FLOAT NOT NULL DEFAULT 0.0,
        rating_count INTEGER NOT NULL DEFAULT 0,
        tags JSON,
        approved_by INTEGER,
        approved_at DATETIME,
        rejection_reason TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users (id),
        FOREIGN KEY (category_id) REFERENCES template_categories (id),
        FOREIGN KEY (approved_by) REFERENCES users (id)
    );
    """

    # Create template_reviews table
    template_reviews_sql = """
    CREATE TABLE IF NOT EXISTS template_reviews (
        id INTEGER PRIMARY KEY,
        template_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE (template_id, user_id)
    );
    """

    # Create template_versions table
    template_versions_sql = """
    CREATE TABLE IF NOT EXISTS template_versions (
        id INTEGER PRIMARY KEY,
        template_id INTEGER NOT NULL,
        version_number VARCHAR(50) NOT NULL,
        docker_compose_yaml TEXT NOT NULL,
        changelog TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE
    );
    """

    # Create indexes for template_categories
    template_categories_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_template_categories_name ON template_categories (name);",
        "CREATE INDEX IF NOT EXISTS ix_template_categories_sort_order ON template_categories (sort_order);",
        "CREATE INDEX IF NOT EXISTS ix_template_categories_is_active ON template_categories (is_active);",
    ]

    # Create indexes for marketplace_templates
    marketplace_templates_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_name ON marketplace_templates (name);",
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_author_id ON marketplace_templates (author_id);",
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_category_id ON marketplace_templates (category_id);",
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_status ON marketplace_templates (status);",
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_rating_avg ON marketplace_templates (rating_avg);",
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_downloads ON marketplace_templates (downloads);",
        "CREATE INDEX IF NOT EXISTS ix_marketplace_templates_created_at ON marketplace_templates (created_at);",
    ]

    # Create indexes for template_reviews
    template_reviews_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_template_reviews_template_id ON template_reviews (template_id);",
        "CREATE INDEX IF NOT EXISTS ix_template_reviews_user_id ON template_reviews (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_template_reviews_rating ON template_reviews (rating);",
    ]

    # Create indexes for template_versions
    template_versions_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_template_versions_template_id ON template_versions (template_id);",
        "CREATE INDEX IF NOT EXISTS ix_template_versions_version_number ON template_versions (version_number);",
    ]

    # Execute all SQL statements
    with engine.connect() as connection:
        # Create tables
        connection.execute(text(template_categories_sql))
        connection.execute(text(marketplace_templates_sql))
        connection.execute(text(template_reviews_sql))
        connection.execute(text(template_versions_sql))

        # Create indexes
        for index_sql in (
            template_categories_indexes
            + marketplace_templates_indexes
            + template_reviews_indexes
            + template_versions_indexes
        ):
            connection.execute(text(index_sql))

        connection.commit()

    print("✅ Migration 002_add_marketplace_tables applied successfully")


def downgrade():
    """Rollback the migration."""

    downgrade_sql = [
        "DROP TABLE IF EXISTS template_versions;",
        "DROP TABLE IF EXISTS template_reviews;",
        "DROP TABLE IF EXISTS marketplace_templates;",
        "DROP TABLE IF EXISTS template_categories;",
    ]

    with engine.connect() as connection:
        for sql in downgrade_sql:
            connection.execute(text(sql))
        connection.commit()

    print("✅ Migration 002_add_marketplace_tables rolled back successfully")


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
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
        insert_default_categories()
