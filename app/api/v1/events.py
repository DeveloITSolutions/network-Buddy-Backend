"""
API endpoints for event management.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form

from app.core.dependencies import DatabaseSession, CurrentActiveUser
from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventListResponse,
    EventAgendaCreate, EventAgendaUpdate, EventAgendaResponse,
    EventExpenseCreate, EventExpenseUpdate, EventExpenseResponse,
    EventMediaCreate, EventMediaUpdate, EventMediaResponse, EventMediaUpload, EventMediaBatchUploadResponse, EventMediaGroupedResponse, MediaZone, ZoneUpdate, ZoneUpdateResponse,
    EventPlugCreate, EventPlugResponse, EventPlugListResponse, EventPlugBatchCreate, EventPlugBatchResponse, EventFilters
)
from app.services.event_service import EventService
from app.services.event_media_service import EventMediaService
from app.services.file_upload_service import FileUploadService
from app.utils.form_parsers import parse_event_form_data

logger = logging.getLogger(__name__)

# Main router for all event-related endpoints
router = APIRouter()


def get_event_service(db: DatabaseSession) -> EventService:
    """Dependency to get event service instance."""
    return EventService(db)


def get_file_upload_service(db: DatabaseSession) -> FileUploadService:
    """Dependency to get file upload service instance."""
    return FileUploadService(db)


def get_event_media_service(db: DatabaseSession) -> EventMediaService:
    """Dependency to get event media service instance."""
    return EventMediaService(db)


# ============================================================================
# EVENT MANAGEMENT ENDPOINTS
# Core CRUD operations for events
# ============================================================================

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED, tags=["Events - Core"])
async def create_event(
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service),
    file_service: FileUploadService = Depends(get_file_upload_service),
    # Form fields
    title: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    location_name: Optional[str] = Form(None),
    location_address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    website_url: Optional[str] = Form(None),
    is_public: bool = Form(False),
    # File upload
    cover_image: Optional[UploadFile] = File(None)
):
    """
    Create a new event with optional cover image upload.
    
    - Requires JWT authentication
    - User can only create their own events
    - Accepts multipart/form-data for file upload
    - All fields are optional per client requirements
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Parse form data using helper function (DRY principle)
        event_dict = await parse_event_form_data(
            title=title,
            theme=theme,
            description=description,
            start_date=start_date,
            end_date=end_date,
            location_name=location_name,
            location_address=location_address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            website_url=website_url,
            is_public=is_public,
            cover_image=cover_image,
            file_service=file_service,
            user_id=user_id
        )
        
        # Create event through repository
        from app.repositories.event_repository import EventRepository
        event_repo = EventRepository(service.db)
        event = await event_repo.create_event(user_id, event_dict)
        
        return EventResponse.model_validate(event)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/{event_id}", response_model=EventResponse, tags=["Events - Core"])
async def update_event(
    event_id: UUID,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service),
    file_service: FileUploadService = Depends(get_file_upload_service),
    # Form fields
    title: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    location_name: Optional[str] = Form(None),
    location_address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    website_url: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(None),
    # File upload
    cover_image: Optional[UploadFile] = File(None)
):
    """
    Update an existing event with optional cover image upload.
    
    - Requires JWT authentication
    - User can only update their own events
    - Accepts multipart/form-data for file upload
    - All fields are optional for partial updates
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Parse form data using helper function (DRY principle)
        update_dict = await parse_event_form_data(
            title=title,
            theme=theme,
            description=description,
            start_date=start_date,
            end_date=end_date,
            location_name=location_name,
            location_address=location_address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            website_url=website_url,
            is_public=is_public,
            cover_image=cover_image,
            file_service=file_service,
            user_id=user_id,
            event_id=event_id
        )
        
        # Update event through service
        event = await service.update_event(user_id, event_id, EventUpdate(**update_dict))
        
        if not event:
            raise NotFoundError("Event not found")
        
        return EventResponse.model_validate(event)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Events - Core"])
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


@router.get("/{event_id}", response_model=EventResponse, tags=["Events - Core"])
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


@router.get("/", response_model=EventListResponse, tags=["Events - Core"])
async def list_events(
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    time_filter: Optional[str] = Query(None, description="Filter by time period: 'today', 'upcoming', 'past'"),
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
    - Supports time-based filtering: 'today', 'upcoming', 'past'
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Apply time-based filtering if time_filter is provided
        from datetime import datetime, timezone
        if time_filter:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if time_filter.lower() == "today":
                # Events happening today (start_date or end_date falls on today)
                start_date_from = today_start.isoformat()
                start_date_to = today_end.isoformat()
            elif time_filter.lower() == "upcoming":
                # Events starting after today
                start_date_from = today_end.isoformat()
                start_date_to = None
            elif time_filter.lower() == "past":
                # Events that ended before today
                start_date_from = None
                start_date_to = today_start.isoformat()
            else:
                raise ValidationError(
                    f"Invalid time_filter value: {time_filter}. Must be 'today', 'upcoming', or 'past'",
                    error_code="INVALID_TIME_FILTER"
                )
        
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



# ============================================================================
# DEEDS MODULE - AGENDA ENDPOINTS
# Event agenda/itinerary management
# ============================================================================

@router.post("/{event_id}/agenda", response_model=EventAgendaResponse, status_code=status.HTTP_201_CREATED, tags=["Deeds - Agenda"])
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


@router.get("/{event_id}/agenda/days", tags=["Deeds - Agenda"])
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


@router.get("/{event_id}/agenda", response_model=List[EventAgendaResponse], tags=["Deeds - Agenda"])
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


@router.put("/{event_id}/agenda/{agenda_id}", response_model=EventAgendaResponse, tags=["Deeds - Agenda"])
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


@router.delete("/{event_id}/agenda/{agenda_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Deeds - Agenda"])
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


# ============================================================================
# DEEDS MODULE - EXPENSE ENDPOINTS
# Event budget and expense tracking
# ============================================================================

@router.post("/{event_id}/expenses", response_model=EventExpenseResponse, status_code=status.HTTP_201_CREATED, tags=["Deeds - Expenses"])
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


@router.get("/{event_id}/expenses", response_model=List[EventExpenseResponse], tags=["Deeds - Expenses"])
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


# ============================================================================
# ZONE MODULE - MEDIA ENDPOINTS
# Event media management (photos, videos, documents)
# ============================================================================

@router.post("/{event_id}/media", tags=["Zone - Media"])
async def upload_media_to_s3(
    event_id: UUID,
    current_user: CurrentActiveUser,
    files: List[UploadFile] = File(..., description="Media file(s) to upload to S3. Can upload single or multiple files."),
    title: Optional[str] = Form(None, description="Zone/Batch title (applied to all files)"),
    description: Optional[str] = Form(None, description="Zone/Batch description (applied to all files)"),
    tags: Optional[str] = Form(None, description="Comma-separated tags (applied to all files)"),
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Upload one or more media files to S3 and create media records.
    
    - Requires JWT authentication
    - User can only add media to their own events
    - Accepts multipart/form-data for file uploads
    - Files uploaded together are grouped as one "zone" with shared metadata
    - **Single File**: Returns EventMediaResponse
    - **Multiple Files**: Returns EventMediaBatchUploadResponse with batch_id
    
    **Simplified Upload**: All files in a single upload share the same title, description, and tags.
    This creates a logical grouping (zone) that can be retrieved together.
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Parse tags (applied to all files)
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Create shared metadata for all files
        upload_metadata = EventMediaUpload(
            title=title,
            description=description,
            tags=tag_list if tag_list else None
        )
        
        # File size limit from settings (supports large videos up to 500MB)
        from app.config.settings import settings
        max_file_size = settings.max_file_size
        
        # Single file upload
        if len(files) == 1:
            file = files[0]
            file_content = await file.read()
            
            if len(file_content) > max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({max_file_size} bytes)"
                )
            
            media = await media_service.upload_media_file(
                user_id=user_id,
                event_id=event_id,
                file_obj=file_content,
                filename=file.filename or "unknown_file",
                upload_data=upload_metadata
            )
            
            return EventMediaResponse.model_validate(media)
        
        # Multiple files upload - batch processing with shared metadata
        else:
            files_data = []
            
            for idx, file in enumerate(files):
                # Read file content
                file_content = await file.read()
                
                # Check file size
                if len(file_content) > max_file_size:
                    logger.warning(f"File {file.filename} ({len(file_content)} bytes) exceeds max size, skipping")
                    continue
                
                files_data.append((
                    file_content,
                    file.filename or f"unknown_file_{idx}"
                ))
            
            # Batch upload with shared metadata
            result = await media_service.batch_upload_media_files(
                user_id=user_id,
                event_id=event_id,
                files_data=files_data,
                upload_metadata=upload_metadata
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
                total_failed=result["total_failed"],
                batch_id=result.get("batch_id")
            )
            
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/media/grouped", response_model=EventMediaGroupedResponse, tags=["Zone - Media"])
async def get_event_media_grouped(
    event_id: UUID,
    current_user: CurrentActiveUser,
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Get media grouped by zones/batches.
    
    - Requires JWT authentication
    - User can only access their own events
    - Returns media grouped by batch_id
    - Each zone contains all files uploaded together with shared metadata
    - Perfect for displaying organized media galleries
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        result = await media_service.get_event_media_grouped(user_id, event_id, file_type)
        
        return EventMediaGroupedResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/media/zones/{zone_id}", response_model=MediaZone, tags=["Zone - Media"])
async def get_zone_details(
    event_id: UUID,
    zone_id: UUID,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Get details of a specific zone with all its media files.
    
    - Requires JWT authentication
    - User can only access their own events
    - Returns complete zone details with all associated media files
    - Useful for viewing a specific upload batch/zone
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        zone_details = await media_service.get_zone_details(user_id, event_id, zone_id)
        
        if not zone_details:
            raise NotFoundError(f"Zone {zone_id} not found for event {event_id}")
        
        return MediaZone(**zone_details)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{event_id}/media/zones/{zone_id}", response_model=ZoneUpdateResponse, tags=["Zone - Media"])
async def update_zone_metadata(
    event_id: UUID,
    zone_id: UUID,
    zone_update: ZoneUpdate,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Update zone metadata (title, description, tags).
    
    - Requires JWT authentication
    - User can only update zones from their own events
    - Updates only the provided fields (partial update)
    - Does not affect media files in the zone
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Convert schema to dict, excluding unset fields
        update_data = zone_update.model_dump(exclude_unset=True)
        
        # Update zone
        updated_zone = await media_service.update_zone(user_id, event_id, zone_id, update_data)
        
        if not updated_zone:
            raise NotFoundError(f"Zone {zone_id} not found for event {event_id}")
        
        return ZoneUpdateResponse(**updated_zone)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{event_id}/media/zones/{zone_id}/files", response_model=EventMediaBatchUploadResponse, tags=["Zone - Media"])
async def add_media_to_zone(
    event_id: UUID,
    zone_id: UUID,
    current_user: CurrentActiveUser,
    files: List[UploadFile] = File(..., description="Media files to add to the zone"),
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Add new media files to an existing zone.
    
    - Requires JWT authentication
    - User can only add media to zones in their own events
    - Files inherit the zone's existing metadata (title, description, tags)
    - Useful for adding more photos to an existing album/zone
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # File size limit from settings (supports large videos up to 500MB)
        from app.config.settings import settings
        max_file_size = settings.max_file_size
        
        # Prepare files data
        files_data = []
        for idx, file in enumerate(files):
            # Read file content
            file_content = await file.read()
            
            # Check file size
            if len(file_content) > max_file_size:
                logger.warning(f"File {file.filename} ({len(file_content)} bytes) exceeds max size, skipping")
                continue
            
            files_data.append((
                file_content,
                file.filename or f"unknown_file_{idx}"
            ))
        
        if not files_data:
            raise ValidationError("No valid files to upload", error_code="NO_VALID_FILES")
        
        # Add files to zone
        result = await media_service.add_media_to_zone(
            user_id=user_id,
            event_id=event_id,
            zone_id=zone_id,
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
            total_failed=result["total_failed"],
            batch_id=result.get("zone_id")
        )
            
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{event_id}/media", response_model=List[EventMediaResponse], tags=["Zone - Media"])
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


@router.delete("/{event_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Zone - Media"])
async def delete_media(
    event_id: UUID,
    media_id: UUID,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Delete a single media file from an event.
    
    - Requires JWT authentication
    - User can only delete media from their own events
    - Removes the file from S3
    - If this is the last file in a zone, the zone is also deleted automatically
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


@router.delete("/{event_id}/media/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Zone - Media"])
async def delete_zone(
    event_id: UUID,
    zone_id: UUID,
    current_user: CurrentActiveUser,
    media_service: EventMediaService = Depends(get_event_media_service)
):
    """
    Delete an entire zone with all its media files.
    
    - Requires JWT authentication
    - User can only delete zones from their own events
    - Removes all associated files from S3
    - Deletes the zone metadata and all media records
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Delete zone with all media files
        deleted = await media_service.delete_zone(user_id, event_id, zone_id)
        if not deleted:
            raise NotFoundError(f"Zone {zone_id} not found for event {event_id}")
            
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))







# ============================================================================
# EVENT-PLUG ASSOCIATION ENDPOINTS
# Manage connections between events and plugs (contacts/targets)
# ============================================================================

@router.post("/{event_id}/plugs", response_model=EventPlugResponse, status_code=status.HTTP_201_CREATED, tags=["Event Plugs"])
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


@router.get("/{event_id}/plugs", response_model=EventPlugListResponse, tags=["Event Plugs"])
async def get_event_plugs(
    event_id: UUID,
    current_user: CurrentActiveUser,
    plug_type: Optional[str] = Query(None, description="Filter by plug type (target/contact)"),
    network_type: Optional[str] = Query(None, description="Filter by network type (new_client, existing_client, new_partnership, etc.)"),
    q: Optional[str] = Query(None, min_length=1, description="Search query (name, company, email, network_type)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    service: EventService = Depends(get_event_service)
):
    """
    Get plugs associated with an event with filtering and search.
    
    - Requires JWT authentication
    - User can only access their own events
    - Returns list with counts of targets and contacts
    - Supports filtering by plug_type and network_type
    - Supports text search across name, company, email, network_type
    
    Examples:
    - All event plugs: GET /events/{event_id}/plugs
    - Filter contacts: ?plug_type=contact
    - Filter by network type: ?network_type=new_client
    - Search plugs: ?q=john
    - Combined filters: ?plug_type=contact&network_type=existing_client&q=acme
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        event_plugs, total = await service.get_event_plugs(
            user_id, event_id, plug_type, network_type, q, skip, limit
        )
        
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


@router.delete("/{event_id}/plugs/{plug_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Event Plugs"])
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


@router.post("/{event_id}/plugs/batch", response_model=EventPlugBatchResponse, status_code=status.HTTP_201_CREATED, tags=["Event Plugs"])
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

