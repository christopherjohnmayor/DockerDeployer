"""
Database migration to add email verification support.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.db.database import get_database_url

def run_migration():
    """Run the migration to add email verification support."""
    engine = create_engine(get_database_url())

    with engine.connect() as connection:
        # Add is_email_verified column to users table
        try:
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE
            """))
            print("Added is_email_verified column to users table")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("Column is_email_verified already exists in users table")
            else:
                print(f"Error adding is_email_verified column: {e}")

        # Create email_verification_tokens table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token VARCHAR UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """))

        # Create index on token for faster lookups
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token
            ON email_verification_tokens (token)
        """))

        # Create index on user_id for faster lookups
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id
            ON email_verification_tokens (user_id)
        """))

        # Create index on expires_at for cleanup
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires_at
            ON email_verification_tokens (expires_at)
        """))

        connection.commit()
        print("Migration completed: Added email verification support")

if __name__ == "__main__":
    run_migration()
