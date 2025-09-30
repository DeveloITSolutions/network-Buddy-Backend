"""
Service layer for event business logic.
This is now a facade that delegates to focused service classes.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventAgenda, EventExpense, EventMedia, EventPlug
from app.schemas.event import (
    EventCreate, EventUpdate, EventFilters, EventStats,
    EventAgendaCreate, EventAgendaUpdate,
    EventExpenseCreate, EventExpenseUpdate,
    EventMediaCreate, EventMediaUpdate,
    EventPlugCreate, EventPlugUpdate
)
from app.services.base_service import BaseService
from app.services.event_service_facade import EventServiceFacade

logger = logging.getLogger(__name__)


class EventService(BaseService[Event]):
    """
    Service for event business logic.
    This class now acts as a facade that delegates to focused service classes.
    """

    def __init__(self, db: Session):
        """Initialize event service with dependencies."""
        super().__init__(db)
        # Use the facade to coordinate all event operations
        self.facade = EventServiceFacade(db)

    def get_model_class(self) -> type[Event]:
        """Get the Event model class."""
        return Event

    # Event CRUD Operations
    async def create_event(self, user_id: UUID, event_data: EventCreate) -> Event:
        """Create a new event with business validation."""
        return await self.facade.create_event(user_id, event_data)

    async def update_event(
        self,
        user_id: UUID,
        event_id: UUID,
        update_data: EventUpdate
    ) -> Optional[Event]:
        """Update an existing event."""
        return await self.facade.update_event(user_id, event_id, update_data)

    async def delete_event(self, user_id: UUID, event_id: UUID) -> bool:
        """Delete a user's event (soft delete)."""
        return await self.facade.delete_event(user_id, event_id)

    async def get_user_event(self, user_id: UUID, event_id: UUID) -> Optional[Event]:
        """Get a specific event for a user."""
        return await self.facade.get_user_event(user_id, event_id)

    async def get_user_events(
        self,
        user_id: UUID,
        filters: Optional[EventFilters] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """Get paginated list of user's events with filtering."""
        return await self.facade.get_user_events(user_id, filters, skip, limit)

    async def search_user_events(
        self,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """Search user's events by term."""
        return await self.facade.search_user_events(user_id, search_term, skip, limit)

    async def get_event_stats(self, user_id: UUID) -> EventStats:
        """Get statistics about user's events."""
        return await self.facade.get_event_stats(user_id)

    # Agenda Operations (Deeds Module)
    async def create_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_data: EventAgendaCreate
    ) -> EventAgenda:
        """Create a new agenda item for an event."""
        return await self.facade.create_agenda_item(user_id, event_id, agenda_data)

    async def get_event_agendas(
        self,
        user_id: UUID,
        event_id: UUID,
        day: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventAgenda], int]:
        """Get agenda items for an event."""
        return await self.facade.get_event_agendas(user_id, event_id, day, skip, limit)

    async def get_event_agenda_days(
        self,
        user_id: UUID,
        event_id: UUID
    ) -> List[dict]:
        """Get available days for agenda items in an event."""
        return await self.facade.get_event_agenda_days(user_id, event_id)

    async def update_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_id: UUID,
        update_data: EventAgendaUpdate
    ) -> Optional[EventAgenda]:
        """Update an agenda item."""
        return await self.facade.update_agenda_item(user_id, event_id, agenda_id, update_data)

    async def delete_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_id: UUID
    ) -> bool:
        """Delete an agenda item."""
        return await self.facade.delete_agenda_item(user_id, event_id, agenda_id)

    # Expense Operations (Deeds Module)
    async def create_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_data: EventExpenseCreate
    ) -> EventExpense:
        """Create a new expense for an event."""
        return await self.facade.create_expense(user_id, event_id, expense_data)

    async def get_event_expenses(
        self,
        user_id: UUID,
        event_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventExpense], int]:
        """Get expenses for an event."""
        return await self.facade.get_event_expenses(user_id, event_id, category, skip, limit)

    # Media Operations (Zone Module)
    async def create_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_data: EventMediaCreate
    ) -> EventMedia:
        """Create a new media item for an event."""
        return await self.facade.create_media(user_id, event_id, media_data)

    async def get_event_media(
        self,
        user_id: UUID,
        event_id: UUID,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """Get media for an event."""
        return await self.facade.get_event_media(user_id, event_id, file_type, skip, limit)

    async def get_event_media_item(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> Optional[EventMedia]:
        """Get a specific media item for an event."""
        return await self.facade.get_event_media_item(user_id, event_id, media_id)

    async def search_media_by_tags(
        self,
        user_id: UUID,
        event_id: UUID,
        tags: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """Search media by tags for an event."""
        return await self.facade.search_media_by_tags(user_id, event_id, tags, skip, limit)

    async def delete_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> bool:
        """Delete a media item from an event."""
        return await self.facade.delete_media(user_id, event_id, media_id)

    # Event-Plug Operations
    async def add_plug_to_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        association_data: Optional[EventPlugCreate] = None
    ) -> EventPlug:
        """Add a plug to an event."""
        return await self.facade.add_plug_to_event(user_id, event_id, plug_id, association_data)

    async def get_event_plugs(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventPlug], int]:
        """Get plugs associated with an event."""
        return await self.facade.get_event_plugs(user_id, event_id, plug_type, skip, limit)

    async def remove_plug_from_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID
    ) -> bool:
        """Remove a plug from an event."""
        return await self.facade.remove_plug_from_event(user_id, event_id, plug_id)

    async def add_multiple_plugs_to_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plugs_data: List[dict]
    ) -> dict:
        """Add multiple plugs to an event in batch."""
        return await self.facade.add_multiple_plugs_to_event(user_id, event_id, plugs_data)
