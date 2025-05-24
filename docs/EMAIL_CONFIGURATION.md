# Email Configuration Guide

This guide explains how to configure email functionality in DockerDeployer for password resets and email verification.

## Overview

DockerDeployer supports two email providers:
- **SendGrid** (recommended for production)
- **Gmail** (good for development and small deployments)

## Email Features

- **User Registration**: Sends email verification link
- **Email Verification**: Confirms user email addresses
- **Password Reset**: Sends secure password reset links
- **Welcome Email**: Sent after successful email verification

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Email Configuration
EMAIL_PROVIDER=sendgrid  # or 'gmail'
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=DockerDeployer

# Frontend URL (for email links)
FRONTEND_URL=https://yourdomain.com

# SendGrid Configuration (if using SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key

# Gmail Configuration (if using Gmail)
GMAIL_USERNAME=your_email@gmail.com
GMAIL_PASSWORD=your_app_password
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
```

## SendGrid Setup (Recommended)

### 1. Create SendGrid Account
1. Go to [SendGrid](https://sendgrid.com/)
2. Sign up for a free account (100 emails/day free tier)
3. Verify your account

### 2. Create API Key
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Choose "Restricted Access"
4. Grant "Mail Send" permissions
5. Copy the API key

### 3. Configure Environment
```bash
EMAIL_PROVIDER=sendgrid
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=DockerDeployer
SENDGRID_API_KEY=SG.your_api_key_here
```

### 4. Domain Authentication (Production)
For production, set up domain authentication:
1. Go to Settings → Sender Authentication
2. Click "Authenticate Your Domain"
3. Follow the DNS setup instructions

## Gmail Setup

### 1. Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Enable 2-Factor Authentication

### 2. Generate App Password
1. Go to Security → 2-Step Verification
2. Click "App passwords"
3. Select "Mail" and your device
4. Copy the generated password

### 3. Configure Environment
```bash
EMAIL_PROVIDER=gmail
EMAIL_FROM=your_email@gmail.com
EMAIL_FROM_NAME=DockerDeployer
GMAIL_USERNAME=your_email@gmail.com
GMAIL_PASSWORD=your_16_character_app_password
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
```

## Testing Email Configuration

### 1. Test Email Service
```python
# Test script
import asyncio
from app.email.service import get_email_service

async def test_email():
    service = get_email_service()
    if not service.is_configured():
        print("❌ Email service not configured")
        return
    
    success = await service.send_email(
        to_emails=["test@example.com"],
        subject="Test Email",
        html_content="<h1>Test successful!</h1>",
        text_content="Test successful!"
    )
    
    if success:
        print("✅ Email sent successfully")
    else:
        print("❌ Failed to send email")

# Run test
asyncio.run(test_email())
```

### 2. Test Registration Flow
1. Register a new user
2. Check email for verification link
3. Click verification link
4. Check for welcome email

### 3. Test Password Reset
1. Request password reset
2. Check email for reset link
3. Use reset link to change password

## Email Templates

Email templates are located in `backend/app/email/templates.py` and include:

- **Email Verification**: Sent during registration
- **Password Reset**: Sent when password reset is requested
- **Welcome Email**: Sent after email verification

### Customizing Templates

To customize email templates, modify the template methods in `templates.py`:

```python
def _render_email_verification(self, **kwargs) -> tuple[str, str]:
    # Customize HTML and text content
    html_template = """
    <!-- Your custom HTML template -->
    """
    
    text_template = """
    Your custom text template
    """
    
    # Return rendered templates
    return html_tmpl.render(**context), text_tmpl.render(**context)
```

## Security Considerations

### SendGrid
- Store API keys securely
- Use restricted API keys with minimal permissions
- Set up domain authentication for production
- Monitor usage and set up alerts

### Gmail
- Use App Passwords, never your main password
- Enable 2-Factor Authentication
- Monitor account activity
- Consider Gmail's sending limits (500 emails/day)

### General
- Use HTTPS for all email links
- Set appropriate token expiration times
- Validate email addresses before sending
- Implement rate limiting for email requests

## Troubleshooting

### Common Issues

1. **Email not sending**
   - Check API keys/credentials
   - Verify email provider configuration
   - Check network connectivity
   - Review application logs

2. **Emails going to spam**
   - Set up domain authentication (SendGrid)
   - Use proper from addresses
   - Include unsubscribe links
   - Monitor sender reputation

3. **Links not working**
   - Verify FRONTEND_URL is correct
   - Check token generation and validation
   - Ensure tokens haven't expired

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Check email service status:

```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

## Production Deployment

### Environment Variables
Set these in your production environment:

```bash
EMAIL_PROVIDER=sendgrid
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=YourAppName
SENDGRID_API_KEY=your_production_api_key
FRONTEND_URL=https://yourdomain.com
```

### Monitoring
- Set up email delivery monitoring
- Track bounce rates and spam reports
- Monitor API usage and limits
- Set up alerts for failures

### Backup Strategy
- Configure secondary email provider
- Implement fallback mechanisms
- Store important emails in logs
- Regular backup of email templates

## Support

For issues with email configuration:
1. Check the application logs
2. Verify environment variables
3. Test with a simple email first
4. Check provider-specific documentation
5. Review network and firewall settings
