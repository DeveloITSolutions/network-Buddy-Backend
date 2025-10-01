"""
Pydantic schemas for event operations.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Dict, Any

if TYPE_CHECKING:
    from app.schemas.plug import PlugResponse


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
    
    # Geographic coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude (-180 to 180)")
    
    # Additional location metadata (Google Places data)
    location_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional location metadata from Google Places")
    
    website_url: Optional[HttpUrl] = Field(None, description="Event website URL")
    cover_image_url: Optional[HttpUrl] = Field(None, description="Cover image URL")
    is_public: bool = Field(False, description="Whether event is public")
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate that end date is after start date."""
        if hasattr(info, 'data') and 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range."""
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range."""
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    @field_validator('location_metadata')
    @classmethod
    def validate_location_metadata(cls, v):
        """Validate location metadata structure."""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Location metadata must be a dictionary')
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
    
    # Geographic coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_metadata: Optional[Dict[str, Any]] = None
    
    website_url: Optional[HttpUrl] = None
    cover_image_url: Optional[HttpUrl] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate that end date is after start date."""
        if (v and hasattr(info, 'data') and 'start_date' in info.data 
            and info.data['start_date'] and v <= info.data['start_date']):
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
    
    # Coordinate-related computed fields
    has_coordinates: bool
    coordinates: Optional[tuple]
    google_maps_url: Optional[str]
    display_address: str
    
    # Plug counts
    plug_counts: dict = Field(default_factory=dict, description="Count of plugs by type (targets/contacts)")
    
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
    file_url: str = Field(..., description="Media file URL (S3 URL)")
    file_type: str = Field(..., min_length=1, max_length=32, description="File type/MIME type")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    tags: Optional[List[str]] = Field(None, description="Media tags")
    s3_key: Optional[str] = Field(None, description="S3 object key for the file")


class EventMediaCreate(EventMediaBase):
    """Schema for creating media."""
    pass


class EventMediaUpload(BaseModel):
    """Schema for media file upload - simplified for batch uploads."""
    
    title: Optional[str] = Field(None, max_length=256, description="Zone/Batch title (applied to all files)")
    description: Optional[str] = Field(None, description="Zone/Batch description (applied to all files)")
    tags: Optional[List[str]] = Field(None, description="Zone/Batch tags (applied to all files)")


class EventMediaUpdate(BaseModel):
    """Schema for updating media."""
    
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = Field(None, min_length=1, max_length=32)
    file_size: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    s3_key: Optional[str] = None


class EventMediaResponse(EventMediaBase):
    """Schema for media response."""
    
    id: UUID
    event_id: UUID
    batch_id: Optional[UUID] = Field(None, description="Batch/Zone ID for grouped media")
    created_at: datetime
    updated_at: datetime
    
    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        """Parse tags from comma-separated string to list."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v
    
    class Config:
        from_attributes = True


class EventMediaBatchUploadResponse(BaseModel):
    """Schema for batch media upload response."""
    
    successful: List[EventMediaResponse] = Field(default_factory=list, description="Successfully uploaded media items")
    failed: List[Dict[str, Any]] = Field(default_factory=list, description="Failed uploads with error details")
    total_requested: int = Field(..., description="Total number of files in the request")
    total_successful: int = Field(..., description="Number of successful uploads")
    total_failed: int = Field(..., description="Number of failed uploads")
    batch_id: Optional[UUID] = Field(None, description="Batch ID for all successfully uploaded files")


class MediaFileSimplified(BaseModel):
    """Simplified schema for media files in a zone - only essential data."""
    
    file_url: str = Field(..., description="Media file URL")
    
    class Config:
        from_attributes = True


class MediaZone(BaseModel):
    """Schema for a zone/batch of media files."""
    
    zone_id: UUID = Field(..., description="Unique identifier for this zone/batch")
    title: Optional[str] = Field(None, description="Zone title")
    description: Optional[str] = Field(None, description="Zone description")
    tags: List[str] = Field(default_factory=list, description="Zone tags")
    media_files: List[MediaFileSimplified] = Field(..., description="Media file URLs in this zone")
    file_count: int = Field(..., description="Number of files in this zone")
    created_at: datetime = Field(..., description="When this zone was created")
    updated_at: datetime = Field(..., description="When this zone was last updated")


class EventMediaGroupedResponse(BaseModel):
    """Schema for grouped media response."""
    
    zones: List[MediaZone] = Field(..., description="Media grouped by zones/batches")
    total_zones: int = Field(..., description="Total number of zones")
    total_files: int = Field(..., description="Total number of media files across all zones")


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
    
    # Include plug details
    plug: Optional["PlugResponse"] = Field(None, description="Plug details")
    
    class Config:
        from_attributes = True


class EventPlugListResponse(BaseModel):
    """Schema for event-plug list response with counts."""
    
    items: List[EventPlugResponse]
    total: int
    counts: Dict[str, int] = Field(..., description="Count of plugs by type (targets/contacts)")


class EventPlugBatchItem(EventPlugBase):
    """Schema for individual plug in batch operations."""
    
    plug_id: UUID = Field(..., description="Plug ID to associate with event")


class EventPlugBatchCreate(BaseModel):
    """Schema for creating multiple event-plug associations."""
    
    plugs: List[EventPlugBatchItem] = Field(..., min_items=1, max_items=50, description="List of plugs to associate with event")
    
    @field_validator('plugs')
    @classmethod
    def validate_unique_plug_ids(cls, v):
        """Validate that all plug IDs are unique."""
        plug_ids = [plug.plug_id for plug in v]
        if len(plug_ids) != len(set(plug_ids)):
            raise ValueError('Duplicate plug IDs are not allowed')
        return v


class EventPlugBatchResponse(BaseModel):
    """Schema for batch event-plug association response."""
    
    created: List[EventPlugResponse] = Field(..., description="Successfully created associations")
    failed: List[dict] = Field(..., description="Failed associations with error details")
    total_requested: int = Field(..., description="Total plugs requested")
    total_created: int = Field(..., description="Total plugs successfully created")
    total_failed: int = Field(..., description="Total plugs that failed to create")


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
    
    # Geographic filtering
    has_coordinates: Optional[bool] = Field(None, description="Filter events with/without coordinates")
    near_latitude: Optional[float] = Field(None, ge=-90, le=90, description="Center latitude for proximity search")
    near_longitude: Optional[float] = Field(None, ge=-180, le=180, description="Center longitude for proximity search")
    radius_km: Optional[float] = Field(None, ge=0.1, le=1000, description="Search radius in kilometers")
    
    @field_validator('radius_km')
    @classmethod
    def validate_proximity_search(cls, v, info):
        """Validate proximity search parameters."""
        if v is not None and hasattr(info, 'data'):
            # If radius is provided, both coordinates must be provided
            if ('near_latitude' not in info.data or 'near_longitude' not in info.data or
                info.data.get('near_latitude') is None or info.data.get('near_longitude') is None):
                raise ValueError('Both near_latitude and near_longitude are required when using radius_km')
        return v


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


# Resolve forward references for EventPlugResponse
from app.schemas.plug import PlugResponse
EventPlugResponse.model_rebuild()
