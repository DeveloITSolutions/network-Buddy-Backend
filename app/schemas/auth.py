"""
Authentication schemas for request/response validation.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from zoneinfo import ZoneInfo, available_timezones

from app.utils.validators import validate_password


class UserLoginRequest(BaseModel):
    """User login request schema."""
        
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class ResetPasswordRequest(BaseModel):
    """Reset password request schema - sends OTP to email."""
    
    email: EmailStr = Field(..., description="User email address")


class SendOTPRequest(BaseModel):
    """Send OTP request schema."""
    
    email: EmailStr = Field(..., description="Email address to send OTP to")


class VerifyOTPRequest(BaseModel):
    """Verify OTP request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    @field_validator('otp_code')
    @classmethod
    def validate_otp_format(cls, v):
        """Validate OTP is 6 digits."""
        if not re.match(r'^\d{6}$', v):
            raise ValueError("OTP must be exactly 6 digits")
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    token: str = Field(..., description="Verification token from OTP verification")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate new password meets security requirements."""
        try:
            validate_password(v)
            return v
        except Exception as e:
            raise ValueError(str(e))


class AuthTokenResponse(BaseModel):
    """Authentication token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class UserResponse(BaseModel):
    """User information response schema."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    timezone: str = Field(..., description="User timezone")
    is_active: bool = Field(..., description="User active status")
    created_at: str = Field(..., description="User creation timestamp")
    updated_at: str = Field(..., description="User last update timestamp")
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Complete authentication response schema."""
    
    user: UserResponse = Field(..., description="User information")
    tokens: AuthTokenResponse = Field(..., description="Authentication tokens")


class MessageResponse(BaseModel):
    """Generic message response schema."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")


class OTPResponse(MessageResponse):
    """OTP response schema."""
    
    email: str = Field(..., description="Email address")
    expires_in: int = Field(..., description="OTP expiration time in seconds")


class VerifyOTPResponse(MessageResponse):
    """OTP verification response schema."""
    
    email: str = Field(..., description="Verified email address")
    token: str = Field(..., description="Verification token for password change")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class UpdateTimezoneRequest(BaseModel):
    """Update user timezone request schema."""
    
    timezone: str = Field(..., description="IANA timezone identifier (e.g., 'America/New_York', 'Europe/London')")
    
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is a valid IANA timezone identifier."""
        if v not in available_timezones():
            raise ValueError(f"Invalid timezone: {v}. Must be a valid IANA timezone identifier.")
        return v


class TimezoneResponse(BaseModel):
    """Timezone update response schema."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Operation success status")
    timezone: str = Field(..., description="Updated timezone")
    utc_offset: str = Field(..., description="UTC offset for the timezone")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(..., description="Valid refresh token")


class LogoutRequest(BaseModel):
    """Logout request schema."""
    
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")


