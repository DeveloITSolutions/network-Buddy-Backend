# Media Upload Fix - Zone Implementation

## Issues Identified

### 1. 413 Request Entity Too Large (NGINX)
**Problem**: NGINX is blocking large file uploads before they reach the FastAPI application.

**Solution**: Update NGINX `client_max_body_size` configuration.

### 2. Correct Endpoint Usage
**Problem**: Using wrong endpoint path or wrong parameters.

**Solution**: Use the correct endpoint: `POST /api/v1/events/{event_id}/media`

---

## NGINX Configuration Fix

### Update NGINX Config on Server

SSH into your server and update the NGINX configuration:

```bash
sudo nano /etc/nginx/sites-available/default
# or
sudo nano /etc/nginx/nginx.conf
```

Add or update in the `http` block or `server` block:

```nginx
http {
    # ... other config ...
    
    # Increase client body size to 200MB
    client_max_body_size 200M;
    
    # Increase buffer sizes
    client_body_buffer_size 128k;
    client_body_timeout 120s;
    
    server {
        listen 80;
        server_name api-networking-app.socailabs.com;
        
        # Override for this specific server block
        client_max_body_size 200M;
        
        location / {
            proxy_pass http://localhost:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Important for large uploads
            proxy_request_buffering off;
            proxy_buffering off;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }
}
```

Then reload NGINX:
```bash
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## Correct API Usage

### Event Media Upload Endpoint

**Endpoint**: `POST /api/v1/events/{event_id}/media`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `files` (required): Array of files to upload
- `title` (optional): Zone title (applies to all files in the batch)
- `description` (optional): Zone description (applies to all files)
- `tags` (optional): Comma-separated tags (applies to all files)

### Example cURL Request

```bash
curl -X POST "https://api-networking-app.socailabs.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@/path/to/image1.jpg" \
  -F "files=@/path/to/image2.jpg" \
  -F "files=@/path/to/image3.jpg" \
  -F "title=Birthday Party Photos" \
  -F "description=Main event photos" \
  -F "tags=party,celebration,2025"
```

### Example JavaScript/Fetch Request

```javascript
const formData = new FormData();

// Add multiple files
files.forEach(file => {
    formData.append('files', file);
});

// Add zone metadata (applied to all files)
formData.append('title', 'Birthday Party Photos');
formData.append('description', 'Main event photos');
formData.append('tags', 'party,celebration,2025');

const response = await fetch(
    `https://api-networking-app.socailabs.com/api/v1/events/${eventId}/media`,
    {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
            // Don't set Content-Type - browser will set it with boundary
        },
        body: formData
    }
);

const result = await response.json();
```

### Example Response (Multiple Files)

```json
{
  "successful": [
    {
      "title": "Birthday Party Photos",
      "description": "Main event photos",
      "file_url": "https://plugs-bucket.s3.eu-north-1.amazonaws.com/events/.../photo1.jpg",
      "file_type": "image/jpeg",
      "file_size": 245678,
      "tags": ["party", "celebration", "2025"],
      "s3_key": "events/.../photo1.jpg",
      "id": "uuid-1",
      "event_id": "event-uuid",
      "batch_id": "batch-uuid",
      "created_at": "2025-10-01T...",
      "updated_at": "2025-10-01T..."
    },
    {
      "title": "Birthday Party Photos",
      "description": "Main event photos",
      "file_url": "https://plugs-bucket.s3.eu-north-1.amazonaws.com/events/.../photo2.jpg",
      "file_type": "image/jpeg",
      "file_size": 198234,
      "tags": ["party", "celebration", "2025"],
      "s3_key": "events/.../photo2.jpg",
      "id": "uuid-2",
      "event_id": "event-uuid",
      "batch_id": "batch-uuid",
      "created_at": "2025-10-01T...",
      "updated_at": "2025-10-01T..."
    }
  ],
  "failed": [],
  "total_requested": 2,
  "total_successful": 2,
  "total_failed": 0,
  "batch_id": "batch-uuid"
}
```

---

## Get Zone Details

**Endpoint**: `GET /api/v1/events/{event_id}/media/zones/{zone_id}`

### Example Request

```bash
curl -X GET "https://api-networking-app.socailabs.com/api/v1/events/{event_id}/media/zones/{batch_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Example Response (Simplified Media Files)

```json
{
  "zone_id": "batch-uuid",
  "title": "Birthday Party Photos",
  "description": "Main event photos",
  "tags": ["party", "celebration", "2025"],
  "media_files": [
    {
      "file_url": "https://plugs-bucket.s3.eu-north-1.amazonaws.com/events/.../photo1.jpg"
    },
    {
      "file_url": "https://plugs-bucket.s3.eu-north-1.amazonaws.com/events/.../photo2.jpg"
    },
    {
      "file_url": "https://plugs-bucket.s3.eu-north-1.amazonaws.com/events/.../photo3.jpg"
    }
  ],
  "file_count": 3,
  "created_at": "2025-10-01T07:36:20.756807Z",
  "updated_at": "2025-10-01T07:36:20.756807Z"
}
```

**Note**: Only `file_url` is returned for each media file. Title, description, and tags are at the zone level only.

---

## Common Errors and Solutions

### Error 413: Request Entity Too Large

**Cause**: NGINX body size limit

**Solutions**:
1. Update NGINX `client_max_body_size` (see above)
2. Reduce file sizes before upload
3. Upload files in smaller batches

### Error 422: Unprocessable Entity

**Cause**: Missing required fields or validation error

**Solutions**:
1. Ensure you're using the correct endpoint
2. Check that `files` parameter contains at least one file
3. Verify Content-Type is `multipart/form-data`
4. Check JWT token is valid and not expired

### Error 401: Unauthorized

**Cause**: Missing or invalid JWT token

**Solution**: Include valid JWT token in Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## File Size Limits

### Application Level (FastAPI)
- **Per File**: 100MB
- **Total Request**: Limited by NGINX configuration

### NGINX Level (After Fix)
- **Per Request**: 200MB

### S3 Level
- **Per File**: No practical limit for our use case

---

## Best Practices

### 1. Zone Organization
- Upload related files together (same title, description, tags)
- Files uploaded together get the same `batch_id`
- Retrieve by zone to get organized groups

### 2. Metadata Strategy
- **Zone Level**: title, description, tags (shared across all files)
- **File Level**: Only file_url, file_type, file_size (individual properties)

### 3. Upload Strategy
- For large batches (>20 files), consider splitting into multiple uploads
- Compress images before upload when possible
- Use appropriate image formats (JPEG for photos, PNG for graphics)

### 4. Error Handling
- Always check response for `failed` array
- Retry failed uploads individually
- Log `batch_id` for successful uploads

---

## Quick Deploy Script for NGINX Update

Save this as `update-nginx-body-size.sh`:

```bash
#!/bin/bash

echo "Updating NGINX client_max_body_size..."

# Backup existing config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Check if client_max_body_size already exists
if grep -q "client_max_body_size" /etc/nginx/nginx.conf; then
    echo "client_max_body_size already configured. Updating..."
    sudo sed -i 's/client_max_body_size .*/client_max_body_size 200M;/' /etc/nginx/nginx.conf
else
    echo "Adding client_max_body_size configuration..."
    sudo sed -i '/http {/a \    client_max_body_size 200M;' /etc/nginx/nginx.conf
fi

# Test configuration
echo "Testing NGINX configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration valid. Reloading NGINX..."
    sudo systemctl reload nginx
    echo "✅ NGINX updated successfully!"
else
    echo "❌ Configuration error. Restoring backup..."
    sudo mv /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
    exit 1
fi
```

Run it:
```bash
chmod +x update-nginx-body-size.sh
./update-nginx-body-size.sh
```

---

## Testing the Fix

### 1. Test Small Upload (Should work immediately)
```bash
curl -X POST "https://api-networking-app.socailabs.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@small-image.jpg" \
  -F "title=Test Upload" \
  -F "description=Testing the endpoint"
```

### 2. Test Large Upload (After NGINX fix)
```bash
curl -X POST "https://api-networking-app.socailabs.com/api/v1/events/{event_id}/media" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@large-image1.jpg" \
  -F "files=@large-image2.jpg" \
  -F "files=@large-image3.jpg" \
  -F "title=Large Batch" \
  -F "description=Testing multiple large files"
```

### 3. Retrieve Zone
```bash
# Get the batch_id from upload response, then:
curl -X GET "https://api-networking-app.socailabs.com/api/v1/events/{event_id}/media/zones/{batch_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Summary

✅ **Fixes Implemented**:
1. Simplified media file response (only file_url in media_files array)
2. Zone metadata stored at zone level only
3. Clean separation between zone metadata and individual files

🔧 **Server Configuration Needed**:
1. Update NGINX `client_max_body_size` to 200M
2. Restart/reload NGINX service

📝 **Usage**:
- Use `POST /api/v1/events/{event_id}/media` for uploads
- Use `GET /api/v1/events/{event_id}/media/zones/{zone_id}` for zone details
- Files uploaded together share metadata and get same batch_id

