"""
Authentication service for user management and OTP verification.
"""
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from app.utils.datetime import get_current_utc_time
import logging

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config.settings import settings
from app.config.security import security_config
from app.core.exceptions import ValidationError, NotFoundError
from app.models.user import User
from app.schemas.auth import (
    UserLoginRequest, ResetPasswordRequest, SendOTPRequest,
    VerifyOTPRequest, ChangePasswordRequest,
    AuthResponse, AuthTokenResponse, UserResponse, MessageResponse,
    OTPResponse, VerifyOTPResponse
)
from app.services.base_service import BaseService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class AuthService(BaseService[User]):
    """Authentication service for user management."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cache_service = CacheService()
        self.otp_expiry = 300  # 5 minutes
        self.verification_token_expiry = 1800  # 30 minutes
    
    def get_model_class(self) -> type[User]:
        """Get the User model class."""
        return User
    
    def _generate_otp(self) -> str:
        """Generate a 6-digit OTP code."""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def _generate_verification_token(self) -> str:
        """Generate a secure verification token for password change."""
        return security_config.generate_secure_token(32)
    
    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.get_by_field("email", email)
    
    def _create_auth_tokens(self, user: User) -> AuthTokenResponse:
        """Create JWT tokens for authenticated user."""
        # Token payload
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "is_active": user.is_active
        }
        
        # Create access token
        access_token = security_config.create_access_token(token_data)
        
        # Create refresh token
        refresh_token = security_config.create_refresh_token({"user_id": str(user.id)})
        
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
    
    def _user_to_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse schema."""
        return UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            timezone=user.timezone,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
    
    async def send_otp(self, request: SendOTPRequest) -> OTPResponse:
        """
        Send OTP to user's email.
        
        Args:
            request: SendOTPRequest containing email address
            
        Returns:
            OTPResponse with success status and expiration time
            
        Raises:
            HTTPException: If OTP sending fails
        """
        try:
            # Generate secure OTP
            otp_code = self._generate_otp()
            
            # Store OTP in cache with expiration
            if not self.cache_service.set_otp(request.email, otp_code):
                self.logger.error(f"Failed to store OTP in cache for {request.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process OTP request"
                )
            
            # Send OTP email asynchronously
            from app.workers.email_worker import send_otp_email
            send_otp_email.delay(
                to_email=request.email,
                otp_code=otp_code,
                expires_minutes=self.otp_expiry // 60
            )
            
            self.logger.info(f"OTP sent successfully to {request.email}")
            
            return OTPResponse(
                message="OTP sent successfully",
                email=request.email,
                expires_in=self.otp_expiry
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self._handle_generic_error(e, "send OTP")
    
    async def verify_otp(self, request: VerifyOTPRequest) -> VerifyOTPResponse:
        """
        Verify OTP and return token for password change.
        
        Args:
            request: VerifyOTPRequest containing email and OTP code
            
        Returns:
            VerifyOTPResponse with verification token and expiration time
            
        Raises:
            ValidationError: If OTP is invalid or expired
            HTTPException: If verification fails
        """
        try:
            # Get OTP from cache
            stored_otp = self.cache_service.get_otp(request.email)
            
            if not stored_otp:
                self.logger.warning(f"OTP verification failed for {request.email}: OTP not found or expired")
                raise ValidationError("OTP has expired or is invalid")
            
            if stored_otp != request.otp_code:
                self.logger.warning(f"OTP verification failed for {request.email}: Invalid OTP code")
                raise ValidationError("Invalid OTP code")
            
            # Remove OTP from cache after successful verification
            self.cache_service.delete_otp(request.email)
            
            # Generate secure verification token
            verification_token = self._generate_verification_token()
            
            # Store verification token in cache
            if not self.cache_service.set_verification_token(request.email, verification_token):
                self.logger.error(f"Failed to store verification token for {request.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process verification"
                )
            
            self.logger.info(f"OTP verified successfully for {request.email}")
            
            return VerifyOTPResponse(
                message="OTP verified successfully",
                email=request.email,
                token=verification_token,
                expires_in=self.verification_token_expiry
            )
            
        except ValidationError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            self._handle_generic_error(e, "verify OTP")
    
    # Removed register_user method - no signup functionality needed
    
    async def login_user(self, request: UserLoginRequest) -> AuthResponse:
        """Authenticate user and return tokens."""
        try:
            # Get user
            user = self._get_user_by_email(request.email)
            if not user:
                raise ValidationError("Invalid email or password")
            
            # Verify password
            if not security_config.verify_password(request.password, user.password):
                raise ValidationError("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise ValidationError("Account is deactivated")
            
            # Note: Email verification removed as per simplified schema
            # Note: last_login field removed as per simplified schema
            
            # Create tokens
            tokens = self._create_auth_tokens(user)
            user_response = self._user_to_response(user)
            
            self.logger.info(f"User logged in successfully: {user.email}")
            
            return AuthResponse(
                user=user_response,
                tokens=tokens
            )
            
        except ValidationError:
            raise
        except Exception as e:
            self._handle_generic_error(e, "login user")
    
    async def reset_password(self, request: ResetPasswordRequest) -> MessageResponse:
        """Reset password - sends OTP to user's email."""
        try:
            # Check if user exists
            user = self._get_user_by_email(request.email)
            if not user:
                # Don't reveal if email exists or not
                return MessageResponse(
                    message="If the email exists, an OTP has been sent",
                    success=True
                )
            
            # Generate and send OTP
            otp_code = self._generate_otp()
            
            # Store OTP in cache
            self.cache_service.set_otp(request.email, otp_code)
            
            # Send OTP email
            from app.workers.email_worker import send_otp_email
            send_otp_email.delay(
                to_email=user.email,
                otp_code=otp_code,
                expires_minutes=self.otp_expiry // 60
            )
            
            self.logger.info(f"Password reset OTP sent to: {user.email}")
            
            return MessageResponse(
                message="If the email exists, an OTP has been sent",
                success=True
            )
            
        except Exception as e:
            self._handle_generic_error(e, "process password reset")
    
    async def change_password(self, request: ChangePasswordRequest) -> MessageResponse:
        """
        Change password using verification token.
        
        Args:
            request: ChangePasswordRequest containing email, new password, and token
            
        Returns:
            MessageResponse with success status
            
        Raises:
            ValidationError: If token is invalid or expired
            NotFoundError: If user is not found
            HTTPException: If password change fails
        """
        try:
            # Verify the token
            stored_token = self.cache_service.get_verification_token(request.email)
            
            if not stored_token or stored_token != request.token:
                self.logger.warning(f"Password change failed for {request.email}: Invalid or expired token")
                raise ValidationError("Invalid or expired verification token")
            
            # Get user
            user = self._get_user_by_email(request.email)
            if not user:
                self.logger.warning(f"Password change failed: User not found for {request.email}")
                raise NotFoundError("User not found")
            
            # Update password with secure hashing
            user.password = security_config.hash_password(request.new_password)
            user.updated_at = get_current_utc_time()
            
            try:
                self.db.commit()
            except Exception as db_error:
                self.logger.error(f"Database error during password change for {request.email}: {db_error}")
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update password"
                )
            
            # Remove verification token from cache
            self.cache_service.delete_verification_token(request.email)
            
            self.logger.info(f"Password changed successfully for: {user.email}")
            
            return MessageResponse(
                message="Password changed successfully",
                success=True
            )
            
        except (ValidationError, NotFoundError):
            raise
        except HTTPException:
            raise
        except Exception as e:
            self._handle_generic_error(e, "change password")

    async def update_timezone(self, user_id: str, timezone: str) -> "TimezoneResponse":
        """
        Update user's timezone.
        
        Args:
            user_id: User ID
            timezone: IANA timezone identifier
            
        Returns:
            TimezoneResponse: Updated timezone information
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If timezone is invalid
        """
        try:
            from zoneinfo import ZoneInfo
            from app.schemas.auth import TimezoneResponse
            
            # Get user
            user = self.get_by_id(user_id)
            if not user:
                self.logger.warning(f"Timezone update failed: User not found for ID {user_id}")
                raise NotFoundError("User not found")
            
            # Validate timezone
            try:
                zone_info = ZoneInfo(timezone)
            except Exception:
                self.logger.warning(f"Invalid timezone provided: {timezone}")
                raise ValidationError("Invalid timezone identifier")
            
            # Update timezone
            user.timezone = timezone
            user.updated_at = get_current_utc_time()
            
            try:
                self.db.commit()
            except Exception as db_error:
                self.logger.error(f"Database error during timezone update for user {user_id}: {db_error}")
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update timezone"
                )
            
            # Get UTC offset for response
            now = datetime.now(zone_info)
            utc_offset = now.strftime("%z")
            utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}" if utc_offset else "+00:00"
            
            self.logger.info(f"Timezone updated successfully for user {user.email}: {timezone}")
            
            return TimezoneResponse(
                message="Timezone updated successfully",
                success=True,
                timezone=timezone,
                utc_offset=utc_offset_formatted
            )
            
        except (ValidationError, NotFoundError):
            raise
        except HTTPException:
            raise
        except Exception as e:
            self._handle_generic_error(e, "update timezone")
