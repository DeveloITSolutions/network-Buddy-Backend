"""
Event media service for media operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventMedia
from app.repositories.event_repository import EventMediaRepository
from app.schemas.event import EventMediaCreate, EventMediaUpdate, EventMediaUpload
from app.services.decorators import handle_service_errors, require_event_ownership
from app.services.event_base_service import EventBaseService
from app.services.s3_service import s3_service

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

    @handle_service_errors("upload media file", "MEDIA_UPLOAD_FAILED")
    @require_event_ownership
    async def upload_media_file(
        self,
        user_id: UUID,
        event_id: UUID,
        file_obj: Union[Any, bytes],  # Can be file-like object or bytes
        filename: str,
        upload_data: EventMediaUpload
    ) -> EventMedia:
        """
        Upload a file to S3 and create a media record.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            file_obj: File object to upload
            filename: Original filename
            upload_data: Upload metadata
            
        Returns:
            Created media item with S3 URL
        """
        try:
            # Get file size BEFORE uploading (file object will be consumed by S3 upload)
            if isinstance(file_obj, bytes):
                file_size = len(file_obj)
            else:
                try:
                    file_obj.seek(0, 2)  # Seek to end
                    file_size = file_obj.tell()
                    file_obj.seek(0)  # Reset to beginning
                except (OSError, ValueError) as e:
                    logger.warning(f"Could not determine file size for {filename}: {e}")
                    file_size = 0  # Default to 0 if we can't determine size
            
            # Determine content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(filename)
            file_type = content_type or 'application/octet-stream'
            
            # Ensure file_type doesn't exceed database limit (32 chars)
            if len(file_type) > 32:
                file_type = file_type[:32]
                logger.warning(f"File type truncated to fit database limit: {file_type}")
            
            # Generate S3 key
            s3_key = s3_service()._generate_s3_key(
                prefix=f"events/{event_id}/media",
                filename=filename
            )
            
            # Ensure s3_key doesn't exceed database limit (512 chars)
            if len(s3_key) > 512:
                logger.error(f"S3 key too long for database: {len(s3_key)} chars")
                raise BusinessLogicError(
                    "Generated S3 key exceeds database storage limit",
                    error_code="S3_KEY_TOO_LONG"
                )
            
            # Upload to S3
            file_url = s3_service().upload_file(
                file_obj=file_obj,
                key=s3_key,
                metadata={
                    'event_id': str(event_id),
                    'user_id': str(user_id),
                    'original_filename': filename
                }
            )
            
            # Ensure file_url doesn't exceed database limit (512 chars)
            if len(file_url) > 512:
                logger.error(f"File URL too long for database: {len(file_url)} chars")
                raise BusinessLogicError(
                    "Generated file URL exceeds database storage limit",
                    error_code="FILE_URL_TOO_LONG"
                )
            
            # Create media record
            media_dict = {
                "event_id": event_id,
                "title": upload_data.title[:256] if upload_data.title and len(upload_data.title) > 256 else upload_data.title,
                "description": upload_data.description,
                "file_url": file_url,
                "s3_key": s3_key,
                "file_type": file_type,
                "file_size": file_size,
                "tags": self._convert_tags_to_string({"tags": upload_data.tags or []})["tags"]
            }
            
            logger.info(f"Creating media record with data: {media_dict}")
            try:
                media = await self.media_repo.create(media_dict)
            except Exception as db_error:
                logger.error(f"Database creation failed: {db_error}")
                logger.error(f"Media dict that failed: {media_dict}")
                raise
            
            logger.info(f"Uploaded media file {filename} to S3 for event {event_id}, media ID: {media.id}")
            return media
            
        except Exception as e:
            # If database creation fails, clean up S3 file
            try:
                if 's3_key' in locals():
                    s3_service().delete_file(s3_key)
                    logger.info(f"Cleaned up S3 file after database error: {s3_key}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup S3 file {s3_key}: {cleanup_error}")
            
            raise e

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
        
        # Delete from S3 if s3_key exists
        if media.s3_key:
            try:
                s3_service().delete_file(media.s3_key)
                logger.info(f"Deleted S3 file: {media.s3_key}")
            except Exception as e:
                logger.error(f"Failed to delete S3 file {media.s3_key}: {e}")
                # Continue with database deletion even if S3 deletion fails
        
        # Delete media record
        return await self.media_repo.delete(media_id, soft=True)

    @handle_service_errors("download media file", "MEDIA_DOWNLOAD_FAILED")
    @require_event_ownership
    async def download_media_file(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> Tuple[bytes, str, str]:
        """
        Download a media file from S3.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            media_id: Media ID
            
        Returns:
            Tuple of (file_content, filename, content_type)
        """
        # Verify media belongs to event
        media = await self.media_repo.get(media_id)
        if not media or media.event_id != event_id:
            raise NotFoundError(
                f"Media {media_id} not found for event {event_id}",
                error_code="MEDIA_NOT_FOUND"
            )
        
        # Download from S3
        if not media.s3_key:
            raise BusinessLogicError(
                "Media file not available for download (no S3 key)",
                error_code="MEDIA_NO_S3_KEY"
            )
        
        file_content = s3_service().download_file(media.s3_key)
        
        # Generate filename
        filename = media.title or f"media_{media_id}"
        if media.file_type:
            # Add appropriate extension based on content type
            import mimetypes
            ext = mimetypes.guess_extension(media.file_type)
            if ext and not filename.endswith(ext):
                filename += ext
        
        return file_content, filename, media.file_type or 'application/octet-stream'

    @handle_service_errors("get media file stream", "MEDIA_STREAM_FAILED")
    @require_event_ownership
    async def get_media_file_stream(
        self,
        user_id: UUID,
        event_id: UUID,
        media_id: UUID
    ) -> Tuple[Any, str, str]:
        """
        Get a streaming download for a media file from S3.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            media_id: Media ID
            
        Returns:
            Tuple of (stream_object, filename, content_type)
        """
        # Verify media belongs to event
        media = await self.media_repo.get(media_id)
        if not media or media.event_id != event_id:
            raise NotFoundError(
                f"Media {media_id} not found for event {event_id}",
                error_code="MEDIA_NOT_FOUND"
            )
        
        # Get stream from S3
        if not media.s3_key:
            raise BusinessLogicError(
                "Media file not available for streaming (no S3 key)",
                error_code="MEDIA_NO_S3_KEY"
            )
        
        stream = s3_service().get_file_stream(media.s3_key)
        
        # Generate filename
        filename = media.title or f"media_{media_id}"
        if media.file_type:
            # Add appropriate extension based on content type
            import mimetypes
            ext = mimetypes.guess_extension(media.file_type)
            if ext and not filename.endswith(ext):
                filename += ext
        
        return stream, filename, media.file_type or 'application/octet-stream'

    @handle_service_errors("batch upload media files", "BATCH_MEDIA_UPLOAD_FAILED")
    @require_event_ownership
    async def batch_upload_media_files(
        self,
        user_id: UUID,
        event_id: UUID,
        files_data: List[Tuple[Union[Any, bytes], str, EventMediaUpload]]
    ) -> Dict[str, Any]:
        """
        Upload multiple files to S3 and create media records in batch.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            files_data: List of tuples (file_obj, filename, upload_data)
            
        Returns:
            Dictionary with successful uploads, failed uploads, and counts
        """
        successful = []
        failed = []
        
        for idx, (file_obj, filename, upload_data) in enumerate(files_data):
            try:
                # Upload individual file
                media = await self.upload_media_file(
                    user_id=user_id,
                    event_id=event_id,
                    file_obj=file_obj,
                    filename=filename,
                    upload_data=upload_data
                )
                successful.append(media)
                logger.info(f"Batch upload: Successfully uploaded file {idx + 1}/{len(files_data)}: {filename}")
                
            except Exception as e:
                error_detail = {
                    "filename": filename,
                    "index": idx,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                failed.append(error_detail)
                logger.error(f"Batch upload: Failed to upload file {idx + 1}/{len(files_data)}: {filename}. Error: {e}")
        
        return {
            "successful": successful,
            "failed": failed,
            "total_requested": len(files_data),
            "total_successful": len(successful),
            "total_failed": len(failed)
        }

    def _convert_tags_to_string(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert tags list to string format for database storage.
        
        Args:
            data: Dictionary containing tags list
            
        Returns:
            Dictionary with tags converted to string
        """
        if 'tags' in data and data['tags'] is not None:
            if isinstance(data['tags'], list):
                # Join tags with comma separator
                data['tags'] = ', '.join(str(tag) for tag in data['tags'])
            elif isinstance(data['tags'], str):
                # Already a string, keep as is
                pass
            else:
                # Convert other types to string
                data['tags'] = str(data['tags'])
        return data


