"""
S3 service for handling file uploads, downloads, and management.
"""
import logging
import mimetypes
from datetime import datetime, timedelta
from typing import BinaryIO, Dict, List, Optional, Union
from urllib.parse import urlparse

import boto3
from botocore.exceptions import (
    ClientError, 
    NoCredentialsError, 
    PartialCredentialsError,
    EndpointConnectionError
)
from botocore.client import Config

from app.config.settings import settings
from app.core.exceptions import BusinessLogicError, ValidationError

logger = logging.getLogger(__name__)


class S3Service:
    """
    Service for AWS S3 operations.
    
    This service handles file uploads, downloads, listing, and deletion
    using the AWS S3 service with proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize S3 service with configuration from settings."""
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.s3_region
        self.max_file_size = settings.max_file_size
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                config=Config(
                    signature_version='s3v4',
                    s3={
                        'addressing_style': 'virtual'
                    }
                )
            )
            
            # Test connection
            self._test_connection()
            logger.info(f"S3 service initialized successfully for bucket: {self.bucket_name}")
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"S3 credentials error: {e}")
            raise BusinessLogicError(
                "S3 credentials not configured properly. Ensure EC2 IAM role has S3 access.",
                error_code="S3_SERVICE_ERROR"
            )
        except Exception as e:
            logger.error(f"S3 service initialization error: {e}")
            raise BusinessLogicError(
                f"Failed to initialize S3 service: {str(e)}",
                error_code="S3_SERVICE_ERROR"
            )
    
    def _test_connection(self) -> None:
        """Test S3 connection by checking bucket access."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise BusinessLogicError(
                    f"S3 bucket '{self.bucket_name}' not found",
                    error_code="S3_BUCKET_NOT_FOUND"
                )
            elif error_code == '403':
                raise BusinessLogicError(
                    f"Access denied to S3 bucket '{self.bucket_name}'",
                    error_code="S3_ACCESS_DENIED"
                )
            else:
                raise BusinessLogicError(
                    f"S3 connection error: {str(e)}",
                    error_code="S3_CONNECTION_ERROR"
                )
        except EndpointConnectionError as e:
            raise BusinessLogicError(
                f"Cannot connect to S3 endpoint: {str(e)}",
                error_code="S3_CONNECTION_ERROR"
            )
    
    def _validate_file_size(self, file_size: int) -> None:
        """Validate file size against configured limits."""
        if file_size > self.max_file_size:
            raise ValidationError(
                f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)",
                error_code="FILE_TOO_LARGE"
            )
    
    def _generate_s3_key(self, prefix: str, filename: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate a unique S3 key for file storage.
        
        Args:
            prefix: S3 key prefix (e.g., 'events', 'users')
            filename: Original filename
            timestamp: Optional timestamp for the key
            
        Returns:
            Unique S3 key
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Extract file extension
        file_ext = ""
        if "." in filename:
            file_ext = filename.split(".")[-1].lower()
        
        # Generate timestamp-based key
        date_str = timestamp.strftime("%Y/%m/%d")
        time_str = timestamp.strftime("%H%M%S")
        unique_id = timestamp.strftime("%f")  # microseconds for uniqueness
        
        key = f"{prefix}/{date_str}/{time_str}_{unique_id}"
        if file_ext:
            key += f".{file_ext}"
        
        return key
    
    def _get_content_type(self, filename: str) -> str:
        """Get MIME type for file."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_obj: File object to upload
            key: S3 object key
            content_type: MIME type of the file
            metadata: Additional metadata for the object
            
        Returns:
            S3 object URL
            
        Raises:
            BusinessLogicError: If upload fails
            ValidationError: If file is too large
        """
        try:
            # Get file size
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            
            # Validate file size
            self._validate_file_size(file_size)
            
            # Determine content type
            if not content_type:
                content_type = self._get_content_type(key)
            
            # Prepare upload parameters
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs=extra_args
            )
            
            # Generate and return URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            
            logger.info(f"Successfully uploaded file to S3: {key} ({file_size} bytes)")
            return url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload error for key '{key}': {e}")
            raise BusinessLogicError(
                f"Failed to upload file to S3: {error_code}",
                error_code="S3_UPLOAD_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload for key '{key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file upload: {str(e)}",
                error_code="S3_UPLOAD_ERROR"
            )
    
    def upload_file_from_path(
        self,
        file_path: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file from local path to S3.
        
        Args:
            file_path: Local file path
            key: S3 object key
            content_type: MIME type of the file
            metadata: Additional metadata for the object
            
        Returns:
            S3 object URL
        """
        try:
            # Get file size
            import os
            file_size = os.path.getsize(file_path)
            
            # Validate file size
            self._validate_file_size(file_size)
            
            # Determine content type
            if not content_type:
                content_type = self._get_content_type(os.path.basename(file_path))
            
            # Prepare upload parameters
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                key,
                ExtraArgs=extra_args
            )
            
            # Generate and return URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            
            logger.info(f"Successfully uploaded file from path to S3: {key} ({file_size} bytes)")
            return url
            
        except FileNotFoundError:
            raise ValidationError(
                f"File not found: {file_path}",
                error_code="FILE_NOT_FOUND"
            )
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload error for file '{file_path}': {e}")
            raise BusinessLogicError(
                f"Failed to upload file to S3: {error_code}",
                error_code="S3_UPLOAD_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload for file '{file_path}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file upload: {str(e)}",
                error_code="S3_UPLOAD_ERROR"
            )
    
    def download_file(self, key: str) -> bytes:
        """
        Download a file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            File content as bytes
            
        Raises:
            BusinessLogicError: If download fails
            ValidationError: If file not found
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            
            logger.info(f"Successfully downloaded file from S3: {key} ({len(content)} bytes)")
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise ValidationError(
                    f"File not found in S3: {key}",
                    error_code="FILE_NOT_FOUND"
                )
            logger.error(f"S3 download error for key '{key}': {e}")
            raise BusinessLogicError(
                f"Failed to download file from S3: {error_code}",
                error_code="S3_DOWNLOAD_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 download for key '{key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file download: {str(e)}",
                error_code="S3_DOWNLOAD_ERROR"
            )
    
    def get_file_stream(self, key: str):
        """
        Get a streaming download for a file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Streaming body object
            
        Raises:
            BusinessLogicError: If download fails
            ValidationError: If file not found
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully opened stream for S3 file: {key}")
            return response['Body']
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise ValidationError(
                    f"File not found in S3: {key}",
                    error_code="FILE_NOT_FOUND"
                )
            logger.error(f"S3 stream error for key '{key}': {e}")
            raise BusinessLogicError(
                f"Failed to stream file from S3: {error_code}",
                error_code="S3_DOWNLOAD_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 stream for key '{key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file streaming: {str(e)}",
                error_code="S3_DOWNLOAD_ERROR"
            )
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted file from S3: {key}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 delete error for key '{key}': {e}")
            raise BusinessLogicError(
                f"Failed to delete file from S3: {error_code}",
                error_code="S3_DELETE_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 delete for key '{key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file deletion: {str(e)}",
                error_code="S3_DELETE_ERROR"
            )
    
    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Union[List[Dict], str]]:
        """
        List files in S3 bucket with optional prefix.
        
        Args:
            prefix: S3 key prefix to filter by
            max_keys: Maximum number of keys to return
            continuation_token: Token for pagination
            
        Returns:
            Dictionary with files list and next continuation token
        """
        try:
            list_kwargs = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                list_kwargs['Prefix'] = prefix
            
            if continuation_token:
                list_kwargs['ContinuationToken'] = continuation_token
            
            response = self.s3_client.list_objects_v2(**list_kwargs)
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"'),
                    'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                })
            
            result = {
                'files': files,
                'is_truncated': response.get('IsTruncated', False),
                'next_continuation_token': response.get('NextContinuationToken')
            }
            
            logger.info(f"Listed {len(files)} files from S3 with prefix '{prefix}'")
            return result
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 list error with prefix '{prefix}': {e}")
            raise BusinessLogicError(
                f"Failed to list files in S3: {error_code}",
                error_code="S3_LIST_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 list with prefix '{prefix}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file listing: {str(e)}",
                error_code="S3_LIST_ERROR"
            )
    
    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> str:
        """
        Generate a presigned URL for S3 object access.
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method for the presigned URL
            
        Returns:
            Presigned URL
        """
        try:
            if http_method == 'get_object':
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
            elif http_method == 'put_object':
                url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
            else:
                raise ValidationError(
                    f"Unsupported HTTP method for presigned URL: {http_method}",
                    error_code="INVALID_HTTP_METHOD"
                )
            
            logger.info(f"Generated presigned URL for S3 key: {key}")
            return url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 presigned URL error for key '{key}': {e}")
            raise BusinessLogicError(
                f"Failed to generate presigned URL: {error_code}",
                error_code="S3_PRESIGNED_URL_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 presigned URL generation for key '{key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during presigned URL generation: {str(e)}",
                error_code="S3_PRESIGNED_URL_ERROR"
            )
    
    def get_file_info(self, key: str) -> Dict:
        """
        Get metadata information for an S3 object.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary with file metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            
            info = {
                'key': key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'metadata': response.get('Metadata', {}),
                'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            }
            
            logger.info(f"Retrieved file info from S3: {key}")
            return info
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise ValidationError(
                    f"File not found in S3: {key}",
                    error_code="FILE_NOT_FOUND"
                )
            logger.error(f"S3 file info error for key '{key}': {e}")
            raise BusinessLogicError(
                f"Failed to get file info from S3: {error_code}",
                error_code="S3_FILE_INFO_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 file info retrieval for key '{key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file info retrieval: {str(e)}",
                error_code="S3_FILE_INFO_ERROR"
            )
    
    def copy_file(self, source_key: str, dest_key: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Copy a file within S3.
        
        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key
            metadata: Optional metadata for the copied object
            
        Returns:
            URL of the copied file
        """
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            
            copy_kwargs = {'CopySource': copy_source}
            if metadata:
                copy_kwargs['Metadata'] = metadata
                copy_kwargs['MetadataDirective'] = 'REPLACE'
            
            self.s3_client.copy_object(**copy_kwargs)
            
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{dest_key}"
            
            logger.info(f"Successfully copied file in S3: {source_key} -> {dest_key}")
            return url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 copy error from '{source_key}' to '{dest_key}': {e}")
            raise BusinessLogicError(
                f"Failed to copy file in S3: {error_code}",
                error_code="S3_COPY_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 copy from '{source_key}' to '{dest_key}': {e}")
            raise BusinessLogicError(
                f"Unexpected error during file copy: {str(e)}",
                error_code="S3_COPY_ERROR"
            )
    
    @staticmethod
    def extract_s3_key_from_url(url: str) -> Optional[str]:
        """
        Extract S3 key from a full S3 URL.
        
        Args:
            url: Full S3 URL
            
        Returns:
            S3 key or None if not a valid S3 URL
        """
        try:
            parsed = urlparse(url)
            if parsed.netloc.endswith('.amazonaws.com') and 's3' in parsed.netloc:
                return parsed.path.lstrip('/')
            return None
        except Exception:
            return None


# Global S3 service instance - lazy initialization
_s3_service_instance = None

def get_s3_service() -> 'S3Service':
    """Get S3 service instance with lazy initialization."""
    global _s3_service_instance
    if _s3_service_instance is None:
        _s3_service_instance = S3Service()
    return _s3_service_instance

# For backward compatibility
s3_service = get_s3_service
