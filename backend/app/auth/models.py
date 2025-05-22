"""
Authentication models for request and response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user model."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8)
    
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
    username: str
    password: str


class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str
