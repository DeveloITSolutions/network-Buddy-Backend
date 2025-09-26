# Event Agenda Workflow Guide

## Overview
This document explains how the event agenda system works and provides clear guidance on the API endpoints and their usage.

## Agenda Flow Understanding

### The Problem
- Users can see agenda items organized by days in the "Manage Agenda" screen
- When adding a new agenda item, users need to specify which day it belongs to
- The day should correspond to the event's date range (Day 1 = start date, Day 2 = start date + 1 day, etc.)

### The Solution
The agenda system now provides clear day management with the following features:
1. **Day Selection**: Users must specify which day (1-based) the agenda item belongs to
2. **Date Calculation**: Days are automatically mapped to actual dates based on the event's start date
3. **Validation**: The system validates that the selected day is within the event's duration
4. **Day Information**: API provides available days with their corresponding dates

## API Endpoints Workflow

### 1. Get Available Days for Event
**Endpoint**: `GET /api/v1/events/{event_id}/agenda/days`

**Purpose**: Get all available days for agenda items with their dates and agenda counts

**Response**:
```json
[
  {
    "day": 1,
    "date": "2024-01-15T00:00:00",
    "agenda_count": 3,
    "is_today": true
  },
  {
    "day": 2,
    "date": "2024-01-16T00:00:00",
    "agenda_count": 1,
    "is_today": false
  },
  {
    "day": 3,
    "date": "2024-01-17T00:00:00",
    "agenda_count": 0,
    "is_today": false
  }
]
```

**Usage**: Call this before showing the "Add Agenda" form to populate day selection dropdown

### 2. Create Agenda Item
**Endpoint**: `POST /api/v1/events/{event_id}/agenda`

**Purpose**: Create a new agenda item for a specific day

**Request Body**:
```json
{
  "title": "Opening Ceremony",
  "description": "Welcome speech and introductions",
  "location": "Main Hall",
  "day": 1,
  "start_time": "2024-01-15T09:00:00",
  "duration_minutes": 60
}
```

**Key Points**:
- `day` is **required** and must be between 1 and the event's total days
- `start_time` should be on the same date as the selected day
- System validates that the day is within the event's duration

**Response**:
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "title": "Opening Ceremony",
  "description": "Welcome speech and introductions",
  "location": "Main Hall",
  "day": 1,
  "start_time": "2024-01-15T09:00:00",
  "duration_minutes": 60,
  "end_time": "2024-01-15T10:00:00",
  "duration_display": "1 hour",
  "created_at": "2024-01-15T08:00:00",
  "updated_at": "2024-01-15T08:00:00"
}
```

### 3. Get Agenda Items
**Endpoint**: `GET /api/v1/events/{event_id}/agenda`

**Purpose**: Get agenda items, optionally filtered by day

**Query Parameters**:
- `day` (optional): Filter by specific day (1-based)
- `page` (optional): Page number for pagination
- `per_page` (optional): Items per page

**Examples**:
- `GET /api/v1/events/{event_id}/agenda` - Get all agenda items
- `GET /api/v1/events/{event_id}/agenda?day=1` - Get only Day 1 items
- `GET /api/v1/events/{event_id}/agenda?day=2&page=1&per_page=10` - Get Day 2 items with pagination

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "event_id": "uuid",
      "title": "Opening Ceremony",
      "description": "Welcome speech and introductions",
      "location": "Main Hall",
      "day": 1,
      "start_time": "2024-01-15T09:00:00",
      "duration_minutes": 60,
      "end_time": "2024-01-15T10:00:00",
      "duration_display": "1 hour",
      "created_at": "2024-01-15T08:00:00",
      "updated_at": "2024-01-15T08:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### 4. Update Agenda Item
**Endpoint**: `PUT /api/v1/events/{event_id}/agenda/{agenda_id}`

**Purpose**: Update an existing agenda item

**Request Body** (all fields optional):
```json
{
  "title": "Updated Opening Ceremony",
  "description": "Updated description",
  "location": "Updated Main Hall",
  "day": 1,
  "start_time": "2024-01-15T10:00:00",
  "duration_minutes": 90
}
```

### 5. Delete Agenda Item
**Endpoint**: `DELETE /api/v1/events/{event_id}/agenda/{agenda_id}`

**Purpose**: Delete an agenda item

**Response**: `204 No Content` on success

## Frontend Implementation Guide

### 1. Manage Agenda Screen (5.6.1)
- Display agenda items grouped by day
- Show day headers with dates: "Day 1 - January 15, 2024"
- Show agenda count for each day
- Allow filtering by day

### 2. Add Agenda Screen (5.6.2)
- **Day Selection**: Dropdown with available days
  - Populate from `/api/v1/events/{event_id}/agenda/days`
  - Show format: "Day 1 - January 15, 2024"
- **Date Field**: Auto-populate based on selected day
- **Time Fields**: Start time and duration
- **Validation**: Ensure start time is on the selected day

### 3. Day Selection Dropdown Example
```javascript
// Fetch available days
const daysResponse = await fetch(`/api/v1/events/${eventId}/agenda/days`);
const days = await daysResponse.json();

// Populate dropdown
const daySelect = document.getElementById('day-select');
days.forEach(day => {
  const option = document.createElement('option');
  option.value = day.day;
  option.textContent = `Day ${day.day} - ${new Date(day.date).toLocaleDateString()}`;
  daySelect.appendChild(option);
});
```

## Validation Rules

### Day Validation
- Day must be between 1 and event's total days
- Day must be a positive integer
- If event has 3 days, valid days are 1, 2, 3

### Time Validation
- Start time must be on the same date as the selected day
- Duration must be between 1 and 1440 minutes (24 hours)
- No overlapping agenda items (optional business rule)

### Required Fields
- `title`: 1-256 characters
- `day`: 1-based integer within event duration
- `start_time`: Valid datetime
- `duration_minutes`: 1-1440 minutes

## Error Handling

### Common Error Responses

**Invalid Day**:
```json
{
  "error": {
    "code": "INVALID_AGENDA_DAY",
    "message": "Day 5 exceeds event duration of 3 days",
    "timestamp": 1758876281.0037954
  }
}
```

**Missing Required Fields**:
```json
{
  "error": {
    "code": "MISSING_REQUIRED_FIELDS",
    "message": "title, day, and start_time are required",
    "timestamp": 1758876281.0037954
  }
}
```

**Event Not Found**:
```json
{
  "error": {
    "code": "EVENT_NOT_FOUND",
    "message": "Event not found",
    "timestamp": 1758876281.0037954
  }
}
```

## Best Practices

### 1. Day Management
- Always fetch available days before showing the add agenda form
- Validate day selection on both frontend and backend
- Show clear day-to-date mapping

### 2. Time Handling
- Use consistent timezone handling
- Validate that start time matches the selected day
- Consider timezone conversion for multi-day events

### 3. User Experience
- Show day headers with dates in the manage agenda screen
- Provide clear day selection in the add agenda form
- Display agenda count per day
- Sort agenda items by start time within each day

### 4. Error Messages
- Provide specific validation error messages
- Guide users to correct day selection
- Show available days when validation fails

## Summary

The agenda system now provides:
1. **Clear Day Management**: Users can see and select specific days
2. **Date Mapping**: Days are automatically mapped to actual dates
3. **Validation**: Proper validation ensures data integrity
4. **User-Friendly API**: Easy to integrate with frontend forms
5. **Comprehensive Information**: Day info includes dates and agenda counts

This resolves the confusion about which day agenda items belong to and provides a clear, intuitive workflow for managing event agendas.
