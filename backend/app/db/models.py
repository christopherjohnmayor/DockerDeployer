"""
Database models for the DockerDeployer application.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Float, BigInteger
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
    user = relationship("User")
