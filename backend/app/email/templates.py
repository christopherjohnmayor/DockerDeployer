"""
Email templates for DockerDeployer.
"""

import os
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, Template


class EmailTemplates:
    """Email template manager using Jinja2."""

    def __init__(self):
        # Try to load templates from file system, fall back to inline templates
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        if os.path.exists(template_dir):
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.env = Environment()

    def render_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """
        Render an email template.

        Returns:
            tuple: (html_content, text_content)
        """
        if template_name == "email_verification":
            return self._render_email_verification(**kwargs)
        elif template_name == "password_reset":
            return self._render_password_reset(**kwargs)
        elif template_name == "welcome":
            return self._render_welcome(**kwargs)
        elif template_name == "alert_notification":
            return self._render_alert_notification(**kwargs)
        else:
            raise ValueError(f"Unknown template: {template_name}")

    def _render_email_verification(self, **kwargs) -> tuple[str, str]:
        """Render email verification template."""
        verification_url = kwargs.get("verification_url", "")
        username = kwargs.get("username", "")
        app_name = kwargs.get("app_name", "DockerDeployer")

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - {{ app_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9fafb; }
        .button { display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ app_name }}</h1>
        </div>
        <div class="content">
            <h2>Verify Your Email Address</h2>
            <p>Hello {{ username }},</p>
            <p>Thank you for registering with {{ app_name }}! To complete your registration and activate your account, please verify your email address by clicking the button below:</p>
            <p style="text-align: center;">
                <a href="{{ verification_url }}" class="button">Verify Email Address</a>
            </p>
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #2563eb;">{{ verification_url }}</p>
            <p><strong>This verification link will expire in 24 hours.</strong></p>
            <p>If you didn't create an account with {{ app_name }}, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2024 {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
{{ app_name }} - Verify Your Email Address

Hello {{ username }},

Thank you for registering with {{ app_name }}! To complete your registration and activate your account, please verify your email address by visiting this link:

{{ verification_url }}

This verification link will expire in 24 hours.

If you didn't create an account with {{ app_name }}, you can safely ignore this email.

© 2024 {{ app_name }}. All rights reserved.
        """

        html_tmpl = Template(html_template)
        text_tmpl = Template(text_template)

        context = {
            "verification_url": verification_url,
            "username": username,
            "app_name": app_name,
        }

        return html_tmpl.render(**context), text_tmpl.render(**context)

    def _render_password_reset(self, **kwargs) -> tuple[str, str]:
        """Render password reset template."""
        reset_url = kwargs.get("reset_url", "")
        username = kwargs.get("username", "")
        app_name = kwargs.get("app_name", "DockerDeployer")

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password - {{ app_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc2626; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9fafb; }
        .button { display: inline-block; background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 14px; }
        .warning { background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ app_name }}</h1>
        </div>
        <div class="content">
            <h2>Reset Your Password</h2>
            <p>Hello {{ username }},</p>
            <p>We received a request to reset your password for your {{ app_name }} account. Click the button below to create a new password:</p>
            <p style="text-align: center;">
                <a href="{{ reset_url }}" class="button">Reset Password</a>
            </p>
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #dc2626;">{{ reset_url }}</p>
            <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul>
                    <li>This password reset link will expire in 1 hour</li>
                    <li>If you didn't request this reset, please ignore this email</li>
                    <li>For security, this link can only be used once</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
{{ app_name }} - Reset Your Password

Hello {{ username }},

We received a request to reset your password for your {{ app_name }} account. Visit this link to create a new password:

{{ reset_url }}

SECURITY NOTICE:
- This password reset link will expire in 1 hour
- If you didn't request this reset, please ignore this email
- For security, this link can only be used once

© 2024 {{ app_name }}. All rights reserved.
        """

        html_tmpl = Template(html_template)
        text_tmpl = Template(text_template)

        context = {
            "reset_url": reset_url,
            "username": username,
            "app_name": app_name,
        }

        return html_tmpl.render(**context), text_tmpl.render(**context)

    def _render_welcome(self, **kwargs) -> tuple[str, str]:
        """Render welcome email template."""
        username = kwargs.get("username", "")
        app_name = kwargs.get("app_name", "DockerDeployer")
        login_url = kwargs.get("login_url", "")

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {{ app_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #059669; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9fafb; }
        .button { display: inline-block; background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 14px; }
        .features { background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to {{ app_name }}!</h1>
        </div>
        <div class="content">
            <h2>Hello {{ username }},</h2>
            <p>Your email has been verified and your account is now active! Welcome to {{ app_name }}, your powerful Docker container management platform.</p>

            <div class="features">
                <h3>🚀 What you can do with {{ app_name }}:</h3>
                <ul>
                    <li><strong>Deploy Templates:</strong> Quickly deploy popular stacks like LEMP, MEAN, and WordPress</li>
                    <li><strong>Natural Language Commands:</strong> Use AI-powered natural language to manage containers</li>
                    <li><strong>Container Management:</strong> Full Docker container lifecycle management</li>
                    <li><strong>Team Collaboration:</strong> Work with your team on deployments</li>
                </ul>
            </div>

            <p style="text-align: center;">
                <a href="{{ login_url }}" class="button">Start Using {{ app_name }}</a>
            </p>

            <p>If you have any questions or need help getting started, don't hesitate to reach out to our support team.</p>
        </div>
        <div class="footer">
            <p>© 2024 {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
🎉 Welcome to {{ app_name }}!

Hello {{ username }},

Your email has been verified and your account is now active! Welcome to {{ app_name }}, your powerful Docker container management platform.

🚀 What you can do with {{ app_name }}:
- Deploy Templates: Quickly deploy popular stacks like LEMP, MEAN, and WordPress
- Natural Language Commands: Use AI-powered natural language to manage containers
- Container Management: Full Docker container lifecycle management
- Team Collaboration: Work with your team on deployments

Get started: {{ login_url }}

If you have any questions or need help getting started, don't hesitate to reach out to our support team.

© 2024 {{ app_name }}. All rights reserved.
        """

        html_tmpl = Template(html_template)
        text_tmpl = Template(text_template)

        context = {
            "username": username,
            "app_name": app_name,
            "login_url": login_url,
        }

        return html_tmpl.render(**context), text_tmpl.render(**context)

    def _render_alert_notification(self, **kwargs) -> tuple[str, str]:
        """Render alert notification email template."""
        username = kwargs.get("username", "")
        alert_name = kwargs.get("alert_name", "")
        alert_description = kwargs.get("alert_description", "")
        container_name = kwargs.get("container_name", "")
        metric_type = kwargs.get("metric_type", "")
        current_value = kwargs.get("current_value", 0)
        threshold_value = kwargs.get("threshold_value", 0)
        comparison_operator = kwargs.get("comparison_operator", "")
        app_name = kwargs.get("app_name", "DockerDeployer")

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} Alert Notification</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
        .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }
        .alert-details { background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .metric-value { font-size: 1.2em; font-weight: bold; color: #f44336; }
        .footer { text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }
        .button { display: inline-block; padding: 10px 20px; background: #2196F3; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Alert Triggered</h1>
            <p>{{ alert_name }}</p>
        </div>
        <div class="content">
            <p>Hello {{ username }},</p>

            <p>An alert has been triggered in your {{ app_name }} environment:</p>

            <div class="alert-details">
                <h3>Alert Details</h3>
                <p><strong>Alert Name:</strong> {{ alert_name }}</p>
                <p><strong>Description:</strong> {{ alert_description }}</p>
                <p><strong>Container:</strong> {{ container_name }}</p>
                <p><strong>Metric:</strong> {{ metric_type }}</p>
                <p><strong>Current Value:</strong> <span class="metric-value">{{ current_value }}</span></p>
                <p><strong>Threshold:</strong> {{ comparison_operator }} {{ threshold_value }}</p>
                <p><strong>Time:</strong> {{ timestamp }}</p>
            </div>

            <p>Please check your containers and take appropriate action if necessary.</p>

            <a href="{{ dashboard_url }}" class="button">View Dashboard</a>
        </div>
        <div class="footer">
            <p>© 2024 {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
🚨 {{ app_name }} Alert Triggered

Hello {{ username }},

An alert has been triggered in your {{ app_name }} environment:

Alert Details:
- Alert Name: {{ alert_name }}
- Description: {{ alert_description }}
- Container: {{ container_name }}
- Metric: {{ metric_type }}
- Current Value: {{ current_value }}
- Threshold: {{ comparison_operator }} {{ threshold_value }}
- Time: {{ timestamp }}

Please check your containers and take appropriate action if necessary.

View Dashboard: {{ dashboard_url }}

© 2024 {{ app_name }}. All rights reserved.
        """

        html_tmpl = Template(html_template)
        text_tmpl = Template(text_template)

        context = {
            "username": username,
            "alert_name": alert_name,
            "alert_description": alert_description,
            "container_name": container_name,
            "metric_type": metric_type,
            "current_value": current_value,
            "threshold_value": threshold_value,
            "comparison_operator": comparison_operator,
            "app_name": app_name,
            "timestamp": kwargs.get("timestamp", ""),
            "dashboard_url": kwargs.get("dashboard_url", ""),
        }

        return html_tmpl.render(**context), text_tmpl.render(**context)


# Global template instance
email_templates = EmailTemplates()
