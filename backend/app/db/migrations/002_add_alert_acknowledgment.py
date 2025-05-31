"""
Migration: Add alert acknowledgment fields

This migration adds acknowledgment fields to the metrics_alerts table:
- is_acknowledged: Boolean flag for acknowledgment status
- acknowledged_at: Timestamp when alert was acknowledged
- acknowledged_by: User ID who acknowledged the alert

Created: 2024-01-XX
"""

from sqlalchemy import text

from app.db.database import engine


def upgrade():
    """Apply the migration."""
    print("🔄 Running migration: Add alert acknowledgment fields...")

    with engine.connect() as connection:
        # Add acknowledgment fields to metrics_alerts table
        try:
            # Add is_acknowledged column
            connection.execute(
                text(
                    """
                ALTER TABLE metrics_alerts 
                ADD COLUMN is_acknowledged BOOLEAN NOT NULL DEFAULT 0
            """
                )
            )
            print("✅ Added is_acknowledged column")

            # Add acknowledged_at column
            connection.execute(
                text(
                    """
                ALTER TABLE metrics_alerts 
                ADD COLUMN acknowledged_at DATETIME
            """
                )
            )
            print("✅ Added acknowledged_at column")

            # Add acknowledged_by column with foreign key
            connection.execute(
                text(
                    """
                ALTER TABLE metrics_alerts 
                ADD COLUMN acknowledged_by INTEGER
            """
                )
            )
            print("✅ Added acknowledged_by column")

            # Add foreign key constraint for acknowledged_by
            # Note: SQLite doesn't support adding foreign key constraints to existing tables
            # This would need to be handled differently in production with proper migration tools

            connection.commit()
            print("✅ Migration completed successfully")

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            connection.rollback()
            raise


def downgrade():
    """Reverse the migration."""
    print("🔄 Reversing migration: Remove alert acknowledgment fields...")

    with engine.connect() as connection:
        try:
            # Remove acknowledgment fields
            # Note: SQLite doesn't support DROP COLUMN, so we'd need to recreate the table
            # For now, we'll just mark this as not supported
            print(
                "⚠️ Downgrade not supported for SQLite - would require table recreation"
            )

        except Exception as e:
            print(f"❌ Downgrade failed: {e}")
            raise


if __name__ == "__main__":
    upgrade()
