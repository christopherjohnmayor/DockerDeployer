"""
Comprehensive tests for the authentication router.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

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

    # XSS Validation Tests
    def test_register_user_xss_script_tag(self):
        """Test registration with XSS script tag in username."""
        response = client.post(
            "/auth/register",
            json={
                "username": "validuser",  # Use valid username
                "email": "xss@example.com",
                "password": "TestPassword123",  # Valid password with uppercase and digit
                "full_name": "<script>alert('xss')</script>",  # XSS in full_name
            },
        )
        # Should get 400 due to XSS validation, not 422 due to Pydantic
        assert response.status_code == 400
        assert "contains invalid characters" in response.json()["detail"]

    def test_register_user_xss_javascript_protocol(self):
        """Test registration with JavaScript protocol in full name."""
        response = client.post(
            "/auth/register",
            json={
                "username": "xssuser",
                "email": "xss2@example.com",
                "password": "TestPassword123",  # Valid password with uppercase and digit
                "full_name": "javascript:alert('xss')",
            },
        )
        assert response.status_code == 400
        assert "contains invalid characters" in response.json()["detail"]

    def test_register_user_xss_html_entities(self):
        """Test registration with HTML entities in username."""
        response = client.post(
            "/auth/register",
            json={
                "username": "test&lt;script&gt;user",  # HTML entities in username
                "email": "entity@example.com",
                "password": "TestPassword123",  # Valid password with uppercase and digit
                "full_name": "Entity User",
            },
        )
        assert response.status_code == 400
        assert "contains invalid characters" in response.json()["detail"]

    def test_register_user_xss_html_tags(self):
        """Test registration with HTML tags in username."""
        response = client.post(
            "/auth/register",
            json={
                "username": "user<div>test</div>",
                "email": "htmltag@example.com",
                "password": "TestPassword123",  # Valid password with uppercase and digit
                "full_name": "HTML User",
            },
        )
        assert response.status_code == 400
        assert "contains invalid characters" in response.json()["detail"]

    @patch("app.auth.router._send_email_verification")
    def test_register_user_xss_empty_input(self, mock_send_email):
        """Test XSS validation with empty input (should pass)."""
        mock_send_email.return_value = None

        response = client.post(
            "/auth/register",
            json={
                "username": "emptytest",
                "email": "empty@example.com",
                "password": "TestPassword123",  # Valid password with uppercase and digit
                "full_name": "",  # Empty full name should be allowed
            },
        )
        assert response.status_code == 201

    # Refresh Token Edge Cases
    def test_refresh_token_missing_sub(self):
        """Test refresh token with missing sub field."""
        # Create token without sub field
        import jwt
        from app.auth.jwt import SECRET_KEY, ALGORITHM

        invalid_token = jwt.encode(
            {"username": "testuser", "type": "refresh"},
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": invalid_token},
        )

        assert response.status_code == 401
        assert "Invalid token payload" in response.json()["detail"]

    def test_refresh_token_inactive_user(self):
        """Test refresh token with inactive user."""
        # Create refresh token
        refresh_token = create_refresh_token(
            data={
                "sub": str(self.test_user.id),
                "username": self.test_user.username,
                "role": self.test_user.role,
            }
        )

        # Store token in database
        db_token = TokenModel(
            token=refresh_token,
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        self.db.add(db_token)

        # Make user inactive
        self.test_user.is_active = False
        self.db.commit()

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert "User not found or inactive" in response.json()["detail"]

    def test_refresh_token_general_exception(self):
        """Test refresh token with general exception handling."""
        # Use a completely malformed token to trigger general exception
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "completely.malformed.token"},
        )

        assert response.status_code == 401
        # The error message could be either depending on which validation fails first
        assert ("Could not validate credentials" in response.json()["detail"] or
                "Invalid token" in response.json()["detail"])

    # Password Reset Edge Cases
    def test_password_reset_confirm_user_not_found(self):
        """Test password reset confirmation when user is deleted."""
        # Create reset token
        reset_token = PasswordResetToken(
            token="orphaned_token",
            user_id=99999,  # Non-existent user ID
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False,
        )
        self.db.add(reset_token)
        self.db.commit()

        response = client.post(
            "/auth/password-reset-confirm",
            json={
                "token": "orphaned_token",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]

    # User Update Edge Cases
    def test_update_user_password_only(self):
        """Test updating user password only."""
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
            json={"password": "NewPassword789"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert response.status_code == 200

        # Verify password was updated by trying to login with new password
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "NewPassword789",
            },
        )
        assert login_response.status_code == 200

    # Email Verification Tests
    @patch("app.auth.router._send_email_verification")
    def test_email_verification_request_success(self, mock_send_email):
        """Test successful email verification request."""
        # Create unverified user
        unverified_user = UserModel(
            username="unverified",
            email="unverified@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Unverified User",
            is_email_verified=False,
        )
        self.db.add(unverified_user)
        self.db.commit()

        mock_send_email.return_value = None

        response = client.post(
            "/auth/email-verification-request",
            json={"email": "unverified@example.com"},
        )

        assert response.status_code == 200
        assert "verification link has been sent" in response.json()["message"]
        mock_send_email.assert_called_once()

    def test_email_verification_request_nonexistent_email(self):
        """Test email verification request for non-existent email."""
        response = client.post(
            "/auth/email-verification-request",
            json={"email": "nonexistent@example.com"},
        )

        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "verification link has been sent" in response.json()["message"]

    def test_email_verification_request_already_verified(self):
        """Test email verification request for already verified email."""
        response = client.post(
            "/auth/email-verification-request",
            json={"email": "test@example.com"},  # test_user is already verified
        )

        assert response.status_code == 400
        assert "already verified" in response.json()["detail"]

    @patch("app.auth.router._send_welcome_email")
    def test_email_verification_confirm_success(self, mock_send_welcome):
        """Test successful email verification confirmation."""
        # Create unverified user
        unverified_user = UserModel(
            username="unverified2",
            email="unverified2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Unverified User 2",
            is_email_verified=False,
        )
        self.db.add(unverified_user)
        self.db.commit()
        self.db.refresh(unverified_user)

        # Create verification token
        verification_token = EmailVerificationToken(
            token="valid_verification_token",
            user_id=unverified_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_used=False,
        )
        self.db.add(verification_token)
        self.db.commit()

        mock_send_welcome.return_value = None

        response = client.post(
            "/auth/email-verification-confirm",
            json={"token": "valid_verification_token"},
        )

        assert response.status_code == 200
        assert "verified successfully" in response.json()["message"]

        # Verify user is now verified
        self.db.refresh(unverified_user)
        assert unverified_user.is_email_verified is True

        # Verify token is marked as used
        self.db.refresh(verification_token)
        assert verification_token.is_used is True

        mock_send_welcome.assert_called_once()

    def test_email_verification_confirm_invalid_token(self):
        """Test email verification confirmation with invalid token."""
        response = client.post(
            "/auth/email-verification-confirm",
            json={"token": "invalid_verification_token"},
        )

        assert response.status_code == 400
        assert "Invalid or expired verification token" in response.json()["detail"]

    def test_email_verification_confirm_expired_token(self):
        """Test email verification confirmation with expired token."""
        # Create expired verification token
        verification_token = EmailVerificationToken(
            token="expired_verification_token",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_used=False,
        )
        self.db.add(verification_token)
        self.db.commit()

        response = client.post(
            "/auth/email-verification-confirm",
            json={"token": "expired_verification_token"},
        )

        assert response.status_code == 400
        assert "Invalid or expired verification token" in response.json()["detail"]


class TestAuthHelperFunctions:
    """Test suite for authentication helper functions."""

    def setup_method(self):
        """Set up test data."""
        self.db = TestingSessionLocal()

        # Create test user
        self.test_user = UserModel(
            username="helpertest",
            email="helper@example.com",
            hashed_password=get_password_hash("testpassword123"),
            full_name="Helper Test User",
            is_email_verified=False,
            is_active=True,
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)

    def teardown_method(self):
        """Clean up test data."""
        self.db.query(EmailVerificationToken).delete()
        self.db.query(PasswordResetToken).delete()
        self.db.query(UserModel).delete()
        self.db.commit()
        self.db.close()

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    @patch("app.auth.router.email_templates.render_template")
    async def test_send_email_verification_success(self, mock_render, mock_get_service):
        """Test successful email verification sending."""
        from app.auth.router import _send_email_verification

        # Mock email service
        mock_email_service = AsyncMock()
        mock_email_service.is_configured.return_value = True
        mock_email_service.send_email.return_value = True
        mock_get_service.return_value = mock_email_service

        # Mock template rendering
        mock_render.return_value = ("<html>Test</html>", "Test text")

        # Call function
        await _send_email_verification(self.test_user, self.db)

        # Verify email service was called
        mock_email_service.send_email.assert_called_once()
        mock_render.assert_called_once()

        # Verify verification token was created
        token = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == self.test_user.id
        ).first()
        assert token is not None
        assert not token.is_used

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    async def test_send_email_verification_service_not_configured(self, mock_get_service):
        """Test email verification when service is not configured."""
        from app.auth.router import _send_email_verification

        # Mock unconfigured email service - use MagicMock for sync methods
        mock_email_service = MagicMock()
        mock_email_service.is_configured.return_value = False  # Sync method
        mock_email_service.send_email = AsyncMock()  # Async method
        mock_get_service.return_value = mock_email_service

        # Call function (should not raise exception)
        await _send_email_verification(self.test_user, self.db)

        # Verify email was not sent
        mock_email_service.send_email.assert_not_called()

        # Verify token was still created
        token = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == self.test_user.id
        ).first()
        assert token is not None

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    @patch("app.auth.router.email_templates.render_template")
    async def test_send_email_verification_timeout(self, mock_render, mock_get_service):
        """Test email verification with timeout."""
        from app.auth.router import _send_email_verification
        import asyncio

        # Mock email service with timeout
        mock_email_service = AsyncMock()
        mock_email_service.is_configured.return_value = True
        mock_email_service.send_email.side_effect = asyncio.TimeoutError()
        mock_get_service.return_value = mock_email_service

        # Mock template rendering
        mock_render.return_value = ("<html>Test</html>", "Test text")

        # Call function (should handle timeout gracefully)
        await _send_email_verification(self.test_user, self.db)

        # Verify token was still created despite timeout
        token = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == self.test_user.id
        ).first()
        assert token is not None

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    async def test_send_email_verification_exception(self, mock_get_service):
        """Test email verification with general exception."""
        from app.auth.router import _send_email_verification

        # Mock email service that raises exception
        mock_get_service.side_effect = Exception("Email service error")

        # Call function (should handle exception gracefully)
        await _send_email_verification(self.test_user, self.db)

        # Function should complete without raising exception
        # (Exception is caught and logged)

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    @patch("app.auth.router.email_templates.render_template")
    async def test_send_password_reset_email_success(self, mock_render, mock_get_service):
        """Test successful password reset email sending."""
        from app.auth.router import _send_password_reset_email

        # Mock email service
        mock_email_service = AsyncMock()
        mock_email_service.is_configured.return_value = True
        mock_email_service.send_email.return_value = True
        mock_get_service.return_value = mock_email_service

        # Mock template rendering
        mock_render.return_value = ("<html>Reset</html>", "Reset text")

        # Call function
        await _send_password_reset_email(self.test_user, "test_reset_token")

        # Verify email service was called
        mock_email_service.send_email.assert_called_once()
        mock_render.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    async def test_send_password_reset_email_not_configured(self, mock_get_service):
        """Test password reset email when service is not configured."""
        from app.auth.router import _send_password_reset_email

        # Mock unconfigured email service - use MagicMock for sync methods
        mock_email_service = MagicMock()
        mock_email_service.is_configured.return_value = False  # Sync method
        mock_email_service.send_email = AsyncMock()  # Async method
        mock_get_service.return_value = mock_email_service

        # Call function (should not raise exception)
        await _send_password_reset_email(self.test_user, "test_reset_token")

        # Verify email was not sent
        mock_email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    @patch("app.auth.router.email_templates.render_template")
    async def test_send_password_reset_email_send_failure(self, mock_render, mock_get_service):
        """Test password reset email when sending fails."""
        from app.auth.router import _send_password_reset_email

        # Mock email service that fails to send
        mock_email_service = AsyncMock()
        mock_email_service.is_configured.return_value = True
        mock_email_service.send_email.return_value = False  # Send failed
        mock_get_service.return_value = mock_email_service

        # Mock template rendering
        mock_render.return_value = ("<html>Reset</html>", "Reset text")

        # Call function (should handle failure gracefully)
        await _send_password_reset_email(self.test_user, "test_reset_token")

        # Verify email service was called
        mock_email_service.send_email.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    async def test_send_password_reset_email_exception(self, mock_get_service):
        """Test password reset email with exception."""
        from app.auth.router import _send_password_reset_email

        # Mock email service that raises exception
        mock_get_service.side_effect = Exception("Email service error")

        # Call function (should handle exception gracefully)
        await _send_password_reset_email(self.test_user, "test_reset_token")

        # Function should complete without raising exception

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    @patch("app.auth.router.email_templates.render_template")
    async def test_send_welcome_email_success(self, mock_render, mock_get_service):
        """Test successful welcome email sending."""
        from app.auth.router import _send_welcome_email

        # Mock email service
        mock_email_service = AsyncMock()
        mock_email_service.is_configured.return_value = True
        mock_email_service.send_email.return_value = True
        mock_get_service.return_value = mock_email_service

        # Mock template rendering
        mock_render.return_value = ("<html>Welcome</html>", "Welcome text")

        # Call function
        await _send_welcome_email(self.test_user)

        # Verify email service was called
        mock_email_service.send_email.assert_called_once()
        mock_render.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    async def test_send_welcome_email_not_configured(self, mock_get_service):
        """Test welcome email when service is not configured."""
        from app.auth.router import _send_welcome_email

        # Mock unconfigured email service - use MagicMock for sync methods
        mock_email_service = MagicMock()
        mock_email_service.is_configured.return_value = False  # Sync method
        mock_email_service.send_email = AsyncMock()  # Async method
        mock_get_service.return_value = mock_email_service

        # Call function (should not raise exception)
        await _send_welcome_email(self.test_user)

        # Verify email was not sent
        mock_email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.auth.router.get_email_service")
    async def test_send_welcome_email_exception(self, mock_get_service):
        """Test welcome email with exception."""
        from app.auth.router import _send_welcome_email

        # Mock email service that raises exception
        mock_get_service.side_effect = Exception("Email service error")

        # Call function (should handle exception gracefully)
        await _send_welcome_email(self.test_user)

        # Function should complete without raising exception
