"""
User detail schemas for comprehensive user dashboard data.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EventStatus(str, Enum):
    """Event status enumeration."""
    UPCOMING = "upcoming"
    HAPPENING_NOW = "happening_now"
    PAST = "past"


class PlugType(str, Enum):
    """Plug type enumeration."""
    TARGET = "target"
    CONTACT = "contact"


class MediaCategory(str, Enum):
    """Media category enumeration."""
    SNAP = "snap"
    VOICE = "voice"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class UserProfile(BaseModel):
    """User profile information."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    full_name: str = Field(..., description="User full name")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    timezone: str = Field(..., description="User timezone")
    is_active: bool = Field(..., description="User active status")
    created_at: str = Field(..., description="User creation timestamp")
    updated_at: str = Field(..., description="User last update timestamp")


class DashboardMetrics(BaseModel):
    """Dashboard metrics and counts."""
    
    events_count: int = Field(..., description="Total number of events")
    leads_count: int = Field(..., description="Total number of leads (targets)")
    contacts_count: int = Field(..., description="Total number of contacts")
    media_drops_count: int = Field(..., description="Total number of media drops")


class EventSummary(BaseModel):
    """Event summary for dashboard display."""
    
    id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    theme: Optional[str] = Field(None, description="Event theme")
    description: Optional[str] = Field(None, description="Event description")
    start_date: str = Field(..., description="Event start date (ISO format)")
    end_date: str = Field(..., description="Event end date (ISO format)")
    location_name: Optional[str] = Field(None, description="Event location name")
    city: Optional[str] = Field(None, description="Event city")
    state: Optional[str] = Field(None, description="Event state")
    country: Optional[str] = Field(None, description="Event country")
    display_address: str = Field(..., description="Formatted display address")
    cover_image_url: Optional[str] = Field(None, description="Event cover image URL")
    is_active: bool = Field(..., description="Event active status")
    is_public: bool = Field(..., description="Event public status")
    total_days: int = Field(..., description="Total number of event days")
    current_day: int = Field(..., description="Current day of event (0 if not started)")
    is_happening_now: bool = Field(..., description="Whether event is currently happening")
    status: EventStatus = Field(..., description="Event status")
    agenda_count: int = Field(..., description="Number of agenda items")
    plug_counts: Dict[str, int] = Field(..., description="Count of plugs by type")


class RecentPlug(BaseModel):
    """Recent plug information for dashboard."""
    
    id: str = Field(..., description="Plug ID")
    plug_type: PlugType = Field(..., description="Type of plug (target or contact)")
    first_name: Optional[str] = Field(None, description="Contact first name")
    last_name: Optional[str] = Field(None, description="Contact last name")
    full_name: str = Field(..., description="Contact full name")
    job_title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    priority: Optional[str] = Field(None, description="Priority level")
    network_type: Optional[str] = Field(None, description="Network type")
    business_type: Optional[str] = Field(None, description="Business type")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class MediaDrop(BaseModel):
    """Media drop information for dashboard."""
    
    id: str = Field(..., description="Media ID")
    file_url: str = Field(..., description="Media file URL")
    file_type: str = Field(..., description="File MIME type")
    media_category: MediaCategory = Field(..., description="Media category")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    event_id: str = Field(..., description="Associated event ID")
    event_title: Optional[str] = Field(None, description="Associated event title")
    plug_id: Optional[str] = Field(None, description="Associated plug ID")
    plug_name: Optional[str] = Field(None, description="Associated plug name")
    created_at: str = Field(..., description="Creation timestamp")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for images/videos")


class ActiveUser(BaseModel):
    """Active user information for chat bubbles."""
    
    id: str = Field(..., description="User ID")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    full_name: str = Field(..., description="User full name")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    last_seen: str = Field(..., description="Last seen timestamp")


class UserDetailResponse(BaseModel):
    """Comprehensive user detail response for dashboard."""
    
    # User profile information
    profile: UserProfile = Field(..., description="User profile information")
    
    # Dashboard metrics
    metrics: DashboardMetrics = Field(..., description="Dashboard metrics and counts")
    
    # Current/Active event
    current_event: Optional[EventSummary] = Field(None, description="Currently happening event")
    
    # Upcoming events (next event)
    upcoming_event: Optional[EventSummary] = Field(None, description="Next upcoming event")
    
    # Recent plugs (contacts/targets)
    recent_plugs: List[RecentPlug] = Field(default_factory=list, description="Recent plugs")
    
    # Latest media drops
    latest_media_drops: List[MediaDrop] = Field(default_factory=list, description="Latest media drops")
    
    # Active users for chat
    active_users: List[ActiveUser] = Field(default_factory=list, description="Active users")
    
    # Additional metadata
    total_events: int = Field(..., description="Total number of events")
    total_plugs: int = Field(..., description="Total number of plugs")
    total_media: int = Field(..., description="Total number of media files")
    
    class Config:
        from_attributes = True


class UserDetailRequest(BaseModel):
    """User detail request schema (for future filtering options)."""
    
    include_events: bool = Field(default=True, description="Include events data")
    include_plugs: bool = Field(default=True, description="Include plugs data")
    include_media: bool = Field(default=True, description="Include media data")
    include_active_users: bool = Field(default=True, description="Include active users")
    recent_plugs_limit: int = Field(default=3, description="Limit for recent plugs")
    recent_media_limit: int = Field(default=2, description="Limit for recent media drops")
    active_users_limit: int = Field(default=3, description="Limit for active users")

