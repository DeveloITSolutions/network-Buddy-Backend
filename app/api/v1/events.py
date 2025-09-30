"""
API endpoints for event management.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import FileResponse, StreamingResponse

from app.core.dependencies import DatabaseSession, CurrentActiveUser
from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventListResponse, EventStats,
    EventAgendaCreate, EventAgendaUpdate, EventAgendaResponse,
    EventExpenseCreate, EventExpenseUpdate, EventExpenseResponse,
    EventMediaCreate, EventMediaUpdate, EventMediaResponse, EventMediaUpload, EventMediaBatchUploadResponse,
    EventPlugCreate, EventPlugResponse, EventPlugListResponse, EventPlugBatchCreate, EventPlugBatchResponse, EventFilters
)
from app.services.event_service import EventService
from app.services.event_media_service import EventMediaService
from app.services.file_upload_service import FileUploadService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])


def get_event_service(db: DatabaseSession) -> EventService:
    """Dependency to get event service instance."""
    return EventService(db)


def get_file_upload_service(db: DatabaseSession) -> FileUploadService:
    """Dependency to get file upload service instance."""
    return FileUploadService(db)


def get_event_media_service(db: DatabaseSession) -> EventMediaService:
    """Dependency to get event media service instance."""
    return EventMediaService(db)


# Event Management Endpoints
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Create a new event.
    
    - Requires JWT authentication
    - User can only create their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Create event through service
        event = await service.create_event(user_id, event_data)
        
        return EventResponse.model_validate(event)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Update an existing event.
    
    - Requires JWT authentication
    - User can only update their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Update event through service
        event = await service.update_event(user_id, event_id, event_data)
        
        if not event:
            raise NotFoundError("Event not found")
        
        return EventResponse.model_validate(event)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Delete an event (soft delete).
    
    - Requires JWT authentication
    - User can only delete their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        deleted = await service.delete_event(user_id, event_id)
        if not deleted:
            raise NotFoundError("Event not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Get a specific event by ID.
    
    - Requires JWT authentication
    - User can only access their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        event = await service.get_user_event(user_id, event_id)
        
        if not event:
            raise NotFoundError("Event not found")
        
        return EventResponse.model_validate(event)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=EventListResponse)
async def list_events(
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    start_date_from: Optional[str] = Query(None, description="Filter events from this date"),
    start_date_to: Optional[str] = Query(None, description="Filter events to this date"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    country: Optional[str] = Query(None, description="Filter by country"),
    service: EventService = Depends(get_event_service)
):
    """
    Get paginated list of all events for authenticated user.
    
    - Requires JWT authentication
    - Returns only the user's own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        if search:
            # Use search functionality
            events, total = await service.search_user_events(user_id, search, skip, limit)
        else:
            # Use regular list with filters
            filters = EventFilters(
                start_date_from=start_date_from,
                start_date_to=start_date_to,
                is_active=is_active,
                is_public=is_public,
                city=city,
                country=country
            )
            events, total = await service.get_user_events(user_id, filters, skip, limit)
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        current_page = skip // limit + 1
        
        return EventListResponse(
            items=[EventResponse.model_validate(event) for event in events],
            total=total,
            page=current_page,
            per_page=limit,
            pages=pages,
            has_next=current_page < pages,
            has_prev=current_page > 1
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/stats", response_model=EventStats)
async def get_event_stats(
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Get statistics about authenticated user's events.
    
    - Requires JWT authentication
    - Returns statistics for the user's own events only
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        stats = await service.get_event_stats(user_id)
        return stats
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Agenda Endpoints (Deeds Module)
@router.post("/{event_id}/agenda", response_model=EventAgendaResponse, status_code=status.HTTP_201_CREATED)
async def create_agenda_item(
    event_id: UUID,
    agenda_data: EventAgendaCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Create a new agenda item for an event.
    
    - Requires JWT authentication
    - User can only add agenda items to their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Create agenda item through service
        agenda = await service.create_agenda_item(user_id, event_id, agenda_data)
        
        return EventAgendaResponse.model_validate(agenda)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/agenda/days")
async def get_event_agenda_days(
    event_id: UUID,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Get available days for agenda items in an event.
    
    - Requires JWT authentication
    - User can only access their own events
    - Returns days with their dates and agenda counts
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        days = await service.get_event_agenda_days(user_id, event_id)
        
        return days
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/agenda", response_model=List[EventAgendaResponse])
async def get_event_agenda(
    event_id: UUID,
    current_user: CurrentActiveUser,
    day: Optional[int] = Query(None, ge=1, description="Filter by specific day"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    service: EventService = Depends(get_event_service)
):
    """
    Get agenda items for an event.
    
    - Requires JWT authentication
    - User can only access their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        agendas, total = await service.get_event_agendas(user_id, event_id, day, skip, limit)
        
        return [EventAgendaResponse.model_validate(agenda) for agenda in agendas]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{event_id}/agenda/{agenda_id}", response_model=EventAgendaResponse)
async def update_agenda_item(
    event_id: UUID,
    agenda_id: UUID,
    agenda_data: EventAgendaUpdate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Update an agenda item.
    
    - Requires JWT authentication
    - User can only update agenda items from their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Update agenda item through service
        agenda = await service.update_agenda_item(user_id, event_id, agenda_id, agenda_data)
        
        if not agenda:
            raise NotFoundError("Agenda item not found")
        
        return EventAgendaResponse.model_validate(agenda)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{event_id}/agenda/{agenda_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agenda_item(
    event_id: UUID,
    agenda_id: UUID,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Delete an agenda item.
    
    - Requires JWT authentication
    - User can only delete agenda items from their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Delete agenda item through service
        deleted = await service.delete_agenda_item(user_id, event_id, agenda_id)
        
        if not deleted:
            raise NotFoundError("Agenda item not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Expense Endpoints (Deeds Module)
@router.post("/{event_id}/expenses", response_model=EventExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    event_id: UUID,
    expense_data: EventExpenseCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Create a new expense for an event.
    
    - Requires JWT authentication
    - User can only add expenses to their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Create expense through service
        expense = await service.create_expense(user_id, event_id, expense_data)
        
        return EventExpenseResponse.model_validate(expense)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/expenses", response_model=List[EventExpenseResponse])
async def get_event_expenses(
    event_id: UUID,
    current_user: CurrentActiveUser,
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    service: EventService = Depends(get_event_service)
):
    """
    Get expenses for an event.
    
    - Requires JWT authentication
    - User can only access their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        expenses, total = await service.get_event_expenses(user_id, event_id, category, skip, limit)
        
        return [EventExpenseResponse.model_validate(expense) for expense in expenses]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Media Endpoints (Zone Module)
@router.post("/{event_id}/media")
async def upload_media_to_s3(
    event_id: UUID,
    current_user: CurrentActiveUser,
    files: List[UploadFile] = File(..., description="Media file(s) to upload to S3. Can upload single or multiple files."),
    titles: Optional[str] = Form(None, description="Pipe-separated titles for each file (e.g., 'Title1|Title2|Title3')"),
    descriptions: Optional[str] = Form(None, description="Pipe-separated descriptions for each file"),
    tags: Optional[str] = Form(None, description="Comma-separated tags (applied to all files)"),
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Upload one or more media files to S3 and create media records.
    
    - Requires JWT authentication
    - User can only add media to their own events
    - Accepts multipart/form-data for file uploads
    - Files are stored in S3, only metadata is stored in database
    - Supports images, videos, documents, and audio files
    - **Single File**: Returns EventMediaResponse (200)
    - **Multiple Files**: Returns EventMediaBatchUploadResponse with successful/failed uploads (200)
    
    **Note**: For multiple files with individual titles/descriptions, separate them with pipe (|) character.
    If titles/descriptions count doesn't match files count, remaining files will have no title/description.
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Parse tags (applied to all files)
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Parse titles and descriptions (pipe-separated)
        title_list = []
        if titles:
            title_list = [t.strip() for t in titles.split("|")]
        
        description_list = []
        if descriptions:
            description_list = [d.strip() for d in descriptions.split("|")]
        
        # File size limit
        max_file_size = 100 * 1024 * 1024  # 100MB per file
        
        # Single file upload - maintain backward compatibility
        if len(files) == 1:
            file = files[0]
            file_content = await file.read()
            
            if len(file_content) > max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({max_file_size} bytes)"
                )
            
            upload_data = EventMediaUpload(
                title=title_list[0] if title_list else None,
                description=description_list[0] if description_list else None,
                tags=tag_list if tag_list else None
            )
            
            media = await media_service.upload_media_file(
                user_id=user_id,
                event_id=event_id,
                file_obj=file_content,
                filename=file.filename or "unknown_file",
                upload_data=upload_data
            )
            
            return EventMediaResponse.model_validate(media)
        
        # Multiple files upload - batch processing
        else:
            files_data = []
            
            for idx, file in enumerate(files):
                # Read file content
                file_content = await file.read()
                
                # Check file size
                if len(file_content) > max_file_size:
                    logger.warning(f"File {file.filename} ({len(file_content)} bytes) exceeds max size, skipping")
                    continue
                
                # Get title and description for this file
                file_title = title_list[idx] if idx < len(title_list) else None
                file_description = description_list[idx] if idx < len(description_list) else None
                
                upload_data = EventMediaUpload(
                    title=file_title,
                    description=file_description,
                    tags=tag_list if tag_list else None
                )
                
                files_data.append((
                    file_content,
                    file.filename or f"unknown_file_{idx}",
                    upload_data
                ))
            
            # Batch upload
            result = await media_service.batch_upload_media_files(
                user_id=user_id,
                event_id=event_id,
                files_data=files_data
            )
            
            # Convert successful uploads to response format
            successful_responses = [
                EventMediaResponse.model_validate(media) 
                for media in result["successful"]
            ]
            
            return EventMediaBatchUploadResponse(
                successful=successful_responses,
                failed=result["failed"],
                total_requested=result["total_requested"],
                total_successful=result["total_successful"],
                total_failed=result["total_failed"]
            )
            
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{event_id}/media/json", response_model=EventMediaResponse, status_code=status.HTTP_201_CREATED)
async def create_media_json(
    event_id: UUID,
    media_data: EventMediaCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Create a new media item for an event using JSON (for URLs).
    
    - Requires JWT authentication
    - User can only add media to their own events
    - Use this endpoint when you have a file URL (e.g., from external storage)
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Create media through service
        media = await service.create_media(user_id, event_id, media_data)
        
        return EventMediaResponse.model_validate(media)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/media", response_model=List[EventMediaResponse])
async def get_event_media(
    event_id: UUID,
    current_user: CurrentActiveUser,
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Get media for an event.
    
    - Requires JWT authentication
    - User can only access their own events
    - Returns media metadata with S3 URLs
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        media, total = await media_service.get_event_media(user_id, event_id, file_type, skip, limit)
        
        return [EventMediaResponse.model_validate(media_item) for media_item in media]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{event_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    event_id: UUID,
    media_id: UUID,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Delete a media item from an event.
    
    - Requires JWT authentication
    - User can only delete media from their own events
    - Also removes the file from S3
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Delete media record and S3 file
        deleted = await media_service.delete_media(user_id, event_id, media_id)
        if not deleted:
            raise NotFoundError("Media not found")
            
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{event_id}/media/{media_id}/download")
async def download_media_file(
    event_id: UUID,
    media_id: UUID,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Download a media file from S3.
    
    - Requires JWT authentication
    - User can only download media from their own events
    - Returns the file content with appropriate headers
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Download file from S3
        file_content, filename, content_type = await media_service.download_media_file(
            user_id, event_id, media_id
        )
        
        # Return file response
        return FileResponse(
            path=None,  # We'll provide content directly
            media_type=content_type,
            filename=filename,
            content=file_content
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{event_id}/media/{media_id}/stream")
async def stream_media_file(
    event_id: UUID,
    media_id: UUID,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Stream a media file from S3.
    
    - Requires JWT authentication
    - User can only stream media from their own events
    - Returns a streaming response for large files
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Get file stream from S3
        stream, filename, content_type = await media_service.get_media_file_stream(
            user_id, event_id, media_id
        )
        
        # Create streaming response
        return StreamingResponse(
            stream,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))




# Event-Plug Association Endpoints
@router.post("/{event_id}/plugs", response_model=EventPlugResponse, status_code=status.HTTP_201_CREATED)
async def add_plug_to_event(
    event_id: UUID,
    plug_data: EventPlugCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Add a plug to an event.
    
    - Requires JWT authentication
    - User can only add their own plugs to their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Add plug to event through service
        event_plug = await service.add_plug_to_event(user_id, event_id, plug_data.plug_id, plug_data)
        
        return EventPlugResponse.model_validate(event_plug)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/plugs", response_model=EventPlugListResponse)
async def get_event_plugs(
    event_id: UUID,
    current_user: CurrentActiveUser,
    plug_type: Optional[str] = Query(None, description="Filter by plug type (target/contact)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    service: EventService = Depends(get_event_service)
):
    """
    Get plugs associated with an event.
    
    - Requires JWT authentication
    - User can only access their own events
    - Returns list with counts of targets and contacts
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        event_plugs, total = await service.get_event_plugs(user_id, event_id, plug_type, skip, limit)
        
        # Calculate counts for targets and contacts
        from app.models.plug import PlugType
        target_count = sum(1 for ep in event_plugs if ep.plug and ep.plug.plug_type == PlugType.TARGET)
        contact_count = sum(1 for ep in event_plugs if ep.plug and ep.plug.plug_type == PlugType.CONTACT)
        
        return EventPlugListResponse(
            items=[EventPlugResponse.model_validate(event_plug) for event_plug in event_plugs],
            total=total,
            counts={
                "targets": target_count,
                "contacts": contact_count
            }
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{event_id}/plugs/{plug_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_plug_from_event(
    event_id: UUID,
    plug_id: UUID,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Remove a plug from an event.
    
    - Requires JWT authentication
    - User can only remove plugs from their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        removed = await service.remove_plug_from_event(user_id, event_id, plug_id)
        if not removed:
            raise NotFoundError("Plug not found in event")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{event_id}/plugs/batch", response_model=EventPlugBatchResponse, status_code=status.HTTP_201_CREATED)
async def add_multiple_plugs_to_event(
    event_id: UUID,
    batch_data: EventPlugBatchCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Add multiple plugs to an event in batch.
    
    - Requires JWT authentication
    - User can only add their own plugs to their own events
    - Supports adding up to 50 plugs at once
    - Returns detailed results for successful and failed associations
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Convert batch data to list of dictionaries
        plugs_data = [plug.model_dump() for plug in batch_data.plugs]
        
        # Add plugs to event through service
        result = await service.add_multiple_plugs_to_event(user_id, event_id, plugs_data)
        
        # Convert created associations to response format
        created_responses = [EventPlugResponse.model_validate(assoc) for assoc in result["created"]]
        
        return EventPlugBatchResponse(
            created=created_responses,
            failed=result["failed"],
            total_requested=result["total_requested"],
            total_created=result["total_created"],
            total_failed=result["total_failed"]
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

