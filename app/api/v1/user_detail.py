"""
User detail API endpoints for comprehensive dashboard data.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.dependencies import DatabaseSession, CurrentUser
from app.core.exceptions import NotFoundError
from app.services.user_detail_service import UserDetailService
from app.schemas.user_detail import UserDetailResponse, UserDetailRequest

router = APIRouter()


@router.get(
    "/me/detail",
    response_model=UserDetailResponse,
    summary="Get User Dashboard Details",
    description="""
    Get comprehensive user dashboard data including:
    - User profile information
    - Dashboard metrics (events, leads, contacts, media drops)
    - Current/active event
    - Upcoming event
    - Recent plugs (contacts/targets)
    - Latest media drops
    - Active users for chat
    
    This endpoint provides all the data needed for the main dashboard UI.
    """,
    tags=["User Dashboard"]
)
async def get_user_detail(
    current_user: CurrentUser,
    db: DatabaseSession,
    include_events: bool = Query(True, description="Include events data"),
    include_plugs: bool = Query(True, description="Include plugs data"),
    include_media: bool = Query(True, description="Include media data"),
    include_active_users: bool = Query(True, description="Include active users"),
    recent_plugs_limit: int = Query(3, ge=1, le=10, description="Limit for recent plugs (1-10)"),
    recent_media_limit: int = Query(2, ge=1, le=10, description="Limit for recent media drops (1-10)"),
    active_users_limit: int = Query(3, ge=1, le=10, description="Limit for active users (1-10)")
):
    """
    Get comprehensive user dashboard details.
    
    This endpoint aggregates data from multiple sources to provide a complete
    dashboard view for the authenticated user, matching the Figma design requirements.
    
    **Features:**
    - User profile information
    - Dashboard metrics (events, leads, contacts, media drops)
    - Current happening event with status
    - Next upcoming event
    - Recent plugs (contacts/targets) with details
    - Latest media drops with thumbnails
    - Active users for chat bubbles
    
    **Query Parameters:**
    - `include_events`: Include events data (default: true)
    - `include_plugs`: Include plugs data (default: true)
    - `include_media`: Include media data (default: true)
    - `include_active_users`: Include active users (default: true)
    - `recent_plugs_limit`: Limit for recent plugs (1-10, default: 3)
    - `recent_media_limit`: Limit for recent media drops (1-10, default: 2)
    - `active_users_limit`: Limit for active users (1-10, default: 3)
    
    **Response:**
    - Complete user dashboard data matching Figma design
    - All metrics and counts
    - Event information with proper status
    - Recent activity data
    - Media content with proper categorization
    
    **Authentication:**
    - Requires valid JWT token
    - Returns data for authenticated user only
    """
    try:
        user_id = current_user["user_id"]
        
        # Prepare request parameters
        request_params = {
            "include_events": include_events,
            "include_plugs": include_plugs,
            "include_media": include_media,
            "include_active_users": include_active_users,
            "recent_plugs_limit": recent_plugs_limit,
            "recent_media_limit": recent_media_limit,
            "active_users_limit": active_users_limit
        }
        
        # Get user detail service
        user_detail_service = UserDetailService(db)
        
        # Get comprehensive user detail data
        user_detail = user_detail_service.get_user_detail(user_id, request_params)
        
        return user_detail
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user detail: {str(e)}"
        )


@router.get(
    "/me/metrics",
    response_model=Dict[str, int],
    summary="Get User Dashboard Metrics",
    description="""
    Get only the dashboard metrics (counts) for the user.
    
    Returns:
    - events_count: Total number of events
    - leads_count: Total number of leads (targets)
    - contacts_count: Total number of contacts
    - media_drops_count: Total number of media drops
    """,
    tags=["User Dashboard"]
)
async def get_user_metrics(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    Get user dashboard metrics only.
    
    This is a lightweight endpoint that returns only the counts/metrics
    for the dashboard cards without the full detail data.
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user detail service
        user_detail_service = UserDetailService(db)
        
        # Get only metrics
        metrics = user_detail_service._get_dashboard_metrics(user_id)
        
        return {
            "events_count": metrics.events_count,
            "leads_count": metrics.leads_count,
            "contacts_count": metrics.contacts_count,
            "media_drops_count": metrics.media_drops_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user metrics: {str(e)}"
        )


@router.get(
    "/me/events/summary",
    response_model=Dict[str, Any],
    summary="Get User Events Summary",
    description="""
    Get summary of user's events including current and upcoming events.
    
    Returns:
    - current_event: Currently happening event (if any)
    - upcoming_event: Next upcoming event (if any)
    - total_events: Total number of events
    """,
    tags=["User Dashboard"]
)
async def get_user_events_summary(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    Get user events summary.
    
    Returns current and upcoming events for the dashboard.
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user detail service
        user_detail_service = UserDetailService(db)
        
        # Get events data
        current_event = user_detail_service._get_current_event(user_id)
        upcoming_event = user_detail_service._get_upcoming_event(user_id)
        metrics = user_detail_service._get_dashboard_metrics(user_id)
        
        return {
            "current_event": current_event.dict() if current_event else None,
            "upcoming_event": upcoming_event.dict() if upcoming_event else None,
            "total_events": metrics.events_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user events summary: {str(e)}"
        )
