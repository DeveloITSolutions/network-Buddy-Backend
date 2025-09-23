# 🔐 Authentication & Plug Management Guide

Complete guide for using The Plugs API authentication system and plug management features with enhanced security.

## 📋 Table of Contents
- [Authentication Flow](#authentication-flow)
- [Security Features](#security-features)
- [API Endpoints](#api-endpoints)
- [Plug Management](#plug-management)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Examples](#examples)

## 🔐 Authentication Flow

### 1. **User Login**
Get access and refresh tokens for API access.

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "timezone": "UTC",
    "is_active": true,
    "created_at": "2025-09-23T07:00:00Z",
    "updated_at": "2025-09-23T07:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 2. **Token Refresh**
Get a new access token when the current one expires.

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. **Password Reset Flow**

#### Step 1: Send OTP
```http
POST /api/v1/auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Step 2: Verify OTP
```http
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

#### Step 3: Change Password
```http
POST /api/v1/auth/change-password
Content-Type: application/json

{
  "email": "user@example.com",
  "new_password": "NewSecurePassword123!",
  "token": "verification_token_from_step2"
}
```

### 4. **Logout**
Invalidate tokens and end session.

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 5. **Update Timezone**
Update user's timezone (requires authentication).

```http
PUT /api/v1/auth/timezone
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "timezone": "America/New_York"
}
```

## 🛡️ Security Features

### **Rate Limiting**
All endpoints are protected with rate limiting:

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 attempts | 15 minutes |
| Send OTP | 3 attempts | 5 minutes |
| Verify OTP | 5 attempts | 15 minutes |
| Change Password | 3 attempts | 30 minutes |
| Refresh Token | 10 attempts | 5 minutes |

### **Account Security**
- **Account Lockout**: Automatic 1-hour lockout after 10 failed login attempts
- **Security Logging**: All authentication events are logged
- **IP Tracking**: Client IP addresses are monitored
- **User Agent Logging**: Browser/app information is recorded

### **Token Security**
- **Access Token**: 30-minute expiration
- **Refresh Token**: 7-day expiration  
- **JWT Validation**: Secure token verification
- **Token Invalidation**: Logout invalidates tokens

## 📡 API Endpoints

### Authentication Endpoints
```
POST   /api/v1/auth/login           # User login
POST   /api/v1/auth/refresh         # Refresh access token
POST   /api/v1/auth/logout          # User logout
POST   /api/v1/auth/send-otp        # Send OTP for password reset
POST   /api/v1/auth/verify-otp      # Verify OTP code
POST   /api/v1/auth/change-password # Change password with token
PUT    /api/v1/auth/timezone        # Update user timezone (auth required)
```

### Plug Management Endpoints
```
POST   /api/v1/plugs/              # Create target or contact
GET    /api/v1/plugs/              # List user's plugs
GET    /api/v1/plugs/{id}          # Get specific plug
PUT    /api/v1/plugs/{id}          # Update plug
DELETE /api/v1/plugs/{id}          # Delete plug
GET    /api/v1/plugs/search        # Search plugs
GET    /api/v1/plugs/stats         # Get plug statistics
POST   /api/v1/plugs/{id}/convert  # Convert target to contact
```

## 🔗 Plug Management

### **Authentication Required**
All plug endpoints require JWT authentication:
```http
Authorization: Bearer <access_token>
```

### **1. Create Plug (Target or Contact)**
The system automatically determines whether to create a target or contact based on data completeness.

**Creates TARGET** (minimal data):
```http
POST /api/v1/plugs/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "company": "Tech Corp"
}
```

**Creates CONTACT** (complete data):
```http
POST /api/v1/plugs/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "company": "Health Tech",
  "email": "jane@healthtech.com",
  "job_title": "Product Manager",
  "network_type": "new_client",
  "business_type": "health_tech",
  "connect_reason": "Interested in our AI platform",
  "tags": ["decision_maker", "high_priority"],
  "priority": "high",
  "hubspot_pipeline_stage": "Qualified Lead",
  "custom_data": {
    "source": "conference",
    "interests": ["AI", "healthcare"],
    "follow_up_date": "2025-10-01"
  }
}
```

**Custom Network/Business Types:**
```json
{
  "network_type": "Strategic Partner",
  "business_type": "AI Consulting",
  "custom_data": {
    "custom_fields": {
      "industry_focus": "Healthcare AI",
      "company_size": "50-100 employees"
    }
  }
}
```

### **2. List Plugs**
Get paginated list of user's plugs.

```http
GET /api/v1/plugs/?skip=0&limit=50&plug_type=contact
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "plug_type": "contact",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@healthtech.com",
      "company": "Health Tech",
      "job_title": "Product Manager",
      "network_type": "new_client",
      "business_type": "health_tech",
      "custom_data": { "source": "conference" },
      "created_at": "2025-09-23T07:00:00Z",
      "full_name": "Jane Smith",
      "is_contact": true,
      "is_target": false
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### **3. Update Plug**
Update target or contact information.

```http
PUT /api/v1/plugs/{plug_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_title": "Senior Product Manager",
  "priority": "high",
  "custom_data": {
    "last_contact": "2025-09-23",
    "notes": "Very interested in partnership"
  }
}
```

### **4. Delete Plug**
Soft delete a plug (can be restored).

```http
DELETE /api/v1/plugs/{plug_id}
Authorization: Bearer <access_token>
```

### **5. Search Plugs**
Search through user's plugs.

```http
GET /api/v1/plugs/search?q=jane&plug_type=contact&skip=0&limit=20
Authorization: Bearer <access_token>
```

### **6. Convert Target to Contact**
Convert a target to a full contact.

```http
POST /api/v1/plugs/{target_id}/convert
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "notes": "Met at tech conference",
  "network_type": "new_partnership",
  "business_type": "health_tech",
  "connect_reason": "Potential collaboration",
  "tags": ["decision_maker"],
  "priority": "medium",
  "hubspot_pipeline_stage": "Initial Contact"
}
```

### **7. Get Plug Statistics**
Get statistics about user's plugs.

```http
GET /api/v1/plugs/stats
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "total_plugs": 25,
  "total_targets": 10,
  "total_contacts": 15,
  "by_priority": {
    "high": 5,
    "medium": 12,
    "low": 8
  },
  "by_business_type": {
    "health_tech": 8,
    "derm_clinic": 5,
    "pharma_biotech": 3
  }
}
```

## ⚠️ Error Handling

### **HTTP Status Codes**
- `200` - Success
- `201` - Created successfully
- `204` - Deleted successfully (no content)
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (business logic error)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

### **Rate Limit Response**
```json
{
  "detail": "Rate limit exceeded. Try again in 300 seconds."
}
```
Headers: `Retry-After: 300`

### **Authentication Error**
```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Authentication required",
    "timestamp": 1758612754.123
  }
}
```

### **Validation Error**
```json
{
  "detail": "Password must contain at least one uppercase letter"
}
```

## 🚀 Best Practices

### **Token Management**
1. **Store tokens securely** (encrypted storage, not localStorage)
2. **Implement automatic refresh** before token expiration
3. **Handle 401 errors** by redirecting to login
4. **Logout on app close** to invalidate tokens

### **API Usage**
1. **Always include Authorization header** for protected endpoints
2. **Handle rate limits** gracefully with exponential backoff
3. **Validate data** on client side before sending requests
4. **Use pagination** for large datasets

### **Security**
1. **Use HTTPS only** in production
2. **Validate SSL certificates**
3. **Don't log sensitive data** (passwords, tokens)
4. **Implement proper error handling**

## 📝 Examples

### **Complete Authentication Flow (JavaScript)**

```javascript
class AuthService {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  async login(email, password) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.tokens.access_token;
      this.refreshToken = data.tokens.refresh_token;
      
      localStorage.setItem('access_token', this.accessToken);
      localStorage.setItem('refresh_token', this.refreshToken);
      
      return data.user;
    } else {
      throw new Error('Login failed');
    }
  }

  async refreshAccessToken() {
    const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      localStorage.setItem('access_token', this.accessToken);
      return true;
    }
    return false;
  }

  async apiCall(endpoint, options = {}) {
    let response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    // Handle token expiration
    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry the request with new token
        response = await fetch(`${this.baseURL}${endpoint}`, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        });
      } else {
        // Redirect to login
        window.location.href = '/login';
        return;
      }
    }

    return response;
  }

  async logout() {
    await fetch(`${this.baseURL}/api/v1/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.accessToken = null;
    this.refreshToken = null;
  }
}
```

### **Plug Management (JavaScript)**

```javascript
class PlugService extends AuthService {
  async createPlug(plugData) {
    const response = await this.apiCall('/api/v1/plugs/', {
      method: 'POST',
      body: JSON.stringify(plugData)
    });
    return response.json();
  }

  async getPlugs(page = 1, limit = 50, plugType = null) {
    const params = new URLSearchParams({
      skip: (page - 1) * limit,
      limit: limit.toString()
    });
    
    if (plugType) params.append('plug_type', plugType);
    
    const response = await this.apiCall(`/api/v1/plugs/?${params}`);
    return response.json();
  }

  async updatePlug(plugId, updateData) {
    const response = await this.apiCall(`/api/v1/plugs/${plugId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    });
    return response.json();
  }

  async deletePlug(plugId) {
    await this.apiCall(`/api/v1/plugs/${plugId}`, {
      method: 'DELETE'
    });
  }

  async convertTargetToContact(targetId, conversionData) {
    const response = await this.apiCall(`/api/v1/plugs/${targetId}/convert`, {
      method: 'POST',
      body: JSON.stringify(conversionData)
    });
    return response.json();
  }

  async searchPlugs(query, plugType = null, page = 1, limit = 20) {
    const params = new URLSearchParams({
      q: query,
      skip: (page - 1) * limit,
      limit: limit.toString()
    });
    
    if (plugType) params.append('plug_type', plugType);
    
    const response = await this.apiCall(`/api/v1/plugs/search?${params}`);
    return response.json();
  }
}
```

### **Error Handling with Retry Logic**

```javascript
class RobustAPIClient extends PlugService {
  async apiCallWithRetry(endpoint, options = {}, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await this.apiCall(endpoint, options);
        
        if (response.status === 429) {
          // Rate limited - wait and retry
          const retryAfter = response.headers.get('Retry-After');
          const delay = retryAfter ? parseInt(retryAfter) * 1000 : Math.pow(2, attempt) * 1000;
          
          console.log(`Rate limited. Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        return response;
      } catch (error) {
        if (attempt === maxRetries) throw error;
        
        // Exponential backoff for network errors
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
}
```

## 🔧 Environment Setup

### **Development**
```bash
# Start the API server
docker-compose up -d

# API will be available at:
# http://localhost:8000

# API Documentation:
# http://localhost:8000/docs
```

### **Production Considerations**
1. **Use HTTPS only**
2. **Set secure JWT secrets**
3. **Configure proper CORS**
4. **Enable security logging**
5. **Set up monitoring**
6. **Implement backup strategies**

---

## 📞 Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review error responses for detailed information
3. Ensure proper authentication headers
4. Verify rate limits are not exceeded

**Happy coding! 🚀**
