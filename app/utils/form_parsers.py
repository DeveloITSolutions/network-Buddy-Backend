"""
Form data parsers for handling multipart/form-data in API endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
import mimetypes

from fastapi import UploadFile
import logging

from app.services.file_upload_service import FileUploadService
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)


async def parse_event_form_data(
    # Form fields
    title: Optional[str] = None,
    theme: Optional[str] = None,
    description: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location_name: Optional[str] = None,
    location_address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    postal_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    website_url: Optional[str] = None,
    is_public: Optional[bool] = None,
    # File upload
    cover_image: Optional[UploadFile] = None,
    # Service and user info
    file_service: Optional[FileUploadService] = None,
    user_id: Optional[UUID] = None,
    event_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Parse event form data into a dictionary.
    
    Args:
        title: Event title
        theme: Event theme
        description: Event description
        start_date: Event start date (ISO format string)
        end_date: Event end date (ISO format string)
        location_name: Location name
        location_address: Location address
        city: City
        state: State
        country: Country
        postal_code: Postal code
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        website_url: Website URL
        is_public: Public visibility flag
        cover_image: Cover image file upload
        file_service: File upload service instance
        user_id: User ID for file upload
        event_id: Optional event ID for updates
        
    Returns:
        Dictionary with parsed event data
        
    Raises:
        ValueError: If date parsing fails
    """
    event_dict = {}
    
    # Parse string fields
    if title is not None:
        event_dict["title"] = title
    if theme is not None:
        event_dict["theme"] = theme
    if description is not None:
        event_dict["description"] = description
    if location_name is not None:
        event_dict["location_name"] = location_name
    if location_address is not None:
        event_dict["location_address"] = location_address
    if city is not None:
        event_dict["city"] = city
    if state is not None:
        event_dict["state"] = state
    if country is not None:
        event_dict["country"] = country
    if postal_code is not None:
        event_dict["postal_code"] = postal_code
    if website_url is not None:
        event_dict["website_url"] = website_url
    
    # Parse numeric fields
    if latitude is not None:
        event_dict["latitude"] = latitude
    if longitude is not None:
        event_dict["longitude"] = longitude
    
    # Parse boolean fields
    if is_public is not None:
        event_dict["is_public"] = is_public
    
    # Parse date fields
    if start_date is not None:
        try:
            event_dict["start_date"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"Failed to parse start_date: {e}")
            raise ValueError(f"Invalid start_date format: {start_date}")
    
    if end_date is not None:
        try:
            event_dict["end_date"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"Failed to parse end_date: {e}")
            raise ValueError(f"Invalid end_date format: {end_date}")
    
    # Handle file upload to S3
    if cover_image and cover_image.filename and user_id:
        try:
            # Read file content
            file_content = await cover_image.read()
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(cover_image.filename)
            file_type = content_type or 'application/octet-stream'
            
            # Generate S3 key
            if event_id:
                s3_key = s3_service()._generate_s3_key(
                    prefix=f"events/{event_id}/cover",
                    filename=cover_image.filename
                )
            else:
                s3_key = s3_service()._generate_s3_key(
                    prefix="events/cover",
                    filename=cover_image.filename
                )
            
            # Upload to S3
            file_url = s3_service().upload_file(
                file_obj=file_content,
                key=s3_key,
                metadata={
                    'user_id': str(user_id),
                    'event_id': str(event_id) if event_id else 'new',
                    'original_filename': cover_image.filename
                }
            )
            
            event_dict["cover_image_url"] = file_url
            logger.info(f"Uploaded cover image to S3: {file_url}")
        except Exception as upload_error:
            logger.error(f"Failed to upload cover image to S3: {upload_error}")
            # Continue without image rather than failing the entire request
    
    return event_dict


def parse_datetime_string(date_string: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO format datetime string.
    
    Args:
        date_string: ISO format datetime string
        
    Returns:
        Parsed datetime object or None
        
    Raises:
        ValueError: If parsing fails
    """
    if date_string is None:
        return None
    
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError as e:
        logger.error(f"Failed to parse datetime: {e}")
        raise ValueError(f"Invalid datetime format: {date_string}")

