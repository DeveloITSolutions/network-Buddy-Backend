# 🔐 Authentication Flow - The Plugs

This document describes the complete authentication flow implementation based on the mobile app screens.

## 📱 Authentication Screens Flow

### 1. Email Verification (First Screen)
**Endpoint**: `POST /api/v1/auth/send-verification`

```json
{
  "email": "user@example.com"
}
```

**Response**:
```json
{
  "message": "Verification code sent successfully",
  "email": "user@example.com",
  "expires_in": 300
}
```

### 2. OTP Verification (Second Screen)
**Endpoint**: `POST /api/v1/auth/verify-email`

```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

**Response**:
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com",
  "is_verified": true
}
```

### 3. User Registration (After Email Verification)
**Endpoint**: `POST /api/v1/auth/register`

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response**:
```json
{
  "message": "User registered successfully",
  "success": true
}
```

### 4. User Login (Third Screen)
**Endpoint**: `POST /api/v1/auth/login`

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**:
```json
{
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "tokens": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 5. Password Reset Flow
**Step 1**: `POST /api/v1/auth/forgot-password`
```json
{
  "email": "user@example.com"
}
```

**Step 2**: `POST /api/v1/auth/reset-password`
```json
{
  "email": "user@example.com",
  "reset_token": "secure-reset-token",
  "new_password": "NewSecurePassword123!"
}
```

## 🔧 Technical Implementation

### OTP Generation & Storage
- **OTP Format**: 6-digit numeric code
- **Storage**: Redis cache with 5-minute expiration
- **Security**: Cryptographically secure random generation

### Email Delivery
- **Primary**: SendGrid API (professional email delivery)
- **Fallback**: SMTP (configurable)
- **Templates**: HTML + Plain text with professional styling

### Password Security
- **Hashing**: bcrypt with salt
- **Requirements**: 
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character

### JWT Tokens
- **Access Token**: 30 minutes (configurable)
- **Refresh Token**: 7 days (configurable)
- **Algorithm**: HS256
- **Payload**: user_id, email, is_active, is_verified

## 🚀 Setup Instructions

### 1. Environment Configuration

Add these variables to your `.env` file:

```bash
# SendGrid Configuration (Recommended)
SENDGRID_API_KEY=your-sendgrid-api-key-here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# SMTP Fallback (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Frontend URL (for password reset links)
FRONTEND_URL=http://localhost:3000

# Security
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. SendGrid Setup

1. **Create SendGrid Account**: Sign up at [sendgrid.com](https://sendgrid.com)
2. **Generate API Key**: 
   - Go to Settings > API Keys
   - Create a new API key with "Full Access" or "Mail Send" permissions
   - Copy the API key to `SENDGRID_API_KEY`
3. **Verify Sender**: Add and verify your sender email address
4. **Update Configuration**: Set `SENDGRID_FROM_EMAIL` to your verified sender

### 3. Database Migration

Create the users table:

```bash
# Run database migrations
./scripts/docker-manage.sh db-migrate

# Or manually with Alembic
docker-compose exec api alembic upgrade head
```

### 4. Start Services

```bash
# Start all services with Docker
./scripts/docker-start.sh

# Or manually
docker-compose up -d
```

## 📋 API Endpoints Summary

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/send-verification` | POST | Send OTP to email | No |
| `/auth/verify-email` | POST | Verify OTP code | No |
| `/auth/register` | POST | Register new user | No* |
| `/auth/login` | POST | User login | No |
| `/auth/login-oauth` | POST | OAuth2 compatible login | No |
| `/auth/refresh` | POST | Refresh access token | No |
| `/auth/forgot-password` | POST | Request password reset | No |
| `/auth/reset-password` | POST | Confirm password reset | No |
| `/auth/logout` | POST | User logout | Yes |
| `/auth/me` | GET | Get current user | Yes |

*Requires email verification first

## 🧪 Testing the Flow

### 1. Test Email Verification

```bash
curl -X POST http://localhost:8000/api/v1/auth/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### 2. Test OTP Verification

```bash
# Check your email for the OTP code, then:
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp_code": "123456"}'
```

### 3. Test Registration

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 4. Test Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

## 🔍 Monitoring & Debugging

### View Logs
```bash
# API logs
./scripts/docker-manage.sh logs api

# Celery worker logs (for email processing)
./scripts/docker-manage.sh logs celery-worker

# Follow logs in real-time
./scripts/docker-manage.sh logs-follow api
```

### Check Celery Tasks
- **Flower UI**: http://localhost:5555
- **View task status, failures, and retry attempts**

### Redis Cache Inspection
```bash
# Connect to Redis
./scripts/docker-manage.sh redis-shell

# Check OTP codes
KEYS "otp:email_verification:*"
GET "otp:email_verification:test@example.com"

# Check email verification flags
KEYS "email_verified:*"
```

## 🛡️ Security Features

- **Rate Limiting**: Prevent OTP spam and brute force attacks
- **OTP Expiration**: 5-minute window for OTP codes
- **Password Validation**: Strong password requirements
- **Email Verification**: Required before registration
- **JWT Security**: Secure token generation and validation
- **CORS Protection**: Configurable origins
- **Input Validation**: Comprehensive request validation
- **Error Handling**: No information leakage in error messages

## 🎯 Frontend Integration

The authentication flow is designed to work seamlessly with the mobile app screens:

1. **Screen 1**: Email input → Send verification
2. **Screen 2**: OTP input → Verify email
3. **Screen 3**: Registration form → Create account
4. **Screen 4**: Login form → Authenticate

The API provides clear responses and error messages for each step, making frontend integration straightforward.

## 📞 Support

For issues or questions:
- Check API documentation: http://localhost:8000/docs
- View health status: http://localhost:8000/health
- Monitor tasks: http://localhost:5555 (Celery Flower)
- Check logs: `./scripts/docker-manage.sh logs api`


