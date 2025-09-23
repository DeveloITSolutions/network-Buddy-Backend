"""
Authentication endpoints for The Plugs platform.
"""
from fastapi import APIRouter, HTTPException, status, Request

from app.core.dependencies import DatabaseSession, CurrentActiveUser
from app.core.rate_limiter import rate_limit, get_client_identifier
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
@rate_limit("login", lambda req, db: req.email.lower().strip())
async def login_user(
    request: UserLoginRequest,
    db: DatabaseSession,
    http_request: Request
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
        ip_address = get_client_identifier(http_request)
        user_agent = http_request.headers.get("User-Agent")
        return await auth_service.login_user(request, ip_address, user_agent)
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
@rate_limit("otp_send", lambda req, db, http_req: req.email.lower().strip())
async def send_otp(
    request: SendOTPRequest,
    db: DatabaseSession,
    http_request: Request
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
        ip_address = get_client_identifier(http_request)
        user_agent = http_request.headers.get("User-Agent")
        return await auth_service.send_otp(request, ip_address, user_agent)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )


@router.post("/verify-otp", response_model=VerifyOTPResponse)
@rate_limit("otp_verify", lambda req, db, http_req: req.email.lower().strip())
async def verify_otp(
    request: VerifyOTPRequest,
    db: DatabaseSession,
    http_request: Request
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
        ip_address = get_client_identifier(http_request)
        user_agent = http_request.headers.get("User-Agent")
        return await auth_service.verify_otp(request, ip_address, user_agent)
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
@rate_limit("password_change", lambda req, db, http_req: req.email.lower().strip())
async def change_password(
    request: ChangePasswordRequest,
    db: DatabaseSession,
    http_request: Request
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
        ip_address = get_client_identifier(http_request)
        user_agent = http_request.headers.get("User-Agent")
        return await auth_service.change_password(request, ip_address, user_agent)
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


@router.put("/timezone", response_model=TimezoneResponse)
async def update_timezone(
    request: UpdateTimezoneRequest,
    db: DatabaseSession,
    current_user: CurrentActiveUser
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
