"""
Database models for the DockerDeployer application.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserRole(str, Enum):
    """User role enum."""

    ADMIN = "admin"
    USER = "user"


# Association table for many-to-many relationship between users and teams
user_team = Table(
    "user_team",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(String, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = relationship("Team", secondary=user_team, back_populates="members")
    owned_teams = relationship("Team", back_populates="owner")
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    deployment_history = relationship("DeploymentHistory", back_populates="user")
    authored_templates = relationship("MarketplaceTemplate", foreign_keys="MarketplaceTemplate.author_id", back_populates="author")
    template_reviews = relationship("TemplateReview", back_populates="user")


class Team(Base):
    """Team model for grouping users."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("User", secondary=user_team, back_populates="teams")
    deployments = relationship("DeploymentHistory", back_populates="team")


class Token(Base):
    """Token model for user authentication."""

    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tokens")


class PasswordResetToken(Base):
    """Password reset token model."""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class EmailVerificationToken(Base):
    """Email verification token model."""

    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class DeploymentHistory(Base):
    """Deployment history model."""

    __tablename__ = "deployment_history"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String, index=True)
    config = Column(String)  # JSON string of the deployment configuration
    status = Column(String)  # success, failed, in_progress
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="deployment_history")
    team = relationship("Team", back_populates="deployments")


class MetricType(str, Enum):
    """Metric type enum for alerts."""

    CPU_PERCENT = "cpu_percent"
    MEMORY_USAGE = "memory_usage"
    MEMORY_PERCENT = "memory_percent"
    NETWORK_RX = "network_rx"
    NETWORK_TX = "network_tx"
    BLOCK_READ = "block_read"
    BLOCK_WRITE = "block_write"


class ComparisonOperator(str, Enum):
    """Comparison operator enum for alerts."""

    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


class ContainerMetrics(Base):
    """
    Enhanced container metrics model for storing high-frequency performance data.
    Optimized for time-series data with partitioning and indexing strategies.
    Supports 100+ containers with <200ms API response targets.
    """

    __tablename__ = "container_metrics"

    # Use BigInteger for high-volume time-series data
    id = Column(BigInteger, primary_key=True, index=True)
    container_id = Column(String(255), index=True, nullable=False)
    container_name = Column(String(255), index=True, nullable=True)

    # Timezone-aware timestamp for global deployments
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Date partition key for table partitioning optimization
    date_partition = Column(DateTime(timezone=True), index=True, nullable=False)

    # CPU metrics with enhanced precision
    cpu_percent = Column(Float, nullable=True)
    cpu_usage_seconds = Column(Float, nullable=True)  # Total CPU time used
    cpu_throttled_periods = Column(BigInteger, nullable=True)  # CPU throttling info

    # Memory metrics (in bytes) with detailed breakdown
    memory_usage_bytes = Column(BigInteger, nullable=True)
    memory_limit_bytes = Column(BigInteger, nullable=True)
    memory_percent = Column(Float, nullable=True)
    memory_cache_bytes = Column(BigInteger, nullable=True)  # Cache memory
    memory_rss_bytes = Column(BigInteger, nullable=True)    # Resident set size
    memory_swap_bytes = Column(BigInteger, nullable=True)   # Swap usage

    # Network metrics (in bytes and packets) with enhanced detail
    network_rx_bytes = Column(BigInteger, nullable=True)
    network_tx_bytes = Column(BigInteger, nullable=True)
    network_rx_packets = Column(BigInteger, nullable=True)
    network_tx_packets = Column(BigInteger, nullable=True)
    network_rx_errors = Column(BigInteger, nullable=True)
    network_tx_errors = Column(BigInteger, nullable=True)

    # Disk I/O metrics (in bytes and operations) with enhanced detail
    disk_read_bytes = Column(BigInteger, nullable=True)
    disk_write_bytes = Column(BigInteger, nullable=True)
    disk_read_ops = Column(BigInteger, nullable=True)      # Read operations count
    disk_write_ops = Column(BigInteger, nullable=True)     # Write operations count
    disk_read_time_ms = Column(BigInteger, nullable=True)  # Time spent reading
    disk_write_time_ms = Column(BigInteger, nullable=True) # Time spent writing

    # Container context and metadata
    image_name = Column(String(512), nullable=True)        # Container image
    container_status = Column(String(50), nullable=True)   # running, stopped, etc.
    container_labels = Column(JSON, nullable=True)         # Container labels as JSON

    # Performance indicators
    restart_count = Column(Integer, default=0, nullable=False)  # Container restarts
    uptime_seconds = Column(BigInteger, nullable=True)          # Container uptime

    # Data quality and collection metadata
    collection_duration_ms = Column(Integer, nullable=True)     # Time to collect metrics
    collection_source = Column(String(50), default='docker_sdk', nullable=False)

    # Timestamps with timezone awareness
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ContainerMetricsAggregated(Base):
    """
    Container metrics aggregated model for pre-computed time-series summaries.
    Optimized for fast dashboard queries and historical analysis.
    Supports hourly, daily, and weekly aggregations with statistical summaries.
    """

    __tablename__ = "container_metrics_aggregated"

    id = Column(BigInteger, primary_key=True, index=True)
    container_id = Column(String(255), index=True, nullable=False)
    container_name = Column(String(255), index=True, nullable=True)

    # Aggregation period configuration
    aggregation_period = Column(String(20), index=True, nullable=False)  # 'hour', 'day', 'week'
    period_start = Column(DateTime(timezone=True), index=True, nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Data quality metrics
    data_points_count = Column(Integer, nullable=False)
    collection_completeness = Column(Float, nullable=True)  # Percentage of expected data points

    # CPU metrics aggregations (min, max, avg, p95, p99)
    cpu_percent_min = Column(Float, nullable=True)
    cpu_percent_max = Column(Float, nullable=True)
    cpu_percent_avg = Column(Float, nullable=True)
    cpu_percent_p95 = Column(Float, nullable=True)
    cpu_percent_p99 = Column(Float, nullable=True)
    cpu_percent_stddev = Column(Float, nullable=True)

    # Memory metrics aggregations
    memory_percent_min = Column(Float, nullable=True)
    memory_percent_max = Column(Float, nullable=True)
    memory_percent_avg = Column(Float, nullable=True)
    memory_percent_p95 = Column(Float, nullable=True)
    memory_percent_p99 = Column(Float, nullable=True)
    memory_usage_bytes_avg = Column(BigInteger, nullable=True)
    memory_usage_bytes_max = Column(BigInteger, nullable=True)

    # Network metrics aggregations (rates and totals)
    network_rx_bytes_total = Column(BigInteger, nullable=True)
    network_tx_bytes_total = Column(BigInteger, nullable=True)
    network_rx_rate_avg = Column(Float, nullable=True)      # Bytes per second
    network_tx_rate_avg = Column(Float, nullable=True)
    network_rx_rate_max = Column(Float, nullable=True)
    network_tx_rate_max = Column(Float, nullable=True)

    # Disk I/O metrics aggregations
    disk_read_bytes_total = Column(BigInteger, nullable=True)
    disk_write_bytes_total = Column(BigInteger, nullable=True)
    disk_read_rate_avg = Column(Float, nullable=True)       # Bytes per second
    disk_write_rate_avg = Column(Float, nullable=True)
    disk_read_ops_total = Column(BigInteger, nullable=True)
    disk_write_ops_total = Column(BigInteger, nullable=True)

    # Performance indicators
    restart_count_total = Column(Integer, default=0, nullable=False)
    uptime_percentage = Column(Float, nullable=True)        # Percentage of period container was running

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ContainerBaseline(Base):
    """
    Container baseline model for storing performance baselines and thresholds.
    Used for anomaly detection and performance comparison.
    """

    __tablename__ = "container_baselines"

    id = Column(BigInteger, primary_key=True, index=True)
    container_id = Column(String(255), index=True, nullable=False)
    container_name = Column(String(255), index=True, nullable=True)

    # Baseline configuration
    baseline_type = Column(String(50), nullable=False)      # 'daily', 'weekly', 'monthly'
    baseline_period_days = Column(Integer, nullable=False)  # Number of days used for baseline
    confidence_level = Column(Float, default=0.95, nullable=False)  # Statistical confidence level

    # CPU baselines and thresholds
    cpu_percent_baseline = Column(Float, nullable=True)
    cpu_percent_lower_bound = Column(Float, nullable=True)
    cpu_percent_upper_bound = Column(Float, nullable=True)
    cpu_percent_anomaly_threshold = Column(Float, nullable=True)

    # Memory baselines and thresholds
    memory_percent_baseline = Column(Float, nullable=True)
    memory_percent_lower_bound = Column(Float, nullable=True)
    memory_percent_upper_bound = Column(Float, nullable=True)
    memory_percent_anomaly_threshold = Column(Float, nullable=True)

    # Network baselines and thresholds
    network_rx_rate_baseline = Column(Float, nullable=True)
    network_tx_rate_baseline = Column(Float, nullable=True)
    network_rx_rate_upper_bound = Column(Float, nullable=True)
    network_tx_rate_upper_bound = Column(Float, nullable=True)

    # Disk I/O baselines and thresholds
    disk_read_rate_baseline = Column(Float, nullable=True)
    disk_write_rate_baseline = Column(Float, nullable=True)
    disk_read_rate_upper_bound = Column(Float, nullable=True)
    disk_write_rate_upper_bound = Column(Float, nullable=True)

    # Baseline metadata
    last_calculated_at = Column(DateTime(timezone=True), nullable=False)
    next_calculation_at = Column(DateTime(timezone=True), nullable=True)
    calculation_status = Column(String(50), default='active', nullable=False)  # active, calculating, error

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MetricsRetentionPolicy(Base):
    """
    Metrics retention policy model for managing data lifecycle.
    Defines retention periods and cleanup schedules for different data types.
    """

    __tablename__ = "metrics_retention_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # Retention configuration
    raw_metrics_retention_days = Column(Integer, default=30, nullable=False)
    aggregated_hourly_retention_days = Column(Integer, default=90, nullable=False)
    aggregated_daily_retention_days = Column(Integer, default=365, nullable=False)
    aggregated_weekly_retention_days = Column(Integer, default=1095, nullable=False)  # 3 years

    # Cleanup configuration
    cleanup_enabled = Column(Boolean, default=True, nullable=False)
    cleanup_schedule_cron = Column(String(100), default='0 2 * * *', nullable=False)  # Daily at 2 AM
    last_cleanup_at = Column(DateTime(timezone=True), nullable=True)
    next_cleanup_at = Column(DateTime(timezone=True), nullable=True)

    # Policy status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MetricsAlert(Base):
    """Metrics alert model for threshold-based alerting."""

    __tablename__ = "metrics_alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    container_id = Column(String, index=True, nullable=False)
    container_name = Column(String, nullable=True)

    # Alert configuration
    metric_type = Column(String, nullable=False)  # MetricType enum
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String, nullable=False)  # ComparisonOperator enum

    # Alert state
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

    # Alert acknowledgment
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # User association
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])


class ContainerMetricsHistory(Base):
    """Container metrics history model for aggregated time-series data."""

    __tablename__ = "container_metrics_history"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, index=True, nullable=False)
    container_name = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    interval_minutes = Column(Integer, default=60, nullable=False)

    # Aggregated CPU metrics
    cpu_percent_avg = Column(Float, nullable=True)
    cpu_percent_min = Column(Float, nullable=True)
    cpu_percent_max = Column(Float, nullable=True)

    # Aggregated Memory metrics
    memory_percent_avg = Column(Float, nullable=True)
    memory_percent_min = Column(Float, nullable=True)
    memory_percent_max = Column(Float, nullable=True)
    memory_usage_avg = Column(BigInteger, nullable=True)
    memory_usage_min = Column(BigInteger, nullable=True)
    memory_usage_max = Column(BigInteger, nullable=True)

    # Aggregated Network metrics
    network_rx_bytes_avg = Column(BigInteger, nullable=True)
    network_rx_bytes_total = Column(BigInteger, nullable=True)
    network_tx_bytes_avg = Column(BigInteger, nullable=True)
    network_tx_bytes_total = Column(BigInteger, nullable=True)

    # Aggregated Disk I/O metrics
    block_read_bytes_avg = Column(BigInteger, nullable=True)
    block_read_bytes_total = Column(BigInteger, nullable=True)
    block_write_bytes_avg = Column(BigInteger, nullable=True)
    block_write_bytes_total = Column(BigInteger, nullable=True)

    # Metadata
    data_points_count = Column(Integer, default=1, nullable=False)
    health_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ContainerHealthScore(Base):
    """Container health score model for tracking health over time."""

    __tablename__ = "container_health_scores"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, index=True, nullable=False)
    container_name = Column(String, nullable=True)
    timestamp = Column(DateTime, index=True, nullable=False)

    # Overall health score (0-100)
    overall_health_score = Column(Float, nullable=False)
    health_status = Column(String, nullable=False)  # excellent, good, warning, critical

    # Component scores
    cpu_health_score = Column(Float, nullable=True)
    memory_health_score = Column(Float, nullable=True)
    network_health_score = Column(Float, nullable=True)
    disk_health_score = Column(Float, nullable=True)

    # Analysis metadata
    analysis_period_hours = Column(Integer, default=1, nullable=False)
    data_points_analyzed = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ContainerPrediction(Base):
    """Container prediction model for storing prediction results."""

    __tablename__ = "container_predictions"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, index=True, nullable=False)
    container_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Prediction metadata
    prediction_timestamp = Column(DateTime, index=True, nullable=False)
    prediction_hours = Column(Integer, default=6, nullable=False)
    analysis_period_hours = Column(Integer, default=24, nullable=False)

    # CPU predictions
    cpu_predicted_value = Column(Float, nullable=True)
    cpu_confidence = Column(Float, nullable=True)
    cpu_trend = Column(String, nullable=True)  # increasing, decreasing, stable

    # Memory predictions
    memory_predicted_value = Column(Float, nullable=True)
    memory_confidence = Column(Float, nullable=True)
    memory_trend = Column(String, nullable=True)  # increasing, decreasing, stable

    # Prediction accuracy (filled when actual data becomes available)
    cpu_actual_value = Column(Float, nullable=True)
    memory_actual_value = Column(Float, nullable=True)
    cpu_accuracy_score = Column(Float, nullable=True)
    memory_accuracy_score = Column(Float, nullable=True)

    # Status
    is_validated = Column(Boolean, default=False, nullable=False)


class TemplateStatus(str, Enum):
    """Template status enum for marketplace templates."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MarketplaceTemplate(Base):
    """Enhanced marketplace template model for storing community-contributed templates with Phase 5 features."""

    __tablename__ = "marketplace_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("template_categories.id"), nullable=False)
    version = Column(String, default="1.0.0", nullable=False)
    docker_compose_yaml = Column(Text, nullable=False)
    status = Column(String, default=TemplateStatus.PENDING, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    rating_avg = Column(Float, default=0.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    tags = Column(JSON, nullable=True)  # Array of tags as JSON

    # Enhanced metadata and categorization (Phase 5)
    subcategory = Column(String, nullable=True)
    difficulty_level = Column(String, default="intermediate", nullable=True)
    estimated_setup_time = Column(Integer, default=10, nullable=True)  # minutes
    resource_requirements = Column(JSON, nullable=True)

    # Performance and analytics integration (Phase 5)
    performance_score = Column(Float, default=0.0, nullable=True)
    deployment_success_rate = Column(Float, default=0.0, nullable=True)
    avg_deployment_time = Column(Integer, default=0, nullable=True)  # seconds
    last_performance_update = Column(DateTime, nullable=True)

    # Enhanced template metadata (Phase 5)
    template_size_mb = Column(Float, default=0.0, nullable=True)
    docker_image_count = Column(Integer, default=1, nullable=True)
    network_ports = Column(JSON, nullable=True)
    volume_mounts = Column(JSON, nullable=True)
    environment_variables = Column(JSON, nullable=True)

    # Security and validation (Phase 5)
    security_score = Column(Integer, default=0, nullable=True)
    last_security_scan = Column(DateTime, nullable=True)
    security_issues_count = Column(Integer, default=0, nullable=True)
    is_security_approved = Column(Boolean, default=False, nullable=True)

    # Usage analytics (Phase 5)
    unique_users_count = Column(Integer, default=0, nullable=True)
    deployment_count = Column(Integer, default=0, nullable=True)
    success_deployment_count = Column(Integer, default=0, nullable=True)
    last_deployed_at = Column(DateTime, nullable=True)

    # Template lifecycle management (Phase 5)
    is_featured = Column(Boolean, default=False, nullable=True)
    is_deprecated = Column(Boolean, default=False, nullable=True)
    deprecation_reason = Column(Text, nullable=True)
    replacement_template_id = Column(Integer, nullable=True)

    # Enhanced search and discovery (Phase 5)
    search_keywords = Column(Text, nullable=True)
    compatibility_tags = Column(JSON, nullable=True)
    minimum_docker_version = Column(String, nullable=True)
    supported_architectures = Column(JSON, default=["amd64"], nullable=True)

    # Approval metadata
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    author = relationship("User", foreign_keys=[author_id], back_populates="authored_templates")
    approver = relationship("User", foreign_keys=[approved_by])
    category = relationship("TemplateCategory", back_populates="templates")
    reviews = relationship("TemplateReview", back_populates="template", cascade="all, delete-orphan")
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")


class TemplateCategory(Base):
    """Enhanced template category model for organizing marketplace templates."""

    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # Icon name or URL
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Enhanced categorization (Phase 5)
    subcategories = Column(Text, nullable=True)  # Comma-separated subcategories

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    templates = relationship("MarketplaceTemplate", back_populates="category")


class TemplateAnalytics(Base):
    """Template analytics model for performance metrics correlation with Phase 4 data."""

    __tablename__ = "template_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("marketplace_templates.id"), nullable=False)
    container_id = Column(String(255), nullable=True)
    deployment_id = Column(String(255), nullable=True)

    # Performance metrics correlation with Phase 4 data
    avg_cpu_usage = Column(Float, nullable=True)
    avg_memory_usage = Column(Float, nullable=True)
    avg_network_io = Column(Float, nullable=True)
    avg_disk_io = Column(Float, nullable=True)
    performance_score = Column(Float, default=0.0, nullable=True)

    # Deployment analytics
    deployment_duration_seconds = Column(Integer, nullable=True)
    startup_time_seconds = Column(Integer, nullable=True)
    first_response_time_ms = Column(Integer, nullable=True)
    deployment_success = Column(Boolean, default=True, nullable=True)
    error_message = Column(Text, nullable=True)

    # Resource utilization
    peak_cpu_usage = Column(Float, nullable=True)
    peak_memory_usage = Column(Float, nullable=True)
    resource_efficiency_score = Column(Float, default=0.0, nullable=True)

    # User experience metrics
    user_satisfaction_score = Column(Integer, nullable=True)  # 1-5 scale
    user_feedback = Column(Text, nullable=True)

    # Timestamps and metadata
    deployment_started_at = Column(DateTime, nullable=False)
    deployment_completed_at = Column(DateTime, nullable=True)
    analysis_period_hours = Column(Integer, default=24, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("MarketplaceTemplate")


class TemplateSecurityScan(Base):
    """Template security scans model for automated security validation."""

    __tablename__ = "template_security_scans"

    id = Column(BigInteger, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("marketplace_templates.id"), nullable=False)
    template_version_id = Column(Integer, ForeignKey("template_versions.id"), nullable=True)
    scan_type = Column(String(50), default="automated", nullable=False)

    # Security scan results
    overall_security_score = Column(Integer, default=0, nullable=True)
    vulnerability_count_critical = Column(Integer, default=0, nullable=True)
    vulnerability_count_high = Column(Integer, default=0, nullable=True)
    vulnerability_count_medium = Column(Integer, default=0, nullable=True)
    vulnerability_count_low = Column(Integer, default=0, nullable=True)

    # Docker security checks
    dockerfile_security_score = Column(Integer, default=0, nullable=True)
    compose_security_score = Column(Integer, default=0, nullable=True)
    image_security_score = Column(Integer, default=0, nullable=True)

    # Specific security issues
    uses_root_user = Column(Boolean, default=False, nullable=True)
    exposes_privileged_ports = Column(Boolean, default=False, nullable=True)
    has_secrets_in_config = Column(Boolean, default=False, nullable=True)
    uses_latest_tags = Column(Boolean, default=False, nullable=True)
    missing_health_checks = Column(Boolean, default=False, nullable=True)

    # Scan metadata
    scan_engine = Column(String(100), default="internal", nullable=True)
    scan_version = Column(String(50), nullable=True)
    scan_duration_seconds = Column(Integer, nullable=True)
    scan_status = Column(String(50), default="completed", nullable=True)
    scan_error_message = Column(Text, nullable=True)

    # Detailed results
    vulnerability_details = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    compliance_status = Column(JSON, nullable=True)

    # Timestamps
    scan_started_at = Column(DateTime, nullable=False)
    scan_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("MarketplaceTemplate")
    template_version = relationship("TemplateVersion")


class TemplateReview(Base):
    """Template review model for user ratings and comments."""

    __tablename__ = "template_reviews"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("marketplace_templates.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("MarketplaceTemplate", back_populates="reviews")
    user = relationship("User", back_populates="template_reviews")

    # Constraints: One review per user per template
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class TemplateDeploymentHistory(Base):
    """Template deployment history model for tracking template usage."""

    __tablename__ = "template_deployment_history"

    id = Column(BigInteger, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("marketplace_templates.id"), nullable=False)
    template_version_id = Column(Integer, ForeignKey("template_versions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deployment_id = Column(String(255), unique=True, nullable=False)

    # Deployment details
    deployment_name = Column(String(255), nullable=False)
    deployment_environment = Column(String(50), default="development", nullable=True)
    deployment_status = Column(String(50), default="pending", nullable=True)

    # Configuration and customization
    custom_configuration = Column(JSON, nullable=True)
    environment_overrides = Column(JSON, nullable=True)
    resource_limits = Column(JSON, nullable=True)

    # Deployment timeline
    deployment_requested_at = Column(DateTime, nullable=False)
    deployment_started_at = Column(DateTime, nullable=True)
    deployment_completed_at = Column(DateTime, nullable=True)
    deployment_failed_at = Column(DateTime, nullable=True)
    deployment_duration_seconds = Column(Integer, nullable=True)

    # Results and feedback
    deployment_success = Column(Boolean, default=False, nullable=True)
    error_message = Column(Text, nullable=True)
    user_notes = Column(Text, nullable=True)
    user_rating = Column(Integer, nullable=True)  # 1-5 scale

    # Resource usage tracking
    containers_created = Column(Integer, default=0, nullable=True)
    networks_created = Column(Integer, default=0, nullable=True)
    volumes_created = Column(Integer, default=0, nullable=True)

    # Integration with Phase 4 metrics
    metrics_collection_enabled = Column(Boolean, default=True, nullable=True)
    performance_monitoring_duration_hours = Column(Integer, default=24, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("MarketplaceTemplate")
    template_version = relationship("TemplateVersion")
    user = relationship("User")


class TemplatePerformanceMetrics(Base):
    """Template performance metrics model for template-specific performance data."""

    __tablename__ = "template_performance_metrics"

    id = Column(BigInteger, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("marketplace_templates.id"), nullable=False)
    deployment_id = Column(String(255), nullable=True)

    # Performance aggregation period
    aggregation_period = Column(String(20), default="daily", nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Template-level performance metrics
    avg_startup_time_seconds = Column(Float, nullable=True)
    avg_response_time_ms = Column(Float, nullable=True)
    success_rate_percentage = Column(Float, default=100.0, nullable=True)
    error_rate_percentage = Column(Float, default=0.0, nullable=True)

    # Resource efficiency metrics
    avg_cpu_efficiency = Column(Float, nullable=True)
    avg_memory_efficiency = Column(Float, nullable=True)
    avg_network_efficiency = Column(Float, nullable=True)
    avg_disk_efficiency = Column(Float, nullable=True)
    overall_efficiency_score = Column(Float, default=0.0, nullable=True)

    # Deployment success metrics
    total_deployments = Column(Integer, default=0, nullable=True)
    successful_deployments = Column(Integer, default=0, nullable=True)
    failed_deployments = Column(Integer, default=0, nullable=True)
    avg_deployment_duration_seconds = Column(Float, nullable=True)

    # User satisfaction metrics
    avg_user_rating = Column(Float, default=0.0, nullable=True)
    total_user_ratings = Column(Integer, default=0, nullable=True)
    user_satisfaction_score = Column(Float, default=0.0, nullable=True)

    # Performance trends
    performance_trend = Column(String(20), nullable=True)
    efficiency_trend = Column(String(20), nullable=True)
    reliability_trend = Column(String(20), nullable=True)

    # Comparison with similar templates
    performance_percentile = Column(Integer, nullable=True)
    efficiency_percentile = Column(Integer, nullable=True)
    popularity_percentile = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("MarketplaceTemplate")


class TemplateMarketplaceCache(Base):
    """Template marketplace cache model for Redis-like caching in database."""

    __tablename__ = "template_marketplace_cache"

    id = Column(BigInteger, primary_key=True, index=True)
    cache_key = Column(String(512), unique=True, nullable=False)
    cache_value = Column(JSON, nullable=False)
    cache_type = Column(String(50), default="search_result", nullable=False)

    # Cache metadata
    cache_size_bytes = Column(Integer, default=0, nullable=True)
    hit_count = Column(Integer, default=0, nullable=True)
    last_hit_at = Column(DateTime, nullable=True)

    # TTL and expiration
    ttl_seconds = Column(Integer, default=3600, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=True)

    # Cache tags for invalidation
    cache_tags = Column(JSON, nullable=True)
    template_ids = Column(JSON, nullable=True)
    category_ids = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TemplateVersion(Base):
    """Template version model for storing version history of marketplace templates."""

    __tablename__ = "template_versions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("marketplace_templates.id"), nullable=False)
    version_number = Column(String, nullable=False)
    docker_compose_yaml = Column(Text, nullable=False)
    changelog = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("MarketplaceTemplate", back_populates="versions")
