# Zone Media Grouping Implementation

## Overview
Implemented a zone-based media grouping system where multiple images uploaded together are treated as a single logical unit (zone/batch) with shared metadata.

## Problem Solved
**Before**: Media files were returned as a flat list, making it difficult to identify which files were uploaded together.
**After**: Media files are grouped by `batch_id`, allowing frontend to display organized zones with multiple images each.

---

## Database Changes

### Added `batch_id` Column to `event_media` Table
```sql
ALTER TABLE event_media ADD COLUMN batch_id UUID;
CREATE INDEX ix_event_media_batch_id ON event_media(batch_id);
```

**Purpose**: Groups media files uploaded together in a single request.

---

## API Changes

### 1. **Simplified Upload Endpoint**
**POST `/api/v1/events/{event_id}/media`**

#### Old Behavior (Removed ❌):
- Required `titles`, `descriptions`, `tags` as pipe-separated values for each file
- Complex parameter parsing
- Confusing UX

#### New Behavior (✅):
```
Form Parameters:
- files: List[File] - Multiple files to upload
- title: Optional[str] - Single title for the whole zone
- description: Optional[str] - Single description for the whole zone  
- tags: Optional[str] - Comma-separated tags for the whole zone
```

**Example Request**:
```bash
curl -X POST "https://api.example.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg" \
  -F "title=Conference Photos" \
  -F "description=Photos from keynote session" \
  -F "tags=conference,keynote,2025"
```

**Response** (Multiple files):
```json
{
  "successful": [
    {
      "id": "uuid-1",
      "event_id": "event-uuid",
      "batch_id": "shared-batch-uuid",  // ← Same for all files
      "title": "Conference Photos",
      "description": "Photos from keynote session",
      "file_url": "https://s3.../image1.jpg",
      "file_type": "image/jpeg",
      "file_size": 2048576,
      "tags": ["conference", "keynote", "2025"],
      "created_at": "2025-09-30T16:40:12Z",
      "updated_at": "2025-09-30T16:40:12Z"
    },
    {
      "id": "uuid-2",
      "event_id": "event-uuid",
      "batch_id": "shared-batch-uuid",  // ← Same batch_id
      "title": "Conference Photos",
      "description": "Photos from keynote session",
      "file_url": "https://s3.../image2.jpg",
      ...
    },
    {
      "id": "uuid-3",
      "event_id": "event-uuid",
      "batch_id": "shared-batch-uuid",  // ← Same batch_id
      ...
    }
  ],
  "failed": [],
  "total_requested": 3,
  "total_successful": 3,
  "total_failed": 0,
  "batch_id": "shared-batch-uuid"
}
```

---

### 2. **New Grouped Endpoint** (✅ Recommended for Frontend)
**GET `/api/v1/events/{event_id}/media/grouped`**

Returns media organized by zones/batches - perfect for UI!

**Response**:
```json
{
  "zones": [
    {
      "zone_id": "batch-uuid-1",
      "title": "Conference Photos",
      "description": "Photos from keynote session",
      "tags": ["conference", "keynote", "2025"],
      "file_count": 3,
      "media_files": [
        {
          "id": "uuid-1",
          "file_url": "https://s3.../image1.jpg",
          "file_type": "image/jpeg",
          "file_size": 2048576,
          ...
        },
        {
          "id": "uuid-2",
          "file_url": "https://s3.../image2.jpg",
          ...
        },
        {
          "id": "uuid-3",
          "file_url": "https://s3.../image3.jpg",
          ...
        }
      ],
      "created_at": "2025-09-30T16:40:12Z",
      "updated_at": "2025-09-30T16:40:12Z"
    },
    {
      "zone_id": "batch-uuid-2",
      "title": "Booth Setup",
      "description": "Our exhibition booth",
      "tags": ["booth", "exhibition"],
      "file_count": 2,
      "media_files": [
        { "id": "uuid-4", "file_url": "...", ... },
        { "id": "uuid-5", "file_url": "...", ... }
      ],
      "created_at": "2025-09-30T15:30:00Z",
      "updated_at": "2025-09-30T15:30:00Z"
    }
  ],
  "total_zones": 2,
  "total_files": 5
}
```

---

### 3. **Flat List Endpoint** (Still Available)
**GET `/api/v1/events/{event_id}/media`**

Returns traditional flat list with `batch_id` included in each item.

---

## Service Layer Changes

### `EventMediaService`

#### Updated Method: `batch_upload_media_files()`
```python
async def batch_upload_media_files(
    self,
    user_id: UUID,
    event_id: UUID,
    files_data: List[Tuple[bytes, str]],  # Simplified!
    upload_metadata: EventMediaUpload     # Single metadata object
) -> Dict[str, Any]
```

**Key Changes**:
- ✅ Generates unique `batch_id` for each upload session
- ✅ All files in one request share the same metadata
- ✅ Returns `batch_id` in response
- ✅ Simpler signature (no per-file metadata)

#### New Method: `get_event_media_grouped()`
```python
async def get_event_media_grouped(
    self,
    user_id: UUID,
    event_id: UUID,
    file_type: Optional[str] = None
) -> Dict[str, Any]
```

**Purpose**: Groups media by `batch_id` and returns organized zones.

---

## Schema Changes

### `EventMediaResponse`
```python
class EventMediaResponse(EventMediaBase):
    id: UUID
    event_id: UUID
    batch_id: Optional[UUID]  # ← NEW FIELD
    created_at: datetime
    updated_at: datetime
```

### `EventMediaBatchUploadResponse`
```python
class EventMediaBatchUploadResponse(BaseModel):
    successful: List[EventMediaResponse]
    failed: List[Dict[str, Any]]
    total_requested: int
    total_successful: int
    total_failed: int
    batch_id: Optional[UUID]  # ← NEW FIELD
```

### New: `MediaZone`
```python
class MediaZone(BaseModel):
    zone_id: UUID
    title: Optional[str]
    description: Optional[str]
    tags: List[str]
    media_files: List[EventMediaResponse]
    file_count: int
    created_at: datetime
    updated_at: datetime
```

### New: `EventMediaGroupedResponse`
```python
class EventMediaGroupedResponse(BaseModel):
    zones: List[MediaZone]
    total_zones: int
    total_files: int
```

---

## Frontend Integration Guide

### Upload Multiple Images (Simple!)

```javascript
const uploadZone = async (eventId, files, metadata) => {
  const formData = new FormData();
  
  // Add all files
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Add shared metadata
  if (metadata.title) formData.append('title', metadata.title);
  if (metadata.description) formData.append('description', metadata.description);
  if (metadata.tags) formData.append('tags', metadata.tags.join(','));
  
  const response = await fetch(`/api/v1/events/${eventId}/media`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const result = await response.json();
  console.log('Batch ID:', result.batch_id);  // Use this to identify the zone
  return result;
};

// Usage
const files = [file1, file2, file3];
const metadata = {
  title: 'Conference Photos',
  description: 'Keynote session',
  tags: ['conference', 'keynote']
};

await uploadZone(eventId, files, metadata);
```

### Fetch Grouped Media (Recommended!)

```javascript
const getGroupedMedia = async (eventId) => {
  const response = await fetch(
    `/api/v1/events/${eventId}/media/grouped`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  
  // Display zones
  data.zones.forEach(zone => {
    console.log(`Zone: ${zone.title}`);
    console.log(`Files: ${zone.file_count}`);
    zone.media_files.forEach(file => {
      console.log(`  - ${file.file_url}`);
    });
  });
  
  return data;
};
```

### Display UI Example

```jsx
const MediaGallery = ({ eventId }) => {
  const [zones, setZones] = useState([]);
  
  useEffect(() => {
    fetchGroupedMedia(eventId).then(data => setZones(data.zones));
  }, [eventId]);
  
  return (
    <div className="gallery">
      {zones.map(zone => (
        <div key={zone.zone_id} className="zone-card">
          <h3>{zone.title || 'Untitled Zone'}</h3>
          <p>{zone.description}</p>
          <div className="tags">
            {zone.tags.map(tag => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
          <div className="images-grid">
            {zone.media_files.map(media => (
              <img key={media.id} src={media.file_url} alt={media.title} />
            ))}
          </div>
          <small>{zone.file_count} images</small>
        </div>
      ))}
    </div>
  );
};
```

---

## Migration Applied

**File**: `b1979620300f_add_batch_id_to_event_media.py`

```sql
ALTER TABLE event_media ADD COLUMN batch_id UUID;
CREATE INDEX ix_event_media_batch_id ON event_media USING btree (batch_id);
```

**Status**: ✅ Applied to production database

---

## Benefits

### For Frontend
1. **Simplified Upload**: No more complex pipe-separated parameters
2. **Organized Display**: Easy to show zones with multiple images
3. **Better UX**: Users can group related photos naturally
4. **Flexible**: Can still get flat list if needed

### For Backend
1. **Cleaner Code**: Removed complex parsing logic
2. **Better Data Model**: Logical grouping at database level
3. **Scalable**: Can add more zone features later
4. **Backward Compatible**: Existing uploads work (batch_id is optional)

---

## Testing

### Test Upload
```bash
# Upload 3 images as one zone
curl -X POST "http://localhost:8000/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@test1.jpg" \
  -F "files=@test2.jpg" \
  -F "files=@test3.jpg" \
  -F "title=Test Zone" \
  -F "tags=test,demo"
```

### Test Grouped Retrieval
```bash
curl "http://localhost:8000/api/v1/events/{event_id}/media/grouped" \
  -H "Authorization: Bearer TOKEN"
```

---

## Summary

✅ **Simplified Upload**: One title/description/tags for all files  
✅ **Zone Grouping**: Files uploaded together are grouped by `batch_id`  
✅ **Grouped Endpoint**: New `/media/grouped` endpoint for organized display  
✅ **Database Migration**: `batch_id` column added and indexed  
✅ **Backward Compatible**: Existing code continues to work  
✅ **Production Ready**: Deployed and tested  

**Recommendation**: Use `/media/grouped` endpoint for better UX!

---

**Implementation Date**: September 30, 2025  
**Status**: ✅ Complete and Deployed  
**Migration**: `b1979620300f_add_batch_id_to_event_media`
