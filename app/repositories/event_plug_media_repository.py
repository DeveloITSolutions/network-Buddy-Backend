"""
Repository for EventPlugMedia operations.
Simple repository for basic CRUD operations.
"""
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models.event import EventPlugMedia, EventPlug
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class EventPlugMediaRepository(BaseRepository[EventPlugMedia]):
    """Simple repository for EventPlugMedia operations."""

    def __init__(self, db: Session):
        super().__init__(db, EventPlugMedia)

    async def get_plug_media(
        self,
        event_id: UUID,
        plug_id: UUID,
        media_category: Optional[str] = None
    ) -> List[EventPlugMedia]:
        """
        Get media for a specific plug within an event.
        
        Args:
            event_id: Event ID
            plug_id: Plug ID
            media_category: Filter by media category ('snap' or 'voice')
            
        Returns:
            List of media items
        """
        try:
            query = self.db.query(EventPlugMedia).filter(
                and_(
                    EventPlugMedia.event_id == event_id,
                    EventPlugMedia.plug_id == plug_id,
                    EventPlugMedia.is_deleted == False
                )
            )
            
            if media_category:
                query = query.filter(EventPlugMedia.media_category == media_category)
            
            media = query.order_by(desc(EventPlugMedia.created_at)).all()
            
            logger.debug(f"Retrieved {len(media)} media items for plug {plug_id} in event {event_id}")
            return media
            
        except Exception as e:
            logger.error(f"Error retrieving plug media: {e}")
            raise

    async def get_by_event_plug_and_id(
        self,
        event_id: UUID,
        plug_id: UUID,
        media_id: UUID
    ) -> Optional[EventPlugMedia]:
        """
        Get a specific media item for a plug within an event.
        
        Args:
            event_id: Event ID
            plug_id: Plug ID
            media_id: Media ID
            
        Returns:
            Media item if found, None otherwise
        """
        try:
            media = self.db.query(EventPlugMedia).filter(
                and_(
                    EventPlugMedia.id == media_id,
                    EventPlugMedia.event_id == event_id,
                    EventPlugMedia.plug_id == plug_id,
                    EventPlugMedia.is_deleted == False
                )
            ).first()
            
            return media
            
        except Exception as e:
            logger.error(f"Error retrieving specific media: {e}")
            raise

    async def validate_event_plug_exists(self, event_id: UUID, plug_id: UUID) -> Optional[UUID]:
        """
        Validate that an event-plug relationship exists and return the event_plug_id.
        
        Args:
            event_id: Event ID
            plug_id: Plug ID
            
        Returns:
            EventPlug ID if exists, None otherwise
        """
        try:
            event_plug = self.db.query(EventPlug).filter(
                and_(
                    EventPlug.event_id == event_id,
                    EventPlug.plug_id == plug_id,
                    EventPlug.is_deleted == False
                )
            ).first()
            
            return event_plug.id if event_plug else None
            
        except Exception as e:
            logger.error(f"Error validating event-plug relationship: {e}")
            raise
