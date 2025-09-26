"""
Service decorators for common validation and error handling patterns.
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from uuid import UUID

from app.core.exceptions import BusinessLogicError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def handle_service_errors(
    operation_name: str,
    error_code: str,
    details: Optional[dict] = None
):
    """
    Decorator to handle common service errors with consistent logging and error codes.
    
    Args:
        operation_name: Human-readable operation name for logging
        error_code: Error code for the exception
        details: Additional details to include in error
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except (ValidationError, NotFoundError, BusinessLogicError):
                # Re-raise known exceptions as-is
                raise
            except Exception as e:
                # Extract user_id and entity_id from common parameter patterns
                error_details = details or {}
                if 'user_id' in kwargs:
                    error_details['user_id'] = str(kwargs['user_id'])
                if 'event_id' in kwargs:
                    error_details['event_id'] = str(kwargs['event_id'])
                if 'media_id' in kwargs:
                    error_details['media_id'] = str(kwargs['media_id'])
                if 'plug_id' in kwargs:
                    error_details['plug_id'] = str(kwargs['plug_id'])
                
                error_details['error'] = str(e)
                
                logger.error(f"Error in {operation_name}: {e}")
                raise BusinessLogicError(
                    f"Failed to {operation_name.lower()}",
                    error_code=error_code,
                    details=error_details
                )
        return wrapper
    return decorator


def require_event_ownership(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to verify event ownership before executing the function.
    Expects user_id and event_id as parameters (positional or keyword).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        # Extract user_id and event_id from args or kwargs
        # Function signature: func(self, user_id, event_id, ...)
        user_id = None
        event_id = None
        
        if len(args) >= 3:  # self, user_id, event_id
            user_id = args[1]
            event_id = args[2]
        else:
            # Fallback to kwargs
            user_id = kwargs.get('user_id')
            event_id = kwargs.get('event_id')
        
        if not user_id or not event_id:
            raise ValidationError(
                "user_id and event_id are required",
                error_code="MISSING_REQUIRED_PARAMETERS"
            )
        
        # Get the service instance (first argument)
        service = args[0]
        
        # Verify ownership
        event = await service._verify_event_ownership(user_id, event_id)
        if not event:
            raise NotFoundError("Event not found")
        
        return await func(*args, **kwargs)
    return wrapper


def require_plug_ownership(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to verify plug ownership before executing the function.
    Expects user_id and plug_id as parameters (positional or keyword).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        # Extract user_id and plug_id from args or kwargs
        # Function signature: func(self, user_id, plug_id, ...)
        user_id = None
        plug_id = None
        
        if len(args) >= 3:  # self, user_id, plug_id
            user_id = args[1]
            plug_id = args[2]
        else:
            # Fallback to kwargs
            user_id = kwargs.get('user_id')
            plug_id = kwargs.get('plug_id')
        
        if not user_id or not plug_id:
            raise ValidationError(
                "user_id and plug_id are required",
                error_code="MISSING_REQUIRED_PARAMETERS"
            )
        
        # Get the service instance (first argument)
        service = args[0]
        
        # Verify ownership
        plug = await service._verify_plug_ownership(user_id, plug_id)
        if not plug:
            raise NotFoundError("Plug not found")
        
        return await func(*args, **kwargs)
    return wrapper


def validate_search_term(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate search terms before executing search functions.
    Expects search_term as a parameter.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        search_term = kwargs.get('search_term')
        
        if not search_term or len(search_term.strip()) < 2:
            raise ValidationError(
                "Search term must be at least 2 characters",
                error_code="INVALID_SEARCH_TERM"
            )
        
        # Clean the search term
        kwargs['search_term'] = search_term.strip()
        
        return await func(*args, **kwargs)
    return wrapper
