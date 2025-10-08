"""
Base service for event-related operations with common validation and ownership checks.
"""
import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError
from app.repositories.event_repository import EventRepository
from app.repositories.plug_repository import PlugRepository

logger = logging.getLogger(__name__)


class EventBaseService:
    """
    Base service providing common event-related functionality.
    """
    
    def __init__(self, db: Session):
        """Initialize base service with database session."""
        self.db = db
        self.event_repo = EventRepository(db)
        self.plug_repo = PlugRepository(db)
    
    async def _verify_event_ownership(self, user_id: UUID, event_id: UUID) -> Optional[Any]:
        """
        Verify that the event belongs to the user.
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            Event if found and owned by user, None otherwise
            
        Raises:
            ValidationError: If access is denied
        """
        event = await self.event_repo.get(event_id)
        if event and event.user_id != user_id:
            raise ValidationError(
                "Event not found or access denied",
                error_code="EVENT_ACCESS_DENIED"
            )
        return event
    
    async def _verify_plug_ownership(self, user_id: UUID, plug_id: UUID) -> Optional[Any]:
        """
        Verify that the plug belongs to the user.
        
        Args:
            user_id: User ID
            plug_id: Plug ID
            
        Returns:
            Plug if found and owned by user, None otherwise
            
        Raises:
            ValidationError: If access is denied
        """
        plug = await self.plug_repo.get(plug_id)
        if plug and plug.user_id != user_id:
            raise ValidationError(
                "Plug not found or access denied",
                error_code="PLUG_ACCESS_DENIED"
            )
        return plug
    
    def _convert_urls_to_strings(self, data: dict) -> dict:
        """
        Convert Pydantic URL objects to strings in data dictionary.
        
        Args:
            data: Data dictionary that may contain URL objects
            
        Returns:
            Data dictionary with URLs converted to strings
        """
        url_fields = ['website_url', 'cover_image_url']
        
        for field in url_fields:
            if field in data and data[field] is not None:
                data[field] = str(data[field])
        
        return data
    
    def _convert_tags_to_string(self, data: dict) -> dict:
        """
        Convert tags list to comma-separated string for database storage.
        
        Args:
            data: Data dictionary that may contain tags list
            
        Returns:
            Data dictionary with tags converted to string
        """
        if 'tags' in data and data['tags'] is not None:
            if isinstance(data['tags'], list):
                data['tags'] = ','.join(data['tags'])
        
        return data
    
    async def _validate_event_creation(self, user_id: UUID, event_data: Any) -> None:
        """
        Validate event creation business rules.
        
        Args:
            user_id: User ID
            event_data: Event creation data
            
        Raises:
            ValidationError: If validation fails
        """
        # No duplicate validation - only start_date uniqueness is enforced at database level
        pass
    
    async def _validate_agenda_creation(self, event: Any, agenda_data: Any) -> None:
        """
        Validate agenda creation business rules.
        
        Args:
            event: Event object
            agenda_data: Agenda creation data
            
        Raises:
            ValidationError: If validation fails
        """
        # Check if day is within event range
        if agenda_data.day > event.total_days:
            raise ValidationError(
                f"Day {agenda_data.day} exceeds event duration of {event.total_days} days",
                error_code="INVALID_AGENDA_DAY"
            )
    
    def _build_filter_dict(self, filters: Any) -> dict:
        """
        Build filter dictionary from EventFilters schema.
        
        Args:
            filters: EventFilters schema object
            
        Returns:
            Dictionary with filter conditions
        """
        filter_dict = {}
        
        if hasattr(filters, 'start_date_from') and filters.start_date_from:
            filter_dict["start_date__gte"] = filters.start_date_from
        if hasattr(filters, 'start_date_to') and filters.start_date_to:
            filter_dict["start_date__lte"] = filters.start_date_to
        if hasattr(filters, 'is_active') and filters.is_active is not None:
            filter_dict["is_active"] = filters.is_active
        if hasattr(filters, 'is_public') and filters.is_public is not None:
            filter_dict["is_public"] = filters.is_public
        if hasattr(filters, 'city') and filters.city:
            filter_dict["city"] = filters.city
        if hasattr(filters, 'country') and filters.country:
            filter_dict["country"] = filters.country
        
        return filter_dict
