"""
Event media service for media operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventMedia
from app.repositories.event_repository import EventMediaRepository
from app.schemas.event import EventMediaCreate, EventMediaUpdate
from app.services.decorators import handle_service_errors, require_event_ownership
from app.services.event_base_service import EventBaseService

logger = logging.getLogger(__name__)


class EventMediaService(EventBaseService):
    """
    Service for event media operations.
    """

    def __init__(self, db: Session):
        """Initialize event media service."""
        super().__init__(db)
        self.media_repo = EventMediaRepository(db)

    @handle_service_errors("create media", "MEDIA_CREATION_FAILED")
    @require_event_ownership
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
        """
        # Convert schema to dict
        media_dict = media_data.model_dump(exclude_unset=True)
        media_dict["event_id"] = event_id
        
        # Convert tags list to comma-separated string
        media_dict = self._convert_tags_to_string(media_dict)
        
        # Create media
        media = await self.media_repo.create(media_dict)
        
        logger.info(f"Created media {media.id} for event {event_id}")
        return media

    @handle_service_errors("get event media", "EVENT_MEDIA_RETRIEVAL_FAILED")
    @require_event_ownership
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
        return await self.media_repo.get_event_media(
            event_id=event_id,
            file_type=file_type,
            skip=skip,
            limit=limit
        )

    @handle_service_errors("get media item", "MEDIA_ITEM_RETRIEVAL_FAILED")
    @require_event_ownership
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
        # Get media item
        media = await self.media_repo.get(media_id)
        if media and media.event_id != event_id:
            return None
            
        return media

    @handle_service_errors("search media by tags", "MEDIA_TAG_SEARCH_FAILED")
    @require_event_ownership
    async def search_media_by_tags(
        self,
        user_id: UUID,
        event_id: UUID,
        tags: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """
        Search media by tags for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            tags: List of tags to search for
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (matching media list, total count)
        """
        return await self.media_repo.search_media_by_tags(
            event_id=event_id,
            tags=tags,
            skip=skip,
            limit=limit
        )

    @handle_service_errors("update media", "MEDIA_UPDATE_FAILED")
    @require_event_ownership
    async def update_media(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID,
        update_data: EventMediaUpdate
    ) -> Optional[EventMedia]:
        """
        Update a media item.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            media_id: Media ID
            update_data: Update data
            
        Returns:
            Updated media item or None if not found
        """
        # Verify media belongs to event
        media = await self.media_repo.get(media_id)
        if not media or media.event_id != event_id:
            return None
        
        # Convert schema to dict
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict = self._convert_tags_to_string(update_dict)
        
        # Update media
        updated_media = await self.media_repo.update(media_id, update_dict)
        
        logger.info(f"Updated media {media_id} for event {event_id}")
        return updated_media

    @handle_service_errors("delete media", "MEDIA_DELETION_FAILED")
    @require_event_ownership
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
        # Verify media belongs to event
        media = await self.media_repo.get(media_id)
        if not media or media.event_id != event_id:
            return False
        
        # Delete media
        return await self.media_repo.delete(media_id, soft=True)

