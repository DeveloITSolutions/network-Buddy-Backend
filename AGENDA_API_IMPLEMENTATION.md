# Agenda API Implementation Guide

## Overview
This document provides the complete API implementation for the event agenda system, matching the UI screenshots provided. The implementation supports the full agenda management workflow shown in the mobile app screens.

## API Endpoints

### 1. Get Available Days for Event
**Endpoint**: `GET /api/v1/events/{event_id}/agenda/days`

**Purpose**: Get all available days for agenda items with their dates and agenda counts (for populating day selection dropdowns)

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response**:
```json
[
  {
    "day": 1,
    "date": "2024-08-15T00:00:00",
    "agenda_count": 3,
    "is_today": true
  },
  {
    "day": 2,
    "date": "2024-08-16T00:00:00",
    "agenda_count": 1,
    "is_today": false
  },
  {
    "day": 3,
    "date": "2024-08-17T00:00:00",
    "agenda_count": 0,
    "is_today": false
  }
]
```

**Usage**: Call this before showing the "Add Agenda" form to populate the day selection dropdown.

### 2. Create Agenda Item
**Endpoint**: `POST /api/v1/events/{event_id}/agenda`

**Purpose**: Create a new agenda item for a specific day (Screen 5.6.2 - Add Agenda)

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "title": "Opening Remarks (Main Hall)",
  "description": "Welcome speech and introductions",
  "location": "Lecture Hall A",
  "day": 1,
  "start_time": "2024-08-15T09:30:00",
  "duration_minutes": 60
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "title": "Opening Remarks (Main Hall)",
  "description": "Welcome speech and introductions",
  "location": "Lecture Hall A",
  "day": 1,
  "start_time": "2024-08-15T09:30:00",
  "duration_minutes": 60,
  "end_time": "2024-08-15T10:30:00",
  "duration_display": "1 hour",
  "created_at": "2024-08-15T08:00:00",
  "updated_at": "2024-08-15T08:00:00"
}
```

### 3. Get Agenda Items
**Endpoint**: `GET /api/v1/events/{event_id}/agenda`

**Purpose**: Get agenda items for an event (Screen 5.6.1 - Manage Agenda)

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Query Parameters**:
- `day` (optional): Filter by specific day (1-based)
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100)

**Examples**:
- `GET /api/v1/events/{event_id}/agenda` - Get all agenda items
- `GET /api/v1/events/{event_id}/agenda?day=1` - Get only Day 1 items
- `GET /api/v1/events/{event_id}/agenda?day=2&skip=0&limit=10` - Get Day 2 items with pagination

**Response**:
```json
[
  {
    "id": "uuid",
    "event_id": "uuid",
    "title": "8:00-9:00 AM Registration & Coffee",
    "description": "Welcome coffee and registration",
    "location": "Main Lobby",
    "day": 1,
    "start_time": "2024-08-15T08:00:00",
    "duration_minutes": 60,
    "end_time": "2024-08-15T09:00:00",
    "duration_display": "1 hour",
    "created_at": "2024-08-15T08:00:00",
    "updated_at": "2024-08-15T08:00:00"
  },
  {
    "id": "uuid",
    "event_id": "uuid",
    "title": "9:00-9:30 AM Opening Remarks (Main Hall)",
    "description": "Welcome speech and introductions",
    "location": "Main Hall",
    "day": 1,
    "start_time": "2024-08-15T09:00:00",
    "duration_minutes": 30,
    "end_time": "2024-08-15T09:30:00",
    "duration_display": "30 minutes",
    "created_at": "2024-08-15T08:00:00",
    "updated_at": "2024-08-15T08:00:00"
  }
]
```

### 4. Update Agenda Item
**Endpoint**: `PUT /api/v1/events/{event_id}/agenda/{agenda_id}`

**Purpose**: Update an existing agenda item (Screen 5.6.3 - Edit Agenda)

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body** (all fields optional):
```json
{
  "title": "Updated Opening Remarks (Main Hall)",
  "description": "Updated welcome speech and introductions",
  "location": "Updated Lecture Hall A",
  "day": 1,
  "start_time": "2024-08-15T10:00:00",
  "duration_minutes": 90
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "title": "Updated Opening Remarks (Main Hall)",
  "description": "Updated welcome speech and introductions",
  "location": "Updated Lecture Hall A",
  "day": 1,
  "start_time": "2024-08-15T10:00:00",
  "duration_minutes": 90,
  "end_time": "2024-08-15T11:30:00",
  "duration_display": "1.5 hours",
  "created_at": "2024-08-15T08:00:00",
  "updated_at": "2024-08-15T08:30:00"
}
```

### 5. Delete Agenda Item
**Endpoint**: `DELETE /api/v1/events/{event_id}/agenda/{agenda_id}`

**Purpose**: Delete an agenda item (from the three-dot menu in Screen 5.6.1)

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response**: `204 No Content` on success

## Frontend Integration Guide

### Screen 5.6.1 - Manage Agenda
This screen displays agenda items grouped by day with day tabs.

**API Calls**:
1. **Get Available Days**: `GET /api/v1/events/{event_id}/agenda/days`
   - Use to populate day tabs
   - Show day headers with dates: "Day 1 Aug 15, 2025"
   - Display agenda count for each day

2. **Get Agenda Items**: `GET /api/v1/events/{event_id}/agenda?day={selected_day}`
   - Use to populate agenda list for selected day
   - Sort by start_time within each day

**UI Elements**:
- Day tabs: "Day 1 Aug 15, 2025", "Day 2 Aug 16, 2025", "Day 3 Aug 17, 2025"
- Agenda list with time ranges, titles, and locations
- Three-dot menu for each agenda item (Edit/Delete)
- "Add Item" button

### Screen 5.6.2 - Add Agenda
This screen is a modal for adding new agenda items.

**API Calls**:
1. **Get Available Days**: `GET /api/v1/events/{event_id}/agenda/days`
   - Use to populate day dropdown
   - Show format: "Day 1 - August 15, 2025"

2. **Create Agenda Item**: `POST /api/v1/events/{event_id}/agenda`
   - Send form data with selected day

**Form Fields**:
- **Day**: Dropdown populated from API
- **Title**: Text input
- **Location**: Text input
- **Start Time**: Time picker (AM/PM toggle)
- **Duration**: Dropdown (1 hour, 2 hours, etc.)

### Screen 5.6.3 - Edit Agenda
This screen is a modal for editing existing agenda items.

**API Calls**:
1. **Update Agenda Item**: `PUT /api/v1/events/{event_id}/agenda/{agenda_id}`
   - Send updated form data

**Form Fields**:
- Pre-filled with existing data
- Same fields as Add Agenda screen
- "Update" button instead of "Submit"

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
  "detail": "Day 5 exceeds event duration of 3 days"
}
```

**Missing Required Fields**:
```json
{
  "detail": "title, day, and start_time are required"
}
```

**Event Not Found**:
```json
{
  "detail": "Event not found"
}
```

**Agenda Item Not Found**:
```json
{
  "detail": "Agenda item not found"
}
```

## Implementation Status

✅ **Completed**:
- All API endpoints implemented
- Proper validation and error handling
- Day management with date calculation
- CRUD operations for agenda items
- JWT authentication
- Service layer refactoring

✅ **Matches UI Screenshots**:
- Day selection dropdown (Screen 5.6.2)
- Agenda list with day tabs (Screen 5.6.1)
- Edit/Delete functionality (Screen 5.6.3)
- Proper form validation
- Time and duration handling

## Testing

### Test Scenarios

1. **Create Agenda Item**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/events/{event_id}/agenda" \
        -H "Authorization: Bearer <token>" \
        -H "Content-Type: application/json" \
        -d '{
          "title": "Opening Remarks",
          "location": "Main Hall",
          "day": 1,
          "start_time": "2024-08-15T09:00:00",
          "duration_minutes": 60
        }'
   ```

2. **Get Available Days**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/events/{event_id}/agenda/days" \
        -H "Authorization: Bearer <token>"
   ```

3. **Get Agenda Items for Day 1**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/events/{event_id}/agenda?day=1" \
        -H "Authorization: Bearer <token>"
   ```

## Summary

The agenda API implementation is now complete and matches the UI screenshots provided. The system provides:

1. **Clear Day Management**: Users can see and select specific days
2. **Date Mapping**: Days are automatically mapped to actual dates
3. **Full CRUD Operations**: Create, read, update, and delete agenda items
4. **Proper Validation**: Ensures data integrity and user guidance
5. **UI Integration**: Ready for frontend implementation

The implementation resolves the original confusion about day selection and provides a seamless agenda management experience.
