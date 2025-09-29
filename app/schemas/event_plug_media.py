"""
Schemas for event plug media operations.
Simple schemas for file upload and retrieval.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class EventPlugMediaUpload(BaseModel):
    """Schema for uploading event plug media files."""
    
    media_category: str = Field(..., description="Media category: 'snap' or 'voice'")
    
    @validator('media_category')
    def validate_media_category(cls, v):
        if v not in ['snap', 'voice']:
            raise ValueError("media_category must be 'snap' or 'voice'")
        return v


class EventPlugMediaResponse(BaseModel):
    """Schema for event plug media response."""
    
    id: UUID = Field(..., description="Media ID")
    file_url: str = Field(..., description="Media file URL")
    s3_key: str = Field(..., description="S3 key for the file")
    file_type: str = Field(..., description="MIME type of the file")
    media_category: str = Field(..., description="Media category: 'snap' or 'voice'")
    event_id: UUID = Field(..., description="Event ID")
    plug_id: UUID = Field(..., description="Plug ID")
    event_plug_id: UUID = Field(..., description="Event-Plug relationship ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    class Config:
        from_attributes = True

