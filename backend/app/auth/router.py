"""
Authentication router for FastAPI.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.auth.models import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    Token,
    User,
    UserCreate,
    UserManagement,
    UserUpdate,
    UserUpdateAdmin,
)
from app.db.database import get_db
from app.db.models import PasswordResetToken, Token as TokenModel
from app.db.models import User as UserModel, UserRole

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.

    Args:
        user_in: User creation data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username already exists
    user = db.query(UserModel).filter(UserModel.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    db_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """
    Login and get access token.

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If login credentials are invalid
    """
    # Get user by username or email
    user = db.query(UserModel).filter(
        (UserModel.username == login_data.username) |
        (UserModel.email == login_data.username)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    # Create refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=refresh_token_expires,
    )

    # Store refresh token in database
    token_expires = datetime.utcnow() + refresh_token_expires
    db_token = TokenModel(
        token=refresh_token,
        user_id=user.id,
        expires_at=token_expires,
    )
    db.add(db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_data: RefreshRequest, db: Session = Depends(get_db)) -> Any:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    try:
        payload = decode_token(refresh_data.refresh_token)

        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user ID from token
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token exists in database
        db_token = (
            db.query(TokenModel)
            .filter(
                TokenModel.token == refresh_data.refresh_token,
                TokenModel.user_id == user_id,
                TokenModel.is_revoked == False,
            )
            .first()
        )
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires,
        )

        # Create new refresh token
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=refresh_token_expires,
        )

        # Revoke old refresh token
        db_token.is_revoked = True

        # Store new refresh token in database
        token_expires = datetime.utcnow() + refresh_token_expires
        new_db_token = TokenModel(
            token=new_refresh_token,
            user_id=user.id,
            expires_at=token_expires,
        )
        db.add(new_db_token)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
def logout(
    refresh_data: RefreshRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Logout and revoke refresh token.

    Args:
        refresh_data: Refresh token data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Find token in database
    db_token = (
        db.query(TokenModel)
        .filter(
            TokenModel.token == refresh_data.refresh_token,
            TokenModel.user_id == current_user.id,
            TokenModel.is_revoked == False,
        )
        .first()
    )

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already revoked token",
        )

    # Revoke token
    db_token.is_revoked = True
    db.commit()

    return {"detail": "Successfully logged out"}


@router.post("/password-reset-request")
def request_password_reset(
    reset_request: PasswordResetRequest, db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset.

    Args:
        reset_request: Password reset request data
        db: Database session

    Returns:
        Success message
    """
    # Find user by email
    user = db.query(UserModel).filter(UserModel.email == reset_request.email).first()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)

    # Set expiration time (1 hour from now)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Invalidate any existing reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False
    ).update({"is_used": True})

    # Create new reset token
    db_reset_token = PasswordResetToken(
        token=reset_token,
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(db_reset_token)
    db.commit()

    # TODO: Send email with reset link
    # For now, we'll just log the token (remove in production)
    print(f"Password reset token for {user.email}: {reset_token}")

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset-confirm")
def confirm_password_reset(
    reset_confirm: PasswordResetConfirm, db: Session = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token.

    Args:
        reset_confirm: Password reset confirmation data
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Find reset token
    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == reset_confirm.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    user = db.query(UserModel).filter(UserModel.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update user password
    user.hashed_password = get_password_hash(reset_confirm.new_password)

    # Mark token as used
    reset_token.is_used = True

    db.commit()

    return {"message": "Password has been reset successfully"}


@router.get("/me", response_model=User)
def read_users_me(current_user: UserModel = Depends(get_current_user)) -> Any:
    """
    Get current user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user data
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update current user.

    Args:
        user_in: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    if user_in.email and user_in.email != current_user.email:
        user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Update user
    if user_in.email:
        current_user.email = user_in.email
    if user_in.full_name:
        current_user.full_name = user_in.full_name
    if user_in.password:
        current_user.hashed_password = get_password_hash(user_in.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user
