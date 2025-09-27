# Bcrypt Authentication Fix Guide

## Problem Summary

Your AWS EC2 deployment was failing with bcrypt-related errors:

1. **bcrypt version compatibility issue**: `module 'bcrypt' has no attribute '__about__'`
2. **Password length validation error**: `password cannot be longer than 72 bytes`

## Root Causes

1. **Outdated bcrypt dependencies**: `passlib[bcrypt]==1.7.4` with incompatible bcrypt version
2. **No password length validation**: bcrypt has a 72-byte limit for passwords
3. **Missing password preprocessing**: Long passwords weren't handled properly

## Fixes Applied

### 1. Updated Dependencies (`requirements.txt`)
```diff
# Authentication and Security
pyjwt==2.8.0
passlib[bcrypt]==1.7.4
+ bcrypt==4.1.2
python-multipart==0.0.6
```

### 2. Enhanced Security Configuration (`app/config/security.py`)

#### Added explicit bcrypt configuration:
```python
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__min_rounds=10,
    bcrypt__max_rounds=15
)
```

#### Added password preprocessing:
```python
def _preprocess_password(self, password: str) -> str:
    """Preprocess password to handle bcrypt limitations."""
    if len(password.encode('utf-8')) > 72:
        # Hash long passwords with SHA-256 to get a fixed 64-byte string
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    return password
```

#### Enhanced password verification with error handling:
```python
def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    try:
        processed_password = self._preprocess_password(plain_password)
        return pwd_context.verify(processed_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False
```

### 3. Added Password Validation (`app/schemas/auth.py`)

```python
@field_validator('password')
@classmethod
def validate_password_length(cls, v):
    """Validate password length to prevent bcrypt issues."""
    if not v or len(v.strip()) == 0:
        raise ValueError("Password cannot be empty")
    
    byte_length = len(v.encode('utf-8'))
    if byte_length > 200:  # Reasonable upper limit
        raise ValueError("Password is too long (maximum 200 characters)")
    
    return v
```

### 4. Enhanced Dockerfile

- **Multi-stage build**: Separate development and production stages
- **Explicit bcrypt installation**: `pip install --upgrade bcrypt==4.1.2`
- **Production optimizations**: Non-root user, gunicorn, proper permissions
- **Better dependency management**: Cached layers and clean builds

## Deployment Instructions

### Option 1: Automated Deployment
```bash
# Set your EC2 details
export EC2_HOST="your-ec2-host.com"
export EC2_USER="ubuntu"
export EC2_KEY="~/.ssh/your-key.pem"

# Run the deployment script
./deploy-fix.sh
```

### Option 2: Manual Deployment

1. **Stop services on EC2**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-host.com
   cd /path/to/the_plugs_backend
   docker compose down
   ```

2. **Copy updated files**:
   ```bash
   scp -i your-key.pem requirements.txt ubuntu@your-ec2-host.com:/path/to/the_plugs_backend/
   scp -i your-key.pem app/config/security.py ubuntu@your-ec2-host.com:/path/to/the_plugs_backend/app/config/
   scp -i your-key.pem app/schemas/auth.py ubuntu@your-ec2-host.com:/path/to/the_plugs_backend/app/schemas/
   scp -i your-key.pem Dockerfile ubuntu@your-ec2-host.com:/path/to/the_plugs_backend/
   ```

3. **Rebuild and restart**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-host.com
   cd /path/to/the_plugs_backend
   docker compose build --no-cache
   docker compose up -d
   ```

4. **Verify deployment**:
   ```bash
   curl http://your-ec2-host.com:8000/health
   ```

## Testing the Fix

### 1. Health Check
```bash
curl http://your-ec2-host.com:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 2. Login Test
```bash
curl -X POST http://your-ec2-host.com:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your_password"
  }'
```

### 3. Monitor Logs
```bash
docker logs -f the_plugs_api
```

## Security Improvements

1. **Password Length Validation**: Prevents bcrypt errors
2. **Long Password Handling**: SHA-256 preprocessing for passwords > 72 bytes
3. **Error Handling**: Graceful failure without exposing details
4. **Production Security**: Non-root user, proper permissions
5. **Explicit Dependencies**: Pinned bcrypt version for consistency

## Best Practices Implemented

1. **Defense in Depth**: Multiple layers of validation
2. **Graceful Degradation**: Error handling without crashes
3. **Security by Design**: Non-root containers, minimal attack surface
4. **Monitoring**: Comprehensive logging for debugging
5. **Consistency**: Same bcrypt version across environments

## Troubleshooting

### If login still fails:
1. Check logs: `docker logs the_plugs_api`
2. Verify bcrypt version: `docker exec the_plugs_api pip show bcrypt`
3. Test password preprocessing manually
4. Check database connectivity

### If deployment fails:
1. Ensure EC2 has sufficient disk space
2. Check Docker daemon is running
3. Verify network connectivity to Supabase
4. Check security groups allow port 8000

## Monitoring

After deployment, monitor:
- Application logs for bcrypt errors
- Login success/failure rates
- Response times for auth endpoints
- Memory usage (bcrypt is memory-intensive)

This fix ensures your authentication system is robust, secure, and production-ready! 🚀
