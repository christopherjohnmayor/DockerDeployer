"""
Tests for email service functionality.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.email.service import EmailService, SendGridProvider, GmailProvider
from app.email.templates import EmailTemplates


class TestEmailProviders:
    """Test email provider implementations."""

    @pytest.mark.asyncio
    async def test_sendgrid_provider_success(self):
        """Test SendGrid provider successful email sending."""
        with patch('app.email.service.SendGridAPIClient') as mock_client_class:
            # Mock the SendGrid client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_client.send.return_value = mock_response
            mock_client_class.return_value = mock_client

            provider = SendGridProvider(
                api_key="test_key",
                from_email="test@example.com",
                from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test"
            )

            assert result is True
            mock_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_sendgrid_provider_failure(self):
        """Test SendGrid provider email sending failure."""
        with patch('app.email.service.SendGridAPIClient') as mock_client_class:
            # Mock the SendGrid client to raise an exception
            mock_client = MagicMock()
            mock_client.send.side_effect = Exception("SendGrid error")
            mock_client_class.return_value = mock_client

            provider = SendGridProvider(
                api_key="test_key",
                from_email="test@example.com",
                from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_gmail_provider_success(self):
        """Test Gmail provider successful email sending."""
        with patch('app.email.service.aiosmtplib.send') as mock_send:
            mock_send.return_value = None  # aiosmtplib.send returns None on success

            provider = GmailProvider(
                username="test@gmail.com",
                password="test_password",
                from_email="test@gmail.com",
                from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test"
            )

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_gmail_provider_failure(self):
        """Test Gmail provider email sending failure."""
        with patch('app.email.service.aiosmtplib.send') as mock_send:
            mock_send.side_effect = Exception("SMTP error")

            provider = GmailProvider(
                username="test@gmail.com",
                password="test_password",
                from_email="test@gmail.com",
                from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test"
            )

            assert result is False


class TestEmailService:
    """Test email service functionality."""

    def test_email_service_initialization_sendgrid(self):
        """Test email service initialization with SendGrid."""
        with patch.dict(os.environ, {
            'EMAIL_PROVIDER': 'sendgrid',
            'EMAIL_FROM': 'test@example.com',
            'EMAIL_FROM_NAME': 'Test App',
            'SENDGRID_API_KEY': 'test_key'
        }):
            service = EmailService()
            assert service.is_configured() is True

    def test_email_service_initialization_gmail(self):
        """Test email service initialization with Gmail."""
        with patch.dict(os.environ, {
            'EMAIL_PROVIDER': 'gmail',
            'EMAIL_FROM': 'test@gmail.com',
            'EMAIL_FROM_NAME': 'Test App',
            'GMAIL_USERNAME': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }):
            service = EmailService()
            assert service.is_configured() is True

    def test_email_service_not_configured(self):
        """Test email service when not properly configured."""
        with patch.dict(os.environ, {
            'EMAIL_PROVIDER': 'sendgrid',
            'EMAIL_FROM': 'test@example.com',
            'EMAIL_FROM_NAME': 'Test App'
            # Missing SENDGRID_API_KEY
        }, clear=True):
            service = EmailService()
            assert service.is_configured() is False

    @pytest.mark.asyncio
    async def test_email_service_send_email_not_configured(self):
        """Test sending email when service is not configured."""
        with patch.dict(os.environ, {}, clear=True):
            service = EmailService()
            result = await service.send_email(
                to_emails=["user@example.com"],
                subject="Test",
                html_content="<h1>Test</h1>"
            )
            assert result is False


class TestEmailTemplates:
    """Test email template functionality."""

    def test_email_verification_template(self):
        """Test email verification template rendering."""
        templates = EmailTemplates()
        
        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url="https://example.com/verify?token=abc123",
            username="testuser",
            app_name="TestApp"
        )
        
        assert "testuser" in html_content
        assert "testuser" in text_content
        assert "https://example.com/verify?token=abc123" in html_content
        assert "https://example.com/verify?token=abc123" in text_content
        assert "TestApp" in html_content
        assert "TestApp" in text_content

    def test_password_reset_template(self):
        """Test password reset template rendering."""
        templates = EmailTemplates()
        
        html_content, text_content = templates.render_template(
            "password_reset",
            reset_url="https://example.com/reset?token=xyz789",
            username="testuser",
            app_name="TestApp"
        )
        
        assert "testuser" in html_content
        assert "testuser" in text_content
        assert "https://example.com/reset?token=xyz789" in html_content
        assert "https://example.com/reset?token=xyz789" in text_content
        assert "TestApp" in html_content
        assert "TestApp" in text_content

    def test_welcome_template(self):
        """Test welcome template rendering."""
        templates = EmailTemplates()
        
        html_content, text_content = templates.render_template(
            "welcome",
            username="testuser",
            app_name="TestApp",
            login_url="https://example.com/login"
        )
        
        assert "testuser" in html_content
        assert "testuser" in text_content
        assert "https://example.com/login" in html_content
        assert "https://example.com/login" in text_content
        assert "TestApp" in html_content
        assert "TestApp" in text_content

    def test_unknown_template(self):
        """Test rendering unknown template raises error."""
        templates = EmailTemplates()
        
        with pytest.raises(ValueError, match="Unknown template"):
            templates.render_template("unknown_template")


class TestEmailConfiguration:
    """Test email configuration scenarios."""

    def test_sendgrid_configuration_validation(self):
        """Test SendGrid configuration validation."""
        # Test missing API key
        with patch.dict(os.environ, {
            'EMAIL_PROVIDER': 'sendgrid',
            'EMAIL_FROM': 'test@example.com'
        }, clear=True):
            service = EmailService()
            assert not service.is_configured()

    def test_gmail_configuration_validation(self):
        """Test Gmail configuration validation."""
        # Test missing credentials
        with patch.dict(os.environ, {
            'EMAIL_PROVIDER': 'gmail',
            'EMAIL_FROM': 'test@gmail.com'
        }, clear=True):
            service = EmailService()
            assert not service.is_configured()

    def test_unknown_provider(self):
        """Test unknown email provider."""
        with patch.dict(os.environ, {
            'EMAIL_PROVIDER': 'unknown',
            'EMAIL_FROM': 'test@example.com'
        }, clear=True):
            service = EmailService()
            assert not service.is_configured()
