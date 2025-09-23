"""
Security audit logging for authentication events.
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.utils.datetime import get_current_utc_time

# Configure security logger
security_logger = logging.getLogger("security_audit")


class SecurityEventType(str, Enum):
    """Security event types for audit logging."""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    
    # Password events
    PASSWORD_CHANGE_SUCCESS = "password_change_success"
    PASSWORD_CHANGE_FAILURE = "password_change_failure"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    
    # OTP events
    OTP_SEND_SUCCESS = "otp_send_success"
    OTP_SEND_FAILURE = "otp_send_failure"
    OTP_VERIFY_SUCCESS = "otp_verify_success"
    OTP_VERIFY_FAILURE = "otp_verify_failure"
    
    # Security violations
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Token events
    TOKEN_CREATED = "token_created"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_REVOKED = "token_revoked"


class SecurityAuditLogger:
    """Security audit logging service."""
    
    def __init__(self):
        self.logger = security_logger
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a security event with comprehensive details.
        
        Args:
            event_type: Type of security event
            user_email: User email (if applicable)
            user_id: User ID (if applicable)
            ip_address: Client IP address
            user_agent: Client user agent
            additional_data: Additional event-specific data
            success: Whether the operation was successful
            error_message: Error message for failed operations
        """
        event_data = {
            "timestamp": get_current_utc_time().isoformat(),
            "event_type": event_type.value,
            "success": success,
            "user_email": user_email,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "error_message": error_message,
            "additional_data": additional_data or {}
        }
        
        # Remove None values for cleaner logs
        event_data = {k: v for k, v in event_data.items() if v is not None}
        
        # Log at appropriate level based on event type and success
        if not success or event_type in [
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            SecurityEventType.ACCOUNT_LOCKED,
            SecurityEventType.SUSPICIOUS_ACTIVITY
        ]:
            self.logger.warning(f"SECURITY_EVENT: {json.dumps(event_data)}")
        else:
            self.logger.info(f"SECURITY_EVENT: {json.dumps(event_data)}")
    
    def log_login_attempt(
        self,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log login attempt."""
        event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILURE
        
        additional_data = {}
        if not success and failure_reason:
            additional_data["failure_reason"] = failure_reason
        
        self.log_security_event(
            event_type=event_type,
            user_email=email,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=failure_reason if not success else None,
            additional_data=additional_data
        )
    
    def log_password_change(
        self,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log password change attempt."""
        event_type = SecurityEventType.PASSWORD_CHANGE_SUCCESS if success else SecurityEventType.PASSWORD_CHANGE_FAILURE
        
        self.log_security_event(
            event_type=event_type,
            user_email=email,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=failure_reason if not success else None
        )
    
    def log_otp_event(
        self,
        event_type: SecurityEventType,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log OTP-related event."""
        self.log_security_event(
            event_type=event_type,
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=failure_reason if not success else None,
            additional_data=additional_data
        )
    
    def log_rate_limit_exceeded(
        self,
        endpoint: str,
        identifier: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log rate limit violation."""
        self.log_security_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            additional_data={
                "endpoint": endpoint,
                "identifier": identifier
            }
        )
    
    def log_account_lockout(
        self,
        email: str,
        duration: int,
        reason: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log account lockout event."""
        self.log_security_event(
            event_type=SecurityEventType.ACCOUNT_LOCKED,
            user_email=email,
            ip_address=ip_address,
            success=False,
            additional_data={
                "duration_seconds": duration,
                "reason": reason
            }
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        details: Dict[str, Any],
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log suspicious activity."""
        self.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            additional_data={
                "activity_type": activity_type,
                **details
            }
        )


# Global security audit logger instance
security_audit_logger = SecurityAuditLogger()
