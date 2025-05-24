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

## Test Mode Configuration

For development and testing, you can use test mode to simulate email sending without actually sending emails:

```bash
# Test Mode Configuration
EMAIL_PROVIDER=test
EMAIL_FROM=test@example.com
EMAIL_FROM_NAME=DockerDeployer Test
FRONTEND_URL=http://localhost:3001
```

In test mode, the system will:

- Generate verification and reset tokens normally
- Log email content and URLs to the console
- Extract action URLs for easy testing
- Simulate successful email delivery

## Troubleshooting

### Gmail Authentication Issues

#### Error: "Username and Password not accepted"

**Cause**: Incorrect Gmail app password or 2FA not enabled.

**Solutions**:

1. **Verify 2-Factor Authentication is enabled**:

   - Go to Google Account Settings → Security
   - Enable 2-Step Verification if not already enabled

2. **Generate a new App Password**:

   - Go to Google Account Settings → Security → 2-Step Verification
   - Click "App passwords" at the bottom
   - Select "Mail" and your device
   - Copy the 16-character password **exactly as shown**

3. **Correct App Password Format**:

   ```bash
   # ✅ Correct (16 characters, no spaces)
   GMAIL_PASSWORD=abcdefghijklmnop

   # ❌ Incorrect (with spaces)
   GMAIL_PASSWORD=abcd efgh ijkl mnop
   ```

4. **Verify Gmail Configuration**:
   ```bash
   EMAIL_PROVIDER=gmail
   GMAIL_USERNAME=your_email@gmail.com
   GMAIL_PASSWORD=your_16_character_app_password
   GMAIL_SMTP_HOST=smtp.gmail.com
   GMAIL_SMTP_PORT=587
   ```

#### Error: "Connection timeout" or "Connection refused"

**Cause**: Network connectivity or firewall issues.

**Solutions**:

1. Check internet connectivity
2. Verify firewall allows outbound connections on port 587
3. Try using port 465 with SSL instead of 587 with TLS
4. Test connection manually:
   ```bash
   telnet smtp.gmail.com 587
   ```

### SendGrid Issues

#### Error: "Unauthorized" or "Invalid API Key"

**Solutions**:

1. Verify API key is correct and has Mail Send permissions
2. Check API key hasn't expired
3. Ensure API key is properly set in environment variables

### Common Issues

1. **Email not sending**

   - Check API keys/credentials format
   - Verify email provider configuration
   - Check network connectivity and firewall settings
   - Review application logs for detailed error messages
   - Test with test mode first

2. **Emails going to spam**

   - Set up domain authentication (SendGrid)
   - Use proper from addresses (avoid generic domains)
   - Include unsubscribe links
   - Monitor sender reputation
   - Start with small volumes and gradually increase

3. **Links not working**

   - Verify FRONTEND_URL matches your actual frontend URL
   - Check token generation and validation logic
   - Ensure tokens haven't expired (24h for verification, 1h for reset)
   - Test URLs manually in browser

4. **Slow email delivery**
   - Check SMTP timeout settings (default 30 seconds)
   - Monitor provider rate limits
   - Consider using async email queues for high volume

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Email Functionality

1. **Test Email Service Configuration**:

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

       print("✅ Email sent" if success else "❌ Email failed")

   asyncio.run(test_email())
   ```

2. **Test Registration Flow**:

   ```bash
   curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "TestPassword123!",
       "full_name": "Test User"
     }'
   ```

3. **Monitor Backend Logs**:
   - Watch for email sending progress messages
   - Check for authentication errors
   - Verify token generation and URL creation

### Health Check

Check email service status:

```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

### Error Message Reference

| Error Message                        | Cause                           | Solution                                             |
| ------------------------------------ | ------------------------------- | ---------------------------------------------------- |
| `Username and Password not accepted` | Invalid Gmail app password      | Generate new app password, ensure 16 chars no spaces |
| `Connection timeout`                 | Network/firewall issue          | Check connectivity, try different port               |
| `Invalid API Key`                    | Wrong SendGrid API key          | Verify API key and permissions                       |
| `Email service not configured`       | Missing environment variables   | Check all required env vars are set                  |
| `Template rendering failed`          | Template syntax error           | Check template syntax and variables                  |
| `Token expired`                      | Verification/reset link too old | Generate new token, check expiration times           |

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
