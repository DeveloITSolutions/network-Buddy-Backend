"""
Core event service for main event operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventUpdate, EventFilters, EventStats
from app.services.base_service import BaseService
from app.services.decorators import handle_service_errors, validate_search_term
from app.services.event_base_service import EventBaseService

logger = logging.getLogger(__name__)


class EventCoreService(EventBaseService):
    """
    Service for core event operations.
    """

    def __init__(self, db: Session):
        """Initialize event core service."""
        super().__init__(db)
        self.event_repo = EventRepository(db)

    @handle_service_errors("create event", "EVENT_CREATION_FAILED")
    async def create_event(self, user_id: UUID, event_data: EventCreate) -> Event:
        """
        Create a new event with business validation.
        
        Args:
            user_id: Owner user ID
            event_data: Event creation data
            
        Returns:
            Created event
        """
        # Validate business rules
        await self._validate_event_creation(user_id, event_data)
        
        # Convert schema to dict and process URLs
        event_dict = event_data.model_dump(exclude_unset=True)
        event_dict = self._convert_urls_to_strings(event_dict)
        
        # Create event through repository
        event = await self.event_repo.create_event(user_id, event_dict)
        
        logger.info(f"Created event {event.id} for user {user_id}")
        return event

    @handle_service_errors("update event", "EVENT_UPDATE_FAILED")
    async def update_event(
        self,
        user_id: UUID,
        event_id: UUID,
        update_data: EventUpdate
    ) -> Optional[Event]:
        """
        Update an existing event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            update_data: Update data
            
        Returns:
            Updated event or None if not found
        """
        # Verify ownership and existence
        event = await self._verify_event_ownership(user_id, event_id)
        if not event:
            return None
        
        # Convert schema to dict and process URLs
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict = self._convert_urls_to_strings(update_dict)
        
        # Update through repository
        updated_event = await self.event_repo.update(event_id, update_dict)
        
        logger.info(f"Updated event {event_id} for user {user_id}")
        return updated_event

    @handle_service_errors("delete event", "EVENT_DELETION_FAILED")
    async def delete_event(self, user_id: UUID, event_id: UUID) -> bool:
        """
        Delete a user's event (soft delete).
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            
        Returns:
            True if deleted, False if not found
        """
        # Verify ownership
        event = await self._verify_event_ownership(user_id, event_id)
        if not event:
            return False
        
        # Perform soft delete
        return await self.event_repo.delete(event_id, soft=True)

    @handle_service_errors("get event", "EVENT_RETRIEVAL_FAILED")
    async def get_user_event(self, user_id: UUID, event_id: UUID) -> Optional[Event]:
        """
        Get a specific event for a user.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            
        Returns:
            Event if found and owned by user, None otherwise
        """
        return await self._verify_event_ownership(user_id, event_id)

    @handle_service_errors("get user events", "USER_EVENTS_RETRIEVAL_FAILED")
    async def get_user_events(
        self,
        user_id: UUID,
        filters: Optional[EventFilters] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """
        Get paginated list of user's events with filtering.
        
        Args:
            user_id: Owner user ID
            filters: Filter criteria
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (events list, total count)
        """
        # Build filter dictionary
        filter_dict = {}
        if filters:
            filter_dict = self._build_filter_dict(filters)
        
        # Get events and count
        return await self.event_repo.get_user_events(
            user_id=user_id,
            skip=skip,
            limit=limit,
            filters=filter_dict
        )

    @handle_service_errors("search user events", "EVENT_SEARCH_FAILED")
    @validate_search_term
    async def search_user_events(
        self,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """
        Search user's events by term.
        
        Args:
            user_id: Owner user ID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (matching events list, total count)
        """
        return await self.event_repo.search_user_events(
            user_id=user_id,
            search_term=search_term,
            skip=skip,
            limit=limit
        )

    @handle_service_errors("get event statistics", "EVENT_STATS_FAILED")
    async def get_event_stats(self, user_id: UUID) -> EventStats:
        """
        Get statistics about user's events.
        
        Args:
            user_id: User ID
            
        Returns:
            Event statistics
        """
        stats_data = await self.event_repo.get_user_event_stats(user_id)
        return EventStats(**stats_data)
