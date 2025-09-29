"""
Service for event plug media operations.
Simple service for uploading files to S3 and managing media records.
"""
import logging
import mimetypes
from typing import Union, List, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import EventPlugMedia
from app.repositories.event_plug_media_repository import EventPlugMediaRepository
from app.schemas.event_plug_media import EventPlugMediaUpload
from app.services.decorators import handle_service_errors, require_event_ownership
from app.services.event_base_service import EventBaseService
from app.services.s3_service import get_s3_service

logger = logging.getLogger(__name__)


class EventPlugMediaService(EventBaseService):
    """
    Simple service for event plug media operations.
    Handles file uploads to S3 and basic media management.
    """

    def __init__(self, db: Session):
        """Initialize event plug media service."""
        super().__init__(db)
        self.media_repo = EventPlugMediaRepository(db)
        self.s3_service = get_s3_service()

    @handle_service_errors("upload plug media file", "PLUG_MEDIA_UPLOAD_FAILED")
    @require_event_ownership
    async def upload_plug_media_file(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        file_obj: Union[bytes, Any],
        filename: str,
        upload_data: EventPlugMediaUpload
    ) -> EventPlugMedia:
        """
        Upload a file to S3 and create a plug media record.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            plug_id: Plug ID
            file_obj: File object or bytes to upload
            filename: Original filename
            upload_data: Upload data with media category
            
        Returns:
            Created media item with S3 URL
        """
        # Validate that the event-plug relationship exists
        event_plug_id = await self.media_repo.validate_event_plug_exists(event_id, plug_id)
        if not event_plug_id:
            raise NotFoundError(
                f"Plug {plug_id} is not associated with event {event_id}",
                error_code="PLUG_NOT_IN_EVENT"
            )
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(filename)
        file_type = content_type or 'application/octet-stream'
        
        # Validate file type based on media category
        if upload_data.media_category == "snap":
            if not file_type.startswith('image/'):
                raise ValidationError(
                    "Snap media must be an image file",
                    error_code="INVALID_SNAP_FILE_TYPE"
                )
        elif upload_data.media_category == "voice":
            if not file_type.startswith('audio/'):
                raise ValidationError(
                    "Voice media must be an audio file",
                    error_code="INVALID_VOICE_FILE_TYPE"
                )
        
        # Truncate file type if needed
        if len(file_type) > 32:
            file_type = file_type[:32]
        
        # Generate S3 key
        s3_key = self.s3_service._generate_s3_key(
            prefix=f"events/{event_id}/plugs/{plug_id}/{upload_data.media_category}",
            filename=filename
        )
        
        try:
            # Upload to S3
            file_url = self.s3_service.upload_file(
                file_obj=file_obj,
                key=s3_key,
                metadata={
                    'event_id': str(event_id),
                    'plug_id': str(plug_id),
                    'user_id': str(user_id),
                    'media_category': upload_data.media_category
                }
            )
            
            # Create media record
            media_dict = {
                "event_id": event_id,
                "plug_id": plug_id,
                "event_plug_id": event_plug_id,
                "file_url": file_url,
                "s3_key": s3_key,
                "file_type": file_type,
                "media_category": upload_data.media_category
            }
            
            media = await self.media_repo.create(media_dict)
            
            logger.info(f"Uploaded {upload_data.media_category} file for plug {plug_id} in event {event_id}")
            return media
            
        except Exception as e:
            # Cleanup S3 file if database creation fails
            try:
                self.s3_service.delete_file(s3_key)
            except Exception:
                pass
            raise e

    @handle_service_errors("get plug media", "PLUG_MEDIA_RETRIEVAL_FAILED")
    @require_event_ownership
    async def get_plug_media(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        media_category: Optional[str] = None
    ) -> List[EventPlugMedia]:
        """Get media for a specific plug within an event."""
        # Validate that the event-plug relationship exists
        event_plug_id = await self.media_repo.validate_event_plug_exists(event_id, plug_id)
        if not event_plug_id:
            raise NotFoundError(
                f"Plug {plug_id} is not associated with event {event_id}",
                error_code="PLUG_NOT_IN_EVENT"
            )
        
        return await self.media_repo.get_plug_media(event_id, plug_id, media_category)

    @handle_service_errors("delete plug media", "PLUG_MEDIA_DELETION_FAILED")
    @require_event_ownership
    async def delete_plug_media(
        self,
        user_id: UUID,
        event_id: UUID,
        plug_id: UUID,
        media_id: UUID
    ) -> bool:
        """Delete a media item from a plug within an event."""
        # Verify media exists
        media = await self.media_repo.get_by_event_plug_and_id(event_id, plug_id, media_id)
        if not media:
            return False
        
        # Delete from S3
        if media.s3_key:
            try:
                self.s3_service.delete_file(media.s3_key)
                logger.info(f"Deleted S3 file: {media.s3_key}")
            except Exception as e:
                logger.error(f"Failed to delete S3 file {media.s3_key}: {e}")
        
        # Delete media record
        return await self.media_repo.delete(media_id, soft=True)
