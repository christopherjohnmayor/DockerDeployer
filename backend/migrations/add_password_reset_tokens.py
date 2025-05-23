"""
Database migration to add password reset tokens table.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.db.database import get_database_url

def run_migration():
    """Run the migration to add password reset tokens table."""
    engine = create_engine(get_database_url())

    with engine.connect() as connection:
        # Create password_reset_tokens table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
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
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token
            ON password_reset_tokens (token)
        """))

        # Create index on user_id for faster lookups
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id
            ON password_reset_tokens (user_id)
        """))

        connection.commit()
        print("Migration completed: Added password_reset_tokens table")

if __name__ == "__main__":
    run_migration()
