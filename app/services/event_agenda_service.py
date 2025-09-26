"""
Event agenda service for agenda operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventAgenda
from app.repositories.event_repository import EventAgendaRepository
from app.schemas.event import EventAgendaCreate, EventAgendaUpdate
from app.services.decorators import handle_service_errors, require_event_ownership
from app.services.event_base_service import EventBaseService

logger = logging.getLogger(__name__)


class EventAgendaService(EventBaseService):
    """
    Service for event agenda operations.
    """

    def __init__(self, db: Session):
        """Initialize event agenda service."""
        super().__init__(db)
        self.agenda_repo = EventAgendaRepository(db)

    @handle_service_errors("create agenda item", "AGENDA_CREATION_FAILED")
    @require_event_ownership
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
        """
        # Get event for validation
        event = await self._verify_event_ownership(user_id, event_id)
        
        # Validate agenda item
        await self._validate_agenda_creation(event, agenda_data)
        
        # Convert schema to dict
        agenda_dict = agenda_data.model_dump(exclude_unset=True)
        agenda_dict["event_id"] = event_id
        
        # Create agenda item
        agenda = await self.agenda_repo.create(agenda_dict)
        
        logger.info(f"Created agenda item {agenda.id} for event {event_id} on day {agenda_data.day}")
        return agenda

    @handle_service_errors("get event agendas", "EVENT_AGENDAS_RETRIEVAL_FAILED")
    @require_event_ownership
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
        return await self.agenda_repo.get_event_agendas(
            event_id=event_id,
            day=day,
            skip=skip,
            limit=limit
        )

    @handle_service_errors("update agenda item", "AGENDA_UPDATE_FAILED")
    @require_event_ownership
    async def update_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_id: UUID,
        update_data: EventAgendaUpdate
    ) -> Optional[EventAgenda]:
        """
        Update an agenda item.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            agenda_id: Agenda item ID
            update_data: Update data
            
        Returns:
            Updated agenda item or None if not found
        """
        # Verify agenda belongs to event
        agenda = await self.agenda_repo.get(agenda_id)
        if not agenda or agenda.event_id != event_id:
            return None
        
        # Convert schema to dict
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Update agenda item
        updated_agenda = await self.agenda_repo.update(agenda_id, update_dict)
        
        logger.info(f"Updated agenda item {agenda_id} for event {event_id}")
        return updated_agenda

    @handle_service_errors("delete agenda item", "AGENDA_DELETION_FAILED")
    @require_event_ownership
    async def delete_agenda_item(
        self,
        user_id: UUID,
        event_id: UUID,
        agenda_id: UUID
    ) -> bool:
        """
        Delete an agenda item.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            agenda_id: Agenda item ID
            
        Returns:
            True if deleted, False if not found
        """
        # Verify agenda belongs to event
        agenda = await self.agenda_repo.get(agenda_id)
        if not agenda or agenda.event_id != event_id:
            return False
        
        # Delete agenda item
        return await self.agenda_repo.delete(agenda_id, soft=True)

    @handle_service_errors("get event agenda days", "EVENT_AGENDA_DAYS_RETRIEVAL_FAILED")
    @require_event_ownership
    async def get_event_agenda_days(
        self,
        user_id: UUID,
        event_id: UUID
    ) -> List[dict]:
        """
        Get available days for agenda items in an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            
        Returns:
            List of days with their dates and agenda counts
        """
        # Get event to calculate dates
        event = await self._verify_event_ownership(user_id, event_id)
        
        # Calculate dates for each day
        from datetime import timedelta
        days_info = []
        
        for day in range(1, event.total_days + 1):
            day_date = event.start_date + timedelta(days=day - 1)
            
            # Get agenda count for this day
            agendas, count = await self.agenda_repo.get_event_agendas(
                event_id=event_id,
                day=day,
                skip=0,
                limit=1  # We only need the count
            )
            
            days_info.append({
                "day": day,
                "date": day_date.isoformat(),
                "agenda_count": count,
                "is_today": day == event.current_day
            })
        
        return days_info
