# S3 Integration Guide for The Plugs Backend

This guide explains how to use the S3 integration for media file storage in The Plugs Backend.

## Overview

The backend now uses AWS S3 for storing media files instead of storing them directly in PostgreSQL. This provides:
- Better scalability
- Reduced database size
- Improved performance
- Better file management capabilities

## Configuration

### Environment Variables

Add these environment variables to your `.env` file:

```bash
# S3 Configuration
S3_BUCKET_NAME=plugs-bucket
S3_REGION=us-east-1
S3_USE_IAM_ROLE=true

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### AWS IAM Role Setup

The application uses EC2 IAM roles for S3 access (recommended approach):

1. **Create an IAM Policy** with the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::plugs-bucket",
                "arn:aws:s3:::plugs-bucket/*"
            ]
        }
    ]
}
```

2. **Attach the policy to your EC2 instance** through an IAM role.

## Database Schema Changes

The `event_media` table now includes an `s3_key` field:

```sql
ALTER TABLE event_media ADD COLUMN s3_key VARCHAR(512);
CREATE INDEX ix_event_media_s3_key ON event_media(s3_key);
```

## API Endpoints

### Upload Media File to S3

**POST** `/api/v1/events/{event_id}/media`

Upload a file to S3 and create a media record.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: The file to upload (required)
  - `title`: Media title (optional)
  - `description`: Media description (optional)
  - `tags`: Comma-separated tags (optional)

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/your/file.jpg" \
  -F "title=Event Photo" \
  -F "description=A great photo from the event" \
  -F "tags=photo,event,memories"
```

**Response:**
```json
{
  "id": "uuid-here",
  "event_id": "event-uuid-here",
  "title": "Event Photo",
  "description": "A great photo from the event",
  "file_url": "https://plugs-bucket.s3.us-east-1.amazonaws.com/events/event-id/media/2024/01/01/120000_123456.jpg",
  "s3_key": "events/event-id/media/2024/01/01/120000_123456.jpg",
  "file_type": "image/jpeg",
  "file_size": 2048576,
  "tags": ["photo", "event", "memories"],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Get Event Media List

**GET** `/api/v1/events/{event_id}/media`

Get a list of media files for an event.

**Query Parameters:**
- `file_type`: Filter by file type (optional)
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/{event_id}/media?file_type=image/jpeg&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Download Media File

**GET** `/api/v1/events/{event_id}/media/{media_id}/download`

Download a media file from S3.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/{event_id}/media/{media_id}/download" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o downloaded_file.jpg
```

### Stream Media File

**GET** `/api/v1/events/{event_id}/media/{media_id}/stream`

Stream a media file from S3 (useful for large files).

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/{event_id}/media/{media_id}/stream" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o streamed_file.mp4
```

### Delete Media File

**DELETE** `/api/v1/events/{event_id}/media/{media_id}`

Delete a media file from both S3 and the database.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/events/{event_id}/media/{media_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## S3 Service Usage

### Direct S3 Service Usage

You can also use the S3 service directly in your code:

```python
from app.services.s3_service import s3_service

# Upload a file
with open('local_file.jpg', 'rb') as file:
    s3_url = s3_service.upload_file(
        file_obj=file,
        key="custom/path/file.jpg",
        content_type="image/jpeg",
        metadata={"user_id": "123", "category": "profile"}
    )

# Download a file
file_content = s3_service.download_file("custom/path/file.jpg")

# Get file info
file_info = s3_service.get_file_info("custom/path/file.jpg")

# List files
files = s3_service.list_files(prefix="custom/path/")

# Delete a file
s3_service.delete_file("custom/path/file.jpg")
```

## File Organization in S3

Files are organized in S3 with the following structure:

```
plugs-bucket/
├── events/
│   └── {event_id}/
│       └── media/
│           └── {year}/
│               └── {month}/
│                   └── {day}/
│                       └── {time}_{microseconds}.{extension}
├── users/
│   └── {user_id}/
│       └── profile/
│           └── {year}/
│               └── {month}/
│                   └── {day}/
│                       └── {time}_{microseconds}.{extension}
└── temp/
    └── {year}/
        └── {month}/
            └── {day}/
                └── {time}_{microseconds}.{extension}
```

## Error Handling

The S3 service includes comprehensive error handling:

- **File too large**: Returns 413 error with size limit information
- **S3 connection issues**: Returns 500 error with connection details
- **File not found**: Returns 404 error
- **Permission denied**: Returns 403 error
- **Invalid credentials**: Returns 500 error with credential guidance

## Security Features

1. **Server-side encryption**: All files are encrypted in S3 using AES256
2. **IAM role authentication**: No hardcoded credentials
3. **Access control**: Users can only access their own event media
4. **File validation**: File size and type validation
5. **Metadata tracking**: Files include metadata about upload context

## Performance Considerations

1. **Streaming downloads**: Large files are streamed to avoid memory issues
2. **Presigned URLs**: Can be generated for direct client access (if needed)
3. **Efficient queries**: S3 keys are indexed in the database
4. **Cleanup on failure**: S3 files are cleaned up if database operations fail

## Migration from Local Storage

If you're migrating from local file storage:

1. **Run the database migration** to add the `s3_key` column
2. **Update existing records** to include S3 URLs and keys
3. **Migrate existing files** to S3 (you'll need a separate script for this)
4. **Update your application code** to use the new S3 endpoints

## Troubleshooting

### Common Issues

1. **"S3 credentials not configured"**
   - Ensure your EC2 instance has the correct IAM role attached
   - Verify the IAM role has S3 permissions
   - Test with `aws s3 ls` from your EC2 instance

2. **"S3 bucket not found"**
   - Verify the bucket name in your environment variables
   - Ensure the bucket exists in the correct region
   - Check bucket permissions

3. **"File too large"**
   - Check the `MAX_FILE_SIZE` setting
   - Consider increasing the limit if needed
   - Use streaming upload for very large files

4. **"Access denied"**
   - Verify IAM role permissions
   - Check bucket policy
   - Ensure the bucket allows your EC2 instance access

### Testing S3 Connection

You can test your S3 connection by running this Python script:

```python
from app.services.s3_service import s3_service

try:
    # Test connection
    files = s3_service.list_files(max_keys=1)
    print("S3 connection successful!")
    print(f"Bucket: {s3_service.bucket_name}")
    print(f"Region: {s3_service.region}")
except Exception as e:
    print(f"S3 connection failed: {e}")
```

## Best Practices

1. **Use appropriate file types**: Set correct MIME types for better browser handling
2. **Implement cleanup**: Regularly clean up temporary or unused files
3. **Monitor usage**: Track S3 usage and costs
4. **Backup strategy**: Consider cross-region replication for important files
5. **CDN integration**: Consider CloudFront for better performance
6. **Lifecycle policies**: Set up S3 lifecycle policies for cost optimization

## Support

For issues or questions about S3 integration:
1. Check the application logs for detailed error messages
2. Verify your AWS configuration
3. Test S3 connectivity from your EC2 instance
4. Review the S3 service code for specific error handling
