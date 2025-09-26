# Plug Search & Filtering API Guide

## Overview

This guide provides comprehensive documentation for the enhanced plug search and filtering API endpoints. The API now supports unified search and filtering capabilities for both targets and contacts through a single endpoint.

## Base URL
```
http://localhost:8000/api/v1/plugs/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Main Endpoint

### GET /api/v1/plugs/

**Description**: Unified endpoint for listing, searching, and filtering plugs (targets and contacts).

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `q` | string | No | Search query (searches name, company, email, network_type, business_type, connect_reason) | `"john"`, `"new client"` |
| `plug_type` | string | No | Filter by plug type | `"target"`, `"contact"` |
| `network_type` | string | No | Filter by network type | `"new_client"`, `"existing_client"`, `"new_partnership"` |
| `status` | string | No | Filter by status (legacy parameter) | `"new_client"`, `"existing_client"` |
| `skip` | integer | No | Number of records to skip (pagination) | `0`, `20`, `40` |
| `limit` | integer | No | Number of records to return (max 1000) | `10`, `50`, `100` |

## Network Types

The API supports the following predefined network types:

| Network Type | Value | Description |
|--------------|-------|-------------|
| New Client | `new_client` | New potential clients |
| Existing Client | `existing_client` | Current clients |
| New Partnership | `new_partnership` | New partnership opportunities |
| Existing Partnership | `existing_partnership` | Current partnerships |
| Vendor | `vendor` | Service providers/vendors |
| Investor | `investor` | Potential or current investors |
| Mentor | `mentor` | Mentors and advisors |
| Other | `other` | Other network types |

**Note**: Custom network types are also supported as long as they are at least 2 characters long.

## API Usage Examples

### 1. Basic Listing

```bash
# Get all plugs
GET /api/v1/plugs/

# Get all contacts
GET /api/v1/plugs/?plug_type=contact

# Get all targets
GET /api/v1/plugs/?plug_type=target
```

### 2. Network Type Filtering

```bash
# Filter by network type
GET /api/v1/plugs/?network_type=new_client
GET /api/v1/plugs/?network_type=existing_client
GET /api/v1/plugs/?network_type=new_partnership

# Filter contacts by network type
GET /api/v1/plugs/?plug_type=contact&network_type=new_client

# Filter targets by network type
GET /api/v1/plugs/?plug_type=target&network_type=new_partnership
```

### 3. Text Search

```bash
# Search by name
GET /api/v1/plugs/?q=john

# Search by company
GET /api/v1/plugs/?q=acme

# Search by email
GET /api/v1/plugs/?q=john@example.com

# Search by network type
GET /api/v1/plugs/?q=new_client

# Search by business type
GET /api/v1/plugs/?q=derm_clinic
```

### 4. Combined Filtering

```bash
# Search contacts by name
GET /api/v1/plugs/?q=john&plug_type=contact

# Search new clients by company
GET /api/v1/plugs/?q=acme&network_type=new_client

# Filter contacts by network type and search
GET /api/v1/plugs/?q=health&plug_type=contact&network_type=new_client
```

### 5. Pagination

```bash
# First page (default)
GET /api/v1/plugs/?skip=0&limit=20

# Second page
GET /api/v1/plugs/?skip=20&limit=20

# Third page
GET /api/v1/plugs/?skip=40&limit=20
```

## Response Format

### Success Response (200 OK)

```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "123e4567-e89b-12d3-a456-426614174001",
      "plug_type": "contact",
      "first_name": "John",
      "last_name": "Doe",
      "job_title": "CEO",
      "company": "Acme Corp",
      "email": "john@acme.com",
      "primary_number": "+1234567890",
      "network_type": "new_client",
      "business_type": "derm_clinic",
      "priority": "high",
      "is_contact": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3,
  "has_next": true,
  "has_prev": false,
  "counts": {
    "targets": 10,
    "contacts": 40
  }
}
```

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "Search term must be at least 2 characters"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": "Invalid plug type: invalid_type"
}
```

## Frontend Implementation Examples

### JavaScript/TypeScript

```typescript
interface PlugFilters {
  q?: string;
  plug_type?: 'target' | 'contact';
  network_type?: string;
  skip?: number;
  limit?: number;
}

class PlugAPI {
  private baseURL = 'http://localhost:8000/api/v1/plugs';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  async getPlugs(filters: PlugFilters = {}) {
    const params = new URLSearchParams();
    
    if (filters.q) params.append('q', filters.q);
    if (filters.plug_type) params.append('plug_type', filters.plug_type);
    if (filters.network_type) params.append('network_type', filters.network_type);
    if (filters.skip) params.append('skip', filters.skip.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());

    const response = await fetch(`${this.baseURL}/?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  // Search by text
  async searchPlugs(query: string, plugType?: string) {
    return this.getPlugs({ q: query, plug_type: plugType });
  }

  // Filter by network type
  async filterByNetworkType(networkType: string, plugType?: string) {
    return this.getPlugs({ network_type: networkType, plug_type: plugType });
  }

  // Get paginated results
  async getPlugsPage(page: number, limit: number = 20) {
    return this.getPlugs({ skip: (page - 1) * limit, limit });
  }
}
```

### React Hook Example

```typescript
import { useState, useEffect } from 'react';

interface UsePlugsOptions {
  searchQuery?: string;
  plugType?: 'target' | 'contact';
  networkType?: string;
  page?: number;
  limit?: number;
}

export function usePlugs(options: UsePlugsOptions = {}) {
  const [plugs, setPlugs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    pages: 0,
    hasNext: false,
    hasPrev: false
  });

  useEffect(() => {
    const fetchPlugs = async () => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (options.searchQuery) params.append('q', options.searchQuery);
        if (options.plugType) params.append('plug_type', options.plugType);
        if (options.networkType) params.append('network_type', options.networkType);
        if (options.page) params.append('skip', ((options.page - 1) * (options.limit || 20)).toString());
        if (options.limit) params.append('limit', options.limit.toString());

        const response = await fetch(`/api/v1/plugs/?${params}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setPlugs(data.items);
        setPagination({
          total: data.total,
          page: data.page,
          pages: data.pages,
          hasNext: data.has_next,
          hasPrev: data.has_prev
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPlugs();
  }, [options.searchQuery, options.plugType, options.networkType, options.page, options.limit]);

  return { plugs, loading, error, pagination };
}
```

## Mobile App Integration

### Filter Tabs Implementation

```typescript
// Network type filter tabs (as shown in your mobile app)
const networkTypeFilters = [
  { label: 'All', value: null },
  { label: 'New Client', value: 'new_client' },
  { label: 'Existing Client', value: 'existing_client' },
  { label: 'New Partnership', value: 'new_partnership' }
];

// Handle filter tab selection
const handleNetworkTypeFilter = (networkType: string | null) => {
  setFilters(prev => ({ ...prev, networkType, page: 1 }));
};
```

### Search Bar Implementation

```typescript
// Search input handler
const handleSearch = (query: string) => {
  setFilters(prev => ({ 
    ...prev, 
    searchQuery: query.trim() || undefined, 
    page: 1 
  }));
};

// Debounced search
const debouncedSearch = useMemo(
  () => debounce(handleSearch, 300),
  []
);
```

## Best Practices

### 1. Error Handling
- Always handle network errors and API errors
- Show appropriate error messages to users
- Implement retry logic for failed requests

### 2. Loading States
- Show loading indicators during API calls
- Implement skeleton screens for better UX
- Use optimistic updates where appropriate

### 3. Caching
- Cache API responses to reduce server load
- Implement cache invalidation strategies
- Use React Query or SWR for data fetching

### 4. Pagination
- Implement infinite scroll or page-based pagination
- Show total count and current page information
- Handle edge cases (empty results, last page, etc.)

### 5. Search Optimization
- Implement debounced search to avoid excessive API calls
- Show search suggestions or autocomplete
- Clear search results when filters change

## Testing

### Unit Tests
```typescript
describe('PlugAPI', () => {
  it('should fetch plugs with filters', async () => {
    const api = new PlugAPI('test-token');
    const mockResponse = { items: [], total: 0 };
    
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    });

    const result = await api.getPlugs({ plug_type: 'contact' });
    
    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('plug_type=contact'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token'
        })
      })
    );
  });
});
```

## Migration Notes

### From Separate Search Endpoint
If you were previously using the separate `/search` endpoint:

**Before:**
```typescript
// Old way
const searchResponse = await fetch('/api/v1/plugs/search?q=john');
const listResponse = await fetch('/api/v1/plugs/?plug_type=contact');
```

**After:**
```typescript
// New unified way
const searchResponse = await fetch('/api/v1/plugs/?q=john');
const listResponse = await fetch('/api/v1/plugs/?plug_type=contact');
```

The API is fully backward compatible, so existing implementations will continue to work without changes.

## Support

For questions or issues with the API, please refer to:
- API documentation: `/docs` (Swagger UI)
- Backend repository: [Repository URL]
- Issue tracker: [Issues URL]

---

**Last Updated**: January 2024  
**API Version**: v1  
**Maintainer**: Backend Team
