"""
Rate limiting utilities for API endpoints security.
"""
import time
import json
import logging
from typing import Optional, Dict, Tuple
from fastapi import HTTPException, Request, status
from functools import wraps

from app.config.redis import get_cache_manager

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting service for security-critical endpoints."""
    
    def __init__(self):
        self.cache = get_cache_manager()
        
        # Rate limiting configurations
        self.limits = {
            "login": {"max_attempts": 5, "window": 900},  # 5 attempts per 15 minutes
            "otp_send": {"max_attempts": 3, "window": 300},  # 3 attempts per 5 minutes
            "otp_verify": {"max_attempts": 5, "window": 900},  # 5 attempts per 15 minutes
            "password_change": {"max_attempts": 3, "window": 1800},  # 3 attempts per 30 minutes
        }
    
    def _get_key(self, endpoint: str, identifier: str) -> str:
        """Generate rate limit cache key."""
        return f"rate_limit:{endpoint}:{identifier}"
    
    def _get_lockout_key(self, identifier: str) -> str:
        """Generate account lockout cache key."""
        return f"account_lockout:{identifier}"
    
    def check_rate_limit(self, endpoint: str, identifier: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limits.
        
        Args:
            endpoint: API endpoint name
            identifier: User identifier (email/IP)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if endpoint not in self.limits:
            return True, None
        
        config = self.limits[endpoint]
        key = self._get_key(endpoint, identifier)
        
        try:
            # Get current attempts
            data = self.cache.get(key)
            current_time = int(time.time())
            
            if data:
                attempts_data = json.loads(data)
                attempts = attempts_data.get("attempts", 0)
                window_start = attempts_data.get("window_start", current_time)
                
                # Check if window has expired
                if current_time - window_start >= config["window"]:
                    # Reset window
                    attempts = 0
                    window_start = current_time
                
                if attempts >= config["max_attempts"]:
                    retry_after = config["window"] - (current_time - window_start)
                    return False, max(retry_after, 0)
            
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, None  # Fail open for availability
    
    def record_attempt(self, endpoint: str, identifier: str, success: bool = False) -> None:
        """
        Record an attempt against rate limits.
        
        Args:
            endpoint: API endpoint name
            identifier: User identifier
            success: Whether the attempt was successful
        """
        if endpoint not in self.limits:
            return
        
        config = self.limits[endpoint]
        key = self._get_key(endpoint, identifier)
        
        try:
            current_time = int(time.time())
            
            # Get current data
            data = self.cache.get(key)
            if data:
                attempts_data = json.loads(data)
                attempts = attempts_data.get("attempts", 0)
                window_start = attempts_data.get("window_start", current_time)
                
                # Check if window has expired
                if current_time - window_start >= config["window"]:
                    attempts = 0
                    window_start = current_time
            else:
                attempts = 0
                window_start = current_time
            
            # Increment attempts only on failure
            if not success:
                attempts += 1
            else:
                # Reset on successful login
                attempts = 0
                window_start = current_time
            
            # Store updated data
            new_data = {
                "attempts": attempts,
                "window_start": window_start
            }
            
            self.cache.set(key, json.dumps(new_data), timeout=config["window"])
            
        except Exception as e:
            logger.error(f"Failed to record rate limit attempt: {e}")
    
    def is_account_locked(self, email: str) -> Tuple[bool, Optional[int]]:
        """
        Check if account is temporarily locked.
        
        Args:
            email: User email address
            
        Returns:
            Tuple of (is_locked, unlock_time_seconds)
        """
        key = self._get_lockout_key(email)
        
        try:
            data = self.cache.get(key)
            if data:
                lockout_data = json.loads(data)
                unlock_time = lockout_data.get("unlock_time", 0)
                current_time = int(time.time())
                
                if current_time < unlock_time:
                    return True, unlock_time - current_time
                else:
                    # Lockout expired, remove it
                    self.cache.delete(key)
            
            return False, None
            
        except Exception as e:
            logger.error(f"Account lockout check failed: {e}")
            return False, None
    
    def lock_account(self, email: str, duration: int = 3600) -> None:
        """
        Temporarily lock account after repeated failures.
        
        Args:
            email: User email address
            duration: Lockout duration in seconds (default 1 hour)
        """
        key = self._get_lockout_key(email)
        unlock_time = int(time.time()) + duration
        
        try:
            lockout_data = {
                "email": email,
                "locked_at": int(time.time()),
                "unlock_time": unlock_time,
                "reason": "repeated_failed_attempts"
            }
            
            self.cache.set(key, json.dumps(lockout_data), timeout=duration)
            logger.warning(f"Account temporarily locked: {email} for {duration} seconds")
            
        except Exception as e:
            logger.error(f"Failed to lock account: {e}")
    
    def check_failed_attempts(self, email: str) -> int:
        """
        Get number of recent failed attempts for an email.
        
        Args:
            email: User email address
            
        Returns:
            Number of failed attempts in current window
        """
        key = self._get_key("login", email)
        
        try:
            data = self.cache.get(key)
            if data:
                attempts_data = json.loads(data)
                return attempts_data.get("attempts", 0)
            return 0
            
        except Exception as e:
            logger.error(f"Failed to check failed attempts: {e}")
            return 0


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(endpoint: str, identifier_func=None):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        endpoint: Endpoint name for rate limiting config
        identifier_func: Function to extract identifier from request
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and identifier
            request = None
            identifier = None
            
            # Find request in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                # Look in kwargs
                request = kwargs.get('request')
            
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # Default to client IP
                identifier = request.client.host if request else "unknown"
            
            # Check rate limit
            allowed, retry_after = rate_limiter.check_rate_limit(endpoint, identifier)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Execute function
            try:
                result = await func(*args, **kwargs)
                # Record successful attempt
                rate_limiter.record_attempt(endpoint, identifier, success=True)
                return result
                
            except HTTPException as e:
                # Record failed attempt for client errors
                if e.status_code in [400, 401, 422]:
                    rate_limiter.record_attempt(endpoint, identifier, success=False)
                raise
            
        return wrapper
    return decorator


def get_client_identifier(request: Request) -> str:
    """Extract client identifier for rate limiting."""
    # Try to get real IP from headers (for reverse proxy setups)
    real_ip = request.headers.get("X-Real-IP")
    forwarded_for = request.headers.get("X-Forwarded-For")
    
    if real_ip:
        return real_ip
    elif forwarded_for:
        # Get first IP from X-Forwarded-For header
        return forwarded_for.split(",")[0].strip()
    else:
        return request.client.host
