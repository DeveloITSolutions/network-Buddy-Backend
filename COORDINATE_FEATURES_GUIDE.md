# Event Coordinate Features Guide

## Overview

This guide explains the new coordinate features added to the Event model for storing latitude/longitude data from Google Maps integration.

## Features Added

### 1. Database Fields

The Event model now includes three new fields:

- **`latitude`**: Decimal field (10,8) for storing latitude (-90 to 90)
- **`longitude`**: Decimal field (11,8) for storing longitude (-180 to 180)  
- **`location_metadata`**: JSONB field for storing Google Places API data

### 2. Model Methods

The Event model includes several helpful methods:

```python
# Check if event has coordinates
event.has_coordinates  # Returns bool

# Get coordinates as tuple
event.coordinates  # Returns (lat, lng) or None

# Set coordinates with validation
event.set_coordinates(lat, lng, metadata_dict)

# Generate Google Maps URL
event.get_google_maps_url()  # Returns Google Maps URL

# Get formatted address
event.get_display_address()  # Returns formatted address string
```

### 3. Schema Validation

The event schemas include comprehensive validation:

- **Coordinate ranges**: Latitude (-90 to 90), Longitude (-180 to 180)
- **Location metadata**: Must be a valid dictionary
- **Proximity search**: Validates radius and coordinate requirements

### 4. Geographic Utilities

A new `geo_utils.py` module provides:

- **Distance calculations**: Haversine formula for accurate distances
- **Radius filtering**: Check if points are within specified radius
- **Google Maps integration**: URL generation and Places API parsing
- **Coordinate validation**: Comprehensive validation utilities

## API Usage Examples

### Creating an Event with Coordinates

```json
POST /api/v1/events
{
  "title": "Tech Conference 2024",
  "start_date": "2024-06-15T09:00:00Z",
  "end_date": "2024-06-17T18:00:00Z",
  "location_name": "Convention Center",
  "city": "San Francisco",
  "state": "California",
  "country": "United States",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_metadata": {
    "place_id": "ChIJVVVVVVVVVVVVVVVVVVVVVVVV",
    "formatted_address": "123 Main St, San Francisco, CA 94102, USA",
    "types": ["establishment", "point_of_interest"],
    "rating": 4.5,
    "website": "https://conventioncenter.com"
  }
}
```

### Updating Event Coordinates

```json
PUT /api/v1/events/{event_id}
{
  "latitude": 37.7849,
  "longitude": -122.4094,
  "location_metadata": {
    "place_id": "ChIJWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "formatted_address": "456 New St, San Francisco, CA 94103, USA"
  }
}
```

### Geographic Filtering

```json
GET /api/v1/events?near_latitude=37.7749&near_longitude=-122.4194&radius_km=10
```

This will return events within 10km of the specified coordinates.

### Response Format

Events now include coordinate-related fields in responses:

```json
{
  "id": "uuid",
  "title": "Tech Conference 2024",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_metadata": {...},
  "has_coordinates": true,
  "coordinates": [37.7749, -122.4194],
  "google_maps_url": "https://www.google.com/maps?q=37.7749,-122.4194",
  "display_address": "Convention Center, 123 Main St, San Francisco, California, United States"
}
```

## Frontend Integration

### Google Maps Integration

1. **Get coordinates from Google Maps**:
```javascript
// When user selects location on map
const coordinates = {
  latitude: map.getCenter().lat(),
  longitude: map.getCenter().lng()
};

// Get place details
const place = autocomplete.getPlace();
const metadata = {
  place_id: place.place_id,
  formatted_address: place.formatted_address,
  types: place.types,
  rating: place.rating,
  website: place.website
};
```

2. **Send to API**:
```javascript
const eventData = {
  title: "My Event",
  start_date: "2024-06-15T09:00:00Z",
  end_date: "2024-06-15T17:00:00Z",
  latitude: coordinates.latitude,
  longitude: coordinates.longitude,
  location_metadata: metadata
};

fetch('/api/v1/events', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(eventData)
});
```

### Display Event Locations

```javascript
// Display events on map
events.forEach(event => {
  if (event.has_coordinates) {
    const marker = new google.maps.Marker({
      position: { lat: event.latitude, lng: event.longitude },
      title: event.title,
      map: map
    });
  }
});
```

## Database Migration

To apply the coordinate fields to your database:

```bash
# Run the migration
alembic upgrade head

# Or run specific migration
alembic upgrade 76b95c39d174
```

## Geographic Search Features

### Proximity Search

Find events near a specific location:

```python
# Using the service
events = event_service.get_events_near_location(
    latitude=37.7749,
    longitude=-122.4194,
    radius_km=10
)
```

### Distance Calculation

```python
from app.utils.geo_utils import GeoCalculator, Coordinates

coord1 = Coordinates(37.7749, -122.4194)  # San Francisco
coord2 = Coordinates(34.0522, -118.2437)  # Los Angeles

distance = GeoCalculator.calculate_distance(coord1, coord2)
print(f"Distance: {distance:.2f} km")
```

## Best Practices

### 1. Data Validation

Always validate coordinates before storing:

```python
from app.utils.geo_utils import LocationValidator

if LocationValidator.validate_coordinates(lat, lng):
    # Safe to store
    event.set_coordinates(lat, lng, metadata)
```

### 2. Error Handling

```python
try:
    event.set_coordinates(latitude, longitude, metadata)
except ValueError as e:
    # Handle invalid coordinates
    logger.error(f"Invalid coordinates: {e}")
```

### 3. Google Places Integration

Store relevant metadata from Google Places API:

```python
metadata = {
    "place_id": place.place_id,
    "formatted_address": place.formatted_address,
    "types": place.types,
    "rating": place.rating,
    "website": place.website,
    "photos": place.photos
}
```

### 4. Performance Considerations

- Use database indexes on latitude/longitude for fast geographic queries
- Consider using PostGIS for advanced geographic operations
- Cache Google Places API responses to reduce API calls

## Security Considerations

1. **Input Validation**: Always validate coordinate ranges
2. **Rate Limiting**: Implement rate limiting for Google Places API calls
3. **Data Privacy**: Be mindful of storing location data (GDPR compliance)
4. **API Keys**: Secure Google Maps API keys properly

## Testing

### Unit Tests

```python
def test_coordinate_validation():
    event = Event()
    
    # Valid coordinates
    event.set_coordinates(37.7749, -122.4194)
    assert event.has_coordinates == True
    
    # Invalid coordinates should raise ValueError
    with pytest.raises(ValueError):
        event.set_coordinates(91, 0)  # Invalid latitude
```

### Integration Tests

```python
def test_geographic_filtering():
    # Create events at different locations
    # Test proximity search
    # Verify results are within radius
```

## Troubleshooting

### Common Issues

1. **Migration fails**: Check database permissions and existing constraints
2. **Invalid coordinates**: Verify coordinate validation is working
3. **Google Maps not loading**: Check API key configuration
4. **Slow geographic queries**: Ensure indexes are created properly

### Debug Tools

```python
# Check if coordinates are valid
from app.utils.geo_utils import LocationValidator
print(LocationValidator.validate_coordinates(lat, lng))

# Calculate distance between points
from app.utils.geo_utils import GeoCalculator, Coordinates
distance = GeoCalculator.calculate_distance(coord1, coord2)
```

This coordinate system provides a robust foundation for location-based features in your event management application! 🗺️
