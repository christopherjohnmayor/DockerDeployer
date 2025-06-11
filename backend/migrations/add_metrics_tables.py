#!/usr/bin/env python3
"""
Database migration to ensure metrics tables are properly configured.

This migration ensures that the following tables exist and are properly configured:
- container_metrics_history
- container_health_scores  
- container_predictions

Run this script to update the database schema for Container Metrics Visualization.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import get_database_url
from app.db.models import Base, ContainerMetricsHistory, ContainerHealthScore, ContainerPrediction

def run_migration():
    """Run the metrics tables migration."""
    print("Starting metrics tables migration...")
    
    try:
        # Get database URL
        database_url = get_database_url()
        print(f"Connecting to database: {database_url}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("Creating/updating metrics tables...")
        
        # Create all tables (this will only create missing tables)
        Base.metadata.create_all(bind=engine)
        
        # Verify tables exist
        inspector = engine.dialect.get_table_names(engine.connect())
        
        required_tables = [
            'container_metrics_history',
            'container_health_scores', 
            'container_predictions'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table not in inspector:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"WARNING: Missing tables: {missing_tables}")
            return False
        
        print("✅ All required metrics tables are present")
        
        # Add indexes for performance if they don't exist
        try:
            # Index for container_metrics_history
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_container_metrics_history_container_timestamp 
                ON container_metrics_history(container_id, timestamp DESC)
            """))
            
            # Index for container_health_scores
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_container_health_scores_container_timestamp 
                ON container_health_scores(container_id, timestamp DESC)
            """))
            
            # Index for container_predictions
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_container_predictions_container_timestamp 
                ON container_predictions(container_id, prediction_timestamp DESC)
            """))
            
            session.commit()
            print("✅ Performance indexes created/verified")
            
        except Exception as e:
            print(f"Warning: Could not create indexes (may already exist): {e}")
            session.rollback()
        
        # Verify table structure
        print("\nVerifying table structures...")
        
        # Check container_metrics_history columns
        result = session.execute(text("PRAGMA table_info(container_metrics_history)"))
        columns = [row[1] for row in result.fetchall()]
        expected_columns = [
            'id', 'container_id', 'container_name', 'timestamp', 'interval_minutes',
            'cpu_percent_avg', 'cpu_percent_min', 'cpu_percent_max',
            'memory_usage_avg', 'memory_usage_min', 'memory_usage_max',
            'memory_percent_avg', 'memory_percent_min', 'memory_percent_max',
            'network_rx_bytes_avg', 'network_rx_bytes_total',
            'network_tx_bytes_avg', 'network_tx_bytes_total',
            'block_read_bytes_avg', 'block_read_bytes_total',
            'block_write_bytes_avg', 'block_write_bytes_total',
            'data_points_count', 'health_score', 'created_at'
        ]
        
        missing_columns = [col for col in expected_columns if col not in columns]
        if missing_columns:
            print(f"WARNING: container_metrics_history missing columns: {missing_columns}")
        else:
            print("✅ container_metrics_history structure verified")
        
        # Check container_health_scores columns
        result = session.execute(text("PRAGMA table_info(container_health_scores)"))
        columns = [row[1] for row in result.fetchall()]
        expected_columns = [
            'id', 'container_id', 'container_name', 'timestamp',
            'overall_health_score', 'cpu_health_score', 'memory_health_score',
            'network_health_score', 'disk_health_score', 'analysis_period_hours',
            'data_points_analyzed', 'recommendations', 'created_at'
        ]
        
        missing_columns = [col for col in expected_columns if col not in columns]
        if missing_columns:
            print(f"WARNING: container_health_scores missing columns: {missing_columns}")
        else:
            print("✅ container_health_scores structure verified")
        
        # Check container_predictions columns
        result = session.execute(text("PRAGMA table_info(container_predictions)"))
        columns = [row[1] for row in result.fetchall()]
        expected_columns = [
            'id', 'container_id', 'container_name', 'prediction_timestamp',
            'prediction_horizon_hours', 'cpu_predicted_value', 'cpu_confidence', 'cpu_trend',
            'memory_predicted_value', 'memory_confidence', 'memory_trend',
            'cpu_actual_value', 'memory_actual_value', 'cpu_accuracy_score',
            'memory_accuracy_score', 'is_validated', 'created_at'
        ]
        
        missing_columns = [col for col in expected_columns if col not in columns]
        if missing_columns:
            print(f"WARNING: container_predictions missing columns: {missing_columns}")
        else:
            print("✅ container_predictions structure verified")
        
        session.close()
        print(f"\n✅ Migration completed successfully at {datetime.utcnow().isoformat()}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
