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
    """Container metrics model for storing historical performance data."""

    __tablename__ = "container_metrics"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, index=True, nullable=False)
    container_name = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # CPU metrics
    cpu_percent = Column(Float, nullable=True)

    # Memory metrics (in bytes)
    memory_usage = Column(BigInteger, nullable=True)
    memory_limit = Column(BigInteger, nullable=True)
    memory_percent = Column(Float, nullable=True)

    # Network metrics (in bytes)
    network_rx_bytes = Column(BigInteger, nullable=True)
    network_tx_bytes = Column(BigInteger, nullable=True)

    # Block I/O metrics (in bytes)
    block_read_bytes = Column(BigInteger, nullable=True)
    block_write_bytes = Column(BigInteger, nullable=True)

    # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)


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
    """Marketplace template model for storing community-contributed templates."""

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
    """Template category model for organizing marketplace templates."""

    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # Icon name or URL
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    templates = relationship("MarketplaceTemplate", back_populates="category")


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
