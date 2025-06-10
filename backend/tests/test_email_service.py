"""
Tests for email service functionality.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
