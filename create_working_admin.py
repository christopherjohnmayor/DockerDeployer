#!/usr/bin/env python3
"""
Script to create a working admin user for DockerDeployer testing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.auth.jwt import get_password_hash
from backend.app.db.database import SessionLocal
from backend.app.db.models import User, UserRole


def create_working_admin():
    """Create a working admin user for testing purposes."""
    db = SessionLocal()

    try:
        # Delete existing testadmin if exists
        existing_user = db.query(User).filter(User.username == "testadmin").first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
            print("Deleted existing testadmin user")

        # Create new admin user with simple credentials
        admin_user = User(
            username="testadmin",
            email="testadmin@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Working admin user created successfully!")
        print("Credentials:")
        print("  Username: testadmin")
        print("  Password: password123")
        print("  Email: testadmin@test.com")
        print("  Role: admin")

        # Verify the user can be authenticated
        from backend.app.auth.jwt import verify_password
        verification_result = verify_password("password123", admin_user.hashed_password)
        print(f"Password verification test: {'✅ PASSED' if verification_result else '❌ FAILED'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_working_admin()
