"""
Common datetime utilities for consistent timezone handling.
"""
from datetime import datetime, timezone
from typing import Optional


def get_current_utc_time() -> datetime:
    """
    Get current UTC time.
    
    Returns:
        datetime: Current UTC time
    """
    return datetime.now(timezone.utc)


def get_current_utc_timestamp() -> float:
    """
    Get current UTC timestamp.
    
    Returns:
        float: Current UTC timestamp
    """
    return datetime.now(timezone.utc).timestamp()


def format_utc_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format UTC datetime to string.
    
    Args:
        dt: Datetime object
        format_string: Format string
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(format_string)


def parse_utc_datetime(datetime_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse UTC datetime from string.
    
    Args:
        datetime_string: Datetime string
        format_string: Format string
        
    Returns:
        datetime: Parsed datetime or None if invalid
    """
    try:
        return datetime.strptime(datetime_string, format_string).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_utc_datetime(dt: datetime) -> bool:
    """
    Check if datetime is UTC.
    
    Args:
        dt: Datetime object
        
    Returns:
        bool: True if UTC, False otherwise
    """
    return dt.tzinfo == timezone.utc


def convert_to_utc(dt: datetime) -> datetime:
    """
    Convert datetime to UTC.
    
    Args:
        dt: Datetime object
        
    Returns:
        datetime: UTC datetime
    """
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
