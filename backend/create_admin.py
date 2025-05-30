#!/usr/bin/env python3
"""
Script to create or update admin user for DockerDeployer.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.db.database import SessionLocal
from app.db.models import User, UserRole
from app.auth.jwt import get_password_hash

def create_admin_user():
    """Create or update the admin user."""
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if admin_user:
            print("Admin user already exists. Updating password...")
            # Update password and ensure admin role
            admin_user.hashed_password = get_password_hash("AdminPassword123")
            admin_user.role = UserRole.ADMIN
            admin_user.is_active = True
            admin_user.is_email_verified = True
            print(f"Updated admin user: {admin_user.username} ({admin_user.email})")
        else:
            print("Creating new admin user...")
            # Create new admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPassword123"),
                full_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_email_verified=True
            )
            db.add(admin_user)
            print("Created new admin user: admin (admin@example.com)")
        
        db.commit()
        print("✅ Admin user setup completed successfully!")
        print("Credentials:")
        print("  Username: admin")
        print("  Password: AdminPassword123")
        print("  Email: admin@example.com")
        
        # List all users
        print("\nAll users in database:")
        users = db.query(User).all()
        for user in users:
            print(f"  - {user.username} ({user.email}) - Role: {user.role}, Active: {user.is_active}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
