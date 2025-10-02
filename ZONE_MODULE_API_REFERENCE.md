# Zone Module - Complete API Reference

## Overview
The Zone module manages media content for events, organizing files into logical groups (zones) with shared metadata. This reference covers all media management endpoints.

---

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/events/{event_id}/media` | Upload single or multiple media files |
| `GET` | `/events/{event_id}/media` | List all media files (ungrouped) |
| `GET` | `/events/{event_id}/media/grouped` | List media grouped by zones |
| `GET` | `/events/{event_id}/media/zones/{zone_id}` | Get specific zone details |
| `PATCH` | `/events/{event_id}/media/zones/{zone_id}` | Update zone metadata |
| `POST` | `/events/{event_id}/media/zones/{zone_id}/files` | Add files to existing zone |
| `DELETE` | `/events/{event_id}/media/{media_id}` | Delete single media file |
| `DELETE` | `/events/{event_id}/media/zones/{zone_id}` | Delete entire zone |

---

## 1. Upload Media

### Endpoint
```
POST /api/v1/events/{event_id}/media
```

### Description
Upload one or more media files to S3 and create media records. Files uploaded together are automatically grouped into a zone.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Parameters**:
- `files` (required): One or more files to upload
- `title` (optional): Zone title (applied to all files)
- `description` (optional): Zone description (applied to all files)
- `tags` (optional): Comma-separated tags (applied to all files)

**Examples**:

Single File:
```bash
curl -X POST "/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@photo.jpg" \
  -F "title=My Photo" \
  -F "tags=event,2025"
```

Multiple Files (Creates Zone):
```bash
curl -X POST "/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "files=@photo3.jpg" \
  -F "title=Birthday Party Photos" \
  -F "description=Main event photos" \
  -F "tags=birthday,celebration,2025"
```

### Response

**Single File** (`200 OK`):
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440001",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "batch_id": null,
  "title": "My Photo",
  "description": null,
  "file_url": "https://s3.amazonaws.com/...",
  "s3_key": "events/.../photo.jpg",
  "file_type": "image/jpeg",
  "file_size": 245678,
  "tags": ["event", "2025"],
  "created_at": "2025-10-02T10:30:00Z",
  "updated_at": "2025-10-02T10:30:00Z"
}
```

**Multiple Files** (`200 OK`):
```json
{
  "successful": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440001",
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "650e8400-e29b-41d4-a716-446655440000",
      "file_url": "https://s3.amazonaws.com/.../photo1.jpg",
      "file_type": "image/jpeg",
      "file_size": 245678,
      "created_at": "2025-10-02T10:30:00Z"
    },
    {
      "id": "750e8400-e29b-41d4-a716-446655440002",
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "650e8400-e29b-41d4-a716-446655440000",
      "file_url": "https://s3.amazonaws.com/.../photo2.jpg",
      "file_type": "image/jpeg",
      "file_size": 198234,
      "created_at": "2025-10-02T10:30:05Z"
    }
  ],
  "failed": [],
  "total_requested": 3,
  "total_successful": 2,
  "total_failed": 0,
  "batch_id": "650e8400-e29b-41d4-a716-446655440000"
}
```

---

## 2. List All Media (Ungrouped)

### Endpoint
```
GET /api/v1/events/{event_id}/media
```

### Description
Get all media files for an event in a flat list (not grouped by zones).

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Query Parameters**:
- `file_type` (optional): Filter by MIME type (e.g., "image/jpeg")
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100, max: 1000)

**Example**:
```bash
curl -X GET "/api/v1/events/{event_id}/media?file_type=image/jpeg&limit=50" \
  -H "Authorization: Bearer TOKEN"
```

### Response (`200 OK`)
```json
[
  {
    "id": "750e8400-e29b-41d4-a716-446655440001",
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "batch_id": "650e8400-e29b-41d4-a716-446655440000",
    "file_url": "https://s3.amazonaws.com/.../photo1.jpg",
    "file_type": "image/jpeg",
    "file_size": 245678,
    "created_at": "2025-10-02T10:30:00Z"
  }
]
```

---

## 3. List Media Grouped by Zones

### Endpoint
```
GET /api/v1/events/{event_id}/media/grouped
```

### Description
Get media organized by zones. Shows zone metadata (title, description, tags) with file URLs.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Query Parameters**:
- `file_type` (optional): Filter by MIME type

**Example**:
```bash
curl -X GET "/api/v1/events/{event_id}/media/grouped" \
  -H "Authorization: Bearer TOKEN"
```

### Response (`200 OK`)
```json
{
  "zones": [
    {
      "zone_id": "650e8400-e29b-41d4-a716-446655440000",
      "title": "Birthday Party Photos",
      "description": "Photos from the main event",
      "tags": ["birthday", "celebration", "2025"],
      "media_files": [
        {"file_url": "https://s3.amazonaws.com/.../photo1.jpg"},
        {"file_url": "https://s3.amazonaws.com/.../photo2.jpg"},
        {"file_url": "https://s3.amazonaws.com/.../photo3.jpg"}
      ],
      "file_count": 3,
      "created_at": "2025-10-02T10:30:00Z",
      "updated_at": "2025-10-02T10:30:05Z"
    }
  ],
  "total_zones": 1,
  "total_files": 3
}
```

---

## 4. Get Zone Details

### Endpoint
```
GET /api/v1/events/{event_id}/media/zones/{zone_id}
```

### Description
Get detailed information about a specific zone with all its media files.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Example**:
```bash
curl -X GET "/api/v1/events/{event_id}/media/zones/{zone_id}" \
  -H "Authorization: Bearer TOKEN"
```

### Response (`200 OK`)
```json
{
  "zone_id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Birthday Party Photos",
  "description": "Photos from the main event",
  "tags": ["birthday", "celebration", "2025"],
  "media_files": [
    {"file_url": "https://s3.amazonaws.com/.../photo1.jpg"},
    {"file_url": "https://s3.amazonaws.com/.../photo2.jpg"}
  ],
  "file_count": 2,
  "created_at": "2025-10-02T10:30:00Z",
  "updated_at": "2025-10-02T10:30:05Z"
}
```

### Error Responses
- `404 Not Found`: Zone doesn't exist or user doesn't own the event

---

## 5. Delete Single Media File

### Endpoint
```
DELETE /api/v1/events/{event_id}/media/{media_id}
```

### Description
Delete a single media file. If this is the last file in a zone, the zone is automatically deleted.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Example**:
```bash
curl -X DELETE "/api/v1/events/{event_id}/media/{media_id}" \
  -H "Authorization: Bearer TOKEN"
```

### Response
- `204 No Content`: File successfully deleted
- `404 Not Found`: Media not found or user doesn't own the event

### Behavior
- Deletes file from S3
- Soft-deletes database record
- **Auto Zone Cleanup**: If last file in zone, zone is also deleted

---

## 5. Update Zone Metadata

### Endpoint
```
PATCH /api/v1/events/{event_id}/media/zones/{zone_id}
```

### Description
Update zone metadata (title, description, tags) without affecting the media files.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Body Parameters**:
- `title` (optional): New zone title (max 256 chars)
- `description` (optional): New zone description
- `tags` (optional): New array of tags

**Note**: All fields are optional. Only provided fields will be updated (partial update).

**Example**:
```bash
curl -X PATCH "/api/v1/events/{event_id}/media/zones/{zone_id}" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Birthday Photos",
    "description": "Added more context to the description",
    "tags": ["birthday", "celebration", "2025", "family"]
  }'
```

### Response (`200 OK`)
```json
{
  "zone_id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Birthday Photos",
  "description": "Added more context to the description",
  "tags": ["birthday", "celebration", "2025", "family"],
  "file_count": 5,
  "updated_at": "2025-10-02T15:30:00Z"
}
```

### Error Responses
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Zone doesn't exist or user doesn't own the event
- `422 Unprocessable Entity`: Business logic error

---

## 6. Add Files to Existing Zone

### Endpoint
```
POST /api/v1/events/{event_id}/media/zones/{zone_id}/files
```

### Description
Add new media files to an existing zone. Files inherit the zone's existing metadata.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Parameters**:
- `files` (required): One or more files to add to the zone

**Example**:
```bash
curl -X POST "/api/v1/events/{event_id}/media/zones/{zone_id}/files" \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@photo4.jpg" \
  -F "files=@photo5.jpg" \
  -F "files=@photo6.jpg"
```

### Response (`200 OK`)
```json
{
  "successful": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440004",
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "650e8400-e29b-41d4-a716-446655440000",
      "file_url": "https://s3.amazonaws.com/.../photo4.jpg",
      "file_type": "image/jpeg",
      "file_size": 245678,
      "created_at": "2025-10-02T15:30:00Z"
    },
    {
      "id": "750e8400-e29b-41d4-a716-446655440005",
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "650e8400-e29b-41d4-a716-446655440000",
      "file_url": "https://s3.amazonaws.com/.../photo5.jpg",
      "file_type": "image/jpeg",
      "file_size": 198234,
      "created_at": "2025-10-02T15:30:05Z"
    }
  ],
  "failed": [],
  "total_requested": 3,
  "total_successful": 2,
  "total_failed": 0,
  "batch_id": "650e8400-e29b-41d4-a716-446655440000"
}
```

### Error Responses
- `400 Bad Request`: No valid files provided
- `404 Not Found`: Zone doesn't exist or user doesn't own the event
- `413 Payload Too Large`: File exceeds 100MB limit

### Behavior
- Files are added to the zone with the zone's existing metadata
- Zone's `updated_at` timestamp is updated
- Oversized files (>100MB) are skipped with a warning
- Partial success is supported (some files can succeed while others fail)

---

## 7. Delete Single Media File

### Endpoint
```
DELETE /api/v1/events/{event_id}/media/{media_id}
```

### Description
Delete a single media file. If this is the last file in a zone, the zone is automatically deleted.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Example**:
```bash
curl -X DELETE "/api/v1/events/{event_id}/media/{media_id}" \
  -H "Authorization: Bearer TOKEN"
```

### Response
- `204 No Content`: File successfully deleted
- `404 Not Found`: Media not found or user doesn't own the event

### Behavior
- Deletes file from S3
- Soft-deletes database record
- **Auto Zone Cleanup**: If last file in zone, zone is also deleted

---

## 8. Delete Entire Zone

### Endpoint
```
DELETE /api/v1/events/{event_id}/media/zones/{zone_id}
```

### Description
Delete an entire zone with all its media files.

### Request
**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Example**:
```bash
curl -X DELETE "/api/v1/events/{event_id}/media/zones/{zone_id}" \
  -H "Authorization: Bearer TOKEN"
```

### Response
- `204 No Content`: Zone and all files successfully deleted
- `404 Not Found`: Zone not found or user doesn't own the event

### Behavior
- Deletes all files from S3
- Soft-deletes all media records
- Soft-deletes zone metadata

---

## Common Response Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| `200 OK` | Success | Successful GET request |
| `201 Created` | Created | Successful POST request |
| `204 No Content` | Deleted | Successful DELETE request |
| `400 Bad Request` | Invalid input | Malformed request or validation error |
| `401 Unauthorized` | Not authenticated | Missing or invalid JWT token |
| `404 Not Found` | Resource not found | Media/zone doesn't exist or wrong owner |
| `413 Payload Too Large` | File too large | File exceeds 100MB limit |
| `422 Unprocessable Entity` | Business logic error | Operation violates business rules |

---

## Authentication

All endpoints require JWT authentication:

```bash
Authorization: Bearer <your_jwt_token>
```

### Getting a Token
1. Register/login via authentication endpoints
2. Use the returned JWT token in all requests
3. Token identifies the user and validates ownership

---

## File Upload Limits

| Limit Type | Value |
|------------|-------|
| Max file size | 100MB per file |
| Max files per upload | No hard limit (recommended: 10-20) |
| Supported file types | All (images, videos, documents, etc.) |

---

## Zone Concepts

### What is a Zone?
A **zone** is a logical grouping of media files that share:
- Same title
- Same description  
- Same tags
- Same upload time (batch)

### When are Zones Created?
- **Automatic**: When uploading 2+ files together
- Files uploaded individually don't create zones (unless specified)

### Zone Lifecycle
```
1. Upload multiple files → Zone created
2. View zone details → See all files
3. Update zone metadata → Title, description, tags changed
4. Add more files → Zone grows
5. Delete one file → Zone remains (if others exist)
6. Update again → Metadata refined
7. Delete last file → Zone auto-deleted
   OR
   Delete zone → All files deleted
```

---

## Best Practices

### Uploading Media
✅ **DO**:
- Upload related files together to create zones
- Use descriptive titles and tags
- Keep files under 100MB
- Use appropriate MIME types

❌ **DON'T**:
- Upload extremely large files
- Mix unrelated content in one zone
- Exceed reasonable batch sizes (>50 files)

### Updating Zones
✅ **DO**:
- Use PATCH for partial updates (only changed fields)
- Update metadata separately from files
- Use descriptive titles and tags
- Add files incrementally as needed

❌ **DON'T**:
- Send unchanged fields in PATCH requests
- Mix metadata updates with file uploads
- Create duplicate zones for related content

### Deleting Media
✅ **DO**:
- Delete entire zones when removing all related content
- Use single file deletion for selective cleanup
- Verify zone_id before bulk deletion

❌ **DON'T**:
- Delete files without verifying ownership
- Rely on hard deletes (use soft delete pattern)

---

## Error Handling Examples

### Invalid Event ID
```bash
DELETE /api/v1/events/invalid-uuid/media/zones/{zone_id}
```
Response: `400 Bad Request`
```json
{
  "detail": "Invalid event_id format"
}
```

### Zone Not Found
```bash
DELETE /api/v1/events/{event_id}/media/zones/nonexistent-uuid
```
Response: `404 Not Found`
```json
{
  "detail": "Zone nonexistent-uuid not found for event {event_id}"
}
```

### Unauthorized Access
```bash
DELETE /api/v1/events/{another_users_event}/media/zones/{zone_id}
```
Response: `404 Not Found` (for security, doesn't reveal event exists)

---

## Integration Examples

### Complete Workflow: Upload, View, Update, Delete

```bash
# 1. Upload multiple files (creates zone)
POST /api/v1/events/{event_id}/media
Files: photo1.jpg, photo2.jpg, photo3.jpg
Title: "Day 1 Photos"
Response: batch_id = "650e8400-..."

# 2. View all zones
GET /api/v1/events/{event_id}/media/grouped
Response: Shows 1 zone with 3 files

# 3. View specific zone
GET /api/v1/events/{event_id}/media/zones/650e8400-...
Response: Zone details with 3 files

# 4. Update zone metadata
PATCH /api/v1/events/{event_id}/media/zones/650e8400-...
Body: { "title": "Day 1 - Morning Session", "description": "Added description" }
Response: 200 OK with updated zone

# 5. Add more files to zone
POST /api/v1/events/{event_id}/media/zones/650e8400-.../files
Files: photo4.jpg, photo5.jpg
Response: 2 files added successfully
# Zone now has 5 files total

# 6. Delete one file
DELETE /api/v1/events/{event_id}/media/{media_id}
Response: 204 No Content
# Zone still exists with 4 files

# 7. Update tags only
PATCH /api/v1/events/{event_id}/media/zones/650e8400-...
Body: { "tags": ["morning", "day1", "breakfast"] }
Response: 200 OK with updated tags

# 8. Delete entire zone
DELETE /api/v1/events/{event_id}/media/zones/650e8400-...
Response: 204 No Content
# All remaining files and zone deleted
```

---

## Performance Considerations

### Pagination
- Use `skip` and `limit` for large media collections
- Default limit: 100 items
- Max limit: 1000 items

### File Sizes
- Larger files take longer to upload
- S3 upload time varies by connection speed
- Consider progress indicators for >10MB files

### Batch Operations
- Uploading many files sequentially (not parallel)
- Each file validated and uploaded individually
- Recommended batch size: 10-20 files

---

## Related Documentation

- [MEDIA_BATCH_UPLOAD_IMPLEMENTATION_SUMMARY.md](./MEDIA_BATCH_UPLOAD_IMPLEMENTATION_SUMMARY.md) - Batch upload details
- [ZONE_DETAIL_ENDPOINT_IMPLEMENTATION.md](./ZONE_DETAIL_ENDPOINT_IMPLEMENTATION.md) - Zone details endpoint
- [ZONE_DELETION_IMPLEMENTATION.md](./ZONE_DELETION_IMPLEMENTATION.md) - Deletion implementation
- [S3_INTEGRATION_GUIDE.md](./S3_INTEGRATION_GUIDE.md) - S3 setup and configuration

---

## Support

For issues or questions:
1. Check error responses for details
2. Review logs for specific error codes
3. Verify JWT token validity
4. Confirm event ownership

---

**Last Updated**: October 2, 2025  
**API Version**: 3.0 (Added Update Operations)  
**Status**: Production Ready ✅

## Changelog

### Version 3.0 (October 2, 2025)
- ✨ Added `PATCH /zones/{zone_id}` - Update zone metadata
- ✨ Added `POST /zones/{zone_id}/files` - Add files to existing zone
- 📝 Updated documentation with new endpoints
- 🔧 Enhanced zone management capabilities

### Version 2.0 (October 2, 2025)
- ✨ Added `DELETE /zones/{zone_id}` - Delete entire zone
- ✨ Enhanced `DELETE /media/{media_id}` - Auto zone cleanup
- 📝 Comprehensive API documentation

### Version 1.0 (September 30, 2025)
- 🎉 Initial release with upload, view, and basic operations

