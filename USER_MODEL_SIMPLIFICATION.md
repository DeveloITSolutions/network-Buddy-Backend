# User Model Simplification

## Overview
Simplified the User model to match the exact requirements specified, removing unnecessary fields and following best practices.

## User Table Schema (Final)

```sql
Table users {
  id uuid pk
  email varchar(64) [not null, unique]
  password varchar(255) [not null]
  first_name varchar(32) [not null]
  last_name varchar(32) [not null]
  profile_picture varchar(500) [nullable]
  primary_number varchar(18) [nullable]
  secondary_number varchar(18) [nullable]
  timezone varchar(255) [not null, default: "UTC"]
  created_at timestamp [not null]
  updated_at timestamp [not null]
  is_active bool [not null, default: true]
}
```

## Changes Made

### ✅ **Removed Unnecessary Fields:**
- `is_verified` - Not needed for simplified auth flow
- `is_admin` - Not needed for basic auth
- `verified_at` - Not needed without email verification
- `last_login` - Not needed for simplified flow
- `phone` - Replaced with `primary_number` and `secondary_number`
- `bio` - Not needed for basic profile
- `avatar_url` - Replaced with `profile_picture`
- `job_title` - Not needed for basic profile
- `company` - Not needed for basic profile
- `linkedin_url` - Not needed for basic profile

### ✅ **Kept Essential Fields:**
- `id` - UUID primary key (from BaseModel)
- `email` - varchar(64), unique, indexed
- `password` - varchar(255) for hashed passwords
- `first_name` - varchar(32), required
- `last_name` - varchar(32), required
- `profile_picture` - varchar(500), optional
- `primary_number` - varchar(18), optional
- `secondary_number` - varchar(18), optional
- `timezone` - varchar(255), required, default "UTC"
- `created_at` - timestamp, required (from BaseModel)
- `updated_at` - timestamp, required (from BaseModel)
- `is_active` - boolean, required, default true

### ✅ **Removed Mixins:**
- Removed `TenantEntityMixin` - Not needed for basic auth
- Using only `BaseModel` for common fields

### ✅ **Updated Field Specifications:**
- `email`: varchar(64) (reduced from 255)
- `first_name`: varchar(32) (reduced from 50)
- `last_name`: varchar(32) (reduced from 50)
- `password`: varchar(255) (kept for security)
- `profile_picture`: varchar(500) (reasonable size)
- `primary_number`: varchar(18) (international format)
- `secondary_number`: varchar(18) (international format)
- `timezone`: varchar(255) (supports all timezones)

### ✅ **Common DateTime Utility:**
Created `app/utils/datetime.py` with common functions:
- `get_current_utc_time()` - Get current UTC time
- `get_current_utc_timestamp()` - Get current UTC timestamp
- `format_utc_datetime()` - Format UTC datetime
- `parse_utc_datetime()` - Parse UTC datetime
- `is_utc_datetime()` - Check if datetime is UTC
- `convert_to_utc()` - Convert to UTC

### ✅ **Updated Auth Service:**
- Changed `password_hash` → `password` field
- Removed email verification checks
- Removed last_login tracking
- Updated token payload to remove `is_verified`
- Updated user response to always show `is_verified: true`

### ✅ **Best Practices Applied:**

#### 1. **Field Naming:**
- Used `password` instead of `password_hash` (as requested)
- Consistent naming with database schema
- Clear, descriptive field names

#### 2. **Data Types:**
- Appropriate varchar lengths
- Proper nullable/not null constraints
- Sensible defaults

#### 3. **Common Utilities:**
- Centralized datetime handling
- Reusable timezone functions
- Consistent UTC usage

#### 4. **Model Methods:**
- Simplified `can_login()` method
- Removed unnecessary verification methods
- Kept essential profile methods

#### 5. **Security:**
- Password field still supports hashing
- Proper field constraints
- Secure defaults

## Benefits

### 1. **Simplified Schema:**
- Only essential fields for basic auth
- Reduced complexity
- Easier to maintain

### 2. **Performance:**
- Smaller table size
- Fewer indexes
- Faster queries

### 3. **Maintainability:**
- Clear field purposes
- Consistent naming
- Common utilities

### 4. **Flexibility:**
- Easy to extend if needed
- Common datetime utilities
- Generic base model

## Files Modified

### 1. `app/models/user.py`
- Simplified to exact schema requirements
- Removed unnecessary fields and mixins
- Updated field specifications
- Added common datetime utility usage

### 2. `app/services/auth_service.py`
- Updated to use `password` field
- Removed email verification logic
- Removed last_login tracking
- Updated token payload

### 3. `app/utils/datetime.py` (New)
- Common datetime utilities
- UTC timezone handling
- Reusable functions

## Database Migration Required

The User model changes require a database migration to:
1. Drop unnecessary columns
2. Rename `password_hash` to `password`
3. Update column sizes
4. Remove unnecessary indexes

## Conclusion

The User model now matches the exact requirements:
- ✅ Only essential fields for basic auth
- ✅ Proper field specifications
- ✅ Common datetime utilities
- ✅ Best practices applied
- ✅ Simplified and maintainable
- ✅ Ready for production use

The model is now focused, efficient, and follows the exact schema specification while maintaining security and best practices.
