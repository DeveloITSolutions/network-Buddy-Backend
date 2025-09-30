# Media Batch Upload Guide

## Overview

The `/api/v1/events/{event_id}/media` endpoint has been enhanced to support **both single and multiple file uploads** in a single request. This guide explains how to use the updated endpoint.

## Endpoint Details

**URL**: `POST /api/v1/events/{event_id}/media`  
**Authentication**: Required (JWT Bearer token)  
**Content-Type**: `multipart/form-data`

## Key Features

✅ Upload single or multiple files in one request  
✅ Backward compatible with existing single-file uploads  
✅ Individual titles and descriptions for each file  
✅ Common tags applied to all files  
✅ Automatic batch processing with detailed results  
✅ Graceful error handling (partial success supported)  
✅ Files stored in S3, metadata in database  

## Request Parameters

### Form Data Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | ✅ Yes | One or more media files to upload |
| `titles` | String | ❌ No | Pipe-separated titles (e.g., "Title1\|Title2\|Title3") |
| `descriptions` | String | ❌ No | Pipe-separated descriptions |
| `tags` | String | ❌ No | Comma-separated tags (applied to all files) |

### File Constraints

- **Max file size**: 100MB per file
- **Supported types**: Images, videos, documents, audio files
- **File type detection**: Automatic via MIME type

## Response Formats

### Single File Upload (1 file)

Returns `EventMediaResponse`:

```json
{
  "id": "uuid",
  "event_id": "uuid",
  "title": "My Photo",
  "description": "A beautiful sunset",
  "file_url": "https://s3.amazonaws.com/...",
  "file_type": "image/jpeg",
  "file_size": 2048576,
  "tags": ["sunset", "photography"],
  "s3_key": "events/event-id/media/...",
  "created_at": "2025-09-30T12:00:00Z",
  "updated_at": "2025-09-30T12:00:00Z"
}
```

### Multiple Files Upload (2+ files)

Returns `EventMediaBatchUploadResponse`:

```json
{
  "successful": [
    {
      "id": "uuid-1",
      "event_id": "uuid",
      "title": "Photo 1",
      "file_url": "https://s3.amazonaws.com/...",
      "file_type": "image/jpeg",
      "file_size": 2048576,
      "tags": ["event", "photos"],
      "created_at": "2025-09-30T12:00:00Z",
      "updated_at": "2025-09-30T12:00:00Z"
    },
    {
      "id": "uuid-2",
      "event_id": "uuid",
      "title": "Photo 2",
      "file_url": "https://s3.amazonaws.com/...",
      "file_type": "image/png",
      "file_size": 1024000,
      "tags": ["event", "photos"],
      "created_at": "2025-09-30T12:00:00Z",
      "updated_at": "2025-09-30T12:00:00Z"
    }
  ],
  "failed": [
    {
      "filename": "corrupted.jpg",
      "index": 2,
      "error": "Invalid file format",
      "error_type": "ValidationError"
    }
  ],
  "total_requested": 3,
  "total_successful": 2,
  "total_failed": 1
}
```

## Usage Examples

### Example 1: Single File Upload

**cURL**:
```bash
curl -X POST "https://api.example.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@photo.jpg" \
  -F "titles=Summer Vacation Photo" \
  -F "descriptions=Taken at the beach" \
  -F "tags=vacation,beach,summer"
```

**Python (requests)**:
```python
import requests

url = f"https://api.example.com/api/v1/events/{event_id}/media"
headers = {"Authorization": f"Bearer {jwt_token}"}

files = {
    'files': open('photo.jpg', 'rb')
}
data = {
    'titles': 'Summer Vacation Photo',
    'descriptions': 'Taken at the beach',
    'tags': 'vacation,beach,summer'
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

**JavaScript (FormData)**:
```javascript
const formData = new FormData();
formData.append('files', fileInput.files[0]);
formData.append('titles', 'Summer Vacation Photo');
formData.append('descriptions', 'Taken at the beach');
formData.append('tags', 'vacation,beach,summer');

fetch(`/api/v1/events/${eventId}/media`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Example 2: Multiple Files Upload

**cURL**:
```bash
curl -X POST "https://api.example.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "files=@photo3.png" \
  -F "titles=First Photo|Second Photo|Third Photo" \
  -F "descriptions=Description 1|Description 2|Description 3" \
  -F "tags=event,conference,2025"
```

**Python (requests)**:
```python
import requests

url = f"https://api.example.com/api/v1/events/{event_id}/media"
headers = {"Authorization": f"Bearer {jwt_token}"}

files = [
    ('files', open('photo1.jpg', 'rb')),
    ('files', open('photo2.jpg', 'rb')),
    ('files', open('photo3.png', 'rb'))
]
data = {
    'titles': 'First Photo|Second Photo|Third Photo',
    'descriptions': 'Description 1|Description 2|Description 3',
    'tags': 'event,conference,2025'
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"Uploaded: {result['total_successful']}/{result['total_requested']}")
print(f"Failed: {result['total_failed']}")
```

**JavaScript (Multiple Files)**:
```javascript
const formData = new FormData();

// Add multiple files
for (let i = 0; i < fileInput.files.length; i++) {
  formData.append('files', fileInput.files[i]);
}

// Add metadata (pipe-separated for multiple files)
formData.append('titles', 'Photo 1|Photo 2|Photo 3');
formData.append('descriptions', 'Desc 1|Desc 2|Desc 3');
formData.append('tags', 'event,photos');

fetch(`/api/v1/events/${eventId}/media`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  },
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log(`Successfully uploaded: ${data.total_successful} files`);
  console.log(`Failed: ${data.total_failed} files`);
  if (data.failed.length > 0) {
    console.log('Failed uploads:', data.failed);
  }
});
```

### Example 3: Multiple Files with Shared Metadata

If you want all files to have no individual titles but share common tags:

```bash
curl -X POST "https://api.example.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg" \
  -F "tags=gallery,event,2025"
```

### Example 4: Postman Configuration

1. **Method**: POST
2. **URL**: `{{base_url}}/api/v1/events/{{event_id}}/media`
3. **Headers**:
   - `Authorization`: `Bearer {{jwt_token}}`
4. **Body** (form-data):
   - `files`: (File) - Select multiple files
   - `titles`: (Text) - `Photo 1|Photo 2|Photo 3`
   - `descriptions`: (Text) - `Description 1|Description 2|Description 3`
   - `tags`: (Text) - `event,photos,2025`

## Important Notes

### Titles and Descriptions Matching

- If you provide **fewer titles/descriptions than files**, remaining files will have `null` values
- If you provide **more titles/descriptions than files**, extra values are ignored
- Use the pipe character (`|`) to separate values, not commas

**Example**:
```
3 files uploaded
titles = "First|Second"
→ File 1: title = "First"
→ File 2: title = "Second"
→ File 3: title = null
```

### Tags Behavior

- Tags are **comma-separated** (not pipe-separated)
- Tags apply to **all files** in the upload
- Individual file tags are not supported in batch uploads

### Error Handling

- **Partial success is allowed**: If 5 files are uploaded and 2 fail, the 3 successful uploads are saved
- Failed uploads include detailed error information (filename, index, error message, error type)
- Files exceeding size limits are logged but don't cause the entire batch to fail

### Backward Compatibility

- **Single file uploads maintain the same response structure** as before
- Existing API clients uploading one file at a time will continue to work without changes
- Response type changes based on number of files uploaded (automatic)

## Best Practices

1. **Validate files client-side** before uploading to reduce failed uploads
2. **Use descriptive titles** to help organize media
3. **Apply consistent tags** for easier searching and filtering
4. **Check the response** for failed uploads and handle them appropriately
5. **Limit batch size** to reasonable numbers (recommended: 10-20 files per request)
6. **Monitor file sizes** to avoid exceeding the 100MB per file limit

## Response Status Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | Success (single or batch) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid JWT) |
| 404 | Not Found (event doesn't exist) |
| 413 | Payload Too Large (file exceeds 100MB) |
| 422 | Unprocessable Entity (business logic error) |

## Architecture Changes

### New Components

1. **Schema**: `EventMediaBatchUploadResponse` in `app/schemas/event.py`
2. **Service Method**: `batch_upload_media_files()` in `app/services/event_media_service.py`
3. **Endpoint Enhancement**: Updated `/api/v1/events/{event_id}/media` in `app/api/v1/events.py`

### Service Layer

The new `batch_upload_media_files()` method:
- Accepts a list of tuples: `(file_content, filename, upload_data)`
- Calls the existing `upload_media_file()` for each file
- Collects successful uploads and failures
- Returns detailed results with counts

### Key Benefits

- **Reuses existing logic**: No code duplication
- **Transactional per file**: Each file upload is independent
- **Robust error handling**: One file failure doesn't affect others
- **Detailed logging**: Track upload progress and issues
- **Clean separation**: Service layer handles business logic, endpoint handles HTTP

## Migration Notes

If you're updating from the previous single-file endpoint:

### No Changes Required If:
- You're only uploading one file at a time
- You're using the `file` field (now renamed to `files`)

### Changes Required If:
- You want to upload multiple files → Use the new `files` array parameter
- You want different titles per file → Use pipe-separated `titles` parameter
- You need to handle batch responses → Check response type based on file count

## Support

For issues or questions about media uploads, check:
- Application logs for detailed error messages
- S3 bucket for uploaded files
- Database `event_media` table for metadata

---

**Last Updated**: September 30, 2025  
**Version**: 2.0  
**Endpoint**: `/api/v1/events/{event_id}/media`
