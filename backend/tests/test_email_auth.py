"""
Tests for email-related authentication functionality.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import get_password_hash
from app.db.database import get_db
from app.db.models import EmailVerificationToken, PasswordResetToken, User
from app.main import app
from tests.conftest import TestingSessionLocal, override_get_db

# Override the get_db dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestEmailVerification:
    """Test email verification functionality."""

    def setup_method(self):
        """Set up test data."""
        self.db = TestingSessionLocal()

        # Create test user (unverified)
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            full_name="Test User",
            is_email_verified=False,
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)

    def teardown_method(self):
        """Clean up test data."""
        self.db.query(EmailVerificationToken).delete()
        self.db.query(PasswordResetToken).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    @patch("app.auth.router._send_email_verification")
    def test_user_registration_sends_verification_email(self, mock_send_email):
        """Test that user registration sends verification email."""
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
        assert data["is_email_verified"] is False

        # Verify email sending was called
        mock_send_email.assert_called_once()

    def test_email_verification_request(self):
        """Test requesting email verification."""
        with patch("app.auth.router._send_email_verification") as mock_send_email:
            mock_send_email.return_value = None

            response = client.post(
                "/auth/email-verification-request", json={"email": "test@example.com"}
            )

            assert response.status_code == 200
            assert "verification link has been sent" in response.json()["message"]
            mock_send_email.assert_called_once()

    def test_email_verification_request_already_verified(self):
        """Test requesting verification for already verified email."""
        # Mark user as verified
        self.test_user.is_email_verified = True
        self.db.commit()

        response = client.post(
            "/auth/email-verification-request", json={"email": "test@example.com"}
        )

        assert response.status_code == 400
        assert "already verified" in response.json()["detail"]

    def test_email_verification_request_nonexistent_email(self):
        """Test requesting verification for non-existent email."""
        response = client.post(
            "/auth/email-verification-request",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200
        assert "verification link has been sent" in response.json()["message"]

    def test_email_verification_confirm_success(self):
        """Test successful email verification confirmation."""
        # Create verification token
        token = EmailVerificationToken(
            token="valid_token_123",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_used=False,
        )
        self.db.add(token)
        self.db.commit()

        with patch("app.auth.router._send_welcome_email") as mock_send_welcome:
            mock_send_welcome.return_value = None

            response = client.post(
                "/auth/email-verification-confirm", json={"token": "valid_token_123"}
            )

            assert response.status_code == 200
            assert "verified successfully" in response.json()["message"]

            # Check user is now verified
            self.db.refresh(self.test_user)
            assert self.test_user.is_email_verified is True

            # Check token is marked as used
            self.db.refresh(token)
            assert token.is_used is True

            # Verify welcome email was sent
            mock_send_welcome.assert_called_once()

    def test_email_verification_confirm_invalid_token(self):
        """Test email verification with invalid token."""
        response = client.post(
            "/auth/email-verification-confirm", json={"token": "invalid_token"}
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_email_verification_confirm_expired_token(self):
        """Test email verification with expired token."""
        # Create expired token
        token = EmailVerificationToken(
            token="expired_token_123",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_used=False,
        )
        self.db.add(token)
        self.db.commit()

        response = client.post(
            "/auth/email-verification-confirm", json={"token": "expired_token_123"}
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_email_verification_confirm_used_token(self):
        """Test email verification with already used token."""
        # Create used token
        token = EmailVerificationToken(
            token="used_token_123",
            user_id=self.test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_used=True,  # Already used
        )
        self.db.add(token)
        self.db.commit()

        response = client.post(
            "/auth/email-verification-confirm", json={"token": "used_token_123"}
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]


class TestPasswordResetWithEmail:
    """Test password reset functionality with email."""

    def setup_method(self):
        """Set up test data."""
        self.db = TestingSessionLocal()

        # Create test user
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            full_name="Test User",
            is_email_verified=True,
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)

    def teardown_method(self):
        """Clean up test data."""
        self.db.query(PasswordResetToken).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    def test_password_reset_request_sends_email(self):
        """Test that password reset request sends email."""
        with patch("app.auth.router._send_password_reset_email") as mock_send_email:
            mock_send_email.return_value = None

            response = client.post(
                "/auth/password-reset-request", json={"email": "test@example.com"}
            )

            assert response.status_code == 200
            assert "reset link has been sent" in response.json()["message"]
            mock_send_email.assert_called_once()

    def test_password_reset_request_nonexistent_email(self):
        """Test password reset request for non-existent email."""
        response = client.post(
            "/auth/password-reset-request", json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]


# Import datetime after other imports to avoid conflicts
from datetime import datetime, timedelta
