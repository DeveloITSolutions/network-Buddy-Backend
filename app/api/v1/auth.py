"""
Authentication endpoints for The Plugs platform.
"""
from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DatabaseSession
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserLoginRequest, ResetPasswordRequest, SendOTPRequest,
    VerifyOTPRequest, ChangePasswordRequest, UpdateTimezoneRequest,
    AuthResponse, MessageResponse, OTPResponse, VerifyOTPResponse, TimezoneResponse
)
from app.core.exceptions import ValidationError, NotFoundError
from app.utils.timezone import get_common_timezones, get_user_friendly_timezone_list

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def login_user(
    request: UserLoginRequest,
    db: DatabaseSession
):
    """
    User login with email and password.
    
    Authenticates the user and returns JWT tokens for accessing protected endpoints.
    
    Args:
        request: UserLoginRequest containing email and password
        db: Database session
        
    Returns:
        AuthResponse with user information and JWT tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.login_user(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user"
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: DatabaseSession
):
    """
    Reset password - sends OTP to user's email.
    
    This is the first step in the password reset flow.
    The user enters their email and receives a 6-digit OTP code.
    
    Security Note: Always returns success to prevent email enumeration attacks.
    
    Args:
        request: ResetPasswordRequest containing email address
        db: Database session
        
    Returns:
        MessageResponse with success status (always returns success for security)
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.reset_password(request)
    except Exception as e:
        # Always return success to prevent email enumeration
        return MessageResponse(
            message="If the email exists, an OTP has been sent",
            success=True
        )


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    request: SendOTPRequest,
    db: DatabaseSession
):
    """
    Send OTP to user's email.
    
    Sends a 6-digit OTP code to the specified email address.
    The OTP expires in 5 minutes for security.
    
    Args:
        request: SendOTPRequest containing email address
        db: Database session
        
    Returns:
        OTPResponse with success status and expiration time
        
    Raises:
        HTTPException: If OTP sending fails
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.send_otp(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )


@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: DatabaseSession
):
    """
    Verify OTP and return token for password change.
    
    Verifies the OTP code and returns a verification token
    that can be used to change the password. The token expires in 30 minutes.
    
    Args:
        request: VerifyOTPRequest containing email and OTP code
        db: Database session
        
    Returns:
        VerifyOTPResponse with verification token and expiration time
        
    Raises:
        HTTPException: If OTP verification fails
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.verify_otp(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    db: DatabaseSession
):
    """
    Change password using verification token.
    
    Changes the user's password using the token received from OTP verification.
    After successful password change, user should be redirected to login screen.
    
    Args:
        request: ChangePasswordRequest containing email, new password, and token
        db: Database session
        
    Returns:
        MessageResponse with success status
        
    Raises:
        HTTPException: If password change fails
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.change_password(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.put("/timezone/{user_id}", response_model=TimezoneResponse)
async def update_timezone(
    user_id: str,
    request: UpdateTimezoneRequest,
    db: DatabaseSession
):
    """
    Update user's timezone.
    
    Args:
        user_id: User ID
        request: Timezone update request
        db: Database session
        
    Returns:
        TimezoneResponse: Updated timezone information
        
    Raises:
        HTTPException: If user not found or timezone invalid
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.update_timezone(user_id, request.timezone)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update timezone"
        )


@router.get("/timezones")
async def get_timezones():
    """
    Get available timezones for frontend selection.
    
    Returns:
        Dict: List of available timezones grouped by region
    """
    try:
        return {
            "common_timezones": get_common_timezones(),
            "grouped_timezones": get_user_friendly_timezone_list()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get timezones"
        )
