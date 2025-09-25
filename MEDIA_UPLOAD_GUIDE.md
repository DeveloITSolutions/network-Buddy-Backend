# Media Upload Implementation Guide

## Overview

The event media upload system has been updated to follow best practices for file uploads using **multipart/form-data** instead of JSON. This provides better security, performance, and user experience.

## Key Features

- ✅ **Multipart/form-data** file uploads
- ✅ **File validation** (type, size, extension)
- ✅ **Secure file storage** with organized directory structure
- ✅ **Backward compatibility** with JSON-based uploads
- ✅ **File serving** endpoint for uploaded files
- ✅ **File deletion** with storage cleanup
- ✅ **Comprehensive error handling**

## API Endpoints

### 1. Upload Media File (Multipart/Form-Data)

**Endpoint:** `POST /api/v1/events/{event_id}/media`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): The file to upload
- `title` (optional): Media title
- `description` (optional): Media description  
- `tags` (optional): Comma-separated tags

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/photo.jpg" \
  -F "title=Event Photo" \
  -F "description=Opening ceremony photo" \
  -F "tags=opening,ceremony,photo"
```

**Example JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'Event Photo');
formData.append('description', 'Opening ceremony');
formData.append('tags', 'opening,ceremony,photo');

const response = await fetch(`/api/v1/events/${eventId}/media`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

### 2. Upload Media with URL (JSON)

**Endpoint:** `POST /api/v1/events/{event_id}/media/json`

**Content-Type:** `application/json`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "External Photo",
    "description": "Photo from external storage",
    "file_url": "https://example.com/photo.jpg",
    "file_type": "image/jpeg",
    "file_size": 2048576,
    "tags": ["external", "photo"]
  }'
```

### 3. Get Event Media

**Endpoint:** `GET /api/v1/events/{event_id}/media`

**Query Parameters:**
- `file_type` (optional): Filter by file type
- `skip` (optional): Pagination offset
- `limit` (optional): Number of records

### 4. Delete Media

**Endpoint:** `DELETE /api/v1/events/{event_id}/media/{media_id}`

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/events/{event_id}/media/{media_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. Serve Media Files

**Endpoint:** `GET /api/v1/events/media/{file_path}`

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/media/events/{event_id}/images/photo.jpg" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## File Type Support

### Images
- **Types:** JPEG, PNG, GIF, WebP, SVG
- **Max Size:** 10MB
- **MIME Types:** `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/svg+xml`

### Videos
- **Types:** MP4, AVI, MOV, WMV, FLV, WebM, MKV
- **Max Size:** 100MB
- **MIME Types:** `video/mp4`, `video/avi`, `video/mov`, etc.

### Documents
- **Types:** PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV
- **Max Size:** 50MB
- **MIME Types:** `application/pdf`, `application/msword`, etc.

### Audio
- **Types:** MP3, WAV, OGG, AAC
- **Max Size:** 20MB
- **MIME Types:** `audio/mpeg`, `audio/wav`, `audio/ogg`, etc.

## File Storage Structure

```
uploads/
├── events/
│   └── {event_id}/
│       ├── images/
│       ├── videos/
│       ├── documents/
│       └── audio/
├── general/
│   ├── images/
│   ├── videos/
│   ├── documents/
│   └── audio/
└── profiles/
    └── images/
```

## Security Features

1. **File Type Validation:** Only allowed MIME types are accepted
2. **File Size Limits:** Different limits for different file categories
3. **Extension Validation:** File extension must match MIME type
4. **Filename Sanitization:** Dangerous characters are removed/replaced
5. **Unique Filenames:** UUID-based naming prevents conflicts
6. **Access Control:** Users can only access their own files

## Error Handling

### Common Error Responses

**File Too Large:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File size (15.2 MB) exceeds maximum allowed size (10.0 MB) for image files"
  }
}
```

**Invalid File Type:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR", 
    "message": "File type 'application/zip' is not allowed"
  }
}
```

**File Not Found:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "File not found"
  }
}
```

## Response Format

### Successful Upload Response

```json
{
  "id": "uuid-here",
  "event_id": "event-uuid-here",
  "title": "Event Photo",
  "description": "Opening ceremony photo",
  "file_url": "/uploads/events/{event_id}/images/photo-uuid.jpg",
  "file_type": "image/jpeg",
  "file_size": 2048576,
  "tags": ["opening", "ceremony", "photo"],
  "created_at": "2025-01-25T10:30:00Z",
  "updated_at": "2025-01-25T10:30:00Z"
}
```

## Best Practices

1. **Use Multipart/Form-Data** for file uploads (not JSON)
2. **Validate files on the client** before uploading
3. **Show upload progress** for large files
4. **Handle errors gracefully** with user-friendly messages
5. **Use appropriate file types** for different content
6. **Implement file compression** for images when possible
7. **Clean up unused files** periodically

## Migration from JSON to Form-Data

### Before (JSON):
```javascript
const response = await fetch('/api/v1/events/123/media', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: 'Photo',
    file_url: 'https://example.com/photo.jpg',
    file_type: 'image/jpeg',
    file_size: 1024000
  })
});
```

### After (Form-Data):
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'Photo');

const response = await fetch('/api/v1/events/123/media', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

## Testing

### Test with cURL

```bash
# Upload an image
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test-image.jpg" \
  -F "title=Test Image" \
  -F "description=Test upload" \
  -F "tags=test,image"

# Upload a video
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test-video.mp4" \
  -F "title=Test Video" \
  -F "tags=test,video"

# Upload a document
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test-document.pdf" \
  -F "title=Test Document" \
  -F "tags=test,document"
```

This implementation follows FastAPI best practices and provides a robust, secure file upload system for the event media module.
