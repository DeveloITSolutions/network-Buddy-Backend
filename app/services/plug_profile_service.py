"""
Service for plug profile picture operations.
"""
import logging
from typing import Union
from uuid import UUID

from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.models.plug import Plug
from app.repositories.plug_repository import PlugRepository
from app.services.s3_service import get_s3_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlugProfileService:
    """
    Service for handling plug profile picture uploads and management.
    
    Follows best practices:
    - Single Responsibility: Handles only profile picture operations
    - Separation of Concerns: Uses S3Service for storage, PlugRepository for data
    - Error Handling: Comprehensive validation and error messages
    """
    
    # Allowed image types for profile pictures
    ALLOWED_PROFILE_IMAGE_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/svg+xml'
    }
    
    # Maximum file size for profile pictures (10MB)
    MAX_PROFILE_IMAGE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, db: Session):
        """Initialize plug profile service with dependencies."""
        self.db = db
        self.plug_repository = PlugRepository(db)
        self.s3_service = get_s3_service()
    
    async def upload_profile_picture(
        self,
        user_id: UUID,
        plug_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Plug:
        """
        Upload profile picture for a plug to S3.
        
        Args:
            user_id: Owner user ID
            plug_id: Plug ID
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Updated plug with new profile picture URL
            
        Raises:
            ValidationError: If file validation fails
            NotFoundError: If plug not found or not owned by user
            BusinessLogicError: If upload fails
        """
        try:
            # Verify plug ownership
            plug = await self.plug_repository.get(plug_id)
            if not plug:
                raise NotFoundError(
                    f"Plug with ID {plug_id} not found",
                    error_code="PLUG_NOT_FOUND"
                )
            
            if plug.user_id != user_id:
                raise ValidationError(
                    "You do not have permission to update this plug",
                    error_code="PLUG_ACCESS_DENIED"
                )
            
            # Validate file
            self._validate_profile_image(file_content, content_type, filename)
            
            # Delete old profile picture from S3 if exists
            if plug.profile_picture:
                await self._delete_old_profile_picture(plug.profile_picture)
            
            # Generate S3 key
            s3_key = self.s3_service._generate_s3_key(
                prefix=f"plugs/{plug_id}/profile",
                filename=filename
            )
            
            # Upload to S3
            profile_picture_url = self.s3_service.upload_file(
                file_obj=file_content,
                key=s3_key,
                content_type=content_type,
                metadata={
                    'user_id': str(user_id),
                    'plug_id': str(plug_id),
                    'original_filename': filename
                }
            )
            
            # Update plug record
            updated_plug = await self.plug_repository.update(
                plug_id,
                {"profile_picture": profile_picture_url}
            )
            
            logger.info(
                f"Successfully uploaded profile picture for plug {plug_id}: {profile_picture_url}"
            )
            
            return updated_plug
            
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error uploading profile picture for plug {plug_id}: {e}")
            raise BusinessLogicError(
                "Failed to upload profile picture",
                error_code="PROFILE_PICTURE_UPLOAD_FAILED",
                details={"plug_id": str(plug_id), "error": str(e)}
            )
    
    async def delete_profile_picture(
        self,
        user_id: UUID,
        plug_id: UUID
    ) -> Plug:
        """
        Delete profile picture for a plug.
        
        Args:
            user_id: Owner user ID
            plug_id: Plug ID
            
        Returns:
            Updated plug with profile picture removed
            
        Raises:
            NotFoundError: If plug not found or not owned by user
            BusinessLogicError: If deletion fails
        """
        try:
            # Verify plug ownership
            plug = await self.plug_repository.get(plug_id)
            if not plug:
                raise NotFoundError(
                    f"Plug with ID {plug_id} not found",
                    error_code="PLUG_NOT_FOUND"
                )
            
            if plug.user_id != user_id:
                raise ValidationError(
                    "You do not have permission to update this plug",
                    error_code="PLUG_ACCESS_DENIED"
                )
            
            # Delete from S3 if exists
            if plug.profile_picture:
                await self._delete_old_profile_picture(plug.profile_picture)
            
            # Update plug record
            updated_plug = await self.plug_repository.update(
                plug_id,
                {"profile_picture": None}
            )
            
            logger.info(f"Successfully deleted profile picture for plug {plug_id}")
            
            return updated_plug
            
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error deleting profile picture for plug {plug_id}: {e}")
            raise BusinessLogicError(
                "Failed to delete profile picture",
                error_code="PROFILE_PICTURE_DELETE_FAILED",
                details={"plug_id": str(plug_id), "error": str(e)}
            )
    
    def _validate_profile_image(
        self,
        file_content: bytes,
        content_type: str,
        filename: str
    ) -> None:
        """Validate profile image file."""
        # Check if file is provided
        if not file_content:
            raise ValidationError(
                "No file content provided",
                error_code="NO_FILE_CONTENT"
            )
        
        # Check filename
        if not filename:
            raise ValidationError(
                "No filename provided",
                error_code="NO_FILENAME"
            )
        
        # Check content type
        if content_type not in self.ALLOWED_PROFILE_IMAGE_TYPES:
            raise ValidationError(
                f"Invalid image type '{content_type}'. Allowed types: {', '.join(self.ALLOWED_PROFILE_IMAGE_TYPES)}",
                error_code="INVALID_IMAGE_TYPE"
            )
        
        # Check file size
        file_size = len(file_content)
        if file_size > self.MAX_PROFILE_IMAGE_SIZE:
            raise ValidationError(
                f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_PROFILE_IMAGE_SIZE} bytes)",
                error_code="FILE_TOO_LARGE"
            )
        
        # Check minimum file size (1KB)
        if file_size < 1024:
            raise ValidationError(
                "File is too small to be a valid image",
                error_code="FILE_TOO_SMALL"
            )
    
    async def _delete_old_profile_picture(self, profile_picture_url: str) -> None:
        """Delete old profile picture from S3."""
        try:
            # Extract S3 key from URL
            s3_key = self.s3_service.extract_s3_key_from_url(profile_picture_url)
            if s3_key:
                self.s3_service.delete_file(s3_key)
                logger.info(f"Deleted old profile picture from S3: {s3_key}")
            else:
                logger.warning(f"Could not extract S3 key from URL: {profile_picture_url}")
        except Exception as e:
            # Log error but don't fail the operation
            logger.warning(f"Failed to delete old profile picture: {e}")

