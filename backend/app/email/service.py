"""
Email service for sending emails via SendGrid or Gmail.
"""

import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import aiosmtplib
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config.settings_manager import SettingsManager


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        pass


class SendGridProvider(EmailProvider):
    """SendGrid email provider."""

    def __init__(self, api_key: str, from_email: str, from_name: str):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.client = SendGridAPIClient(api_key=api_key)

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via SendGrid."""
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
            )

            response = self.client.send(message)
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"SendGrid email error: {e}")
            return False


class GmailProvider(EmailProvider):
    """Gmail SMTP email provider."""

    def __init__(
        self,
        username: str,
        password: str,
        from_email: str,
        from_name: str,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
    ):
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via Gmail SMTP."""
        try:
            print(f"📧 Attempting to send email to {to_emails} via Gmail SMTP...")

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = ", ".join(to_emails)

            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            print(f"🔗 Connecting to {self.smtp_host}:{self.smtp_port}...")

            # Send email with timeout
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password,
                timeout=30,  # 30 second timeout
            )
            print("✅ Email sent successfully via Gmail SMTP")
            return True
        except Exception as e:
            print(f"❌ Gmail SMTP email error: {e}")
            import traceback

            traceback.print_exc()
            return False


class TestEmailProvider(EmailProvider):
    """Test email provider that simulates email sending."""

    def __init__(self, from_email: str, from_name: str):
        self.from_email = from_email
        self.from_name = from_name

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Simulate email sending for testing."""
        try:
            print(f"📧 [TEST MODE] Simulating email send to {to_emails}")
            print(f"📧 [TEST MODE] Subject: {subject}")
            print(f"📧 [TEST MODE] From: {self.from_name} <{self.from_email}>")
            print(f"📧 [TEST MODE] HTML Content Length: {len(html_content)} chars")
            if text_content:
                print(f"📧 [TEST MODE] Text Content Length: {len(text_content)} chars")

            # Extract verification/reset URLs from content for easy testing
            import re

            url_pattern = (
                r'http[s]?://[^\s<>"]+(?:verify-email|reset-password)[^\s<>"]*'
            )
            urls = re.findall(url_pattern, html_content)
            if urls:
                print(f"🔗 [TEST MODE] Action URL: {urls[0]}")

            print("✅ [TEST MODE] Email simulation completed successfully")
            return True
        except Exception as e:
            print(f"❌ [TEST MODE] Email simulation error: {e}")
            return False


class EmailService:
    """Main email service that manages different providers."""

    def __init__(self, settings_manager: Optional[SettingsManager] = None):
        self.settings_manager = settings_manager or SettingsManager()
        self._provider: Optional[EmailProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the email provider based on configuration."""
        try:
            # Get email configuration from environment variables
            email_provider = os.getenv("EMAIL_PROVIDER", "sendgrid").lower()
            from_email = os.getenv("EMAIL_FROM", "noreply@example.com")
            from_name = os.getenv("EMAIL_FROM_NAME", "DockerDeployer")

            if email_provider == "sendgrid":
                api_key = os.getenv("SENDGRID_API_KEY")
                if not api_key:
                    print("Warning: SENDGRID_API_KEY not configured")
                    return
                self._provider = SendGridProvider(api_key, from_email, from_name)

            elif email_provider == "gmail":
                username = os.getenv("GMAIL_USERNAME")
                password = os.getenv("GMAIL_PASSWORD")
                smtp_host = os.getenv("GMAIL_SMTP_HOST", "smtp.gmail.com")
                smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))

                if not username or not password:
                    print("Warning: Gmail credentials not configured")
                    return

                self._provider = GmailProvider(
                    username, password, from_email, from_name, smtp_host, smtp_port
                )

            elif email_provider == "test":
                print("📧 Using test email provider (emails will be simulated)")
                self._provider = TestEmailProvider(from_email, from_name)

            else:
                print(f"Warning: Unknown email provider: {email_provider}")

        except Exception as e:
            print(f"Error initializing email provider: {e}")

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email using the configured provider."""
        if not self._provider:
            print("Error: No email provider configured")
            return False

        return await self._provider.send_email(
            to_emails, subject, html_content, text_content
        )

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return self._provider is not None


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
