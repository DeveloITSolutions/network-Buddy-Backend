"""
Email worker for background email processing with SendGrid support.
"""
from typing import List, Dict, Any, Optional
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from .celery_app import celery_app
from app.config.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Send email asynchronously.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        from_email: Sender email (optional)
        html_body: HTML email body (optional)
        attachments: List of attachments (optional)
        
    Returns:
        Dict with send status and message ID
    """
    try:
        if not settings.smtp_host:
            logger.warning("SMTP not configured, skipping email send")
            return {"status": "skipped", "reason": "SMTP not configured"}
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_email or settings.smtp_username
        message["To"] = to_email
        
        # Add text part
        text_part = MIMEText(body, "plain")
        message.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment['filename']}"
                )
                message.attach(part)
        
        # Send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls(context=context)
            
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            
            text = message.as_string()
            server.sendmail(from_email or settings.smtp_username, to_email, text)
        
        logger.info(f"Email sent successfully to {to_email}")
        return {
            "status": "sent",
            "to_email": to_email,
            "subject": subject,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_bulk_email(
    self,
    email_list: List[Dict[str, Any]],
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email to multiple recipients.
    
    Args:
        email_list: List of email dictionaries with 'email' and optional 'name'
        subject: Email subject
        body: Plain text email body
        from_email: Sender email (optional)
        html_body: HTML email body (optional)
        
    Returns:
        Dict with send results
    """
    try:
        results = {
            "total": len(email_list),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for email_data in email_list:
            try:
                # Personalize subject and body if name is provided
                personalized_subject = subject
                personalized_body = body
                personalized_html = html_body
                
                if email_data.get("name"):
                    name = email_data["name"]
                    personalized_subject = subject.replace("{{name}}", name)
                    personalized_body = body.replace("{{name}}", name)
                    if html_body:
                        personalized_html = html_body.replace("{{name}}", name)
                
                # Send individual email
                send_email.delay(
                    to_email=email_data["email"],
                    subject=personalized_subject,
                    body=personalized_body,
                    from_email=from_email,
                    html_body=personalized_html
                )
                
                results["sent"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "email": email_data["email"],
                    "error": str(e)
                })
                logger.error(f"Failed to queue email for {email_data['email']}: {e}")
        
        logger.info(f"Bulk email processing completed: {results['sent']} sent, {results['failed']} failed")
        return results
        
    except Exception as e:
        logger.error(f"Bulk email processing failed: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_template_email(
    self,
    to_email: str,
    template_name: str,
    template_data: Dict[str, Any],
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email using a template.
    
    Args:
        to_email: Recipient email address
        template_name: Name of the email template
        template_data: Data to populate template
        from_email: Sender email (optional)
        
    Returns:
        Dict with send status
    """
    try:
        # TODO: Implement template loading and rendering
        # This would typically load templates from a template engine like Jinja2
        
        # For now, return a placeholder
        logger.info(f"Template email {template_name} queued for {to_email}")
        return {
            "status": "template_not_implemented",
            "to_email": to_email,
            "template_name": template_name,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.error(f"Failed to send template email {template_name} to {to_email}: {e}")
        raise


@celery_app.task(bind=True)
def send_notification_email(
    self,
    to_email: str,
    notification_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send notification email based on type.
    
    Args:
        to_email: Recipient email address
        notification_type: Type of notification
        data: Notification data
        
    Returns:
        Dict with send status
    """
    try:
        # Define notification templates
        templates = {
            "welcome": {
                "subject": "Welcome to The Plugs!",
                "body": "Welcome {{name}}! Thank you for joining The Plugs platform."
            },
            "password_reset": {
                "subject": "Password Reset Request",
                "body": "Click the link to reset your password: {{reset_link}}"
            },
            "event_reminder": {
                "subject": "Event Reminder: {{event_name}}",
                "body": "Don't forget about the upcoming event: {{event_name}} on {{event_date}}"
            },
            "connection_request": {
                "subject": "New Connection Request",
                "body": "{{requester_name}} wants to connect with you on The Plugs."
            }
        }
        
        if notification_type not in templates:
            raise ValueError(f"Unknown notification type: {notification_type}")
        
        template = templates[notification_type]
        
        # Replace placeholders with actual data
        subject = template["subject"]
        body = template["body"]
        
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        
        # Send the email
        return send_email.delay(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification email {notification_type} to {to_email}: {e}")
        raise


def _send_with_sendgrid(
    to_email: str,
    subject: str,
    plain_content: str,
    html_content: Optional[str] = None,
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """Send email using SendGrid API."""
    try:
        if not SENDGRID_AVAILABLE:
            raise Exception("SendGrid library not installed")
        
        if not settings.sendgrid_api_key:
            raise Exception("SendGrid API key not configured")
        
        # Create SendGrid client
        sg = SendGridAPIClient(api_key=settings.sendgrid_api_key)
        
        # Create mail object
        from_email = from_email or settings.sendgrid_from_email or settings.smtp_username
        
        message = Mail(
            from_email=From(from_email, settings.app_name),
            to_emails=To(to_email),
            subject=Subject(subject),
            plain_text_content=PlainTextContent(plain_content)
        )
        
        if html_content:
            message.html_content = HtmlContent(html_content)
        
        # Send email
        response = sg.send(message)
        
        return {
            "status": "sent",
            "provider": "sendgrid",
            "status_code": response.status_code,
            "message_id": response.headers.get("X-Message-Id")
        }
        
    except Exception as e:
        logger.error(f"SendGrid send failed: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_otp_email(
    self,
    to_email: str,
    otp_code: str,
    expires_minutes: int = 5
) -> Dict[str, Any]:
    """
    Send OTP verification email.
    
    Args:
        to_email: Recipient email address
        otp_code: 6-digit OTP code
        expires_minutes: OTP expiration time in minutes
        
    Returns:
        Dict with send status
    """
    try:
        subject = "Your Verification Code - The Plugs"
        
        # Plain text content
        plain_content = f"""
Your verification code is: {otp_code}

This code will expire in {expires_minutes} minutes.

If you didn't request this code, please ignore this email.

Best regards,
The Plugs Team
        """.strip()
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; }}
        .content {{ padding: 40px 20px; text-align: center; }}
        .otp-code {{ background-color: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px; padding: 20px; margin: 30px 0; font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #495057; }}
        .footer {{ padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #dee2e6; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 20px 0; color: #856404; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>The Plugs</h1>
        </div>
        <div class="content">
            <h2>Email Verification</h2>
            <p>Please use the following verification code to complete your registration:</p>
            <div class="otp-code">{otp_code}</div>
            <div class="warning">
                <strong>Important:</strong> This code will expire in {expires_minutes} minutes.
            </div>
            <p>If you didn't request this code, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 The Plugs. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Try SendGrid first, fallback to SMTP
        try:
            if settings.sendgrid_api_key:
                result = _send_with_sendgrid(to_email, subject, plain_content, html_content)
                logger.info(f"OTP email sent via SendGrid to {to_email}")
                return result
        except Exception as e:
            logger.warning(f"SendGrid failed, falling back to SMTP: {e}")
        
        # Fallback to SMTP
        result = send_email.delay(
            to_email=to_email,
            subject=subject,
            body=plain_content,
            html_body=html_content
        )
        
        logger.info(f"OTP email sent via SMTP to {to_email}")
        return {"status": "sent", "provider": "smtp", "task_id": self.request.id}
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_welcome_email(
    self,
    to_email: str,
    user_name: str
) -> Dict[str, Any]:
    """
    Send welcome email to new users.
    
    Args:
        to_email: Recipient email address
        user_name: User's full name
        
    Returns:
        Dict with send status
    """
    try:
        subject = f"Welcome to The Plugs, {user_name.split()[0]}!"
        
        # Plain text content
        plain_content = f"""
Hi {user_name},

Welcome to The Plugs! We're excited to have you join our professional networking community.

Your account has been successfully created and verified. You can now:
- Connect with professionals across industries
- Discover and attend networking events
- Build meaningful business relationships
- Expand your professional network

Get started by logging in to your account and completing your profile.

If you have any questions, feel free to reach out to our support team.

Best regards,
The Plugs Team
        """.strip()
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to The Plugs</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; }}
        .content {{ padding: 40px 20px; }}
        .welcome-message {{ text-align: center; margin-bottom: 30px; }}
        .features {{ margin: 30px 0; }}
        .feature {{ display: flex; align-items: center; margin: 15px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }}
        .feature-icon {{ width: 24px; height: 24px; margin-right: 15px; background-color: #667eea; border-radius: 50%; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #dee2e6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>The Plugs</h1>
        </div>
        <div class="content">
            <div class="welcome-message">
                <h2>Welcome, {user_name}! 🎉</h2>
                <p>We're excited to have you join our professional networking community.</p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon"></div>
                    <div>
                        <strong>Connect with Professionals</strong><br>
                        Build meaningful relationships across industries
                    </div>
                </div>
                <div class="feature">
                    <div class="feature-icon"></div>
                    <div>
                        <strong>Discover Events</strong><br>
                        Find and attend networking events in your area
                    </div>
                </div>
                <div class="feature">
                    <div class="feature-icon"></div>
                    <div>
                        <strong>Grow Your Network</strong><br>
                        Expand your professional connections and opportunities
                    </div>
                </div>
            </div>
            
            <div style="text-align: center;">
                <p>Ready to get started?</p>
                <a href="#" class="cta-button">Complete Your Profile</a>
            </div>
            
            <p>If you have any questions, feel free to reach out to our support team.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 The Plugs. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Try SendGrid first, fallback to SMTP
        try:
            if settings.sendgrid_api_key:
                result = _send_with_sendgrid(to_email, subject, plain_content, html_content)
                logger.info(f"Welcome email sent via SendGrid to {to_email}")
                return result
        except Exception as e:
            logger.warning(f"SendGrid failed, falling back to SMTP: {e}")
        
        # Fallback to SMTP
        result = send_email.delay(
            to_email=to_email,
            subject=subject,
            body=plain_content,
            html_body=html_content
        )
        
        logger.info(f"Welcome email sent via SMTP to {to_email}")
        return {"status": "sent", "provider": "smtp", "task_id": self.request.id}
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {to_email}: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_password_reset_email(
    self,
    to_email: str,
    user_name: str,
    reset_token: str
) -> Dict[str, Any]:
    """
    Send password reset email.
    
    Args:
        to_email: Recipient email address
        user_name: User's full name
        reset_token: Password reset token
        
    Returns:
        Dict with send status
    """
    try:
        subject = "Password Reset Request - The Plugs"
        
        # Create reset URL (you'll need to adjust this based on your frontend)
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}&email={to_email}"
        
        # Plain text content
        plain_content = f"""
Hi {user_name},

You requested a password reset for your The Plugs account.

Please use the following link to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
The Plugs Team
        """.strip()
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; }}
        .content {{ padding: 40px 20px; }}
        .reset-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 20px 0; color: #856404; }}
        .footer {{ padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #dee2e6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>The Plugs</h1>
        </div>
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>Hi {user_name},</p>
            <p>You requested a password reset for your The Plugs account.</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="reset-button">Reset Your Password</a>
            </div>
            
            <div class="warning">
                <strong>Important:</strong> This link will expire in 1 hour for security reasons.
            </div>
            
            <p>If you didn't request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 The Plugs. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Try SendGrid first, fallback to SMTP
        try:
            if settings.sendgrid_api_key:
                result = _send_with_sendgrid(to_email, subject, plain_content, html_content)
                logger.info(f"Password reset email sent via SendGrid to {to_email}")
                return result
        except Exception as e:
            logger.warning(f"SendGrid failed, falling back to SMTP: {e}")
        
        # Fallback to SMTP
        result = send_email.delay(
            to_email=to_email,
            subject=subject,
            body=plain_content,
            html_body=html_content
        )
        
        logger.info(f"Password reset email sent via SMTP to {to_email}")
        return {"status": "sent", "provider": "smtp", "task_id": self.request.id}
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        raise
