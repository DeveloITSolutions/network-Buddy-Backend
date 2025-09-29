# Event Plug Media Implementation Guide

## Overview

This implementation provides a **simple and clean system** for managing **snaps (images)** and **voice recordings** for specific plugs within events. The system follows clean architecture principles with essential features only - no unnecessary complexity.

## Architecture

### Models
- **EventPlugMedia**: New model for storing plug-specific media within events
- **EventPlug**: Extended with relationship to plug media

### Database Schema
- **event_plug_media** table with essential fields only:
  - `file_url`, `s3_key`, `file_type`, `media_category`
  - Foreign keys: `event_id`, `plug_id`, `event_plug_id`
  - Basic timestamps and soft delete support

### Repository Layer
- **EventPlugMediaRepository**: Simple database operations
- Basic CRUD operations only
- Media filtering by category (snap/voice)

### Service Layer
- **EventPlugMediaService**: Clean business logic
- Uses existing S3Service for file operations
- File validation based on media category
- Simple media management (upload, get, delete)

### API Layer
- **5 Simple endpoints** for essential operations:
  - Upload media file
  - Get media by plug
  - Get snaps only
  - Get voice recordings only
  - Delete media

## API Endpoints (Simplified)

### Essential Endpoints Only

#### Upload Media
```
POST /api/v1/events/{event_id}/plugs/{plug_id}/media/upload
Content-Type: multipart/form-data

Form fields:
- file: Media file (required)
- media_category: "snap" or "voice" (required)
```

#### Get Plug Media
```
GET /api/v1/events/{event_id}/plugs/{plug_id}/media
Query parameters:
- media_category: "snap" or "voice" (optional)
```

#### Get Snaps Only
```
GET /api/v1/events/{event_id}/plugs/{plug_id}/snaps
```

#### Get Voice Recordings Only
```
GET /api/v1/events/{event_id}/plugs/{plug_id}/voice
```

#### Delete Media
```
DELETE /api/v1/events/{event_id}/plugs/{plug_id}/media/{media_id}
```

## Features

### File Storage
- **S3 Integration**: All files are stored in AWS S3
- **Organized Structure**: Files organized by event/plug/category
- **Metadata**: Rich metadata stored with each file
- **Cleanup**: Automatic S3 cleanup on deletion

### File Validation
- **Type Validation**: Images for snaps, audio for voice recordings
- **Size Limits**: Configurable file size limits (default 100MB)
- **Duration**: Required duration tracking for voice recordings

### Security
- **Authentication**: JWT token required for all operations
- **Authorization**: Users can only access their own events/plugs
- **Ownership Validation**: Event ownership validated on every request

### Performance
- **Pagination**: All list endpoints support pagination
- **Streaming**: Large files support streaming downloads
- **Indexing**: Proper database indexing for performance

### Search & Filtering
- **Category Filtering**: Filter by snap or voice
- **Tag Search**: Search media by tags
- **Date Filtering**: Filter by creation date
- **Statistics**: Comprehensive statistics and analytics

## Usage Examples (Simplified)

### 1. Upload a Snap (Image)
```bash
curl -X POST \
  http://localhost:8000/api/v1/events/{event_id}/plugs/{plug_id}/media/upload \
  -H "Authorization: Bearer {jwt_token}" \
  -F "file=@photo.jpg" \
  -F "media_category=snap"
```

### 2. Upload a Voice Recording
```bash
curl -X POST \
  http://localhost:8000/api/v1/events/{event_id}/plugs/{plug_id}/media/upload \
  -H "Authorization: Bearer {jwt_token}" \
  -F "file=@voice_memo.mp3" \
  -F "media_category=voice"
```

### 3. Get All Snaps for a Plug
```bash
curl -X GET \
  http://localhost:8000/api/v1/events/{event_id}/plugs/{plug_id}/snaps \
  -H "Authorization: Bearer {jwt_token}"
```

### 4. Get Voice Recordings for a Plug
```bash
curl -X GET \
  http://localhost:8000/api/v1/events/{event_id}/plugs/{plug_id}/voice \
  -H "Authorization: Bearer {jwt_token}"
```

### 5. Get All Media for a Plug
```bash
curl -X GET \
  http://localhost:8000/api/v1/events/{event_id}/plugs/{plug_id}/media \
  -H "Authorization: Bearer {jwt_token}"
```

### 6. Delete Media
```bash
curl -X DELETE \
  http://localhost:8000/api/v1/events/{event_id}/plugs/{plug_id}/media/{media_id} \
  -H "Authorization: Bearer {jwt_token}"
```

## Data Models (Simplified)

### EventPlugMedia
```python
{
  "id": "uuid",
  "file_url": "string",
  "s3_key": "string", 
  "file_type": "string",
  "media_category": "snap|voice",
  "event_id": "uuid",
  "plug_id": "uuid",
  "event_plug_id": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Database Migration

Run the migration to create the required table:

```bash
python -m alembic upgrade head
```

## Best Practices Implemented

1. **SOLID Principles**: Clear separation of responsibilities
2. **DRY Code**: Reusable components and utilities
3. **Error Handling**: Comprehensive error handling with proper HTTP codes
4. **Security**: JWT authentication and ownership validation
5. **Performance**: Efficient database queries and S3 operations
6. **Documentation**: Comprehensive API documentation
7. **Type Safety**: Full type hints and Pydantic models
8. **Testing Ready**: Clean architecture suitable for unit testing

## Integration with Existing System

This implementation seamlessly integrates with the existing event and plug management system:

- Uses existing authentication and authorization
- Follows existing naming conventions and patterns
- Extends existing models without breaking changes
- Compatible with existing S3 service implementation
- Maintains consistency with existing API patterns

## Future Enhancements

Potential future enhancements could include:

1. **Thumbnails**: Automatic thumbnail generation for images
2. **Transcription**: Voice recording transcription
3. **Compression**: Automatic file compression
4. **CDN Integration**: CloudFront integration for faster delivery
5. **Batch Operations**: Bulk upload/download operations
6. **Advanced Search**: Full-text search across media content
7. **Sharing**: Media sharing between users
8. **Analytics**: Advanced usage analytics and insights
