"""
Database optimization service for connection pooling and query optimization.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class DatabaseOptimizationService:
    """Service for database performance optimization."""

    def __init__(self, database_url: str):
        """
        Initialize database optimization service.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_size": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalidated": 0,
        }

    def create_optimized_engine(
        self,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ) -> Engine:
        """
        Create an optimized database engine with connection pooling.
        
        Args:
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum number of connections that can overflow the pool
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Time in seconds to recycle connections
            echo: Whether to echo SQL statements
            
        Returns:
            Optimized SQLAlchemy engine
        """
        # Connection pool configuration for production
        engine_config = {
            "poolclass": QueuePool,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": True,  # Validate connections before use
            "echo": echo,
        }

        # SQLite-specific optimizations
        if "sqlite" in self.database_url:
            engine_config.update({
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                    # SQLite performance optimizations
                    "isolation_level": None,  # Enable autocommit mode
                },
                # SQLite doesn't support connection pooling in the traditional sense
                "poolclass": pool.StaticPool,
                "pool_size": 1,
                "max_overflow": 0,
            })

        # PostgreSQL-specific optimizations
        elif "postgresql" in self.database_url:
            engine_config.update({
                "connect_args": {
                    "connect_timeout": 10,
                    "command_timeout": 60,
                    "server_settings": {
                        "application_name": "DockerDeployer",
                        "jit": "off",  # Disable JIT for faster connection times
                    }
                }
            })

        # MySQL-specific optimizations
        elif "mysql" in self.database_url:
            engine_config.update({
                "connect_args": {
                    "connect_timeout": 10,
                    "read_timeout": 60,
                    "write_timeout": 60,
                    "charset": "utf8mb4",
                }
            })

        self.engine = create_engine(self.database_url, **engine_config)
        
        # Set up event listeners for monitoring
        self._setup_event_listeners()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Created optimized database engine with pool_size={pool_size}")
        return self.engine

    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring."""
        if not self.engine:
            return

        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new database connections."""
            self._connection_stats["total_connections"] += 1
            logger.debug("New database connection established")

        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout from pool."""
            self._connection_stats["active_connections"] += 1

        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Handle connection checkin to pool."""
            self._connection_stats["active_connections"] = max(
                0, self._connection_stats["active_connections"] - 1
            )

        @event.listens_for(self.engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Handle connection invalidation."""
            self._connection_stats["invalidated"] += 1
            logger.warning(f"Database connection invalidated: {exception}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection pool statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        stats = self._connection_stats.copy()
        
        if self.engine and hasattr(self.engine.pool, 'size'):
            stats.update({
                "pool_size": self.engine.pool.size(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow(),
                "checked_in": self.engine.pool.checkedin(),
            })
        
        return stats

    @asynccontextmanager
    async def get_db_session(self):
        """
        Get a database session with proper cleanup.
        
        Yields:
            Database session
        """
        if not self.SessionLocal:
            raise RuntimeError("Database engine not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def optimize_sqlite_settings(self):
        """Apply SQLite-specific performance optimizations."""
        if not self.engine or "sqlite" not in self.database_url:
            return

        with self.engine.connect() as connection:
            # Apply SQLite performance optimizations
            optimizations = [
                "PRAGMA journal_mode=WAL",  # Write-Ahead Logging
                "PRAGMA synchronous=NORMAL",  # Faster than FULL, safer than OFF
                "PRAGMA cache_size=10000",  # 10MB cache
                "PRAGMA temp_store=MEMORY",  # Store temp tables in memory
                "PRAGMA mmap_size=268435456",  # 256MB memory-mapped I/O
                "PRAGMA optimize",  # Optimize query planner
            ]
            
            for pragma in optimizations:
                try:
                    connection.execute(pragma)
                    logger.debug(f"Applied SQLite optimization: {pragma}")
                except Exception as e:
                    logger.warning(f"Failed to apply SQLite optimization {pragma}: {e}")

    def get_query_performance_stats(self) -> Dict[str, Any]:
        """
        Get query performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        if not self.engine:
            return {}

        try:
            with self.engine.connect() as connection:
                if "sqlite" in self.database_url:
                    # SQLite-specific stats
                    result = connection.execute("PRAGMA compile_options").fetchall()
                    compile_options = [row[0] for row in result]
                    
                    return {
                        "database_type": "sqlite",
                        "compile_options": compile_options,
                        "connection_stats": self.get_connection_stats(),
                    }
                
                elif "postgresql" in self.database_url:
                    # PostgreSQL-specific stats
                    result = connection.execute("""
                        SELECT 
                            datname,
                            numbackends,
                            xact_commit,
                            xact_rollback,
                            blks_read,
                            blks_hit,
                            tup_returned,
                            tup_fetched,
                            tup_inserted,
                            tup_updated,
                            tup_deleted
                        FROM pg_stat_database 
                        WHERE datname = current_database()
                    """).fetchone()
                    
                    if result:
                        return {
                            "database_type": "postgresql",
                            "database_name": result[0],
                            "active_connections": result[1],
                            "transactions_committed": result[2],
                            "transactions_rolled_back": result[3],
                            "blocks_read": result[4],
                            "blocks_hit": result[5],
                            "cache_hit_ratio": result[5] / (result[4] + result[5]) if (result[4] + result[5]) > 0 else 0,
                            "tuples_returned": result[6],
                            "tuples_fetched": result[7],
                            "tuples_inserted": result[8],
                            "tuples_updated": result[9],
                            "tuples_deleted": result[10],
                            "connection_stats": self.get_connection_stats(),
                        }
                
                return {
                    "database_type": "unknown",
                    "connection_stats": self.get_connection_stats(),
                }
                
        except Exception as e:
            logger.error(f"Error getting query performance stats: {e}")
            return {"error": str(e)}

    def cleanup(self):
        """Clean up database connections and resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")


# Global database optimization service
_db_optimization_service: Optional[DatabaseOptimizationService] = None


def get_db_optimization_service(database_url: str) -> DatabaseOptimizationService:
    """Get the global database optimization service instance."""
    global _db_optimization_service
    if _db_optimization_service is None:
        _db_optimization_service = DatabaseOptimizationService(database_url)
    return _db_optimization_service
