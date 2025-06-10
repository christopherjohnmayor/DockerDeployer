#!/usr/bin/env python3
"""
Script to create a test user for DockerDeployer testing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.auth.jwt import get_password_hash
from backend.app.db.database import SessionLocal
from backend.app.db.models import User, UserRole


def create_test_user():
    """Create a test user for testing purposes."""
    db = SessionLocal()

    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.username == "testuser").first()

        if test_user:
            print("Test user already exists. Updating password...")
            # Update password and ensure user role
            test_user.hashed_password = get_password_hash("testpassword123")
            test_user.role = UserRole.ADMIN  # Make admin for testing
            test_user.is_active = True
            test_user.is_email_verified = True
            print(f"Updated test user: {test_user.username} ({test_user.email})")
        else:
            print("Creating new test user...")
            # Create new test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpassword123"),
                full_name="Test User",
                role=UserRole.ADMIN,  # Make admin for testing
                is_active=True,
                is_email_verified=True,
            )
            db.add(test_user)
            print("Created new test user: testuser (test@example.com)")

        db.commit()
        print("✅ Test user setup completed successfully!")
        print("Credentials:")
        print("  Username: testuser")
        print("  Password: testpassword123")
        print("  Email: test@example.com")
        print("  Role: admin")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
