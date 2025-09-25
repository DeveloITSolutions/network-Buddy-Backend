"""
Service layer for event business logic.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventAgenda, EventExpense, EventMedia, EventPlug
from app.repositories.event_repository import (
    EventRepository, EventAgendaRepository, EventExpenseRepository,
    EventMediaRepository, EventPlugRepository
)
from app.schemas.event import (
    EventCreate, EventUpdate, EventFilters, EventStats,
    EventAgendaCreate, EventAgendaUpdate,
    EventExpenseCreate, EventExpenseUpdate,
    EventMediaCreate, EventMediaUpdate,
    EventPlugCreate, EventPlugUpdate
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class EventService(BaseService[Event]):
    """
    Service for event business logic.
    """

    def __init__(self, db: Session):
        """Initialize event service with dependencies."""
        super().__init__(db)
        self.event_repo = EventRepository(db)
        self.agenda_repo = EventAgendaRepository(db)
        self.expense_repo = EventExpenseRepository(db)
        self.media_repo = EventMediaRepository(db)
        self.plug_repo = EventPlugRepository(db)

    def get_model_class(self) -> type[Event]:
        """Get the Event model class."""
        return Event

    # Event CRUD Operations
    async def create_event(self, user_id: UUID, event_data: EventCreate) -> Event:
        """
        Create a new event with business validation.
        
        Args:
            user_id: Owner user ID
            event_data: Event creation data
            
        Returns:
            Created event
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate business rules
            await self._validate_event_creation(user_id, event_data)
            
            # Convert schema to dict
            event_dict = event_data.model_dump(exclude_unset=True)
            
            # Convert Pydantic URLs to strings
            if 'website_url' in event_dict and event_dict['website_url'] is not None:
                event_dict['website_url'] = str(event_dict['website_url'])
            if 'cover_image_url' in event_dict and event_dict['cover_image_url'] is not None:
                event_dict['cover_image_url'] = str(event_dict['cover_image_url'])
            
            # Create event through repository
            event = await self.event_repo.create_event(user_id, event_dict)
            
            logger.info(f"Created event {event.id} for user {user_id}")
            return event
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating event for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to create event",
                error_code="EVENT_CREATION_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

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
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify ownership and existence
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                return None
            
            # Validate business rules
            await self._validate_event_update(event, update_data)
            
            # Convert schema to dict, excluding unset fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Convert Pydantic URLs to strings
            if 'website_url' in update_dict and update_dict['website_url'] is not None:
                update_dict['website_url'] = str(update_dict['website_url'])
            if 'cover_image_url' in update_dict and update_dict['cover_image_url'] is not None:
                update_dict['cover_image_url'] = str(update_dict['cover_image_url'])
            
            # Update through repository
            updated_event = await self.event_repo.update(event_id, update_dict)
            
            logger.info(f"Updated event {event_id} for user {user_id}")
            return updated_event
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating event {event_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to update event",
                error_code="EVENT_UPDATE_FAILED",
                details={"event_id": str(event_id), "user_id": str(user_id), "error": str(e)}
            )

    async def delete_event(self, user_id: UUID, event_id: UUID) -> bool:
        """
        Delete a user's event (soft delete).
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Verify ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                return False
            
            # Perform soft delete
            return await self.event_repo.delete(event_id, soft=True)
            
        except Exception as e:
            logger.error(f"Error deleting event {event_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to delete event",
                error_code="EVENT_DELETION_FAILED",
                details={"event_id": str(event_id), "user_id": str(user_id), "error": str(e)}
            )

    async def get_user_event(self, user_id: UUID, event_id: UUID) -> Optional[Event]:
        """
        Get a specific event for a user.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            
        Returns:
            Event if found and owned by user, None otherwise
        """
        try:
            return await self._verify_user_event_ownership(user_id, event_id)
        except Exception as e:
            logger.error(f"Error getting event {event_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to get event",
                error_code="EVENT_RETRIEVAL_FAILED",
                details={"event_id": str(event_id), "user_id": str(user_id), "error": str(e)}
            )

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
        try:
            # Build filter dictionary
            filter_dict = {}
            if filters:
                filter_dict = await self._build_filter_dict(filters)
            
            # Get events and count
            events, total_count = await self.event_repo.get_user_events(
                user_id=user_id,
                skip=skip,
                limit=limit,
                filters=filter_dict
            )
            
            return events, total_count
            
        except Exception as e:
            logger.error(f"Error getting events for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to get user events",
                error_code="USER_EVENTS_RETRIEVAL_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

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
        try:
            # Validate search term
            if not search_term or len(search_term.strip()) < 2:
                raise ValidationError(
                    "Search term must be at least 2 characters",
                    error_code="INVALID_SEARCH_TERM"
                )
            
            return await self.event_repo.search_user_events(
                user_id=user_id,
                search_term=search_term.strip(),
                skip=skip,
                limit=limit
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error searching events for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to search user events",
                error_code="EVENT_SEARCH_FAILED",
                details={"user_id": str(user_id), "search_term": search_term, "error": str(e)}
            )

    async def get_event_stats(self, user_id: UUID) -> EventStats:
        """
        Get statistics about user's events.
        
        Args:
            user_id: User ID
            
        Returns:
            Event statistics
        """
        try:
            stats_data = await self.event_repo.get_user_event_stats(user_id)
            return EventStats(**stats_data)
            
        except Exception as e:
            logger.error(f"Error getting event stats for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to get event statistics",
                error_code="EVENT_STATS_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

    # Agenda Operations (Deeds Module)
    async def create_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_data: EventAgendaCreate
    ) -> EventAgenda:
        """
        Create a new agenda item for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            agenda_data: Agenda creation data
            
        Returns:
            Created agenda item
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Validate agenda item
            await self._validate_agenda_creation(event, agenda_data)
            
            # Convert schema to dict
            agenda_dict = agenda_data.model_dump(exclude_unset=True)
            agenda_dict["event_id"] = event_id
            
            # Create agenda item
            agenda = await self.agenda_repo.create(agenda_dict)
            
            logger.info(f"Created agenda item {agenda.id} for event {event_id}")
            return agenda
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating agenda item for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to create agenda item",
                error_code="AGENDA_CREATION_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def get_event_agendas(
        self,
        user_id: UUID,
        event_id: UUID,
        day: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventAgenda], int]:
        """
        Get agenda items for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            day: Filter by specific day (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (agenda items list, total count)
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            return await self.agenda_repo.get_event_agendas(
                event_id=event_id,
                day=day,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error getting agendas for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to get event agendas",
                error_code="EVENT_AGENDAS_RETRIEVAL_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    # Expense Operations (Deeds Module)
    async def create_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_data: EventExpenseCreate
    ) -> EventExpense:
        """
        Create a new expense for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            expense_data: Expense creation data
            
        Returns:
            Created expense
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Convert schema to dict
            expense_dict = expense_data.model_dump(exclude_unset=True)
            expense_dict["event_id"] = event_id
            
            # Create expense
            expense = await self.expense_repo.create(expense_dict)
            
            logger.info(f"Created expense {expense.id} for event {event_id}")
            return expense
            
        except Exception as e:
            logger.error(f"Error creating expense for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to create expense",
                error_code="EXPENSE_CREATION_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def get_event_expenses(
        self,
        user_id: UUID,
        event_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventExpense], int]:
        """
        Get expenses for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            category: Filter by category (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (expenses list, total count)
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            return await self.expense_repo.get_event_expenses(
                event_id=event_id,
                category=category,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error getting expenses for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to get event expenses",
                error_code="EVENT_EXPENSES_RETRIEVAL_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    # Media Operations (Zone Module)
    async def create_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_data: EventMediaCreate
    ) -> EventMedia:
        """
        Create a new media item for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            media_data: Media creation data
            
        Returns:
            Created media item
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Convert schema to dict
            media_dict = media_data.model_dump(exclude_unset=True)
            media_dict["event_id"] = event_id
            
            # Convert tags list to comma-separated string for database storage
            if 'tags' in media_dict and media_dict['tags'] is not None:
                if isinstance(media_dict['tags'], list):
                    media_dict['tags'] = ','.join(media_dict['tags'])
            
            # Create media
            media = await self.media_repo.create(media_dict)
            
            logger.info(f"Created media {media.id} for event {event_id}")
            return media
            
        except Exception as e:
            logger.error(f"Error creating media for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to create media",
                error_code="MEDIA_CREATION_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def get_event_media(
        self,
        user_id: UUID,
        event_id: UUID,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """
        Get media for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            file_type: Filter by file type (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (media list, total count)
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            return await self.media_repo.get_event_media(
                event_id=event_id,
                file_type=file_type,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error getting media for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to get event media",
                error_code="EVENT_MEDIA_RETRIEVAL_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def get_event_media_item(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> Optional[EventMedia]:
        """
        Get a specific media item for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            media_id: Media ID
            
        Returns:
            Media item if found and owned by user, None otherwise
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Get media item
            media = await self.media_repo.get(media_id)
            if media and media.event_id != event_id:
                return None
                
            return media
            
        except Exception as e:
            logger.error(f"Error getting media item {media_id} for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to get media item",
                error_code="MEDIA_ITEM_RETRIEVAL_FAILED",
                details={"event_id": str(event_id), "media_id": str(media_id), "error": str(e)}
            )

    async def delete_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> bool:
        """
        Delete a media item from an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            media_id: Media ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Get media item to verify it belongs to the event
            media = await self.media_repo.get(media_id)
            if not media or media.event_id != event_id:
                return False
            
            # Delete media
            return await self.media_repo.delete(media_id, soft=True)
            
        except Exception as e:
            logger.error(f"Error deleting media {media_id} from event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to delete media",
                error_code="MEDIA_DELETION_FAILED",
                details={"event_id": str(event_id), "media_id": str(media_id), "error": str(e)}
            )

    # Event-Plug Operations
    async def add_plug_to_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        association_data: Optional[EventPlugCreate] = None
    ) -> EventPlug:
        """
        Add a plug to an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plug_id: Plug ID
            association_data: Additional association data
            
        Returns:
            Created event-plug association
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Verify plug ownership
            plug = await self._verify_user_plug_ownership(user_id, plug_id)
            if not plug:
                raise NotFoundError("Plug not found")
            
            # Prepare association data
            assoc_dict = {}
            if association_data:
                assoc_dict = association_data.model_dump(exclude_unset=True, exclude={"plug_id"})
            
            # Add plug to event
            event_plug = await self.plug_repo.add_plug_to_event(
                event_id=event_id,
                plug_id=plug_id,
                association_data=assoc_dict
            )
            
            logger.info(f"Added plug {plug_id} to event {event_id}")
            return event_plug
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding plug {plug_id} to event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to add plug to event",
                error_code="ADD_PLUG_TO_EVENT_FAILED",
                details={"event_id": str(event_id), "plug_id": str(plug_id), "error": str(e)}
            )

    async def get_event_plugs(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventPlug], int]:
        """
        Get plugs associated with an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plug_type: Filter by plug type (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (event-plug associations list, total count)
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            return await self.plug_repo.get_event_plugs(
                event_id=event_id,
                plug_type=plug_type,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error getting plugs for event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to get event plugs",
                error_code="EVENT_PLUGS_RETRIEVAL_FAILED",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def remove_plug_from_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID
    ) -> bool:
        """
        Remove a plug from an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plug_id: Plug ID
            
        Returns:
            True if removed, False if not found
        """
        try:
            # Verify event ownership
            event = await self._verify_user_event_ownership(user_id, event_id)
            if not event:
                raise NotFoundError("Event not found")
            
            # Remove plug from event
            removed = await self.plug_repo.remove_plug_from_event(
                event_id=event_id,
                plug_id=plug_id
            )
            
            if removed:
                logger.info(f"Removed plug {plug_id} from event {event_id}")
            
            return removed
            
        except Exception as e:
            logger.error(f"Error removing plug {plug_id} from event {event_id}: {e}")
            raise BusinessLogicError(
                "Failed to remove plug from event",
                error_code="REMOVE_PLUG_FROM_EVENT_FAILED",
                details={"event_id": str(event_id), "plug_id": str(plug_id), "error": str(e)}
            )

    # Private Validation Methods
    async def _verify_user_event_ownership(self, user_id: UUID, event_id: UUID) -> Optional[Event]:
        """Verify that the event belongs to the user."""
        event = await self.event_repo.get(event_id)
        if event and event.user_id != user_id:
            raise ValidationError(
                "Event not found or access denied",
                error_code="EVENT_ACCESS_DENIED"
            )
        return event

    async def _verify_user_plug_ownership(self, user_id: UUID, plug_id: UUID) -> Optional[Any]:
        """Verify that the plug belongs to the user."""
        from app.repositories.plug_repository import PlugRepository
        plug_repo = PlugRepository(self.db)
        plug = await plug_repo.get(plug_id)
        if plug and plug.user_id != user_id:
            raise ValidationError(
                "Plug not found or access denied",
                error_code="PLUG_ACCESS_DENIED"
            )
        return plug

    async def _validate_event_creation(self, user_id: UUID, event_data: EventCreate) -> None:
        """Validate event creation business rules."""
        # Check for duplicate events based on title and start date
        existing_events = await self.event_repo.find_by({
            "user_id": user_id,
            "title": event_data.title,
            "start_date": event_data.start_date
        }, limit=1)
        
        if existing_events:
            raise ValidationError(
                "Event with this title and start date already exists",
                error_code="DUPLICATE_EVENT"
            )

    async def _validate_event_update(self, event: Event, update_data: EventUpdate) -> None:
        """Validate event update business rules."""
        # Additional validation can be added here
        pass

    async def _validate_agenda_creation(self, event: Event, agenda_data: EventAgendaCreate) -> None:
        """Validate agenda creation business rules."""
        # Check if day is within event range
        if agenda_data.day > event.total_days:
            raise ValidationError(
                f"Day {agenda_data.day} exceeds event duration of {event.total_days} days",
                error_code="INVALID_AGENDA_DAY"
            )

    async def _build_filter_dict(self, filters: EventFilters) -> Dict[str, Any]:
        """Build filter dictionary from EventFilters schema."""
        filter_dict = {}
        
        if filters.start_date_from:
            filter_dict["start_date__gte"] = filters.start_date_from
        if filters.start_date_to:
            filter_dict["start_date__lte"] = filters.start_date_to
        if filters.is_active is not None:
            filter_dict["is_active"] = filters.is_active
        if filters.is_public is not None:
            filter_dict["is_public"] = filters.is_public
        if filters.city:
            filter_dict["city"] = filters.city
        if filters.country:
            filter_dict["country"] = filters.country
        
        return filter_dict
