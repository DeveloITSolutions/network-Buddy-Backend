"""
User detail service for comprehensive dashboard data aggregation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.event import Event, EventAgenda, EventMedia, EventMediaZone
from app.models.plug import Plug, PlugType
from app.models.event import EventPlugMedia
from app.schemas.user_detail import (
    UserDetailResponse, UserProfile, DashboardMetrics, EventSummary,
    RecentPlug, MediaDrop, ActiveUser, EventStatus, MediaCategory
)
from app.services.base_service import BaseService


class UserDetailService(BaseService[User]):
    """Service for comprehensive user detail data aggregation."""

    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_model_class(self) -> type[User]:
        """Get the User model class."""
        return User
    
    def _get_user_profile(self, user: User) -> UserProfile:
        """Convert User model to UserProfile schema."""
        return UserProfile(
            id=str(user.id),
            email=user.email,                                                                                                                                                                                                                                                                                                                                       
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            profile_picture=user.profile_picture,
            timezone=user.timezone,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
    
    def _get_dashboard_metrics(self, user_id: str) -> DashboardMetrics:
        """Get dashboard metrics for the user."""
        # Count events
        events_count = self.db.query(Event).filter(
            and_(Event.user_id == user_id, Event.is_deleted == False)
        ).count()
        
        # Count leads (targets)
        leads_count = self.db.query(Plug).filter(
            and_(
                Plug.user_id == user_id,
                Plug.plug_type == PlugType.TARGET,
                Plug.is_deleted == False
            )
        ).count()
        
        # Count contacts
        contacts_count = self.db.query(Plug).filter(
            and_(
                Plug.user_id == user_id,
                Plug.plug_type == PlugType.CONTACT,
                Plug.is_deleted == False
            )
        ).count()
        
        # Count media drops (event media + plug media)
        event_media_count = self.db.query(EventMedia).join(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.is_deleted == False,
                EventMedia.is_deleted == False
            )
        ).count()
        
        plug_media_count = self.db.query(EventPlugMedia).join(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.is_deleted == False,
                EventPlugMedia.is_deleted == False
            )
        ).count()
        
        media_drops_count = event_media_count + plug_media_count
        
        return DashboardMetrics(
            events_count=events_count,
            leads_count=leads_count,
            contacts_count=contacts_count,
            media_drops_count=media_drops_count
        )
    
    def _get_event_summary(self, event: Event) -> EventSummary:
        """Convert Event model to EventSummary schema."""
        # Determine event status
        now = datetime.now(timezone.utc)
        if event.start_date and event.end_date:
            if now < event.start_date:
                status = EventStatus.UPCOMING
            elif event.start_date <= now <= event.end_date:
                status = EventStatus.HAPPENING_NOW
            else:
                status = EventStatus.PAST
        else:
            status = EventStatus.UPCOMING
        
        # Get agenda count
        agenda_count = self.db.query(EventAgenda).filter(
            and_(
                EventAgenda.event_id == event.id,
                EventAgenda.is_deleted == False
            )
        ).count()
        
        # Get plug counts
        plug_counts = event.plug_counts
        
        return EventSummary(
            id=str(event.id),
            title=event.title or "Untitled Event",
            theme=event.theme,
            description=event.description,
            start_date=event.start_date.isoformat() if event.start_date else "",
            end_date=event.end_date.isoformat() if event.end_date else "",
            location_name=event.location_name,
            city=event.city,
            state=event.state,
            country=event.country,
            display_address=event.display_address,
            cover_image_url=event.cover_image_url,
            is_active=event.is_active,
            is_public=event.is_public,
            total_days=event.total_days,
            current_day=event.current_day,
            is_happening_now=event.is_happening_now,
            status=status,
            agenda_count=agenda_count,
            plug_counts=plug_counts
        )
    
    def _get_current_event(self, user_id: str) -> Optional[EventSummary]:
        """Get currently happening event for the user."""
        now = datetime.now(timezone.utc)
        
        current_event = self.db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.is_deleted == False,
                Event.is_active == True,
                Event.start_date <= now,
                Event.end_date >= now
            )
        ).order_by(Event.start_date.desc()).first()
        
        if current_event:
            return self._get_event_summary(current_event)
        return None
    
    def _get_upcoming_event(self, user_id: str) -> Optional[EventSummary]:
        """Get next upcoming event for the user."""
        now = datetime.now(timezone.utc)
        
        upcoming_event = self.db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.is_deleted == False,
                Event.is_active == True,
                Event.start_date > now
            )
        ).order_by(Event.start_date.asc()).first()
        
        if upcoming_event:
            return self._get_event_summary(upcoming_event)
        return None
    
    def _get_recent_plugs(self, user_id: str, limit: int = 3) -> List[RecentPlug]:
        """Get recent plugs for the user."""
        recent_plugs = self.db.query(Plug).filter(
            and_(
                Plug.user_id == user_id,
                Plug.is_deleted == False
            )
        ).order_by(Plug.updated_at.desc()).limit(limit).all()
        
        result = []
        for plug in recent_plugs:
            result.append(RecentPlug(
                id=str(plug.id),
                plug_type=plug.plug_type,
                first_name=plug.first_name,
                last_name=plug.last_name,
                full_name=plug.full_name,
                job_title=plug.job_title,
                company=plug.company,
                profile_picture=plug.profile_picture,
                priority=plug.priority.value if plug.priority else None,
                network_type=plug.network_type,
                business_type=plug.business_type,
                created_at=plug.created_at.isoformat(),
                updated_at=plug.updated_at.isoformat()
            ))
        
        return result
    
    def _get_latest_media_drops(self, user_id: str, limit: int = 2) -> List[MediaDrop]:
        """Get latest media drops for the user."""
        # Get event media
        event_media = self.db.query(EventMedia).join(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.is_deleted == False,
                EventMedia.is_deleted == False
            )
        ).order_by(EventMedia.created_at.desc()).limit(limit).all()
        
        result = []
        for media in event_media:
            # Determine media category
            if media.file_type.startswith('image/'):
                category = MediaCategory.IMAGE
            elif media.file_type.startswith('video/'):
                category = MediaCategory.VIDEO
            elif media.file_type.startswith('audio/'):
                category = MediaCategory.VOICE
            else:
                category = MediaCategory.DOCUMENT
            
            result.append(MediaDrop(
                id=str(media.id),
                file_url=media.file_url,
                file_type=media.file_type,
                media_category=category,
                file_size=media.file_size,
                event_id=str(media.event_id),
                event_title=media.event.title if media.event else None,
                plug_id=None,
                plug_name=None,
                created_at=media.created_at.isoformat(),
                thumbnail_url=media.file_url if category in [MediaCategory.IMAGE, MediaCategory.VIDEO] else None
            ))
        
        # Get plug media if we need more items
        if len(result) < limit:
            remaining_limit = limit - len(result)
            plug_media = self.db.query(EventPlugMedia).join(Event).filter(
                and_(
                    Event.user_id == user_id,
                    Event.is_deleted == False,
                    EventPlugMedia.is_deleted == False
                )
            ).order_by(EventPlugMedia.created_at.desc()).limit(remaining_limit).all()
            
            for media in plug_media:
                # Determine media category
                if media.media_category == 'snap':
                    category = MediaCategory.SNAP
                elif media.media_category == 'voice':
                    category = MediaCategory.VOICE
                else:
                    category = MediaCategory.IMAGE
                
                result.append(MediaDrop(
                    id=str(media.id),
                    file_url=media.file_url,
                    file_type=media.file_type,
                    media_category=category,
                    file_size=None,
                    event_id=str(media.event_id),
                    event_title=media.event.title if media.event else None,
                    plug_id=str(media.plug_id),
                    plug_name=media.plug.full_name if media.plug else None,
                    created_at=media.created_at.isoformat(),
                    thumbnail_url=media.file_url if category in [MediaCategory.SNAP, MediaCategory.IMAGE] else None
                ))
        
        # Sort by creation date and limit
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result[:limit]
    
    def _get_active_users(self, user_id: str, limit: int = 3) -> List[ActiveUser]:
        """Get active users for chat bubbles (mock data for now)."""
        # This would typically come from a real-time system or session tracking
        # For now, we'll return a mock list or empty list
        # In a real implementation, this would query active sessions or recent activity
        
        # Mock active users - in production, this would be from session tracking
        mock_active_users = [
            ActiveUser(
                id="mock-user-1",
                first_name="Sarah",
                last_name="Johnson",
                full_name="Sarah Johnson",
                profile_picture="https://via.placeholder.com/40",
                last_seen=datetime.now(timezone.utc).isoformat()
            ),
            ActiveUser(
                id="mock-user-2",
                first_name="Michael",
                last_name="Chen",
                full_name="Michael Chen",
                profile_picture="https://via.placeholder.com/40",
                last_seen=datetime.now(timezone.utc).isoformat()
            )
        ]
        
        return mock_active_users[:limit]
    
    def get_user_detail(self, user_id: str, request_params: Optional[Dict[str, Any]] = None) -> UserDetailResponse:
        """
        Get comprehensive user detail data for dashboard.
        
        Args:
            user_id: User ID
            request_params: Optional request parameters for filtering
            
        Returns:
            UserDetailResponse: Comprehensive user detail data
            
        Raises:
            NotFoundError: If user not found
        """
        # Get user
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Parse request parameters
        include_events = request_params.get('include_events', True) if request_params else True
        include_plugs = request_params.get('include_plugs', True) if request_params else True
        include_media = request_params.get('include_media', True) if request_params else True
        include_active_users = request_params.get('include_active_users', True) if request_params else True
        recent_plugs_limit = request_params.get('recent_plugs_limit', 3) if request_params else 3
        recent_media_limit = request_params.get('recent_media_limit', 2) if request_params else 2
        active_users_limit = request_params.get('active_users_limit', 3) if request_params else 3
        
        # Get user profile
        profile = self._get_user_profile(user)
        
        # Get dashboard metrics
        metrics = self._get_dashboard_metrics(user_id)
        
        # Get current event
        current_event = None
        if include_events:
            current_event = self._get_current_event(user_id)
        
        # Get upcoming event
        upcoming_event = None
        if include_events:
            upcoming_event = self._get_upcoming_event(user_id)
        
        # Get recent plugs
        recent_plugs = []
        if include_plugs:
            recent_plugs = self._get_recent_plugs(user_id, recent_plugs_limit)
        
        # Get latest media drops
        latest_media_drops = []
        if include_media:
            latest_media_drops = self._get_latest_media_drops(user_id, recent_media_limit)
        
        # Get active users
        active_users = []
        if include_active_users:
            active_users = self._get_active_users(user_id, active_users_limit)
        
        # Get total counts
        total_events = metrics.events_count
        total_plugs = metrics.leads_count + metrics.contacts_count
        total_media = metrics.media_drops_count
        
        return UserDetailResponse(
            profile=profile,
            metrics=metrics,
            current_event=current_event,
            upcoming_event=upcoming_event,
            recent_plugs=recent_plugs,
            latest_media_drops=latest_media_drops,
            active_users=active_users,
            total_events=total_events,
            total_plugs=total_plugs,
            total_media=total_media
        )
