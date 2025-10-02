"""
Pydantic schemas for plug operations.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from typing import Dict, Any

from app.models.plug import PlugType, NetworkType, BusinessType, Priority


class PlugBase(BaseModel):
    """Base schema for plug operations. All fields are optional."""
    
    first_name: Optional[str] = Field(None, max_length=32, description="Contact's first name")
    last_name: Optional[str] = Field(None, max_length=32, description="Contact's last name")
    job_title: Optional[str] = Field(None, max_length=64, description="Contact's job title")
    profile_picture: Optional[HttpUrl] = Field(None, description="Profile picture URL")
    company: Optional[str] = Field(None, max_length=64, description="Company name")
    email: Optional[EmailStr] = Field(None, description="Contact's email address")
    primary_number: Optional[str] = Field(None, max_length=18, description="Primary phone number")
    secondary_number: Optional[str] = Field(None, max_length=18, description="Secondary phone number")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")


class TargetCreate(PlugBase):
    """Schema for creating a target (incomplete plug)."""
    
    # Targets only need basic information
    pass


class TargetUpdate(BaseModel):
    """Schema for updating a target. All fields are optional."""
    
    first_name: Optional[str] = Field(None, max_length=32)
    last_name: Optional[str] = Field(None, max_length=32)
    job_title: Optional[str] = Field(None, max_length=64)
    profile_picture: Optional[HttpUrl] = Field(None)
    company: Optional[str] = Field(None, max_length=64)
    email: Optional[EmailStr] = Field(None)
    primary_number: Optional[str] = Field(None, max_length=18)
    secondary_number: Optional[str] = Field(None, max_length=18)
    linkedin_url: Optional[HttpUrl] = Field(None)


class ContactCreate(PlugBase):
    """Schema for creating a contact (complete plug). All fields are optional."""
    
    # Contact-specific fields
    notes: Optional[str] = Field(None, description="Notes about the contact")
    network_type: Optional[str] = Field(None, description="Type of network relationship (can be enum value or custom string)")
    business_type: Optional[str] = Field(None, description="Type of business (can be enum value or custom string)")
    connect_reason: Optional[str] = Field(None, description="Reason for connecting")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the contact")
    priority: Optional[Priority] = Field(None, description="Priority level for the contact")
    
    # Flexible custom_data for additional fields
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Additional custom_data including custom fields")
    
    # HubSpot integration
    hubspot_pipeline_stage: Optional[str] = Field(None, max_length=64, description="HubSpot pipeline stage")
    
    @validator('custom_data')
    def validate_custom_data(cls, v):
        """Validate custom data structure (only if provided)."""
        if v is not None:
            # Ensure custom_data is a dictionary
            if not isinstance(v, dict):
                raise ValueError('Custom data must be a dictionary')
            # Limit custom_data size to prevent abuse
            if len(str(v)) > 10000:  # 10KB limit
                raise ValueError('Custom data is too large (max 10KB)')
        return v


class ContactUpdate(BaseModel):
    """Schema for updating a contact. All fields are optional."""
    
    first_name: Optional[str] = Field(None, max_length=32)
    last_name: Optional[str] = Field(None, max_length=32)
    job_title: Optional[str] = Field(None, max_length=64)
    profile_picture: Optional[HttpUrl] = Field(None)
    company: Optional[str] = Field(None, max_length=64)
    email: Optional[EmailStr] = Field(None)
    primary_number: Optional[str] = Field(None, max_length=18)
    secondary_number: Optional[str] = Field(None, max_length=18)
    linkedin_url: Optional[HttpUrl] = Field(None)
    notes: Optional[str] = Field(None)
    network_type: Optional[str] = Field(None, description="Type of network relationship (can be enum value or custom string)")
    business_type: Optional[str] = Field(None, description="Type of business (can be enum value or custom string)")
    connect_reason: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(None)
    priority: Optional[Priority] = Field(None)
    
    # Flexible custom_data for additional fields
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Additional custom_data including custom fields")
    
    # HubSpot integration
    hubspot_pipeline_stage: Optional[str] = Field(None, max_length=64, description="HubSpot pipeline stage")
    
    @validator('custom_data')
    def validate_custom_data(cls, v):
        """Validate custom_data structure (only if provided)."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            if len(str(v)) > 10000:
                raise ValueError('Metadata is too large (max 10KB)')
        return v


class TargetToContactConversion(BaseModel):
    """Schema for converting a target to contact. All fields are optional."""
    
    notes: Optional[str] = Field(None, description="Notes about the contact")
    network_type: Optional[str] = Field(None, description="Type of network relationship (can be enum value or custom string)")
    business_type: Optional[str] = Field(None, description="Type of business (can be enum value or custom string)")
    connect_reason: Optional[str] = Field(None, description="Reason for connecting")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the contact")
    priority: Optional[Priority] = Field(None, description="Priority level for the contact")
    
    # Flexible custom_data for additional fields
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Additional custom_data including custom fields")
    
    # HubSpot integration
    hubspot_pipeline_stage: Optional[str] = Field(None, max_length=64, description="HubSpot pipeline stage")
    
    @validator('custom_data')
    def validate_custom_data(cls, v):
        """Validate custom_data structure (only if provided)."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            if len(str(v)) > 10000:
                raise ValueError('Metadata is too large (max 10KB)')
        return v


class PlugResponse(BaseModel):
    """Base response schema for plug operations."""
    
    id: UUID
    user_id: UUID
    plug_type: PlugType
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str]
    profile_picture: Optional[str]
    company: Optional[str]
    email: Optional[str]
    primary_number: Optional[str]
    secondary_number: Optional[str]
    linkedin_url: Optional[str]
    is_contact: bool
    created_at: datetime
    updated_at: datetime
    
    # Contact-specific fields (will be None for targets)
    notes: Optional[str] = None
    network_type: Optional[str] = None  # Can be enum value or custom string
    business_type: Optional[str] = None  # Can be enum value or custom string
    connect_reason: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[Priority] = None
    custom_data: Optional[Dict[str, Any]] = None  # Flexible custom data field
    hubspot_pipeline_stage: Optional[str] = None
    
    # Derived properties
    full_name: str
    display_name: str
    is_target: bool
    is_complete_contact: bool
    
    class Config:
        from_attributes = True


class TargetResponse(PlugResponse):
    """Response schema for target operations."""
    pass


class ContactResponse(PlugResponse):
    """Response schema for contact operations."""
    
    notes: Optional[str]
    network_type: Optional[str]  # Can be enum value or custom string
    business_type: Optional[str]  # Can be enum value or custom string
    connect_reason: Optional[str]
    tags: Optional[List[str]]
    priority: Optional[Priority]
    custom_data: Optional[Dict[str, Any]]  # Flexible custom data field
    hubspot_pipeline_stage: Optional[str]


class PlugListResponse(BaseModel):
    """Response schema for paginated plug lists."""
    
    items: List[PlugResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
    
    # Count information for targets and contacts
    counts: Dict[str, int] = Field(..., description="Count of plugs by type")


class PlugFilters(BaseModel):
    """Schema for filtering plugs."""
    
    plug_type: Optional[PlugType] = Field(None, description="Filter by plug type")
    network_type: Optional[NetworkType] = Field(None, description="Filter by network type")
    business_type: Optional[BusinessType] = Field(None, description="Filter by business type")
    priority: Optional[Priority] = Field(None, description="Filter by priority")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search in name, company, or email")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_contact: Optional[bool] = Field(None, description="Filter by contact status")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags filter."""
        if v is not None and len(v) > 5:
            raise ValueError('Maximum 5 tags for filtering')
        return v


class PlugStats(BaseModel):
    """Schema for plug statistics."""
    
    total_plugs: int
    total_targets: int
    total_contacts: int
    targets_by_priority: dict
    contacts_by_network_type: dict
    contacts_by_business_type: dict
    recent_conversions: int  # Targets converted to contacts in last 30 days
