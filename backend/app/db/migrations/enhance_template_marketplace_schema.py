"""
Migration: Enhance Template Marketplace Schema for Phase 5

This migration enhances the template marketplace with advanced features:
- Enhanced marketplace_templates table with performance analytics integration
- template_analytics table for performance metrics correlation with Phase 4 data
- template_security_scans table for automated security validation
- template_deployment_history table for tracking template usage
- template_performance_metrics table for template-specific performance data
- Enhanced indexing and optimization for 1000+ templates and 100+ concurrent users
- Integration with Phase 4 container metrics for performance-based recommendations

Created: Phase 5 - Template Marketplace Enhancement
"""

import os
from sqlalchemy import text, create_engine

# Create a simple engine for migration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/dockerdeployer.db")
engine = create_engine(DATABASE_URL)


def upgrade():
    """Apply the migration - enhance template marketplace schema."""
    
    print("🚀 Starting Phase 5 template marketplace schema enhancement...")
    
    # Step 1: Enhance existing marketplace_templates table
    enhance_marketplace_templates_table()
    
    # Step 2: Create template analytics table
    create_template_analytics_table()
    
    # Step 3: Create template security scans table
    create_template_security_scans_table()
    
    # Step 4: Create template deployment history table
    create_template_deployment_history_table()
    
    # Step 5: Create template performance metrics table
    create_template_performance_metrics_table()
    
    # Step 6: Create template marketplace cache table
    create_template_marketplace_cache_table()
    
    # Step 7: Create optimized indexes for performance
    create_marketplace_optimized_indexes()
    
    # Step 8: Insert enhanced default categories
    insert_enhanced_default_categories()
    
    print("✅ Phase 5 template marketplace schema enhancement completed successfully")


def enhance_marketplace_templates_table():
    """Enhance the existing marketplace_templates table with new fields."""

    print("📊 Enhancing marketplace_templates table...")

    # Check if we're using SQLite and use compatible syntax
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_templates';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        # SQLite-compatible column additions
        enhancement_sql = [
            # Enhanced metadata and categorization
            "ALTER TABLE marketplace_templates ADD COLUMN subcategory TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN difficulty_level TEXT DEFAULT 'intermediate';",
            "ALTER TABLE marketplace_templates ADD COLUMN estimated_setup_time INTEGER DEFAULT 10;",
            "ALTER TABLE marketplace_templates ADD COLUMN resource_requirements TEXT;",
            
            # Performance and analytics integration
            "ALTER TABLE marketplace_templates ADD COLUMN performance_score REAL DEFAULT 0.0;",
            "ALTER TABLE marketplace_templates ADD COLUMN deployment_success_rate REAL DEFAULT 0.0;",
            "ALTER TABLE marketplace_templates ADD COLUMN avg_deployment_time INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN last_performance_update TEXT;",
            
            # Enhanced template metadata
            "ALTER TABLE marketplace_templates ADD COLUMN template_size_mb REAL DEFAULT 0.0;",
            "ALTER TABLE marketplace_templates ADD COLUMN docker_image_count INTEGER DEFAULT 1;",
            "ALTER TABLE marketplace_templates ADD COLUMN network_ports TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN volume_mounts TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN environment_variables TEXT;",
            
            # Security and validation
            "ALTER TABLE marketplace_templates ADD COLUMN security_score INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN last_security_scan TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN security_issues_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN is_security_approved INTEGER DEFAULT 0;",
            
            # Usage analytics
            "ALTER TABLE marketplace_templates ADD COLUMN unique_users_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN deployment_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN success_deployment_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN last_deployed_at TEXT;",
            
            # Template lifecycle management
            "ALTER TABLE marketplace_templates ADD COLUMN is_featured INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN is_deprecated INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN deprecation_reason TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN replacement_template_id INTEGER;",
            
            # Enhanced search and discovery
            "ALTER TABLE marketplace_templates ADD COLUMN search_keywords TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN compatibility_tags TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN minimum_docker_version TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN supported_architectures TEXT DEFAULT 'amd64';",
        ]
    else:
        # PostgreSQL-compatible syntax
        enhancement_sql = [
            # Enhanced metadata and categorization
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS subcategory VARCHAR(100);",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS difficulty_level VARCHAR(20) DEFAULT 'intermediate';",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS estimated_setup_time INTEGER DEFAULT 10;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS resource_requirements JSONB;",
            
            # Performance and analytics integration
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS performance_score FLOAT DEFAULT 0.0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS deployment_success_rate FLOAT DEFAULT 0.0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS avg_deployment_time INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS last_performance_update TIMESTAMP WITH TIME ZONE;",
            
            # Enhanced template metadata
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS template_size_mb FLOAT DEFAULT 0.0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS docker_image_count INTEGER DEFAULT 1;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS network_ports JSONB;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS volume_mounts JSONB;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS environment_variables JSONB;",
            
            # Security and validation
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS security_score INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS last_security_scan TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS security_issues_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS is_security_approved BOOLEAN DEFAULT FALSE;",
            
            # Usage analytics
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS unique_users_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS deployment_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS success_deployment_count INTEGER DEFAULT 0;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS last_deployed_at TIMESTAMP WITH TIME ZONE;",
            
            # Template lifecycle management
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS is_deprecated BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS deprecation_reason TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS replacement_template_id INTEGER;",
            
            # Enhanced search and discovery
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS search_keywords TEXT;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS compatibility_tags JSONB;",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS minimum_docker_version VARCHAR(20);",
            "ALTER TABLE marketplace_templates ADD COLUMN IF NOT EXISTS supported_architectures JSONB DEFAULT '[\"amd64\"]';",
        ]
    
    with engine.connect() as connection:
        for sql in enhancement_sql:
            try:
                connection.execute(text(sql))
                connection.commit()
            except Exception as e:
                print(f"⚠️  Warning: {sql} - {e}")
                connection.rollback()
    
    print("✅ Marketplace templates table enhanced")


def create_template_analytics_table():
    """Create the template_analytics table for performance metrics integration."""

    print("📈 Creating template_analytics table...")

    # Check if we're using SQLite
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_templates';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        analytics_table_sql = """
        CREATE TABLE IF NOT EXISTS template_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            container_id TEXT,
            deployment_id TEXT,
            
            -- Performance metrics correlation with Phase 4 data
            avg_cpu_usage REAL,
            avg_memory_usage REAL,
            avg_network_io REAL,
            avg_disk_io REAL,
            performance_score REAL DEFAULT 0.0,
            
            -- Deployment analytics
            deployment_duration_seconds INTEGER,
            startup_time_seconds INTEGER,
            first_response_time_ms INTEGER,
            deployment_success INTEGER DEFAULT 1,
            error_message TEXT,
            
            -- Resource utilization
            peak_cpu_usage REAL,
            peak_memory_usage REAL,
            resource_efficiency_score REAL DEFAULT 0.0,
            
            -- User experience metrics
            user_satisfaction_score INTEGER,
            user_feedback TEXT,
            
            -- Timestamps and metadata
            deployment_started_at TEXT NOT NULL,
            deployment_completed_at TEXT,
            analysis_period_hours INTEGER DEFAULT 24,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE
        );
        """
    else:
        analytics_table_sql = """
        CREATE TABLE IF NOT EXISTS template_analytics (
            id BIGSERIAL PRIMARY KEY,
            template_id INTEGER NOT NULL,
            container_id VARCHAR(255),
            deployment_id VARCHAR(255),
            
            -- Performance metrics correlation with Phase 4 data
            avg_cpu_usage FLOAT,
            avg_memory_usage FLOAT,
            avg_network_io FLOAT,
            avg_disk_io FLOAT,
            performance_score FLOAT DEFAULT 0.0,
            
            -- Deployment analytics
            deployment_duration_seconds INTEGER,
            startup_time_seconds INTEGER,
            first_response_time_ms INTEGER,
            deployment_success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            
            -- Resource utilization
            peak_cpu_usage FLOAT,
            peak_memory_usage FLOAT,
            resource_efficiency_score FLOAT DEFAULT 0.0,
            
            -- User experience metrics
            user_satisfaction_score INTEGER CHECK (user_satisfaction_score >= 1 AND user_satisfaction_score <= 5),
            user_feedback TEXT,
            
            -- Timestamps and metadata
            deployment_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            deployment_completed_at TIMESTAMP WITH TIME ZONE,
            analysis_period_hours INTEGER DEFAULT 24,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE
        );
        """
    
    with engine.connect() as connection:
        connection.execute(text(analytics_table_sql))
        connection.commit()
    
    print("✅ Template analytics table created")


def create_template_security_scans_table():
    """Create the template_security_scans table for automated security validation."""

    print("🔒 Creating template_security_scans table...")

    # Check if we're using SQLite
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_templates';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        security_scans_table_sql = """
        CREATE TABLE IF NOT EXISTS template_security_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            template_version_id INTEGER,
            scan_type TEXT NOT NULL DEFAULT 'automated',

            -- Security scan results
            overall_security_score INTEGER DEFAULT 0,
            vulnerability_count_critical INTEGER DEFAULT 0,
            vulnerability_count_high INTEGER DEFAULT 0,
            vulnerability_count_medium INTEGER DEFAULT 0,
            vulnerability_count_low INTEGER DEFAULT 0,

            -- Docker security checks
            dockerfile_security_score INTEGER DEFAULT 0,
            compose_security_score INTEGER DEFAULT 0,
            image_security_score INTEGER DEFAULT 0,

            -- Specific security issues
            uses_root_user INTEGER DEFAULT 0,
            exposes_privileged_ports INTEGER DEFAULT 0,
            has_secrets_in_config INTEGER DEFAULT 0,
            uses_latest_tags INTEGER DEFAULT 0,
            missing_health_checks INTEGER DEFAULT 0,

            -- Scan metadata
            scan_engine TEXT DEFAULT 'internal',
            scan_version TEXT,
            scan_duration_seconds INTEGER,
            scan_status TEXT DEFAULT 'completed',
            scan_error_message TEXT,

            -- Detailed results
            vulnerability_details TEXT,
            recommendations TEXT,
            compliance_status TEXT,

            -- Timestamps
            scan_started_at TEXT NOT NULL,
            scan_completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE,
            FOREIGN KEY (template_version_id) REFERENCES template_versions (id) ON DELETE CASCADE
        );
        """
    else:
        security_scans_table_sql = """
        CREATE TABLE IF NOT EXISTS template_security_scans (
            id BIGSERIAL PRIMARY KEY,
            template_id INTEGER NOT NULL,
            template_version_id INTEGER,
            scan_type VARCHAR(50) NOT NULL DEFAULT 'automated',

            -- Security scan results
            overall_security_score INTEGER DEFAULT 0,
            vulnerability_count_critical INTEGER DEFAULT 0,
            vulnerability_count_high INTEGER DEFAULT 0,
            vulnerability_count_medium INTEGER DEFAULT 0,
            vulnerability_count_low INTEGER DEFAULT 0,

            -- Docker security checks
            dockerfile_security_score INTEGER DEFAULT 0,
            compose_security_score INTEGER DEFAULT 0,
            image_security_score INTEGER DEFAULT 0,

            -- Specific security issues
            uses_root_user BOOLEAN DEFAULT FALSE,
            exposes_privileged_ports BOOLEAN DEFAULT FALSE,
            has_secrets_in_config BOOLEAN DEFAULT FALSE,
            uses_latest_tags BOOLEAN DEFAULT FALSE,
            missing_health_checks BOOLEAN DEFAULT FALSE,

            -- Scan metadata
            scan_engine VARCHAR(100) DEFAULT 'internal',
            scan_version VARCHAR(50),
            scan_duration_seconds INTEGER,
            scan_status VARCHAR(50) DEFAULT 'completed',
            scan_error_message TEXT,

            -- Detailed results
            vulnerability_details JSONB,
            recommendations JSONB,
            compliance_status JSONB,

            -- Timestamps
            scan_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            scan_completed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE,
            FOREIGN KEY (template_version_id) REFERENCES template_versions (id) ON DELETE CASCADE
        );
        """

    with engine.connect() as connection:
        connection.execute(text(security_scans_table_sql))
        connection.commit()

    print("✅ Template security scans table created")


def create_template_deployment_history_table():
    """Create the template_deployment_history table for tracking template usage."""

    print("📋 Creating template_deployment_history table...")

    # Check if we're using SQLite
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_templates';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        deployment_history_table_sql = """
        CREATE TABLE IF NOT EXISTS template_deployment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            template_version_id INTEGER,
            user_id INTEGER NOT NULL,
            deployment_id TEXT UNIQUE NOT NULL,

            -- Deployment details
            deployment_name TEXT NOT NULL,
            deployment_environment TEXT DEFAULT 'development',
            deployment_status TEXT DEFAULT 'pending',

            -- Configuration and customization
            custom_configuration TEXT,
            environment_overrides TEXT,
            resource_limits TEXT,

            -- Deployment timeline
            deployment_requested_at TEXT NOT NULL,
            deployment_started_at TEXT,
            deployment_completed_at TEXT,
            deployment_failed_at TEXT,
            deployment_duration_seconds INTEGER,

            -- Results and feedback
            deployment_success INTEGER DEFAULT 0,
            error_message TEXT,
            user_notes TEXT,
            user_rating INTEGER,

            -- Resource usage tracking
            containers_created INTEGER DEFAULT 0,
            networks_created INTEGER DEFAULT 0,
            volumes_created INTEGER DEFAULT 0,

            -- Integration with Phase 4 metrics
            metrics_collection_enabled INTEGER DEFAULT 1,
            performance_monitoring_duration_hours INTEGER DEFAULT 24,

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE,
            FOREIGN KEY (template_version_id) REFERENCES template_versions (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    else:
        deployment_history_table_sql = """
        CREATE TABLE IF NOT EXISTS template_deployment_history (
            id BIGSERIAL PRIMARY KEY,
            template_id INTEGER NOT NULL,
            template_version_id INTEGER,
            user_id INTEGER NOT NULL,
            deployment_id VARCHAR(255) UNIQUE NOT NULL,

            -- Deployment details
            deployment_name VARCHAR(255) NOT NULL,
            deployment_environment VARCHAR(50) DEFAULT 'development',
            deployment_status VARCHAR(50) DEFAULT 'pending',

            -- Configuration and customization
            custom_configuration JSONB,
            environment_overrides JSONB,
            resource_limits JSONB,

            -- Deployment timeline
            deployment_requested_at TIMESTAMP WITH TIME ZONE NOT NULL,
            deployment_started_at TIMESTAMP WITH TIME ZONE,
            deployment_completed_at TIMESTAMP WITH TIME ZONE,
            deployment_failed_at TIMESTAMP WITH TIME ZONE,
            deployment_duration_seconds INTEGER,

            -- Results and feedback
            deployment_success BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            user_notes TEXT,
            user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),

            -- Resource usage tracking
            containers_created INTEGER DEFAULT 0,
            networks_created INTEGER DEFAULT 0,
            volumes_created INTEGER DEFAULT 0,

            -- Integration with Phase 4 metrics
            metrics_collection_enabled BOOLEAN DEFAULT TRUE,
            performance_monitoring_duration_hours INTEGER DEFAULT 24,

            -- Timestamps
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE,
            FOREIGN KEY (template_version_id) REFERENCES template_versions (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """

    with engine.connect() as connection:
        connection.execute(text(deployment_history_table_sql))
        connection.commit()

    print("✅ Template deployment history table created")


def create_template_performance_metrics_table():
    """Create the template_performance_metrics table for template-specific performance data."""

    print("⚡ Creating template_performance_metrics table...")

    # Check if we're using SQLite
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_templates';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        performance_metrics_table_sql = """
        CREATE TABLE IF NOT EXISTS template_performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            deployment_id TEXT,

            -- Performance aggregation period
            aggregation_period TEXT NOT NULL DEFAULT 'daily',
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,

            -- Template-level performance metrics
            avg_startup_time_seconds REAL,
            avg_response_time_ms REAL,
            success_rate_percentage REAL DEFAULT 100.0,
            error_rate_percentage REAL DEFAULT 0.0,

            -- Resource efficiency metrics
            avg_cpu_efficiency REAL,
            avg_memory_efficiency REAL,
            avg_network_efficiency REAL,
            avg_disk_efficiency REAL,
            overall_efficiency_score REAL DEFAULT 0.0,

            -- Deployment success metrics
            total_deployments INTEGER DEFAULT 0,
            successful_deployments INTEGER DEFAULT 0,
            failed_deployments INTEGER DEFAULT 0,
            avg_deployment_duration_seconds REAL,

            -- User satisfaction metrics
            avg_user_rating REAL DEFAULT 0.0,
            total_user_ratings INTEGER DEFAULT 0,
            user_satisfaction_score REAL DEFAULT 0.0,

            -- Performance trends
            performance_trend TEXT,
            efficiency_trend TEXT,
            reliability_trend TEXT,

            -- Comparison with similar templates
            performance_percentile INTEGER,
            efficiency_percentile INTEGER,
            popularity_percentile INTEGER,

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE
        );
        """
    else:
        performance_metrics_table_sql = """
        CREATE TABLE IF NOT EXISTS template_performance_metrics (
            id BIGSERIAL PRIMARY KEY,
            template_id INTEGER NOT NULL,
            deployment_id VARCHAR(255),

            -- Performance aggregation period
            aggregation_period VARCHAR(20) NOT NULL DEFAULT 'daily',
            period_start TIMESTAMP WITH TIME ZONE NOT NULL,
            period_end TIMESTAMP WITH TIME ZONE NOT NULL,

            -- Template-level performance metrics
            avg_startup_time_seconds FLOAT,
            avg_response_time_ms FLOAT,
            success_rate_percentage FLOAT DEFAULT 100.0,
            error_rate_percentage FLOAT DEFAULT 0.0,

            -- Resource efficiency metrics
            avg_cpu_efficiency FLOAT,
            avg_memory_efficiency FLOAT,
            avg_network_efficiency FLOAT,
            avg_disk_efficiency FLOAT,
            overall_efficiency_score FLOAT DEFAULT 0.0,

            -- Deployment success metrics
            total_deployments INTEGER DEFAULT 0,
            successful_deployments INTEGER DEFAULT 0,
            failed_deployments INTEGER DEFAULT 0,
            avg_deployment_duration_seconds FLOAT,

            -- User satisfaction metrics
            avg_user_rating FLOAT DEFAULT 0.0,
            total_user_ratings INTEGER DEFAULT 0,
            user_satisfaction_score FLOAT DEFAULT 0.0,

            -- Performance trends
            performance_trend VARCHAR(20),
            efficiency_trend VARCHAR(20),
            reliability_trend VARCHAR(20),

            -- Comparison with similar templates
            performance_percentile INTEGER,
            efficiency_percentile INTEGER,
            popularity_percentile INTEGER,

            -- Timestamps
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            FOREIGN KEY (template_id) REFERENCES marketplace_templates (id) ON DELETE CASCADE
        );
        """

    with engine.connect() as connection:
        connection.execute(text(performance_metrics_table_sql))
        connection.commit()

    print("✅ Template performance metrics table created")


def create_template_marketplace_cache_table():
    """Create the template_marketplace_cache table for Redis-like caching in database."""

    print("🗄️ Creating template_marketplace_cache table...")

    # Check if we're using SQLite
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_templates';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        cache_table_sql = """
        CREATE TABLE IF NOT EXISTS template_marketplace_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            cache_value TEXT NOT NULL,
            cache_type TEXT NOT NULL DEFAULT 'search_result',

            -- Cache metadata
            cache_size_bytes INTEGER DEFAULT 0,
            hit_count INTEGER DEFAULT 0,
            last_hit_at TEXT,

            -- TTL and expiration
            ttl_seconds INTEGER DEFAULT 3600,
            expires_at TEXT NOT NULL,
            is_expired INTEGER DEFAULT 0,

            -- Cache tags for invalidation
            cache_tags TEXT,
            template_ids TEXT,
            category_ids TEXT,

            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    else:
        cache_table_sql = """
        CREATE TABLE IF NOT EXISTS template_marketplace_cache (
            id BIGSERIAL PRIMARY KEY,
            cache_key VARCHAR(512) UNIQUE NOT NULL,
            cache_value JSONB NOT NULL,
            cache_type VARCHAR(50) NOT NULL DEFAULT 'search_result',

            -- Cache metadata
            cache_size_bytes INTEGER DEFAULT 0,
            hit_count INTEGER DEFAULT 0,
            last_hit_at TIMESTAMP WITH TIME ZONE,

            -- TTL and expiration
            ttl_seconds INTEGER DEFAULT 3600,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_expired BOOLEAN DEFAULT FALSE,

            -- Cache tags for invalidation
            cache_tags JSONB,
            template_ids JSONB,
            category_ids JSONB,

            -- Timestamps
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

    with engine.connect() as connection:
        connection.execute(text(cache_table_sql))
        connection.commit()

    print("✅ Template marketplace cache table created")


def create_marketplace_optimized_indexes():
    """Create optimized indexes for marketplace performance."""

    print("🔍 Creating marketplace optimized indexes...")

    index_sql = [
        # Enhanced marketplace_templates indexes
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_performance_score ON marketplace_templates (performance_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_security_score ON marketplace_templates (security_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_deployment_success_rate ON marketplace_templates (deployment_success_rate DESC);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_featured ON marketplace_templates (is_featured) WHERE is_featured = 1;",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_deprecated ON marketplace_templates (is_deprecated) WHERE is_deprecated = 0;",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_difficulty ON marketplace_templates (difficulty_level);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_subcategory ON marketplace_templates (subcategory) WHERE subcategory IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_templates_search_keywords ON marketplace_templates (search_keywords) WHERE search_keywords IS NOT NULL;",

        # Template analytics indexes
        "CREATE INDEX IF NOT EXISTS idx_template_analytics_template_performance ON template_analytics (template_id, performance_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_analytics_deployment_success ON template_analytics (deployment_success, deployment_started_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_analytics_container_id ON template_analytics (container_id) WHERE container_id IS NOT NULL;",

        # Template security scans indexes
        "CREATE INDEX IF NOT EXISTS idx_template_security_scans_template ON template_security_scans (template_id, scan_completed_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_security_scans_security_score ON template_security_scans (overall_security_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_security_scans_status ON template_security_scans (scan_status);",

        # Template deployment history indexes
        "CREATE INDEX IF NOT EXISTS idx_template_deployment_history_template ON template_deployment_history (template_id, deployment_requested_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_deployment_history_user ON template_deployment_history (user_id, deployment_requested_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_deployment_history_status ON template_deployment_history (deployment_status);",
        "CREATE INDEX IF NOT EXISTS idx_template_deployment_history_success ON template_deployment_history (deployment_success, deployment_completed_at DESC);",

        # Template performance metrics indexes
        "CREATE INDEX IF NOT EXISTS idx_template_performance_metrics_template_period ON template_performance_metrics (template_id, aggregation_period, period_start DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_performance_metrics_efficiency ON template_performance_metrics (overall_efficiency_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_template_performance_metrics_success_rate ON template_performance_metrics (success_rate_percentage DESC);",

        # Template marketplace cache indexes
        "CREATE INDEX IF NOT EXISTS idx_template_marketplace_cache_key ON template_marketplace_cache (cache_key);",
        "CREATE INDEX IF NOT EXISTS idx_template_marketplace_cache_expires ON template_marketplace_cache (expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_template_marketplace_cache_type ON template_marketplace_cache (cache_type);",
        "CREATE INDEX IF NOT EXISTS idx_template_marketplace_cache_expired ON template_marketplace_cache (is_expired, expires_at) WHERE is_expired = 0;",
    ]

    with engine.connect() as connection:
        for sql in index_sql:
            try:
                connection.execute(text(sql))
                connection.commit()
            except Exception as e:
                print(f"⚠️  Warning creating index: {e}")
                connection.rollback()

    print("✅ Marketplace optimized indexes created")


def insert_enhanced_default_categories():
    """Insert enhanced default template categories with subcategories."""

    print("📋 Inserting enhanced default categories...")

    # Enhanced categories with subcategories and metadata
    enhanced_categories = [
        {
            "name": "Web Servers",
            "description": "Web server stacks, reverse proxies, and load balancers",
            "icon": "web",
            "sort_order": 1,
            "subcategories": "nginx,apache,traefik,haproxy,caddy"
        },
        {
            "name": "Databases",
            "description": "Relational and NoSQL database systems with clustering",
            "icon": "database",
            "sort_order": 2,
            "subcategories": "mysql,postgresql,mongodb,redis,elasticsearch,cassandra"
        },
        {
            "name": "Development Tools",
            "description": "IDEs, build tools, and development environments",
            "icon": "code",
            "sort_order": 3,
            "subcategories": "vscode,jenkins,gitlab,sonarqube,nexus"
        },
        {
            "name": "Monitoring & Observability",
            "description": "Monitoring, logging, and observability platforms",
            "icon": "chart",
            "sort_order": 4,
            "subcategories": "grafana,prometheus,elk,jaeger,datadog"
        },
        {
            "name": "CI/CD & DevOps",
            "description": "Continuous integration and deployment pipelines",
            "icon": "pipeline",
            "sort_order": 5,
            "subcategories": "jenkins,gitlab-ci,github-actions,drone,tekton"
        },
        {
            "name": "E-commerce & CMS",
            "description": "E-commerce platforms and content management systems",
            "icon": "shopping",
            "sort_order": 6,
            "subcategories": "wordpress,drupal,magento,shopify,prestashop"
        },
        {
            "name": "Analytics & Big Data",
            "description": "Data processing, analytics, and machine learning platforms",
            "icon": "analytics",
            "sort_order": 7,
            "subcategories": "kafka,spark,airflow,jupyter,superset"
        },
        {
            "name": "Security & Compliance",
            "description": "Security tools, vulnerability scanners, and compliance",
            "icon": "shield",
            "sort_order": 8,
            "subcategories": "vault,keycloak,oauth,ldap,fail2ban"
        },
        {
            "name": "Networking & Infrastructure",
            "description": "Network tools, VPNs, and infrastructure services",
            "icon": "network",
            "sort_order": 9,
            "subcategories": "openvpn,wireguard,dns,dhcp,proxy"
        },
        {
            "name": "AI & Machine Learning",
            "description": "AI/ML frameworks, model serving, and data science tools",
            "icon": "brain",
            "sort_order": 10,
            "subcategories": "tensorflow,pytorch,mlflow,kubeflow,jupyter"
        }
    ]

    # Check if we're using SQLite for proper syntax
    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='template_categories';"))
            is_sqlite = result.fetchone() is not None
        except:
            is_sqlite = False

    if is_sqlite:
        # Add subcategories column if it doesn't exist
        try:
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE template_categories ADD COLUMN subcategories TEXT;"))
                connection.commit()
        except:
            pass  # Column might already exist

        insert_sql = """
        INSERT OR IGNORE INTO template_categories (name, description, icon, sort_order, subcategories)
        VALUES (:name, :description, :icon, :sort_order, :subcategories);
        """
    else:
        # Add subcategories column if it doesn't exist
        try:
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE template_categories ADD COLUMN IF NOT EXISTS subcategories TEXT;"))
                connection.commit()
        except:
            pass  # Column might already exist

        insert_sql = """
        INSERT INTO template_categories (name, description, icon, sort_order, subcategories)
        VALUES (:name, :description, :icon, :sort_order, :subcategories)
        ON CONFLICT (name) DO UPDATE SET
            description = EXCLUDED.description,
            subcategories = EXCLUDED.subcategories,
            updated_at = NOW();
        """

    with engine.connect() as connection:
        for category in enhanced_categories:
            connection.execute(text(insert_sql), category)
        connection.commit()

    print("✅ Enhanced default categories inserted successfully")


def downgrade():
    """Rollback the migration."""

    print("🔄 Rolling back Phase 5 template marketplace schema enhancement...")

    downgrade_sql = [
        "DROP TABLE IF EXISTS template_marketplace_cache;",
        "DROP TABLE IF EXISTS template_performance_metrics;",
        "DROP TABLE IF EXISTS template_deployment_history;",
        "DROP TABLE IF EXISTS template_security_scans;",
        "DROP TABLE IF EXISTS template_analytics;",
        # Note: We don't drop marketplace_templates as it existed before this migration
        # Instead, we would need to remove the added columns (not implemented for safety)
    ]

    with engine.connect() as connection:
        for sql in downgrade_sql:
            connection.execute(text(sql))
        connection.commit()

    print("✅ Phase 5 template marketplace schema enhancement rolled back")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
