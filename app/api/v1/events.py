"""
API endpoints for event management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import DatabaseSession, CurrentActiveUser
from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventListResponse, EventStats,
    EventAgendaCreate, EventAgendaUpdate, EventAgendaResponse,
    EventExpenseCreate, EventExpenseUpdate, EventExpenseResponse,
    EventMediaCreate, EventMediaUpdate, EventMediaResponse,
    EventPlugCreate, EventPlugResponse, EventFilters
)
from app.services.event_service import EventService

router = APIRouter(tags=["Events"])


def get_event_service(db: DatabaseSession) -> EventService:
    """Dependency to get event service instance."""
    return EventService(db)


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
@router.post("/{event_id}/media", response_model=EventMediaResponse, status_code=status.HTTP_201_CREATED)
async def create_media(
    event_id: UUID,
    media_data: EventMediaCreate,
    current_user: CurrentActiveUser,
    service: EventService = Depends(get_event_service)
):
    """
    Create a new media item for an event.
    
    - Requires JWT authentication
    - User can only add media to their own events
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
    service: EventService = Depends(get_event_service)
):
    """
    Get media for an event.
    
    - Requires JWT authentication
    - User can only access their own events
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        media, total = await service.get_event_media(user_id, event_id, file_type, skip, limit)
        
        return [EventMediaResponse.model_validate(media_item) for media_item in media]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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


@router.get("/{event_id}/plugs", response_model=List[EventPlugResponse])
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
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        event_plugs, total = await service.get_event_plugs(user_id, event_id, plug_type, skip, limit)
        
        return [EventPlugResponse.model_validate(event_plug) for event_plug in event_plugs]
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

