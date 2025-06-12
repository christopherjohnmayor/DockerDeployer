"""
Tests for email service functionality.
"""

import os
import secrets
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jinja2 import Template, TemplateError

from app.email.service import EmailService, GmailProvider, SendGridProvider, TestEmailProvider, get_email_service
from app.email.templates import EmailTemplates


class TestEmailProviders:
    """Test email provider implementations."""

    @pytest.mark.asyncio
    async def test_sendgrid_provider_success(self):
        """Test SendGrid provider successful email sending."""
        with patch("app.email.service.SendGridAPIClient") as mock_client_class:
            # Mock the SendGrid client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_client.send.return_value = mock_response
            mock_client_class.return_value = mock_client

            provider = SendGridProvider(
                api_key="test_key", from_email="test@example.com", from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is True
            mock_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_sendgrid_provider_failure(self):
        """Test SendGrid provider email sending failure."""
        with patch("app.email.service.SendGridAPIClient") as mock_client_class:
            # Mock the SendGrid client to raise an exception
            mock_client = MagicMock()
            mock_client.send.side_effect = Exception("SendGrid error")
            mock_client_class.return_value = mock_client

            provider = SendGridProvider(
                api_key="test_key", from_email="test@example.com", from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_gmail_provider_success(self):
        """Test Gmail provider successful email sending."""
        with patch("app.email.service.aiosmtplib.send") as mock_send:
            mock_send.return_value = None  # aiosmtplib.send returns None on success

            provider = GmailProvider(
                username="test@gmail.com",
                password="test_password",
                from_email="test@gmail.com",
                from_name="Test App",
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_gmail_provider_failure(self):
        """Test Gmail provider email sending failure."""
        with patch("app.email.service.aiosmtplib.send") as mock_send:
            mock_send.side_effect = Exception("SMTP error")

            provider = GmailProvider(
                username="test@gmail.com",
                password="test_password",
                from_email="test@gmail.com",
                from_name="Test App",
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_test_email_provider_success(self):
        """Test TestEmailProvider successful email sending."""
        provider = TestEmailProvider(
            from_email="test@example.com",
            from_name="Test App"
        )

        result = await provider.send_email(
            to_emails=["user@example.com"],
            subject="Test Subject",
            html_content="<h1>Test</h1><a href='https://example.com/verify-email?token=abc123'>Verify</a>",
            text_content="Test content"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_test_email_provider_without_text_content(self):
        """Test TestEmailProvider without text content."""
        provider = TestEmailProvider(
            from_email="test@example.com",
            from_name="Test App"
        )

        result = await provider.send_email(
            to_emails=["user@example.com"],
            subject="Test Subject",
            html_content="<h1>Test</h1><a href='https://example.com/reset-password?token=xyz789'>Reset</a>"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_test_email_provider_url_extraction(self):
        """Test TestEmailProvider URL extraction functionality."""
        provider = TestEmailProvider(
            from_email="test@example.com",
            from_name="Test App"
        )

        # Test with verification URL
        html_with_verify = '<p>Click <a href="https://example.com/verify-email?token=abc123">here</a> to verify</p>'
        result = await provider.send_email(
            to_emails=["user@example.com"],
            subject="Verification",
            html_content=html_with_verify
        )
        assert result is True

        # Test with reset password URL
        html_with_reset = '<p>Click <a href="https://example.com/reset-password?token=xyz789">here</a> to reset</p>'
        result = await provider.send_email(
            to_emails=["user@example.com"],
            subject="Reset Password",
            html_content=html_with_reset
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_test_email_provider_error_handling(self):
        """Test TestEmailProvider error handling."""
        provider = TestEmailProvider(
            from_email="test@example.com",
            from_name="Test App"
        )

        # Mock re.findall to raise an exception
        with patch("re.findall", side_effect=Exception("Regex error")):
            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>"
            )
            assert result is False


class TestEmailService:
    """Test email service functionality."""

    def test_email_service_initialization_sendgrid(self):
        """Test email service initialization with SendGrid."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
                "SENDGRID_API_KEY": "test_key",
            },
        ):
            service = EmailService()
            assert service.is_configured() is True

    def test_email_service_initialization_gmail(self):
        """Test email service initialization with Gmail."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "EMAIL_FROM_NAME": "Test App",
                "GMAIL_USERNAME": "test@gmail.com",
                "GMAIL_PASSWORD": "test_password",
            },
        ):
            service = EmailService()
            assert service.is_configured() is True

    def test_email_service_not_configured(self):
        """Test email service when not properly configured."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App"
                # Missing SENDGRID_API_KEY
            },
            clear=True,
        ):
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
                html_content="<h1>Test</h1>",
            )
            assert result is False

    def test_email_service_initialization_test_provider(self):
        """Test email service initialization with test provider."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()
            assert service.is_configured() is True

    def test_email_service_initialization_error_handling(self):
        """Test email service initialization error handling."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "EMAIL_FROM_NAME": "Test App",
                "GMAIL_USERNAME": "test@gmail.com",
                "GMAIL_PASSWORD": "test_password",
                "GMAIL_SMTP_PORT": "invalid_port",  # Invalid port to trigger error
            },
        ):
            with patch("builtins.print") as mock_print:
                service = EmailService()
                assert service.is_configured() is False
                mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_email_service_send_email_with_configured_provider(self):
        """Test sending email with configured provider."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()
            result = await service.send_email(
                to_emails=["user@example.com"],
                subject="Test",
                html_content="<h1>Test</h1>",
            )
            assert result is True

    def test_get_email_service_singleton(self):
        """Test global email service instance management."""
        # Clear the global instance first
        import app.email.service
        app.email.service._email_service = None

        # Test singleton behavior
        service1 = get_email_service()
        service2 = get_email_service()
        assert service1 is service2

        # Test that the global instance is set
        assert app.email.service._email_service is not None

    def test_get_email_service_existing_instance(self):
        """Test getting existing email service instance."""
        # Set up an existing instance
        import app.email.service
        existing_service = EmailService()
        app.email.service._email_service = existing_service

        # Get the service and verify it's the same instance
        service = get_email_service()
        assert service is existing_service


class TestEmailTemplates:
    """Test email template functionality."""

    def test_email_verification_template(self):
        """Test email verification template rendering."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url="https://example.com/verify?token=abc123",
            username="testuser",
            app_name="TestApp",
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
            app_name="TestApp",
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
            login_url="https://example.com/login",
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

    def test_alert_notification_template(self):
        """Test alert notification template rendering."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "alert_notification",
            username="testuser",
            alert_name="High CPU Usage",
            alert_description="CPU usage exceeded threshold",
            container_name="web-server",
            metric_type="cpu_percent",
            current_value=85.5,
            threshold_value=80.0,
            comparison_operator=">",
            app_name="TestApp",
            timestamp="2024-01-01T12:00:00Z",
            dashboard_url="https://example.com/dashboard"
        )

        # Verify HTML content
        assert "testuser" in html_content
        assert "High CPU Usage" in html_content
        assert "CPU usage exceeded threshold" in html_content
        assert "web-server" in html_content
        assert "cpu_percent" in html_content
        assert "85.5" in html_content
        assert "80.0" in html_content
        assert ">" in html_content
        assert "TestApp" in html_content
        assert "2024-01-01T12:00:00Z" in html_content
        assert "https://example.com/dashboard" in html_content

        # Verify text content
        assert "testuser" in text_content
        assert "High CPU Usage" in text_content
        assert "CPU usage exceeded threshold" in text_content
        assert "web-server" in text_content
        assert "cpu_percent" in text_content
        assert "85.5" in text_content
        assert "80.0" in text_content
        assert ">" in text_content
        assert "TestApp" in text_content
        assert "2024-01-01T12:00:00Z" in text_content
        assert "https://example.com/dashboard" in text_content

    def test_alert_notification_template_minimal_data(self):
        """Test alert notification template with minimal data."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "alert_notification",
            username="testuser",
            alert_name="Test Alert"
        )

        assert "testuser" in html_content
        assert "Test Alert" in html_content
        assert "testuser" in text_content
        assert "Test Alert" in text_content

    def test_email_templates_file_system_loading(self):
        """Test EmailTemplates file system template loading."""
        # Test when template directory doesn't exist (default behavior)
        with patch("os.path.exists", return_value=False):
            templates = EmailTemplates()
            # Should still work with inline templates
            html_content, text_content = templates.render_template(
                "welcome",
                username="testuser",
                app_name="TestApp",
                login_url="https://example.com/login"
            )
            assert "testuser" in html_content

        # Test when template directory exists
        with patch("os.path.exists", return_value=True):
            with patch("app.email.templates.FileSystemLoader") as mock_loader:
                with patch("app.email.templates.Environment") as mock_env:
                    templates = EmailTemplates()
                    mock_loader.assert_called_once()
                    mock_env.assert_called_once()


class TestEmailConfiguration:
    """Test email configuration scenarios."""

    def test_sendgrid_configuration_validation(self):
        """Test SendGrid configuration validation."""
        # Test missing API key
        with patch.dict(
            os.environ,
            {"EMAIL_PROVIDER": "sendgrid", "EMAIL_FROM": "test@example.com"},
            clear=True,
        ):
            service = EmailService()
            assert not service.is_configured()

    def test_gmail_configuration_validation(self):
        """Test Gmail configuration validation."""
        # Test missing credentials
        with patch.dict(
            os.environ,
            {"EMAIL_PROVIDER": "gmail", "EMAIL_FROM": "test@gmail.com"},
            clear=True,
        ):
            service = EmailService()
            assert not service.is_configured()

    def test_unknown_provider(self):
        """Test unknown email provider."""
        with patch.dict(
            os.environ,
            {"EMAIL_PROVIDER": "unknown", "EMAIL_FROM": "test@example.com"},
            clear=True,
        ):
            service = EmailService()
            assert not service.is_configured()


class TestEmailIntegration:
    """Test email service integration scenarios."""

    @pytest.mark.asyncio
    async def test_gmail_provider_timeout_handling(self):
        """Test Gmail provider SMTP timeout handling."""
        import asyncio

        with patch("app.email.service.aiosmtplib.send") as mock_send:
            mock_send.side_effect = asyncio.TimeoutError("SMTP timeout")

            provider = GmailProvider(
                username="test@gmail.com",
                password="test_password",
                from_email="test@gmail.com",
                from_name="Test App",
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_gmail_provider_connection_error(self):
        """Test Gmail provider connection error handling."""
        with patch("app.email.service.aiosmtplib.send") as mock_send:
            mock_send.side_effect = ConnectionError("Connection failed")

            provider = GmailProvider(
                username="test@gmail.com",
                password="test_password",
                from_email="test@gmail.com",
                from_name="Test App",
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_sendgrid_provider_rate_limit_handling(self):
        """Test SendGrid provider rate limit handling."""
        with patch("app.email.service.SendGridAPIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 429  # Rate limit status code
            mock_client.send.return_value = mock_response
            mock_client_class.return_value = mock_client

            provider = SendGridProvider(
                api_key="test_key", from_email="test@example.com", from_name="Test App"
            )

            result = await provider.send_email(
                to_emails=["user@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_email_service_with_multiple_recipients(self):
        """Test email service with multiple recipients."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()
            result = await service.send_email(
                to_emails=["user1@example.com", "user2@example.com", "user3@example.com"],
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test content",
            )
            assert result is True

    def test_email_service_provider_initialization_edge_cases(self):
        """Test email service provider initialization edge cases."""
        # Test with empty environment variables
        with patch.dict(os.environ, {}, clear=True):
            service = EmailService()
            assert not service.is_configured()

        # Test with invalid SMTP port
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "GMAIL_USERNAME": "test@gmail.com",
                "GMAIL_PASSWORD": "test_password",
                "GMAIL_SMTP_PORT": "not_a_number",
            },
        ):
            with patch("builtins.print") as mock_print:
                service = EmailService()
                assert not service.is_configured()
                mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_email_templates_with_special_characters(self):
        """Test email templates with special characters and encoding."""
        templates = EmailTemplates()

        # Test with special characters in content
        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url="https://example.com/verify?token=abc123&user=test%40example.com",
            username="test_user_ñáéíóú",
            app_name="TestApp™"
        )

        assert "test_user_ñáéíóú" in html_content
        assert "TestApp™" in html_content
        assert "test_user_ñáéíóú" in text_content
        assert "TestApp™" in text_content
        assert "test%40example.com" in html_content
        assert "test%40example.com" in text_content

    @pytest.mark.asyncio
    async def test_email_service_error_recovery(self):
        """Test email service error recovery scenarios."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
                "SENDGRID_API_KEY": "test_key",
            },
        ):
            with patch("app.email.service.SendGridAPIClient") as mock_client_class:
                # First call fails
                mock_client = MagicMock()
                mock_client.send.side_effect = Exception("Network error")
                mock_client_class.return_value = mock_client

                service = EmailService()
                result1 = await service.send_email(
                    to_emails=["user@example.com"],
                    subject="Test",
                    html_content="<h1>Test</h1>",
                )
                assert result1 is False

                # Second call succeeds
                mock_response = MagicMock()
                mock_response.status_code = 202
                mock_client.send.side_effect = None
                mock_client.send.return_value = mock_response

                result2 = await service.send_email(
                    to_emails=["user@example.com"],
                    subject="Test",
                    html_content="<h1>Test</h1>",
                )
                assert result2 is True


class TestEmailTemplatesComprehensive:
    """Comprehensive tests for EmailTemplates functionality."""

    def test_email_templates_initialization_default(self):
        """Test EmailTemplates initialization with default settings."""
        with patch("os.path.exists", return_value=False):
            templates = EmailTemplates()
            assert templates is not None

    def test_email_templates_initialization_with_file_system(self):
        """Test EmailTemplates initialization with file system loader."""
        with patch("os.path.exists", return_value=True):
            with patch("app.email.templates.FileSystemLoader") as mock_loader:
                with patch("app.email.templates.Environment") as mock_env:
                    templates = EmailTemplates()
                    mock_loader.assert_called_once()
                    mock_env.assert_called_once()

    def test_email_verification_template_comprehensive(self):
        """Test email verification template with comprehensive parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url="https://example.com/verify?token=abc123&user=test",
            username="test_user_123",
            app_name="TestApplication"
        )

        # Verify HTML content structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html>" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert "test_user_123" in html_content
        assert "TestApplication" in html_content
        assert "https://example.com/verify?token=abc123&user=test" in html_content
        assert "Verify Your Email" in html_content

        # Verify text content structure
        assert "test_user_123" in text_content
        assert "TestApplication" in text_content
        assert "https://example.com/verify?token=abc123&user=test" in text_content
        assert "Verify Your Email" in text_content

    def test_email_verification_template_minimal_parameters(self):
        """Test email verification template with minimal parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url="",
            username="",
            app_name=""
        )

        # Should still render without errors
        assert html_content is not None
        assert text_content is not None
        assert len(html_content) > 0
        assert len(text_content) > 0

    def test_password_reset_template_comprehensive(self):
        """Test password reset template with comprehensive parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "password_reset",
            reset_url="https://example.com/reset?token=xyz789&user=test",
            username="test_user_456",
            app_name="TestApplication"
        )

        # Verify HTML content structure
        assert "<!DOCTYPE html>" in html_content
        assert "Reset Your Password" in html_content
        assert "test_user_456" in html_content
        assert "TestApplication" in html_content
        assert "https://example.com/reset?token=xyz789&user=test" in html_content
        assert "Security Notice" in html_content
        assert "1 hour" in html_content

        # Verify text content structure
        assert "Reset Your Password" in text_content
        assert "test_user_456" in text_content
        assert "TestApplication" in text_content
        assert "https://example.com/reset?token=xyz789&user=test" in text_content
        assert "SECURITY NOTICE" in text_content

    def test_password_reset_template_default_app_name(self):
        """Test password reset template with default app name."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "password_reset",
            reset_url="https://example.com/reset",
            username="testuser"
        )

        # Should use default app name
        assert "DockerDeployer" in html_content
        assert "DockerDeployer" in text_content

    def test_welcome_template_comprehensive(self):
        """Test welcome template with comprehensive parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "welcome",
            username="new_user_789",
            app_name="TestApplication",
            login_url="https://example.com/login?ref=welcome"
        )

        # Verify HTML content structure
        assert "<!DOCTYPE html>" in html_content
        assert "Welcome to" in html_content
        assert "new_user_789" in html_content
        assert "TestApplication" in html_content
        assert "https://example.com/login?ref=welcome" in html_content
        assert "Start Using" in html_content

        # Verify text content structure
        assert "Welcome to" in text_content
        assert "new_user_789" in text_content
        assert "TestApplication" in text_content
        assert "https://example.com/login?ref=welcome" in text_content

    def test_welcome_template_minimal_parameters(self):
        """Test welcome template with minimal parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "welcome",
            username="testuser"
        )

        # Should use default values
        assert "DockerDeployer" in html_content
        assert "DockerDeployer" in text_content
        assert "testuser" in html_content
        assert "testuser" in text_content

    def test_alert_notification_template_comprehensive(self):
        """Test alert notification template with comprehensive parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "alert_notification",
            username="admin_user",
            alert_name="Critical CPU Alert",
            alert_description="CPU usage has exceeded critical threshold",
            container_name="production-web-server",
            metric_type="cpu_percent",
            current_value=95.7,
            threshold_value=90.0,
            comparison_operator=">",
            app_name="TestApplication",
            timestamp="2024-01-15T14:30:00Z",
            dashboard_url="https://example.com/dashboard/alerts"
        )

        # Verify HTML content structure
        assert "<!DOCTYPE html>" in html_content
        assert "Alert Triggered" in html_content
        assert "admin_user" in html_content
        assert "Critical CPU Alert" in html_content
        assert "CPU usage has exceeded critical threshold" in html_content
        assert "production-web-server" in html_content
        assert "cpu_percent" in html_content
        assert "95.7" in html_content
        assert "90.0" in html_content
        assert ">" in html_content
        assert "TestApplication" in html_content
        assert "2024-01-15T14:30:00Z" in html_content
        assert "https://example.com/dashboard/alerts" in html_content

        # Verify text content structure
        assert "Alert Triggered" in text_content
        assert "admin_user" in text_content
        assert "Critical CPU Alert" in text_content
        assert "production-web-server" in text_content

    def test_alert_notification_template_with_optional_parameters(self):
        """Test alert notification template with optional parameters."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "alert_notification",
            username="testuser",
            alert_name="Memory Alert",
            alert_description="",  # Empty description
            container_name="",     # Empty container name
            metric_type="memory_percent",
            current_value=85.0,
            threshold_value=80.0,
            comparison_operator=">=",
            app_name="DockerDeployer"
        )

        # Should handle empty values gracefully
        assert "testuser" in html_content
        assert "Memory Alert" in html_content
        assert "memory_percent" in html_content
        assert "85.0" in html_content
        assert "80.0" in html_content
        assert ">=" in html_content

    def test_template_rendering_with_special_characters(self):
        """Test template rendering with special characters and encoding."""
        templates = EmailTemplates()

        # Test with various special characters
        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url="https://example.com/verify?token=abc123&user=test%40domain.com",
            username="user_ñáéíóú_测试",
            app_name="TestApp™ & Co."
        )

        # Verify special characters are preserved
        assert "user_ñáéíóú_测试" in html_content
        assert "TestApp™ & Co." in html_content
        assert "test%40domain.com" in html_content
        assert "user_ñáéíóú_测试" in text_content
        assert "TestApp™ & Co." in text_content

    def test_template_rendering_with_html_entities(self):
        """Test template rendering with HTML entities and escaping."""
        templates = EmailTemplates()

        html_content, text_content = templates.render_template(
            "password_reset",
            reset_url="https://example.com/reset?token=xyz&param=<script>alert('test')</script>",
            username="user<script>alert('xss')</script>",
            app_name="Test & Development"
        )

        # Verify content is rendered (Jinja2 handles escaping)
        assert "user<script>alert('xss')</script>" in html_content
        assert "Test & Development" in html_content
        assert "<script>alert('test')</script>" in html_content

    def test_unknown_template_error_handling(self):
        """Test error handling for unknown template names."""
        templates = EmailTemplates()

        with pytest.raises(ValueError, match="Unknown template: nonexistent_template"):
            templates.render_template("nonexistent_template")

        with pytest.raises(ValueError, match="Unknown template: invalid_template"):
            templates.render_template("invalid_template", param1="value1")

    def test_template_rendering_with_none_values(self):
        """Test template rendering with None values."""
        templates = EmailTemplates()

        # Test with None values (should be handled gracefully)
        html_content, text_content = templates.render_template(
            "welcome",
            username=None,
            app_name=None,
            login_url=None
        )

        # Should render without errors (None values become empty strings)
        assert html_content is not None
        assert text_content is not None
        assert len(html_content) > 0
        assert len(text_content) > 0


class TestPasswordResetIntegration:
    """Test password reset functionality integration with email service."""

    @pytest.mark.asyncio
    async def test_password_reset_token_generation(self):
        """Test password reset token generation and uniqueness."""
        # Test token generation
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)

        # Tokens should be unique
        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0

        # Tokens should be URL-safe
        assert "+" not in token1
        assert "/" not in token1
        assert "=" not in token1

    @pytest.mark.asyncio
    async def test_password_reset_email_sending_success(self):
        """Test successful password reset email sending."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
                "FRONTEND_URL": "https://example.com"
            },
        ):
            # Mock user object
            mock_user = MagicMock()
            mock_user.email = "user@example.com"
            mock_user.username = "testuser"

            # Import the function to test
            from app.auth.router import _send_password_reset_email

            # Test email sending
            reset_token = "test_reset_token_123"
            await _send_password_reset_email(mock_user, reset_token)

            # Should complete without errors

    @pytest.mark.asyncio
    async def test_password_reset_email_sending_not_configured(self):
        """Test password reset email sending when service not configured."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock user object
            mock_user = MagicMock()
            mock_user.email = "user@example.com"
            mock_user.username = "testuser"

            # Import the function to test
            from app.auth.router import _send_password_reset_email

            # Test email sending with unconfigured service
            reset_token = "test_reset_token_123"
            with patch("builtins.print") as mock_print:
                await _send_password_reset_email(mock_user, reset_token)
                # Should print warning message
                mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_password_reset_email_template_integration(self):
        """Test password reset email template integration."""
        templates = EmailTemplates()

        # Test template rendering for password reset
        reset_url = "https://example.com/reset-password?token=abc123"
        username = "testuser"
        app_name = "DockerDeployer"

        html_content, text_content = templates.render_template(
            "password_reset",
            reset_url=reset_url,
            username=username,
            app_name=app_name
        )

        # Verify reset URL is properly embedded
        assert reset_url in html_content
        assert reset_url in text_content

        # Verify security notice is included
        assert "1 hour" in html_content
        assert "1 hour" in text_content
        assert "Security Notice" in html_content or "SECURITY NOTICE" in text_content

    @pytest.mark.asyncio
    async def test_password_reset_url_generation(self):
        """Test password reset URL generation with different base URLs."""
        test_cases = [
            ("http://localhost:3000", "token123", "http://localhost:3000/reset-password?token=token123"),
            ("https://example.com", "token456", "https://example.com/reset-password?token=token456"),
            ("https://app.domain.com:8080", "token789", "https://app.domain.com:8080/reset-password?token=token789"),
        ]

        for base_url, token, expected_url in test_cases:
            with patch.dict(os.environ, {"FRONTEND_URL": base_url}):
                # Import the function to test
                from app.auth.router import _send_password_reset_email

                # Mock user and email service
                mock_user = MagicMock()
                mock_user.email = "user@example.com"
                mock_user.username = "testuser"

                with patch("app.auth.router.get_email_service") as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.is_configured.return_value = True
                    mock_service.send_email = AsyncMock(return_value=True)
                    mock_get_service.return_value = mock_service

                    with patch("app.auth.router.email_templates.render_template") as mock_render:
                        mock_render.return_value = ("<html>test</html>", "test")

                        await _send_password_reset_email(mock_user, token)

                        # Verify template was called with correct URL
                        mock_render.assert_called_once_with(
                            "password_reset",
                            reset_url=expected_url,
                            username="testuser",
                            app_name="DockerDeployer"
                        )

    @pytest.mark.asyncio
    async def test_password_reset_email_error_handling(self):
        """Test password reset email error handling."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "SENDGRID_API_KEY": "test_key",
                "FRONTEND_URL": "https://example.com"
            },
        ):
            # Mock user object
            mock_user = MagicMock()
            mock_user.email = "user@example.com"
            mock_user.username = "testuser"

            # Mock email service to fail
            with patch("app.auth.router.get_email_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.is_configured.return_value = True
                mock_service.send_email = AsyncMock(return_value=False)  # Simulate failure
                mock_get_service.return_value = mock_service

                # Import the function to test
                from app.auth.router import _send_password_reset_email

                # Test error handling
                reset_token = "test_reset_token_123"
                with patch("builtins.print") as mock_print:
                    await _send_password_reset_email(mock_user, reset_token)
                    # Should print error message
                    mock_print.assert_called()

    def test_password_reset_token_expiration_calculation(self):
        """Test password reset token expiration calculation."""
        from datetime import datetime, timedelta

        # Test 1 hour expiration
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=1)

        # Should be exactly 1 hour later
        time_diff = expires_at - now
        assert time_diff.total_seconds() == 3600  # 1 hour = 3600 seconds

        # Test that expiration is in the future
        assert expires_at > now


class TestEmailServiceEnhancedConfiguration:
    """Test enhanced email service configuration and error handling."""

    def test_email_provider_switching_sendgrid_to_gmail(self):
        """Test switching email providers from SendGrid to Gmail."""
        # Test SendGrid configuration
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
                "SENDGRID_API_KEY": "test_key",
            },
        ):
            service1 = EmailService()
            assert service1.is_configured() is True
            assert isinstance(service1._provider, SendGridProvider)

        # Test Gmail configuration
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "EMAIL_FROM_NAME": "Test App",
                "GMAIL_USERNAME": "test@gmail.com",
                "GMAIL_PASSWORD": "test_password",
            },
        ):
            service2 = EmailService()
            assert service2.is_configured() is True
            assert isinstance(service2._provider, GmailProvider)

    def test_email_provider_fallback_to_test_provider(self):
        """Test fallback to test provider when others fail."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()
            assert service.is_configured() is True
            assert isinstance(service._provider, TestEmailProvider)

    def test_smtp_configuration_with_custom_host_and_port(self):
        """Test SMTP configuration with custom host and port."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@custom.com",
                "EMAIL_FROM_NAME": "Test App",
                "GMAIL_USERNAME": "test@custom.com",
                "GMAIL_PASSWORD": "test_password",
                "GMAIL_SMTP_HOST": "smtp.custom.com",
                "GMAIL_SMTP_PORT": "465",
            },
        ):
            service = EmailService()
            assert service.is_configured() is True
            assert service._provider.smtp_host == "smtp.custom.com"
            assert service._provider.smtp_port == 465

    def test_email_service_initialization_with_invalid_port(self):
        """Test email service initialization with invalid SMTP port."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "GMAIL_USERNAME": "test@gmail.com",
                "GMAIL_PASSWORD": "test_password",
                "GMAIL_SMTP_PORT": "invalid_port",
            },
        ):
            with patch("builtins.print") as mock_print:
                service = EmailService()
                assert service.is_configured() is False
                mock_print.assert_called()

    def test_email_service_environment_variable_validation(self):
        """Test email service environment variable validation."""
        # Test missing EMAIL_FROM
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "SENDGRID_API_KEY": "test_key",
                # Missing EMAIL_FROM
            },
            clear=True,
        ):
            service = EmailService()
            # Should use default email
            assert service._provider.from_email == "noreply@example.com"

    def test_email_service_provider_authentication_validation(self):
        """Test email provider authentication validation."""
        # Test SendGrid with empty API key
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "SENDGRID_API_KEY": "",  # Empty API key
            },
            clear=True,
        ):
            with patch("builtins.print") as mock_print:
                service = EmailService()
                assert service.is_configured() is False
                mock_print.assert_called()

        # Test Gmail with empty credentials
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "GMAIL_USERNAME": "",  # Empty username
                "GMAIL_PASSWORD": "",  # Empty password
            },
            clear=True,
        ):
            with patch("builtins.print") as mock_print:
                service = EmailService()
                assert service.is_configured() is False
                mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_email_delivery_retry_logic_simulation(self):
        """Test email delivery retry logic simulation."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "SENDGRID_API_KEY": "test_key",
            },
        ):
            with patch("app.email.service.SendGridAPIClient") as mock_client_class:
                mock_client = MagicMock()

                # First attempt fails, second succeeds
                mock_response_fail = MagicMock()
                mock_response_fail.status_code = 500  # Server error
                mock_response_success = MagicMock()
                mock_response_success.status_code = 202  # Success

                mock_client.send.side_effect = [mock_response_fail, mock_response_success]
                mock_client_class.return_value = mock_client

                service = EmailService()

                # First attempt should fail
                result1 = await service.send_email(
                    to_emails=["user@example.com"],
                    subject="Test",
                    html_content="<h1>Test</h1>",
                )
                assert result1 is False

                # Second attempt should succeed
                result2 = await service.send_email(
                    to_emails=["user@example.com"],
                    subject="Test",
                    html_content="<h1>Test</h1>",
                )
                assert result2 is True

    @pytest.mark.asyncio
    async def test_email_service_timeout_handling(self):
        """Test email service timeout handling."""
        import asyncio

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "gmail",
                "EMAIL_FROM": "test@gmail.com",
                "GMAIL_USERNAME": "test@gmail.com",
                "GMAIL_PASSWORD": "test_password",
            },
        ):
            with patch("app.email.service.aiosmtplib.send") as mock_send:
                mock_send.side_effect = asyncio.TimeoutError("Connection timeout")

                service = EmailService()
                result = await service.send_email(
                    to_emails=["user@example.com"],
                    subject="Test",
                    html_content="<h1>Test</h1>",
                )
                assert result is False

    def test_email_service_singleton_reset(self):
        """Test email service singleton reset functionality."""
        import app.email.service

        # Clear singleton
        app.email.service._email_service = None

        # Create first instance
        service1 = get_email_service()
        assert service1 is not None

        # Get second instance (should be same)
        service2 = get_email_service()
        assert service1 is service2

        # Reset singleton
        app.email.service._email_service = None

        # Create new instance (should be different)
        service3 = get_email_service()
        assert service3 is not service1


class TestEmailVerificationIntegration:
    """Test email verification functionality integration with email service."""

    @pytest.mark.asyncio
    async def test_email_verification_token_generation(self):
        """Test email verification token generation and uniqueness."""
        # Test token generation
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)

        # Tokens should be unique
        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0

        # Tokens should be URL-safe
        assert "+" not in token1
        assert "/" not in token1

    @pytest.mark.asyncio
    async def test_email_verification_email_sending_success(self):
        """Test successful email verification email sending."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
                "FRONTEND_URL": "https://example.com"
            },
        ):
            # Mock user object and database session
            mock_user = MagicMock()
            mock_user.email = "user@example.com"
            mock_user.username = "testuser"
            mock_user.id = 1

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.update.return_value = None
            mock_db.add.return_value = None
            mock_db.commit.return_value = None

            # Import the function to test
            from app.auth.router import _send_email_verification

            # Test email sending
            await _send_email_verification(mock_user, mock_db)

            # Should complete without errors
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_email_verification_template_integration(self):
        """Test email verification template integration."""
        templates = EmailTemplates()

        # Test template rendering for email verification
        verification_url = "https://example.com/verify-email?token=abc123"
        username = "testuser"
        app_name = "DockerDeployer"

        html_content, text_content = templates.render_template(
            "email_verification",
            verification_url=verification_url,
            username=username,
            app_name=app_name
        )

        # Verify verification URL is properly embedded
        assert verification_url in html_content
        assert verification_url in text_content

        # Verify welcome message is included
        assert "Verify Your Email" in html_content
        assert username in html_content
        assert username in text_content

    @pytest.mark.asyncio
    async def test_email_verification_url_generation(self):
        """Test email verification URL generation with different base URLs."""
        test_cases = [
            ("http://localhost:3001", "token123", "http://localhost:3001/verify-email?token=token123"),
            ("https://example.com", "token456", "https://example.com/verify-email?token=token456"),
            ("https://app.domain.com:8080", "token789", "https://app.domain.com:8080/verify-email?token=token789"),
        ]

        for base_url, token, expected_url in test_cases:
            with patch.dict(os.environ, {"FRONTEND_URL": base_url}):
                # Mock database and user
                mock_user = MagicMock()
                mock_user.email = "user@example.com"
                mock_user.username = "testuser"
                mock_user.id = 1

                mock_db = MagicMock()
                mock_db.query.return_value.filter.return_value.update.return_value = None

                with patch("app.auth.router.get_email_service") as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.is_configured.return_value = True
                    mock_service.send_email = AsyncMock(return_value=True)
                    mock_get_service.return_value = mock_service

                    with patch("app.auth.router.email_templates.render_template") as mock_render:
                        mock_render.return_value = ("<html>test</html>", "test")

                        with patch("secrets.token_urlsafe", return_value=token):
                            # Import the function to test
                            from app.auth.router import _send_email_verification

                            await _send_email_verification(mock_user, mock_db)

                            # Verify template was called with correct URL
                            mock_render.assert_called_once_with(
                                "email_verification",
                                verification_url=expected_url,
                                username="testuser",
                                app_name="DockerDeployer"
                            )

    @pytest.mark.asyncio
    async def test_email_verification_timeout_handling(self):
        """Test email verification timeout handling."""
        import asyncio

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "FRONTEND_URL": "https://example.com"
            },
        ):
            # Mock user and database
            mock_user = MagicMock()
            mock_user.email = "user@example.com"
            mock_user.username = "testuser"
            mock_user.id = 1

            mock_db = MagicMock()

            # Mock email service to timeout
            with patch("app.auth.router.get_email_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.is_configured.return_value = True
                mock_service.send_email = AsyncMock(side_effect=asyncio.TimeoutError("Email timeout"))
                mock_get_service.return_value = mock_service

                # Import the function to test
                from app.auth.router import _send_email_verification

                # Test timeout handling
                with patch("builtins.print") as mock_print:
                    await _send_email_verification(mock_user, mock_db)
                    # Should print timeout message
                    mock_print.assert_called()

    def test_email_verification_token_expiration_calculation(self):
        """Test email verification token expiration calculation."""
        from datetime import datetime, timedelta

        # Test 24 hour expiration
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)

        # Should be exactly 24 hours later
        time_diff = expires_at - now
        assert time_diff.total_seconds() == 86400  # 24 hours = 86400 seconds

        # Test that expiration is in the future
        assert expires_at > now


class TestEmailServiceAdvanced:
    """Advanced email service testing scenarios."""

    @pytest.mark.asyncio
    async def test_email_service_with_large_recipient_list(self):
        """Test email service with large recipient list."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()

            # Test with large recipient list
            large_recipient_list = [f"user{i}@example.com" for i in range(100)]

            result = await service.send_email(
                to_emails=large_recipient_list,
                subject="Bulk Email Test",
                html_content="<h1>Bulk Email</h1>",
                text_content="Bulk Email"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_email_service_with_long_content(self):
        """Test email service with long email content."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()

            # Generate long content
            long_html_content = "<h1>Long Email</h1>" + "<p>Content line</p>" * 1000
            long_text_content = "Long Email\n" + "Content line\n" * 1000

            result = await service.send_email(
                to_emails=["user@example.com"],
                subject="Long Content Test",
                html_content=long_html_content,
                text_content=long_text_content
            )
            assert result is True

    def test_email_templates_performance_with_large_data(self):
        """Test email templates performance with large data sets."""
        templates = EmailTemplates()

        # Test with large data
        large_description = "Alert description " * 100
        large_container_name = "very-long-container-name-" * 10

        html_content, text_content = templates.render_template(
            "alert_notification",
            username="testuser",
            alert_name="Performance Test Alert",
            alert_description=large_description,
            container_name=large_container_name,
            metric_type="cpu_percent",
            current_value=95.0,
            threshold_value=90.0,
            comparison_operator=">",
            app_name="DockerDeployer"
        )

        # Should handle large data without issues
        assert large_description in html_content
        assert large_container_name in html_content
        assert len(html_content) > 1000
        assert len(text_content) > 1000

    @pytest.mark.asyncio
    async def test_email_service_concurrent_sending(self):
        """Test email service concurrent email sending."""
        import asyncio

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "test",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_FROM_NAME": "Test App",
            },
        ):
            service = EmailService()

            # Create multiple concurrent email sending tasks
            tasks = []
            for i in range(10):
                task = service.send_email(
                    to_emails=[f"user{i}@example.com"],
                    subject=f"Concurrent Test {i}",
                    html_content=f"<h1>Test {i}</h1>",
                    text_content=f"Test {i}"
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(results)
            assert len(results) == 10

    def test_email_service_memory_usage_optimization(self):
        """Test email service memory usage with multiple instances."""
        # Test creating multiple service instances
        services = []
        for i in range(50):
            with patch.dict(
                os.environ,
                {
                    "EMAIL_PROVIDER": "test",
                    "EMAIL_FROM": f"test{i}@example.com",
                    "EMAIL_FROM_NAME": f"Test App {i}",
                },
            ):
                service = EmailService()
                services.append(service)

        # All services should be configured
        assert len(services) == 50
        assert all(service.is_configured() for service in services)

    @pytest.mark.asyncio
    async def test_email_service_error_recovery_scenarios(self):
        """Test email service error recovery in various scenarios."""
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "sendgrid",
                "EMAIL_FROM": "test@example.com",
                "SENDGRID_API_KEY": "test_key",
            },
        ):
            with patch("app.email.service.SendGridAPIClient") as mock_client_class:
                mock_client = MagicMock()

                # Test various error scenarios
                error_scenarios = [
                    Exception("Network error"),
                    ConnectionError("Connection failed"),
                    TimeoutError("Request timeout"),
                    ValueError("Invalid data"),
                ]

                for error in error_scenarios:
                    mock_client.send.side_effect = error
                    mock_client_class.return_value = mock_client

                    service = EmailService()
                    result = await service.send_email(
                        to_emails=["user@example.com"],
                        subject="Error Recovery Test",
                        html_content="<h1>Test</h1>",
                    )
                    assert result is False

    def test_email_templates_edge_case_parameters(self):
        """Test email templates with edge case parameters."""
        templates = EmailTemplates()

        # Test with extreme values
        edge_cases = [
            {
                "username": "",
                "app_name": "",
                "verification_url": "",
            },
            {
                "username": "a" * 1000,  # Very long username
                "app_name": "b" * 500,   # Very long app name
                "verification_url": "https://example.com/" + "c" * 2000,  # Very long URL
            },
            {
                "username": "user@domain.com",  # Email as username
                "app_name": "App & Co. <script>",  # Special characters
                "verification_url": "https://example.com/verify?param=value&other=test",
            },
        ]

        for case in edge_cases:
            html_content, text_content = templates.render_template(
                "email_verification",
                **case
            )

            # Should render without errors
            assert html_content is not None
            assert text_content is not None
            assert len(html_content) > 0
            assert len(text_content) > 0
