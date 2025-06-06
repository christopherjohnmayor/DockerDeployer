"""
Migration 003: Add container metrics history table for enhanced visualization

This migration adds:
- container_metrics_history: For aggregated time-series data storage
- container_health_scores: For health tracking
- container_predictions: For predictive analytics
- Indexes for efficient time-range queries
- Data retention policies support

Created: 2024-01-XX
"""

from sqlalchemy import text

from app.db.database import engine


def upgrade():
    """Apply the migration."""

    # Create container_metrics_history table for aggregated data
    container_metrics_history_sql = """
    CREATE TABLE IF NOT EXISTS container_metrics_history (
        id INTEGER PRIMARY KEY,
        container_id VARCHAR(255) NOT NULL,
        container_name VARCHAR(255),
        timestamp DATETIME NOT NULL,
        interval_minutes INTEGER NOT NULL DEFAULT 60,
        
        -- Aggregated CPU metrics
        cpu_percent_avg FLOAT,
        cpu_percent_min FLOAT,
        cpu_percent_max FLOAT,
        
        -- Aggregated Memory metrics
        memory_percent_avg FLOAT,
        memory_percent_min FLOAT,
        memory_percent_max FLOAT,
        memory_usage_avg BIGINT,
        memory_usage_min BIGINT,
        memory_usage_max BIGINT,
        
        -- Aggregated Network metrics
        network_rx_bytes_avg BIGINT,
        network_rx_bytes_total BIGINT,
        network_tx_bytes_avg BIGINT,
        network_tx_bytes_total BIGINT,
        
        -- Aggregated Disk I/O metrics
        block_read_bytes_avg BIGINT,
        block_read_bytes_total BIGINT,
        block_write_bytes_avg BIGINT,
        block_write_bytes_total BIGINT,
        
        -- Metadata
        data_points_count INTEGER NOT NULL DEFAULT 1,
        health_score FLOAT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Create indexes for container_metrics_history
    container_metrics_history_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_history_container_id ON container_metrics_history (container_id);",
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_history_timestamp ON container_metrics_history (timestamp);",
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_history_interval ON container_metrics_history (interval_minutes);",
        "CREATE INDEX IF NOT EXISTS ix_container_metrics_history_container_timestamp ON container_metrics_history (container_id, timestamp);",
    ]

    # Create container_health_scores table for health tracking
    container_health_scores_sql = """
    CREATE TABLE IF NOT EXISTS container_health_scores (
        id INTEGER PRIMARY KEY,
        container_id VARCHAR(255) NOT NULL,
        container_name VARCHAR(255),
        timestamp DATETIME NOT NULL,
        
        -- Overall health score (0-100)
        overall_health_score FLOAT NOT NULL,
        health_status VARCHAR(20) NOT NULL,
        
        -- Component scores
        cpu_health_score FLOAT,
        memory_health_score FLOAT,
        network_health_score FLOAT,
        disk_health_score FLOAT,
        
        -- Analysis metadata
        analysis_period_hours INTEGER NOT NULL DEFAULT 1,
        data_points_analyzed INTEGER NOT NULL DEFAULT 0,
        
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Create indexes for container_health_scores
    container_health_scores_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_container_health_scores_container_id ON container_health_scores (container_id);",
        "CREATE INDEX IF NOT EXISTS ix_container_health_scores_timestamp ON container_health_scores (timestamp);",
        "CREATE INDEX IF NOT EXISTS ix_container_health_scores_health_status ON container_health_scores (health_status);",
        "CREATE INDEX IF NOT EXISTS ix_container_health_scores_container_timestamp ON container_health_scores (container_id, timestamp);",
    ]

    # Create container_predictions table for storing prediction results
    container_predictions_sql = """
    CREATE TABLE IF NOT EXISTS container_predictions (
        id INTEGER PRIMARY KEY,
        container_id VARCHAR(255) NOT NULL,
        container_name VARCHAR(255),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        -- Prediction metadata
        prediction_timestamp DATETIME NOT NULL,
        prediction_hours INTEGER NOT NULL DEFAULT 6,
        analysis_period_hours INTEGER NOT NULL DEFAULT 24,
        
        -- CPU predictions
        cpu_predicted_value FLOAT,
        cpu_confidence FLOAT,
        cpu_trend VARCHAR(20),
        
        -- Memory predictions
        memory_predicted_value FLOAT,
        memory_confidence FLOAT,
        memory_trend VARCHAR(20),
        
        -- Prediction accuracy (filled when actual data becomes available)
        cpu_actual_value FLOAT,
        memory_actual_value FLOAT,
        cpu_accuracy_score FLOAT,
        memory_accuracy_score FLOAT,
        
        -- Status
        is_validated BOOLEAN NOT NULL DEFAULT 0
    );
    """

    # Create indexes for container_predictions
    container_predictions_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_container_predictions_container_id ON container_predictions (container_id);",
        "CREATE INDEX IF NOT EXISTS ix_container_predictions_prediction_timestamp ON container_predictions (prediction_timestamp);",
        "CREATE INDEX IF NOT EXISTS ix_container_predictions_created_at ON container_predictions (created_at);",
        "CREATE INDEX IF NOT EXISTS ix_container_predictions_container_prediction ON container_predictions (container_id, prediction_timestamp);",
    ]

    # Execute all SQL statements
    with engine.connect() as connection:
        # Create tables
        connection.execute(text(container_metrics_history_sql))
        connection.execute(text(container_health_scores_sql))
        connection.execute(text(container_predictions_sql))

        # Create indexes
        for index_sql in (
            container_metrics_history_indexes +
            container_health_scores_indexes +
            container_predictions_indexes
        ):
            connection.execute(text(index_sql))

        connection.commit()

    print("✅ Migration 002_add_metrics_history_table applied successfully")


def downgrade():
    """Rollback the migration."""

    downgrade_sql = [
        "DROP TABLE IF EXISTS container_predictions;",
        "DROP TABLE IF EXISTS container_health_scores;",
        "DROP TABLE IF EXISTS container_metrics_history;",
    ]

    with engine.connect() as connection:
        for sql in downgrade_sql:
            connection.execute(text(sql))
        connection.commit()

    print("✅ Migration 002_add_metrics_history_table rolled back successfully")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
