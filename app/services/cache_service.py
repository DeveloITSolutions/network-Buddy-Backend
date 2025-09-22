"""
Generic cache service for common caching operations.
"""
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timezone, timedelta

from app.config.redis import get_cache_manager

logger = logging.getLogger(__name__)


class CacheService:
    """
    Generic cache service providing common caching operations.
    
    Follows DRY principle by centralizing cache operations.
    """
    
    def __init__(self):
        self.cache = get_cache_manager()
        self.default_ttl = 3600  # 1 hour
        self.otp_ttl = 300  # 5 minutes
        self.token_ttl = 1800  # 30 minutes
    
    def generate_key(self, prefix: str, identifier: str, *args) -> str:
        """
        Generate cache key with consistent format.
        
        Args:
            prefix: Key prefix (e.g., 'otp', 'token', 'session')
            identifier: Primary identifier (e.g., email, user_id)
            *args: Additional key components
            
        Returns:
            Formatted cache key
        """
        key_parts = [prefix, identifier] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def set_with_ttl(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            return self.cache.set(key, value, timeout=ttl)
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            return self.cache.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.cache.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return self.cache.exists(key)
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    def set_otp(self, email: str, otp: str) -> bool:
        """
        Store OTP in cache.
        
        Args:
            email: User email
            otp: OTP code
            
        Returns:
            True if successful, False otherwise
        """
        key = self.generate_key("otp", email)
        return self.set_with_ttl(key, otp, self.otp_ttl)
    
    def get_otp(self, email: str) -> Optional[str]:
        """
        Get OTP from cache.
        
        Args:
            email: User email
            
        Returns:
            OTP code if found, None otherwise
        """
        key = self.generate_key("otp", email)
        return self.get(key)
    
    def delete_otp(self, email: str) -> bool:
        """
        Delete OTP from cache.
        
        Args:
            email: User email
            
        Returns:
            True if deleted, False otherwise
        """
        key = self.generate_key("otp", email)
        return self.delete(key)
    
    def set_verification_token(self, email: str, token: str) -> bool:
        """
        Store verification token in cache.
        
        Args:
            email: User email
            token: Verification token
            
        Returns:
            True if successful, False otherwise
        """
        key = self.generate_key("verification_token", email)
        return self.set_with_ttl(key, token, self.token_ttl)
    
    def get_verification_token(self, email: str) -> Optional[str]:
        """
        Get verification token from cache.
        
        Args:
            email: User email
            
        Returns:
            Verification token if found, None otherwise
        """
        key = self.generate_key("verification_token", email)
        return self.get(key)
    
    def delete_verification_token(self, email: str) -> bool:
        """
        Delete verification token from cache.
        
        Args:
            email: User email
            
        Returns:
            True if deleted, False otherwise
        """
        key = self.generate_key("verification_token", email)
        return self.delete(key)
    
    def set_session_data(self, session_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store session data in cache.
        
        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        key = self.generate_key("session", session_id)
        return self.set_with_ttl(key, data, ttl)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data from cache.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data if found, None otherwise
        """
        key = self.generate_key("session", session_id)
        return self.get(key)
    
    def delete_session_data(self, session_id: str) -> bool:
        """
        Delete session data from cache.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False otherwise
        """
        key = self.generate_key("session", session_id)
        return self.delete(key)
    
    def set_user_data(self, user_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store user data in cache.
        
        Args:
            user_id: User identifier
            data: User data
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        key = self.generate_key("user", user_id)
        return self.set_with_ttl(key, data, ttl)
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data if found, None otherwise
        """
        key = self.generate_key("user", user_id)
        return self.get(key)
    
    def delete_user_data(self, user_id: str) -> bool:
        """
        Delete user data from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False otherwise
        """
        key = self.generate_key("user", user_id)
        return self.delete(key)
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear cache keys matching pattern.
        
        Args:
            pattern: Redis key pattern
            
        Returns:
            Number of keys deleted
        """
        try:
            return self.cache.clear_cache(pattern)
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
