"""
Pydantic schemas for event operations.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator


# Base schemas
class EventBase(BaseModel):
    """Base schema for event operations."""
    
    title: str = Field(..., min_length=1, max_length=128, description="Event title")
    theme: Optional[str] = Field(None, max_length=64, description="Event theme")
    description: Optional[str] = Field(None, description="Event description")
    start_date: datetime = Field(..., description="Event start date and time")
    end_date: datetime = Field(..., description="Event end date and time")
    location_name: Optional[str] = Field(None, max_length=128, description="Location name")
    location_address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, max_length=64, description="City")
    state: Optional[str] = Field(None, max_length=64, description="State/Province")
    country: Optional[str] = Field(None, max_length=64, description="Country")
    postal_code: Optional[str] = Field(None, max_length=16, description="Postal code")
    website_url: Optional[HttpUrl] = Field(None, description="Event website URL")
    cover_image_url: Optional[HttpUrl] = Field(None, description="Cover image URL")
    is_public: bool = Field(False, description="Whether event is public")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end date is after start date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class EventCreate(EventBase):
    """Schema for creating an event."""
    pass


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    theme: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location_name: Optional[str] = Field(None, max_length=128)
    location_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=64)
    state: Optional[str] = Field(None, max_length=64)
    country: Optional[str] = Field(None, max_length=64)
    postal_code: Optional[str] = Field(None, max_length=16)
    website_url: Optional[HttpUrl] = None
    cover_image_url: Optional[HttpUrl] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end date is after start date."""
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class EventResponse(EventBase):
    """Schema for event response."""
    
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_days: int
    current_day: int
    is_happening_now: bool
    total_budget: float
    expenses_by_category: dict
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for paginated event list response."""
    
    items: List[EventResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


# Agenda schemas
class EventAgendaBase(BaseModel):
    """Base schema for event agenda operations."""
    
    title: str = Field(..., min_length=1, max_length=256, description="Agenda item title")
    description: Optional[str] = Field(None, description="Agenda item description")
    location: Optional[str] = Field(None, max_length=128, description="Location")
    day: int = Field(..., ge=1, description="Event day (1-based)")
    start_time: datetime = Field(..., description="Start time")
    duration_minutes: int = Field(60, ge=1, le=1440, description="Duration in minutes")


class EventAgendaCreate(EventAgendaBase):
    """Schema for creating an agenda item."""
    pass


class EventAgendaUpdate(BaseModel):
    """Schema for updating an agenda item."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=128)
    day: Optional[int] = Field(None, ge=1)
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)


class EventAgendaResponse(EventAgendaBase):
    """Schema for agenda item response."""
    
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime
    end_time: datetime
    duration_display: str
    
    class Config:
        from_attributes = True


# Expense schemas
class EventExpenseBase(BaseModel):
    """Base schema for event expense operations."""
    
    category: str = Field(..., min_length=1, max_length=64, description="Expense category")
    description: Optional[str] = Field(None, max_length=256, description="Expense description")
    amount: float = Field(..., ge=0, description="Expense amount")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")


class EventExpenseCreate(EventExpenseBase):
    """Schema for creating an expense."""
    pass


class EventExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    
    category: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=256)
    amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)


class EventExpenseResponse(EventExpenseBase):
    """Schema for expense response."""
    
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Media schemas
class EventMediaBase(BaseModel):
    """Base schema for event media operations."""
    
    title: Optional[str] = Field(None, max_length=256, description="Media title")
    description: Optional[str] = Field(None, description="Media description")
    file_url: str = Field(..., description="Media file URL")
    file_type: str = Field(..., min_length=1, max_length=32, description="File type")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    tags: Optional[List[str]] = Field(None, description="Media tags")


class EventMediaCreate(EventMediaBase):
    """Schema for creating media."""
    pass


class EventMediaUpdate(BaseModel):
    """Schema for updating media."""
    
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = Field(None, min_length=1, max_length=32)
    file_size: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None


class EventMediaResponse(EventMediaBase):
    """Schema for media response."""
    
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """Parse tags from comma-separated string to list."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v
    
    class Config:
        from_attributes = True


# Event-Plug association schemas
class EventPlugBase(BaseModel):
    """Base schema for event-plug association operations."""
    
    notes: Optional[str] = Field(None, description="Notes about the plug in this event")
    priority: Optional[str] = Field(None, max_length=32, description="Priority level")


class EventPlugCreate(EventPlugBase):
    """Schema for creating event-plug association."""
    
    plug_id: UUID = Field(..., description="Plug ID to associate with event")


class EventPlugUpdate(EventPlugBase):
    """Schema for updating event-plug association."""
    pass


class EventPlugResponse(EventPlugBase):
    """Schema for event-plug association response."""
    
    id: UUID
    event_id: UUID
    plug_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Filter schemas
class EventFilters(BaseModel):
    """Schema for event filtering."""
    
    search: Optional[str] = Field(None, description="Search term")
    start_date_from: Optional[datetime] = Field(None, description="Filter events from this date")
    start_date_to: Optional[datetime] = Field(None, description="Filter events to this date")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    city: Optional[str] = Field(None, description="Filter by city")
    country: Optional[str] = Field(None, description="Filter by country")


class EventStats(BaseModel):
    """Schema for event statistics."""
    
    total_events: int
    active_events: int
    upcoming_events: int
    past_events: int
    total_budget: float
    events_by_month: dict
    events_by_city: dict
    events_by_country: dict


# Import/Export schemas
class AgendaImportRequest(BaseModel):
    """Schema for importing agenda from URL."""
    
    url: HttpUrl = Field(..., description="URL to import agenda from")


class AgendaImportResponse(BaseModel):
    """Schema for agenda import response."""
    
    success: bool
    message: str
    imported_items: Optional[List[EventAgendaResponse]] = None
