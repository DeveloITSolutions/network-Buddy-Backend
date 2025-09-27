"""
Geographic utilities for handling coordinates and location data.
"""
import math
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass


@dataclass
class Coordinates:
    """Represents geographic coordinates."""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validate coordinates after initialization."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
    
    def __str__(self) -> str:
        return f"({self.latitude}, {self.longitude})"
    
    def __repr__(self) -> str:
        return f"Coordinates(lat={self.latitude}, lng={self.longitude})"


class GeoCalculator:
    """Geographic calculation utilities."""
    
    EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers
    
    @staticmethod
    def calculate_distance(
        coord1: Coordinates, 
        coord2: Coordinates, 
        unit: str = "km"
    ) -> float:
        """
        Calculate the great-circle distance between two points using the Haversine formula.
        
        Args:
            coord1: First set of coordinates
            coord2: Second set of coordinates
            unit: Distance unit ("km" or "miles")
            
        Returns:
            Distance between the two points
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(coord1.latitude), math.radians(coord1.longitude)
        lat2, lon2 = math.radians(coord2.latitude), math.radians(coord2.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Calculate distance
        distance_km = GeoCalculator.EARTH_RADIUS_KM * c
        
        if unit.lower() == "miles":
            return distance_km * 0.621371
        return distance_km
    
    @staticmethod
    def is_within_radius(
        center: Coordinates,
        point: Coordinates,
        radius_km: float
    ) -> bool:
        """
        Check if a point is within a specified radius of a center point.
        
        Args:
            center: Center coordinates
            point: Point to check
            radius_km: Radius in kilometers
            
        Returns:
            True if point is within radius, False otherwise
        """
        distance = GeoCalculator.calculate_distance(center, point)
        return distance <= radius_km
    
    @staticmethod
    def get_bounding_box(
        center: Coordinates,
        radius_km: float
    ) -> Tuple[float, float, float, float]:
        """
        Get bounding box coordinates for a center point and radius.
        
        Args:
            center: Center coordinates
            radius_km: Radius in kilometers
            
        Returns:
            Tuple of (min_lat, min_lng, max_lat, max_lng)
        """
        # Convert radius to degrees (approximate)
        lat_degrees = radius_km / 111.0  # 1 degree ≈ 111 km
        lng_degrees = radius_km / (111.0 * math.cos(math.radians(center.latitude)))
        
        min_lat = center.latitude - lat_degrees
        max_lat = center.latitude + lat_degrees
        min_lng = center.longitude - lng_degrees
        max_lng = center.longitude + lng_degrees
        
        return min_lat, min_lng, max_lat, max_lng


class GoogleMapsUtils:
    """Utilities for Google Maps integration."""
    
    @staticmethod
    def generate_maps_url(
        latitude: float,
        longitude: float,
        zoom: int = 15,
        map_type: str = "roadmap"
    ) -> str:
        """
        Generate Google Maps URL for coordinates.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            zoom: Zoom level (1-20)
            map_type: Map type (roadmap, satellite, hybrid, terrain)
            
        Returns:
            Google Maps URL
        """
        base_url = "https://www.google.com/maps"
        params = {
            "q": f"{latitude},{longitude}",
            "z": zoom,
            "t": map_type
        }
        
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_str}"
    
    @staticmethod
    def generate_embed_url(
        latitude: float,
        longitude: float,
        width: int = 600,
        height: int = 450,
        zoom: int = 15
    ) -> str:
        """
        Generate Google Maps embed URL for iframe.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            width: Map width
            height: Map height
            zoom: Zoom level
            
        Returns:
            Google Maps embed URL
        """
        base_url = "https://www.google.com/maps/embed/v1/view"
        params = {
            "key": "YOUR_API_KEY",  # This should be configured
            "center": f"{latitude},{longitude}",
            "zoom": zoom
        }
        
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_str}"
    
    @staticmethod
    def parse_google_places_data(places_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize Google Places API response data.
        
        Args:
            places_data: Raw Google Places API response
            
        Returns:
            Normalized location metadata
        """
        metadata = {
            "place_id": places_data.get("place_id"),
            "formatted_address": places_data.get("formatted_address"),
            "types": places_data.get("types", []),
            "business_status": places_data.get("business_status"),
            "rating": places_data.get("rating"),
            "user_ratings_total": places_data.get("user_ratings_total"),
            "price_level": places_data.get("price_level"),
            "website": places_data.get("website"),
            "formatted_phone_number": places_data.get("formatted_phone_number"),
            "international_phone_number": places_data.get("international_phone_number"),
            "opening_hours": places_data.get("opening_hours"),
            "photos": places_data.get("photos", []),
            "reviews": places_data.get("reviews", []),
            "utc_offset": places_data.get("utc_offset"),
            "vicinity": places_data.get("vicinity"),
        }
        
        # Add address components
        address_components = places_data.get("address_components", [])
        for component in address_components:
            types = component.get("types", [])
            long_name = component.get("long_name")
            short_name = component.get("short_name")
            
            if "locality" in types:
                metadata["city"] = long_name
            elif "administrative_area_level_1" in types:
                metadata["state"] = long_name
            elif "country" in types:
                metadata["country"] = long_name
                metadata["country_code"] = short_name
            elif "postal_code" in types:
                metadata["postal_code"] = long_name
        
        return {k: v for k, v in metadata.items() if v is not None}


class LocationValidator:
    """Location data validation utilities."""
    
    @staticmethod
    def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
        """
        Validate coordinate values.
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        if latitude is None or longitude is None:
            return False
        
        return (
            -90 <= latitude <= 90 and
            -180 <= longitude <= 180
        )
    
    @staticmethod
    def validate_radius(radius_km: float) -> bool:
        """
        Validate radius value.
        
        Args:
            radius_km: Radius in kilometers
            
        Returns:
            True if radius is valid, False otherwise
        """
        return 0.1 <= radius_km <= 1000
    
    @staticmethod
    def normalize_coordinates(
        latitude: float,
        longitude: float,
        precision: int = 8
    ) -> Tuple[float, float]:
        """
        Normalize coordinates to specified precision.
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            precision: Decimal precision
            
        Returns:
            Normalized coordinates tuple
        """
        return (
            round(latitude, precision),
            round(longitude, precision)
        )


def create_coordinates_from_dict(data: Dict[str, Any]) -> Optional[Coordinates]:
    """
    Create Coordinates object from dictionary data.
    
    Args:
        data: Dictionary containing latitude and longitude
        
    Returns:
        Coordinates object or None if invalid
    """
    try:
        lat = data.get("latitude") or data.get("lat")
        lng = data.get("longitude") or data.get("lng") or data.get("lon")
        
        if lat is not None and lng is not None:
            return Coordinates(float(lat), float(lng))
    except (ValueError, TypeError):
        pass
    
    return None


def format_coordinates_display(
    latitude: float,
    longitude: float,
    format_type: str = "decimal"
) -> str:
    """
    Format coordinates for display.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        format_type: Display format ("decimal", "dms")
        
    Returns:
        Formatted coordinate string
    """
    if format_type == "dms":
        # Convert to degrees, minutes, seconds
        lat_dir = "N" if latitude >= 0 else "S"
        lng_dir = "E" if longitude >= 0 else "W"
        
        lat_abs = abs(latitude)
        lng_abs = abs(longitude)
        
        lat_d = int(lat_abs)
        lat_m = int((lat_abs - lat_d) * 60)
        lat_s = ((lat_abs - lat_d) * 60 - lat_m) * 60
        
        lng_d = int(lng_abs)
        lng_m = int((lng_abs - lng_d) * 60)
        lng_s = ((lng_abs - lng_d) * 60 - lng_m) * 60
        
        return f"{lat_d}°{lat_m}'{lat_s:.2f}\"{lat_dir} {lng_d}°{lng_m}'{lng_s:.2f}\"{lng_dir}"
    
    return f"{latitude:.8f}, {longitude:.8f}"
