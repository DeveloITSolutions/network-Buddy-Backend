"""
Event service facade that coordinates all event-related services.
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
from app.services.event_core_service import EventCoreService
from app.services.event_agenda_service import EventAgendaService
from app.services.event_expense_service import EventExpenseService
from app.services.event_media_service import EventMediaService
from app.services.event_plug_service import EventPlugService

logger = logging.getLogger(__name__)


class EventServiceFacade:
    """
    Facade that coordinates all event-related services.
    Provides a unified interface for all event operations.
    """

    def __init__(self, db: Session):
        """Initialize event service facade with all sub-services."""
        self.db = db
        self.core_service = EventCoreService(db)
        self.agenda_service = EventAgendaService(db)
        self.expense_service = EventExpenseService(db)
        self.media_service = EventMediaService(db)
        self.plug_service = EventPlugService(db)

    # Event Core Operations
    async def create_event(self, user_id: UUID, event_data: EventCreate) -> Event:
        """Create a new event."""
        return await self.core_service.create_event(user_id, event_data)

    async def update_event(
        self,
        user_id: UUID,
        event_id: UUID,
        update_data: EventUpdate
    ) -> Optional[Event]:
        """Update an existing event."""
        return await self.core_service.update_event(user_id, event_id, update_data)

    async def delete_event(self, user_id: UUID, event_id: UUID) -> bool:
        """Delete a user's event."""
        return await self.core_service.delete_event(user_id, event_id)

    async def get_user_event(self, user_id: UUID, event_id: UUID) -> Optional[Event]:
        """Get a specific event for a user."""
        return await self.core_service.get_user_event(user_id, event_id)

    async def get_user_events(
        self,
        user_id: UUID,
        filters: Optional[EventFilters] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """Get paginated list of user's events with filtering."""
        return await self.core_service.get_user_events(user_id, filters, skip, limit)

    async def search_user_events(
        self,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """Search user's events by term."""
        return await self.core_service.search_user_events(user_id, search_term, skip, limit)

    async def get_event_stats(self, user_id: UUID) -> EventStats:
        """Get statistics about user's events."""
        return await self.core_service.get_event_stats(user_id)

    # Event Agenda Operations
    async def create_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_data: EventAgendaCreate
    ) -> EventAgenda:
        """Create a new agenda item for an event."""
        return await self.agenda_service.create_agenda_item(user_id, event_id, agenda_data)

    async def get_event_agendas(
        self,
        user_id: UUID,
        event_id: UUID,
        day: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventAgenda], int]:
        """Get agenda items for an event."""
        return await self.agenda_service.get_event_agendas(user_id, event_id, day, skip, limit)

    async def get_event_agenda_days(
        self,
        user_id: UUID,
        event_id: UUID
    ) -> List[dict]:
        """Get available days for agenda items in an event."""
        return await self.agenda_service.get_event_agenda_days(user_id, event_id)

    async def update_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_id: UUID,
        update_data: EventAgendaUpdate
    ) -> Optional[EventAgenda]:
        """Update an agenda item."""
        return await self.agenda_service.update_agenda_item(user_id, event_id, agenda_id, update_data)

    async def delete_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_id: UUID
    ) -> bool:
        """Delete an agenda item."""
        return await self.agenda_service.delete_agenda_item(user_id, event_id, agenda_id)

    # Event Expense Operations
    async def create_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_data: EventExpenseCreate
    ) -> EventExpense:
        """Create a new expense for an event."""
        return await self.expense_service.create_expense(user_id, event_id, expense_data)

    async def get_event_expenses(
        self,
        user_id: UUID,
        event_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventExpense], int]:
        """Get expenses for an event."""
        return await self.expense_service.get_event_expenses(user_id, event_id, category, skip, limit)

    async def get_expense_categories(self, user_id: UUID, event_id: UUID) -> List[str]:
        """Get unique expense categories for an event."""
        return await self.expense_service.get_expense_categories(user_id, event_id)

    async def update_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_id: UUID,
        update_data: EventExpenseUpdate
    ) -> Optional[EventExpense]:
        """Update an expense."""
        return await self.expense_service.update_expense(user_id, event_id, expense_id, update_data)

    async def delete_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_id: UUID
    ) -> bool:
        """Delete an expense."""
        return await self.expense_service.delete_expense(user_id, event_id, expense_id)

    # Event Media Operations
    async def create_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_data: EventMediaCreate
    ) -> EventMedia:
        """Create a new media item for an event."""
        return await self.media_service.create_media(user_id, event_id, media_data)

    async def get_event_media(
        self,
        user_id: UUID,
        event_id: UUID,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """Get media for an event."""
        return await self.media_service.get_event_media(user_id, event_id, file_type, skip, limit)

    async def get_event_media_item(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> Optional[EventMedia]:
        """Get a specific media item for an event."""
        return await self.media_service.get_event_media_item(user_id, event_id, media_id)

    async def search_media_by_tags(
        self,
        user_id: UUID,
        event_id: UUID,
        tags: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """Search media by tags for an event."""
        return await self.media_service.search_media_by_tags(user_id, event_id, tags, skip, limit)

    async def update_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID,
        update_data: EventMediaUpdate
    ) -> Optional[EventMedia]:
        """Update a media item."""
        return await self.media_service.update_media(user_id, event_id, media_id, update_data)

    async def delete_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> bool:
        """Delete a media item from an event."""
        return await self.media_service.delete_media(user_id, event_id, media_id)

    # Event-Plug Operations
    async def add_plug_to_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        association_data: Optional[EventPlugCreate] = None
    ) -> EventPlug:
        """Add a plug to an event."""
        return await self.plug_service.add_plug_to_event(user_id, event_id, plug_id, association_data)

    async def get_event_plugs(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_type: Optional[str] = None,
        network_type: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventPlug], int]:
        """Get plugs associated with an event with filtering and search."""
        return await self.plug_service.get_event_plugs(
            user_id, event_id, plug_type, network_type, search_query, skip, limit
        )

    async def update_event_plug(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        update_data: EventPlugUpdate
    ) -> Optional[EventPlug]:
        """Update an event-plug association."""
        return await self.plug_service.update_event_plug(user_id, event_id, plug_id, update_data)

    async def remove_plug_from_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID
    ) -> bool:
        """Remove a plug from an event."""
        return await self.plug_service.remove_plug_from_event(user_id, event_id, plug_id)

    async def add_multiple_plugs_to_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plugs_data: List[dict]
    ) -> dict:
        """Add multiple plugs to an event in batch."""
        return await self.plug_service.add_multiple_plugs_to_event(user_id, event_id, plugs_data)
