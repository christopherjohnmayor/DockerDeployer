"""
Database migrations module for DockerDeployer.

This module provides utilities for managing database schema changes
through versioned migration scripts.
"""

import importlib.util
import os
from pathlib import Path
from typing import List


def get_migration_files() -> List[str]:
    """
    Get list of migration files in order.

    Returns:
        List of migration file names sorted by version
    """
    migrations_dir = Path(__file__).parent
    migration_files = []

    for file in migrations_dir.glob("*.py"):
        if file.name != "__init__.py" and file.name.endswith(".py"):
            migration_files.append(file.name)

    # Sort by version number (assuming format: XXX_description.py)
    migration_files.sort()
    return migration_files


def run_migration(migration_file: str, action: str = "upgrade"):
    """
    Run a specific migration file.

    Args:
        migration_file: Name of the migration file
        action: Either 'upgrade' or 'downgrade'
    """
    migrations_dir = Path(__file__).parent
    migration_path = migrations_dir / migration_file

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")

    # Load the migration module
    spec = importlib.util.spec_from_file_location("migration", migration_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)

    # Execute the migration
    if action == "upgrade":
        if hasattr(migration_module, "upgrade"):
            migration_module.upgrade()
        else:
            raise AttributeError(f"Migration {migration_file} has no upgrade function")
    elif action == "downgrade":
        if hasattr(migration_module, "downgrade"):
            migration_module.downgrade()
        else:
            raise AttributeError(
                f"Migration {migration_file} has no downgrade function"
            )
    else:
        raise ValueError(f"Invalid action: {action}. Must be 'upgrade' or 'downgrade'")


def run_all_migrations():
    """Run all pending migrations."""
    migration_files = get_migration_files()

    print(f"Found {len(migration_files)} migration(s)")

    for migration_file in migration_files:
        print(f"Running migration: {migration_file}")
        try:
            run_migration(migration_file, "upgrade")
        except Exception as e:
            print(f"❌ Error running migration {migration_file}: {e}")
            raise

    print("✅ All migrations completed successfully")


if __name__ == "__main__":
    run_all_migrations()
