"""
API endpoints for event plug media management.
Simple endpoints for uploading and retrieving media files.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query

from app.core.dependencies import DatabaseSession, CurrentActiveUser
from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.schemas.event_plug_media import EventPlugMediaUpload, EventPlugMediaResponse
from app.services.event_plug_media_service import EventPlugMediaService

router = APIRouter(tags=["Event Plug Media"])


def get_event_plug_media_service(db: DatabaseSession) -> EventPlugMediaService:
    """Dependency to get event plug media service instance."""
    return EventPlugMediaService(db)


# Simple endpoints for file upload and retrieval

@router.post("/{event_id}/plugs/{plug_id}/media/upload-multiple", response_model=List[EventPlugMediaResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_plug_media_to_s3(
    event_id: UUID,
    plug_id: UUID,
    current_user: CurrentActiveUser,
    files: List[UploadFile] = File(..., description="Multiple media files to upload to S3"),
    media_category: str = Form(..., description="Media category: 'snap' or 'voice'"),
    service: EventPlugMediaService = Depends(get_event_plug_media_service)
):
    """
    Upload multiple media files (snaps or voice) to S3 for a specific plug within an event.
    
    - Requires JWT authentication
    - User can only add media to their own events and plugs
    - Files are stored in S3 with organized paths
    - Supports multiple images (snaps) and audio files (voice recordings) in one request
    - Maximum 20 files per request
    - Each file max size: 100MB
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Validate number of files
        if len(files) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 files allowed per upload"
            )
        
        if len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required"
            )
        
        uploaded_media = []
        failed_uploads = []
        
        # Process each file
        for file in files:
            try:
                # Create upload data
                upload_data = EventPlugMediaUpload(media_category=media_category)
                
                # Read file content
                file_content = await file.read()
                
                # Check file size (100MB max)
                max_file_size = 100 * 1024 * 1024
                if len(file_content) > max_file_size:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": "File size exceeds maximum allowed size (100MB)"
                    })
                    continue
                
                # Upload file to S3 and create media record
                media = await service.upload_plug_media_file(
                    user_id=user_id,
                    event_id=event_id,
                    plug_id=plug_id,
                    file_obj=file_content,
                    filename=file.filename or "unknown_file",
                    upload_data=upload_data
                )
                
                uploaded_media.append(EventPlugMediaResponse.model_validate(media))
                
            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        # If all uploads failed, raise error
        if len(uploaded_media) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All uploads failed. Errors: {failed_uploads}"
            )
        
        # If some uploads failed, log warning but return successful ones
        if len(failed_uploads) > 0:
            logger = logging.getLogger(__name__)
            logger.warning(f"Some uploads failed for plug {plug_id} in event {event_id}: {failed_uploads}")
        
        return uploaded_media
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/plugs/{plug_id}/media", response_model=List[EventPlugMediaResponse])
async def get_plug_media(
    event_id: UUID,
    plug_id: UUID,
    current_user: CurrentActiveUser,
    media_category: Optional[str] = Query(None, description="Filter by media category ('snap' or 'voice')"),
    service: EventPlugMediaService = Depends(get_event_plug_media_service)
):
    """
    Get media for a specific plug within an event.
    
    - Requires JWT authentication
    - User can only access their own events and plugs
    - Returns media metadata with S3 URLs
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        media = await service.get_plug_media(user_id, event_id, plug_id, media_category)
        
        return [EventPlugMediaResponse.model_validate(media_item) for media_item in media]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/plugs/{plug_id}/snaps", response_model=List[EventPlugMediaResponse])
async def get_plug_snaps(
    event_id: UUID,
    plug_id: UUID,
    current_user: CurrentActiveUser,
    service: EventPlugMediaService = Depends(get_event_plug_media_service)
):
    """Get snaps (images) for a specific plug within an event."""
    try:
        user_id = UUID(current_user["user_id"])
        media = await service.get_plug_media(user_id, event_id, plug_id, "snap")
        return [EventPlugMediaResponse.model_validate(media_item) for media_item in media]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/plugs/{plug_id}/voice", response_model=List[EventPlugMediaResponse])
async def get_plug_voice_recordings(
    event_id: UUID,
    plug_id: UUID,
    current_user: CurrentActiveUser,
    service: EventPlugMediaService = Depends(get_event_plug_media_service)
):
    """Get voice recordings for a specific plug within an event."""
    try:
        user_id = UUID(current_user["user_id"])
        media = await service.get_plug_media(user_id, event_id, plug_id, "voice")
        return [EventPlugMediaResponse.model_validate(media_item) for media_item in media]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{event_id}/plugs/{plug_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plug_media(
    event_id: UUID,
    plug_id: UUID,
    media_id: UUID,
    current_user: CurrentActiveUser,
    service: EventPlugMediaService = Depends(get_event_plug_media_service)
):
    """
    Delete a media item from a plug within an event.
    Also removes the file from S3.
    """
    try:
        user_id = UUID(current_user["user_id"])
        deleted = await service.delete_plug_media(user_id, event_id, plug_id, media_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
