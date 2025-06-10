#!/usr/bin/env python3
"""
Debug authentication issues by testing password verification directly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.auth.jwt import get_password_hash, verify_password
from backend.app.db.database import SessionLocal
from backend.app.db.models import User, UserRole

def debug_authentication():
    """Debug authentication by testing password verification."""
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        print("=== All Users in Database ===")
        for user in users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print(f"Email Verified: {user.is_email_verified}")
            print(f"Hashed Password: {user.hashed_password[:50]}...")
            print("---")
        
        # Test password verification for admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("\n=== Testing Admin Password Verification ===")
            test_passwords = ["admin123", "AdminPassword123", "password123"]
            
            for password in test_passwords:
                try:
                    result = verify_password(password, admin_user.hashed_password)
                    print(f"Password '{password}': {'✅ VALID' if result else '❌ INVALID'}")
                except Exception as e:
                    print(f"Password '{password}': ❌ ERROR - {e}")
        
        # Create a simple test user with known password
        print("\n=== Creating Simple Test User ===")
        test_user = db.query(User).filter(User.username == "simpletest").first()
        if test_user:
            db.delete(test_user)
            db.commit()
        
        # Create new simple test user
        simple_password = "test123"
        hashed_password = get_password_hash(simple_password)
        
        new_user = User(
            username="simpletest",
            email="simpletest@test.com",
            hashed_password=hashed_password,
            full_name="Simple Test User",
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Test the new user's password
        verification_result = verify_password(simple_password, new_user.hashed_password)
        print(f"Simple test user created: simpletest / {simple_password}")
        print(f"Password verification: {'✅ PASSED' if verification_result else '❌ FAILED'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    debug_authentication()
