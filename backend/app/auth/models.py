"""
Authentication models for request and response validation.
"""

import html
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user model."""

    username: str
    email: EmailStr
    full_name: Optional[str] = None

    @validator("username")
    def sanitize_username(cls, v):
        """Sanitize username to prevent XSS."""
        if v:
            # Remove HTML tags and escape special characters
            sanitized = html.escape(v.strip())
            # Remove script tags and other dangerous patterns
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>.*?</embed>'
            ]
            for pattern in dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            return sanitized
        return v

    @validator("full_name")
    def sanitize_full_name(cls, v):
        """Sanitize full name to prevent XSS."""
        if v:
            # Remove HTML tags and escape special characters
            sanitized = html.escape(v.strip())
            # Remove script tags and other dangerous patterns
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>.*?</embed>'
            ]
            for pattern in dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            return sanitized
        return v


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8)

    @validator("username", pre=True)
    def sanitize_username_create(cls, v):
        """Sanitize username to prevent XSS."""
        if v:
            # Remove HTML tags and escape special characters
            sanitized = html.escape(str(v).strip())
            # Remove script tags and other dangerous patterns
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>.*?</embed>'
            ]
            for pattern in dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            # Also reject if it still contains dangerous characters
            if '<' in sanitized or '>' in sanitized or 'javascript:' in sanitized.lower():
                raise ValueError("Username contains invalid characters")
            return sanitized
        return v

    @validator("full_name", pre=True)
    def sanitize_full_name_create(cls, v):
        """Sanitize full name to prevent XSS."""
        if v:
            # Remove HTML tags and escape special characters
            sanitized = html.escape(str(v).strip())
            # Remove script tags and other dangerous patterns
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>.*?</embed>'
            ]
            for pattern in dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            # Also reject if it still contains dangerous characters
            if '<' in sanitized or '>' in sanitized or 'javascript:' in sanitized.lower():
                raise ValueError("Full name contains invalid characters")
            return sanitized
        return v

    @validator("password")
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserInDB(UserBase):
    """User model as stored in the database."""

    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        orm_mode = True


class User(UserBase):
    """User model for API responses."""

    id: int
    role: str
    is_active: bool
    is_email_verified: bool

    class Config:
        """Pydantic config."""

        orm_mode = True


class Token(BaseModel):
    """Token model for API responses."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload model."""

    sub: Optional[int] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class TokenData(BaseModel):
    """Token data model."""

    user_id: int
    username: str
    role: str


class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=1, description="User password")

    @validator("username")
    def validate_username_or_email(cls, v):
        """Validate that username is not empty."""
        if not v or not v.strip():
            raise ValueError("Username or email is required")
        return v.strip()


class RefreshRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: EmailStr = Field(..., description="Email address to send reset link to")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator("new_password")
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request model."""

    email: EmailStr = Field(
        ..., description="Email address to send verification link to"
    )


class EmailVerificationConfirm(BaseModel):
    """Email verification confirmation model."""

    token: str = Field(..., description="Email verification token")


class UserManagement(BaseModel):
    """User management model for admin operations."""

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        orm_mode = True


class UserUpdateAdmin(BaseModel):
    """User update model for admin operations."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
