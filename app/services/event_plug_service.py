"""
Event plug service for plug operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventPlug
from app.repositories.event_repository import EventPlugRepository
from app.schemas.event import EventPlugCreate, EventPlugUpdate
from app.services.decorators import handle_service_errors, require_event_ownership, require_plug_ownership
from app.services.event_base_service import EventBaseService
from app.services.plug_service import PlugService

logger = logging.getLogger(__name__)


class EventPlugService(EventBaseService):
    """
    Service for event-plug association operations.
    """

    def __init__(self, db: Session):
        """Initialize event plug service."""
        super().__init__(db)
        self.plug_repo = EventPlugRepository(db)
        self.plug_service = PlugService(db)

    @handle_service_errors("add plug to event", "ADD_PLUG_TO_EVENT_FAILED")
    @require_event_ownership
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
        """
        # Verify plug ownership
        plug = await self.plug_service.get_user_plug(user_id, plug_id)
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

    @handle_service_errors("get event plugs", "EVENT_PLUGS_RETRIEVAL_FAILED")
    @require_event_ownership
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
        """
        Get plugs associated with an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plug_type: Filter by plug type (optional)
            network_type: Filter by network type (optional)
            search_query: Search in plug name, company, email (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (event-plug associations list, total count)
        """
        return await self.plug_repo.get_event_plugs(
            event_id=event_id,
            plug_type=plug_type,
            network_type=network_type,
            search_query=search_query,
            skip=skip,
            limit=limit
        )

    @handle_service_errors("update event plug", "EVENT_PLUG_UPDATE_FAILED")
    @require_event_ownership
    async def update_event_plug(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        update_data: EventPlugUpdate
    ) -> Optional[EventPlug]:
        """
        Update an event-plug association.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plug_id: Plug ID
            update_data: Update data
            
        Returns:
            Updated event-plug association or None if not found
        """
        # Find the association
        associations = await self.plug_repo.find_by({
            "event_id": event_id,
            "plug_id": plug_id
        }, limit=1)
        
        if not associations:
            return None
        
        association = associations[0]
        
        # Convert schema to dict
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Update association
        updated_association = await self.plug_repo.update(association.id, update_dict)
        
        logger.info(f"Updated plug {plug_id} association for event {event_id}")
        return updated_association

    @handle_service_errors("remove plug from event", "REMOVE_PLUG_FROM_EVENT_FAILED")
    @require_event_ownership
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
        # Remove plug from event
        removed = await self.plug_repo.remove_plug_from_event(
            event_id=event_id,
            plug_id=plug_id
        )
        
        if removed:
            logger.info(f"Removed plug {plug_id} from event {event_id}")
        
        return removed

    @handle_service_errors("add multiple plugs to event", "BATCH_ADD_PLUGS_TO_EVENT_FAILED")
    @require_event_ownership
    async def add_multiple_plugs_to_event(
        self,
        user_id: UUID,
        event_id: UUID,
        plugs_data: List[dict]
    ) -> dict:
        """
        Add multiple plugs to an event in batch.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plugs_data: List of plug data with plug_id, notes, priority
            
        Returns:
            Dictionary with created and failed associations
        """
        created = []
        failed = []
        
        for plug_data in plugs_data:
            try:
                plug_id = plug_data["plug_id"]
                
                # Verify plug ownership
                plug = await self.plug_service.get_user_plug(user_id, plug_id)
                if not plug:
                    failed.append({
                        "plug_id": str(plug_id),
                        "error": "Plug not found or not owned by user",
                        "error_code": "PLUG_NOT_FOUND"
                    })
                    continue
                
                # Check if association already exists
                existing = await self.plug_repo.get_event_plug_by_ids(event_id, plug_id)
                if existing:
                    failed.append({
                        "plug_id": str(plug_id),
                        "error": "Plug is already associated with this event",
                        "error_code": "PLUG_ALREADY_ASSOCIATED"
                    })
                    continue
                
                # Prepare association data
                assoc_dict = {
                    "notes": plug_data.get("notes"),
                    "priority": plug_data.get("priority")
                }
                
                # Add plug to event
                event_plug = await self.plug_repo.add_plug_to_event(
                    event_id=event_id,
                    plug_id=plug_id,
                    association_data=assoc_dict
                )
                
                created.append(event_plug)
                logger.info(f"Added plug {plug_id} to event {event_id}")
                
            except Exception as e:
                logger.error(f"Failed to add plug {plug_data.get('plug_id')} to event {event_id}: {e}")
                failed.append({
                    "plug_id": str(plug_data.get("plug_id", "unknown")),
                    "error": str(e),
                    "error_code": "ADD_PLUG_FAILED"
                })
        
        return {
            "created": created,
            "failed": failed,
            "total_requested": len(plugs_data),
            "total_created": len(created),
            "total_failed": len(failed)
        }






