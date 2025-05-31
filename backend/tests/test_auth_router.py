"""
Comprehensive tests for the authentication router.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, create_refresh_token, get_password_hash
from app.db.database import get_db
from app.db.models import EmailVerificationToken, PasswordResetToken
from app.db.models import Token as TokenModel
from app.db.models import User as UserModel
from app.main import app
from tests.conftest import TestingSessionLocal, override_get_db

# Override the get_db dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestAuthRouter:
    """Test suite for authentication router endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.db = TestingSessionLocal()

        # Create test user
        self.test_user = UserModel(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            full_name="Test User",
            is_email_verified=True,
            is_active=True,
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)

    def teardown_method(self):
        """Clean up test data."""
        self.db.query(TokenModel).delete()
        self.db.query(PasswordResetToken).delete()
        self.db.query(EmailVerificationToken).delete()
        self.db.query(UserModel).delete()
        self.db.commit()
        self.db.close()

    @patch("app.auth.router._send_email_verification")
    def test_register_user_success(self, mock_send_email):
        """Test successful user registration."""
        mock_send_email.return_value = None

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewPassword123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_email_verified"] is False
        mock_send_email.assert_called_once()

    def test_register_user_duplicate_username(self):
        """Test registration with duplicate username."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "NewPassword123",
                "full_name": "Different User",
            },
        )

        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        response = client.post(
            "/auth/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",  # Already exists
                "password": "NewPassword123",
                "full_name": "Different User",
            },
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_login_with_username_success(self):
        """Test successful login with username."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_email_success(self):
        """Test successful login with email."""
        response = client.post(
            "/auth/login",
            json={
                "username": "test@example.com",  # Using email as username
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self):
        """Test login with invalid username."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 401
        assert "Invalid username/email or password" in response.json()["detail"]

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Invalid username/email or password" in response.json()["detail"]

    def test_login_inactive_user(self):
        """Test login with inactive user."""
        # Make user inactive
        self.test_user.is_active = False
        self.db.commit()

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 401
        assert "Inactive user" in response.json()["detail"]

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Verify the refresh token exists in database
        db_token = (
            self.db.query(TokenModel)
            .filter(
                TokenModel.token == tokens["refresh_token"],
                TokenModel.user_id == self.test_user.id,
            )
            .first()
        )
        assert db_token is not None, "Refresh token should be stored in database"

        # Use refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # Should get new tokens
        assert data["access_token"] != tokens["access_token"]
        assert data["refresh_token"] != tokens["refresh_token"]

    def test_refresh_token_invalid(self):
        """Test refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401
        # The actual error message may vary, just check it's an auth error
        assert (
            "Invalid token" in response.json()["detail"]
            or "Could not validate credentials" in response.json()["detail"]
        )

    def test_refresh_token_wrong_type(self):
        """Test refresh with access token instead of refresh token."""
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(self.test_user.id),
                "username": self.test_user.username,
                "role": self.test_user.role,
            }
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]

    def test_refresh_token_revoked(self):
        """Test refresh with revoked token."""
        # Create and store refresh token
        refresh_token = create_refresh_token(
            data={
                "sub": str(self.test_user.id),
                "username": self.test_user.username,
                "role": self.test_user.role,
            }
        )

        db_token = TokenModel(
            token=refresh_token,
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=True,  # Already revoked
        )
        self.db.add(db_token)
        self.db.commit()

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert "Invalid or revoked token" in response.json()["detail"]

    def test_logout_success(self):
        """Test successful logout."""
        # First login to get tokens
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        tokens = login_response.json()

        # Logout
        response = client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["detail"]

    def test_logout_invalid_token(self):
        """Test logout with invalid refresh token."""
        # Get access token for authentication
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        tokens = login_response.json()

        response = client.post(
            "/auth/logout",
            json={"refresh_token": "invalid_token"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert response.status_code == 400
        assert "Invalid or already revoked token" in response.json()["detail"]

    def test_get_current_user_success(self):
        """Test getting current user information."""
        # Login to get access token
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        tokens = login_response.json()

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"

    def test_get_current_user_unauthorized(self):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_update_user_success(self):
        """Test successful user update."""
        # Login to get access token
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        tokens = login_response.json()

        response = client.put(
            "/auth/me",
            json={
                "email": "updated@example.com",
                "full_name": "Updated User",
            },
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["full_name"] == "Updated User"

    def test_update_user_duplicate_email(self):
        """Test user update with duplicate email."""
        # Create another user
        other_user = UserModel(
            username="otheruser",
            email="other@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Other User",
        )
        self.db.add(other_user)
        self.db.commit()

        # Login to get access token
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        tokens = login_response.json()

        response = client.put(
            "/auth/me",
            json={"email": "other@example.com"},  # Already exists
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @patch("app.auth.router._send_password_reset_email")
    def test_password_reset_request_success(self, mock_send_email):
        """Test successful password reset request."""
        mock_send_email.return_value = None

        response = client.post(
            "/auth/password-reset-request",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]
        mock_send_email.assert_called_once()

    def test_password_reset_request_nonexistent_email(self):
        """Test password reset request for non-existent email."""
        response = client.post(
            "/auth/password-reset-request",
            json={"email": "nonexistent@example.com"},
        )

        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]

    def test_password_reset_confirm_success(self):
        """Test successful password reset confirmation."""
        # Create reset token
        reset_token = PasswordResetToken(
            token="valid_reset_token",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False,
        )
        self.db.add(reset_token)
        self.db.commit()

        response = client.post(
            "/auth/password-reset-confirm",
            json={
                "token": "valid_reset_token",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"]

        # Verify token is marked as used
        self.db.refresh(reset_token)
        assert reset_token.is_used is True

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset confirmation with invalid token."""
        response = client.post(
            "/auth/password-reset-confirm",
            json={
                "token": "invalid_token",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_password_reset_confirm_expired_token(self):
        """Test password reset confirmation with expired token."""
        # Create expired token
        reset_token = PasswordResetToken(
            token="expired_reset_token",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_used=False,
        )
        self.db.add(reset_token)
        self.db.commit()

        response = client.post(
            "/auth/password-reset-confirm",
            json={
                "token": "expired_reset_token",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_password_reset_confirm_used_token(self):
        """Test password reset confirmation with already used token."""
        # Create used token
        reset_token = PasswordResetToken(
            token="used_reset_token",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=True,  # Already used
        )
        self.db.add(reset_token)
        self.db.commit()

        response = client.post(
            "/auth/password-reset-confirm",
            json={
                "token": "used_reset_token",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]
