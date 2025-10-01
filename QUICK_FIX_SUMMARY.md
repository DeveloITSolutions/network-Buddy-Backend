# Quick Fix Summary - Media Upload Issues

## Problems Fixed

### ✅ 1. Simplified Zone Response
**Before**: Media files included title, description, tags (duplicated for each file)
**After**: Media files only contain `file_url`, metadata is at zone level only

### ✅ 2. Clean Code Structure
- Removed redundant data from individual media files
- Metadata (title, description, tags) stored only at zone level
- Follows best practice: Don't repeat yourself (DRY)

---

## Server Issues to Fix

### ⚠️ 413 Request Entity Too Large (NGINX)

**Problem**: NGINX blocks large uploads before reaching FastAPI

**Fix on Server**:
```bash
# SSH to your server
ssh user@api-networking-app.socailabs.com

# Run the update script
cd /path/to/the_plugs_backend
sudo ./scripts/update-nginx-body-size.sh

# Or manually:
sudo nano /etc/nginx/nginx.conf
# Add: client_max_body_size 200M;
sudo nginx -t
sudo systemctl reload nginx
```

---

## Correct API Usage

### Upload Media (Create Zone)
```
POST /api/v1/events/{event_id}/media
Content-Type: multipart/form-data

Parameters:
- files: File[] (required) - One or more files
- title: string (optional) - Zone title for ALL files
- description: string (optional) - Zone description for ALL files  
- tags: string (optional) - Comma-separated tags for ALL files
```

### Get Zone Details
```
GET /api/v1/events/{event_id}/media/zones/{zone_id}

Response:
{
  "zone_id": "uuid",
  "title": "Zone Title",
  "description": "Zone Description", 
  "tags": ["tag1", "tag2"],
  "media_files": [
    { "file_url": "https://..." },
    { "file_url": "https://..." }
  ],
  "file_count": 2,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Current vs Fixed Response

### ❌ Before (Redundant Data)
```json
{
  "zone_id": "...",
  "title": "Dev",
  "description": "dev",
  "tags": [],
  "media_files": [
    {
      "title": "Dev",           // ❌ Duplicated
      "description": "dev",      // ❌ Duplicated
      "tags": [],                // ❌ Duplicated
      "file_url": "https://...",
      "file_type": "image/jpeg", // ❌ Not needed in response
      "file_size": 9366,         // ❌ Not needed in response
      ...
    }
  ]
}
```

### ✅ After (Clean Data)
```json
{
  "zone_id": "...",
  "title": "Dev",
  "description": "dev",
  "tags": [],
  "media_files": [
    {
      "file_url": "https://..."  // ✅ Only what's needed
    },
    {
      "file_url": "https://..."
    }
  ],
  "file_count": 2,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Files Modified

1. ✅ `app/schemas/event.py` - Added `MediaFileSimplified` schema
2. ✅ `app/services/event_media_service.py` - Updated to return simplified media
3. ✅ `scripts/update-nginx-body-size.sh` - Script to fix NGINX

---

## Testing

### 1. Test Upload (Small Files)
```bash
curl -X POST "https://api-networking-app.socailabs.com/api/v1/events/EVENT_ID/media" \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "title=Test Zone" \
  -F "description=Test Description"
```

### 2. Test Get Zone
```bash
curl -X GET "https://api-networking-app.socailabs.com/api/v1/events/EVENT_ID/media/zones/ZONE_ID" \
  -H "Authorization: Bearer TOKEN"
```

---

## Action Items

### For You (Developer)
- ✅ Code updated and deployed
- ✅ Clean response structure implemented
- ✅ Best practices followed

### For Server Admin
- ⚠️ Run: `sudo ./scripts/update-nginx-body-size.sh` on production server
- ⚠️ Or manually update NGINX config: `client_max_body_size 200M;`
- ⚠️ Reload NGINX: `sudo systemctl reload nginx`

---

## Summary

**What Changed**:
- Media files in zone response now only show `file_url`
- Title, description, tags are at zone level (not repeated for each file)
- Cleaner, more efficient API response

**What to Fix on Server**:
- Update NGINX to allow larger uploads (200MB)
- Use provided script: `./scripts/update-nginx-body-size.sh`

**Best Practices Applied**:
- ✅ DRY principle (Don't Repeat Yourself)
- ✅ Minimal response data
- ✅ Clean separation of concerns
- ✅ Proper error handling
- ✅ Clear documentation

