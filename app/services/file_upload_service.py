"""
File upload service for handling file uploads and storage.
"""
import os
import uuid
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, BusinessLogicError
from app.utils.helpers import sanitize_filename, format_file_size
import logging

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads and storage."""
    
    # Allowed file types and their MIME types
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/svg+xml'
    }
    
    ALLOWED_VIDEO_TYPES = {
        'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 
        'video/flv', 'video/webm', 'video/mkv'
    }
    
    ALLOWED_DOCUMENT_TYPES = {
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain', 'text/csv'
    }
    
    ALLOWED_AUDIO_TYPES = {
        'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp3', 'audio/aac'
    }
    
    # Maximum file sizes (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB - supports large videos
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB - supports high quality audio
    
    def __init__(self, db: Session, upload_dir: str = "uploads"):
        """Initialize file upload service."""
        self.db = db
        self.upload_dir = Path(upload_dir)
        
        # Create base upload directory if it doesn't exist
        # Subdirectories are created lazily when files are uploaded
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.warning(f"Cannot create upload directory {self.upload_dir}: {e}. Directory must exist with proper permissions.")
        except Exception as e:
            logger.error(f"Unexpected error creating upload directory: {e}")
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: UUID,
        event_id: Optional[UUID] = None,
        subdirectory: str = "general"
    ) -> Tuple[str, str, int, str]:
        """
        Upload a file and return file information.
        
        Args:
            file: Uploaded file
            user_id: User ID uploading the file
            event_id: Optional event ID for event-related files
            subdirectory: Subdirectory within uploads (e.g., 'events', 'profiles')
            
        Returns:
            Tuple of (file_url, file_type, file_size, original_filename)
            
        Raises:
            ValidationError: If file validation fails
            BusinessLogicError: If upload fails
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Determine file category and subdirectory
            file_category = self._get_file_category(file.content_type)
            if event_id:
                upload_path = self.upload_dir / "events" / str(event_id) / file_category
            else:
                upload_path = self.upload_dir / subdirectory / file_category
            
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = upload_path / unique_filename
            file_url = f"/uploads/{subdirectory}/{file_category}/{unique_filename}"
            if event_id:
                file_url = f"/uploads/events/{event_id}/{file_category}/{unique_filename}"
            
            # Read and save file content
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Get file size
            file_size = len(content)
            
            logger.info(
                f"File uploaded successfully: {file.filename} -> {file_url} "
                f"(Size: {format_file_size(file_size)})"
            )
            
            return file_url, file.content_type, file_size, file.filename
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            raise BusinessLogicError(
                "Failed to upload file",
                error_code="FILE_UPLOAD_FAILED",
                details={"filename": file.filename, "error": str(e)}
            )
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_url: URL of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Convert URL to file path
            if file_url.startswith("/uploads/"):
                file_path = self.upload_dir / file_url[9:]  # Remove "/uploads/" prefix
            else:
                file_path = Path(file_url)
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted successfully: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_url}: {e}")
            return False
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        if not file.filename:
            raise ValidationError("No filename provided", error_code="NO_FILENAME")
        
        if not file.content_type:
            raise ValidationError("File type could not be determined", error_code="UNKNOWN_FILE_TYPE")
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer
        
        file_category = self._get_file_category(file.content_type)
        max_size = self._get_max_file_size(file_category)
        
        if file_size > max_size:
            raise ValidationError(
                f"File size ({format_file_size(file_size)}) exceeds maximum allowed size "
                f"({format_file_size(max_size)}) for {file_category} files",
                error_code="FILE_TOO_LARGE"
            )
        
        # Validate file type
        if not self._is_allowed_file_type(file.content_type):
            raise ValidationError(
                f"File type '{file.content_type}' is not allowed",
                error_code="INVALID_FILE_TYPE"
            )
        
        # Validate file extension
        file_extension = self._get_file_extension(file.filename)
        if not self._is_valid_extension(file_extension, file.content_type):
            raise ValidationError(
                f"File extension '{file_extension}' does not match file type '{file.content_type}'",
                error_code="INVALID_FILE_EXTENSION"
            )
    
    def _get_file_category(self, content_type: str) -> str:
        """Get file category based on content type."""
        if content_type in self.ALLOWED_IMAGE_TYPES:
            return "images"
        elif content_type in self.ALLOWED_VIDEO_TYPES:
            return "videos"
        elif content_type in self.ALLOWED_DOCUMENT_TYPES:
            return "documents"
        elif content_type in self.ALLOWED_AUDIO_TYPES:
            return "audio"
        else:
            return "general"
    
    def _get_max_file_size(self, file_category: str) -> int:
        """Get maximum file size for category."""
        size_map = {
            "images": self.MAX_IMAGE_SIZE,
            "videos": self.MAX_VIDEO_SIZE,
            "documents": self.MAX_DOCUMENT_SIZE,
            "audio": self.MAX_AUDIO_SIZE,
            "general": self.MAX_DOCUMENT_SIZE
        }
        return size_map.get(file_category, self.MAX_DOCUMENT_SIZE)
    
    def _is_allowed_file_type(self, content_type: str) -> bool:
        """Check if file type is allowed."""
        all_allowed_types = (
            self.ALLOWED_IMAGE_TYPES | 
            self.ALLOWED_VIDEO_TYPES | 
            self.ALLOWED_DOCUMENT_TYPES | 
            self.ALLOWED_AUDIO_TYPES
        )
        return content_type in all_allowed_types
    
    def _is_valid_extension(self, extension: str, content_type: str) -> bool:
        """Validate file extension matches content type."""
        # Get expected extensions for content type
        expected_extensions = mimetypes.guess_all_extensions(content_type)
        return extension.lower() in [ext.lower() for ext in expected_extensions]
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        if not filename or '.' not in filename:
            return ""
        return '.' + filename.rsplit('.', 1)[1].lower()
    
    def get_file_info(self, file_url: str) -> Optional[dict]:
        """Get file information."""
        try:
            if file_url.startswith("/uploads/"):
                file_path = self.upload_dir / file_url[9:]
            else:
                file_path = Path(file_url)
            
            if file_path.exists():
                stat = file_path.stat()
                return {
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "exists": True
                }
            return None
        except Exception as e:
            logger.error(f"Error getting file info for {file_url}: {e}")
            return None
