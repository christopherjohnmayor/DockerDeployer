"""
Migration: Add container metrics and alerts tables

This migration adds the following tables:
- container_metrics: For storing historical container performance data
- metrics_alerts: For threshold-based alerting configuration

Created: 2024-01-XX
"""

from sqlalchemy import text
from app.db.database import engine


def upgrade():
    """Apply the migration."""
    
    # Create container_metrics table
    container_metrics_sql = """
    CREATE TABLE IF NOT EXISTS container_metrics (
        id INTEGER PRIMARY KEY,
        container_id VARCHAR(255) NOT NULL,
        container_name VARCHAR(255),
        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        cpu_percent FLOAT,
        memory_usage BIGINT,
        memory_limit BIGINT,
        memory_percent FLOAT,
        network_rx_bytes BIGINT,
        network_tx_bytes BIGINT,
        block_read_bytes BIGINT,
        block_write_bytes BIGINT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Create indexes for container_metrics
    container_metrics_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_container_id ON container_metrics (container_id);",
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_container_name ON container_metrics (container_name);",
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_timestamp ON container_metrics (timestamp);",
    ]
    
    # Create metrics_alerts table
    metrics_alerts_sql = """
    CREATE TABLE IF NOT EXISTS metrics_alerts (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        container_id VARCHAR(255) NOT NULL,
        container_name VARCHAR(255),
        metric_type VARCHAR(50) NOT NULL,
        threshold_value FLOAT NOT NULL,
        comparison_operator VARCHAR(10) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        is_triggered BOOLEAN NOT NULL DEFAULT 0,
        last_triggered_at DATETIME,
        trigger_count INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (id)
    );
    """
    
    # Create indexes for metrics_alerts
    metrics_alerts_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_metrics_alerts_container_id ON metrics_alerts (container_id);",
        "CREATE INDEX IF NOT EXISTS ix_metrics_alerts_created_by ON metrics_alerts (created_by);",
    ]
    
    # Execute all SQL statements
    with engine.connect() as connection:
        # Create tables
        connection.execute(text(container_metrics_sql))
        connection.execute(text(metrics_alerts_sql))
        
        # Create indexes
        for index_sql in container_metrics_indexes + metrics_alerts_indexes:
            connection.execute(text(index_sql))
        
        connection.commit()
    
    print("✅ Migration 001_add_metrics_tables applied successfully")


def downgrade():
    """Rollback the migration."""
    
    downgrade_sql = [
        "DROP TABLE IF EXISTS metrics_alerts;",
        "DROP TABLE IF EXISTS container_metrics;",
    ]
    
    with engine.connect() as connection:
        for sql in downgrade_sql:
            connection.execute(text(sql))
        connection.commit()
    
    print("✅ Migration 001_add_metrics_tables rolled back successfully")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
