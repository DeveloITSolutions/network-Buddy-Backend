"""
Timezone utilities for handling user timezone detection and validation.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, available_timezones
import logging

logger = logging.getLogger(__name__)


def get_available_timezones() -> List[str]:
    """
    Get list of all available IANA timezone identifiers.
    
    Returns:
        List[str]: Sorted list of timezone identifiers
    """
    return sorted(list(available_timezones()))


def validate_timezone(timezone: str) -> bool:
    """
    Validate if a timezone identifier is valid.
    
    Args:
        timezone: Timezone identifier to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ZoneInfo(timezone)
        return True
    except Exception:
        return False


def get_timezone_info(timezone: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a timezone.
    
    Args:
        timezone: IANA timezone identifier
        
    Returns:
        Optional[Dict[str, Any]]: Timezone information or None if invalid
    """
    try:
        zone_info = ZoneInfo(timezone)
        now = datetime.now(zone_info)
        
        # Get UTC offset
        utc_offset = now.strftime("%z")
        utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}" if utc_offset else "+00:00"
        
        # Get timezone name
        timezone_name = now.tzname()
        
        return {
            "timezone": timezone,
            "utc_offset": utc_offset_formatted,
            "timezone_name": timezone_name,
            "is_dst": now.dst() != timedelta(0),
            "current_time": now.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get timezone info for {timezone}: {e}")
        return None


def get_common_timezones() -> List[Dict[str, str]]:
    """
    Get list of common timezones for frontend selection.
    
    Returns:
        List[Dict[str, str]]: List of common timezones with display names
    """
    common_timezones = [
        "UTC",
        "America/New_York",
        "America/Chicago", 
        "America/Denver",
        "America/Los_Angeles",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/Rome",
        "Europe/Madrid",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Kolkata",
        "Asia/Dubai",
        "Australia/Sydney",
        "Australia/Melbourne",
        "Pacific/Auckland",
        "America/Sao_Paulo",
        "America/Mexico_City",
        "America/Toronto"
    ]
    
    result = []
    for tz in common_timezones:
        if validate_timezone(tz):
            info = get_timezone_info(tz)
            if info:
                result.append({
                    "value": tz,
                    "label": f"{tz} ({info['utc_offset']})",
                    "utc_offset": info["utc_offset"]
                })
    
    return result


def detect_timezone_from_offset(utc_offset_minutes: int) -> List[str]:
    """
    Detect possible timezones from UTC offset in minutes.
    
    Args:
        utc_offset_minutes: UTC offset in minutes (e.g., -300 for EST)
        
    Returns:
        List[str]: List of possible timezone identifiers
    """
    possible_timezones = []
    
    for tz in available_timezones():
        try:
            zone_info = ZoneInfo(tz)
            now = datetime.now(zone_info)
            tz_offset_minutes = now.utcoffset().total_seconds() / 60
            
            if tz_offset_minutes == utc_offset_minutes:
                possible_timezones.append(tz)
        except Exception:
            continue
    
    return possible_timezones


def format_timezone_display(timezone: str) -> str:
    """
    Format timezone for display purposes.
    
    Args:
        timezone: IANA timezone identifier
        
    Returns:
        str: Formatted timezone display string
    """
    info = get_timezone_info(timezone)
    if not info:
        return timezone
    
    return f"{timezone} ({info['utc_offset']})"


def get_user_friendly_timezone_list() -> List[Dict[str, Any]]:
    """
    Get user-friendly timezone list with regions grouped.
    
    Returns:
        List[Dict[str, Any]]: Grouped timezone list
    """
    regions = {
        "Americas": [
            "America/New_York", "America/Chicago", "America/Denver", 
            "America/Los_Angeles", "America/Toronto", "America/Vancouver",
            "America/Mexico_City", "America/Sao_Paulo", "America/Argentina/Buenos_Aires"
        ],
        "Europe": [
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
            "Europe/Madrid", "Europe/Amsterdam", "Europe/Stockholm", "Europe/Moscow"
        ],
        "Asia": [
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Asia/Dubai",
            "Asia/Singapore", "Asia/Seoul", "Asia/Bangkok", "Asia/Hong_Kong"
        ],
        "Oceania": [
            "Australia/Sydney", "Australia/Melbourne", "Australia/Perth",
            "Pacific/Auckland", "Pacific/Fiji"
        ],
        "Africa": [
            "Africa/Cairo", "Africa/Johannesburg", "Africa/Lagos", "Africa/Nairobi"
        ]
    }
    
    result = []
    for region, timezones in regions.items():
        region_timezones = []
        for tz in timezones:
            if validate_timezone(tz):
                info = get_timezone_info(tz)
                if info:
                    region_timezones.append({
                        "value": tz,
                        "label": f"{tz} ({info['utc_offset']})",
                        "utc_offset": info["utc_offset"]
                    })
        
        if region_timezones:
            result.append({
                "region": region,
                "timezones": region_timezones
            })
    
    return result
