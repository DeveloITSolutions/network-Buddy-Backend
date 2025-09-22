"""
User management endpoints - Simplified for The Plugs.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import DatabaseSession, CurrentUser
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get current authenticated user information."""
    try:
        user = db.query(User).filter(
            User.id == current_user["user_id"],
            User.is_deleted == False
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
