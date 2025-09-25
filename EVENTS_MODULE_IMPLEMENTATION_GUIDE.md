# Events Module Implementation Guide

## Overview

The Events Module is a comprehensive system for managing conferences, summits, and gatherings with multiple sub-modules. It provides complete CRUD functionality for events and their associated components: Deeds (agenda & expenses), Plugs (contacts/targets), Zone (media), and Tea (additional features).

## Architecture

The implementation follows a clean, layered architecture:

```
┌─────────────────┐
│   API Layer     │  ← FastAPI endpoints with Pydantic validation
├─────────────────┤
│  Service Layer  │  ← Business logic and validation
├─────────────────┤
│Repository Layer │  ← Data access and database operations
├─────────────────┤
│  Database Layer │  ← SQLAlchemy models and relationships
└─────────────────┘
```

## Database Schema

### Core Tables

#### 1. Events Table
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(128) NOT NULL,
    theme VARCHAR(64),
    description TEXT,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    location_name VARCHAR(128),
    location_address TEXT,
    city VARCHAR(64),
    state VARCHAR(64),
    country VARCHAR(64),
    postal_code VARCHAR(16),
    website_url VARCHAR(512),
    cover_image_url VARCHAR(512),
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_end_after_start CHECK (end_date > start_date),
    CONSTRAINT unique_user_event UNIQUE (user_id, title, start_date)
);
```

#### 2. Event Agenda Table (Deeds Module)
```sql
CREATE TABLE event_agendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    location VARCHAR(128),
    day INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_positive_day CHECK (day > 0),
    CONSTRAINT check_positive_duration CHECK (duration_minutes > 0)
);
```

#### 3. Event Expenses Table (Deeds Module)
```sql
CREATE TABLE event_expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    category VARCHAR(64) NOT NULL,
    description VARCHAR(256),
    amount DECIMAL NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_non_negative_amount CHECK (amount >= 0)
);
```

#### 4. Event Media Table (Zone Module)
```sql
CREATE TABLE event_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(256),
    description TEXT,
    file_url VARCHAR(512) NOT NULL,
    file_type VARCHAR(32) NOT NULL,
    file_size INTEGER,
    tags TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

#### 5. Event-Plug Association Table
```sql
CREATE TABLE event_plugs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    plug_id UUID NOT NULL REFERENCES plugs(id) ON DELETE CASCADE,
    notes TEXT,
    priority VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_event_plug UNIQUE (event_id, plug_id)
);
```

## API Endpoints

### Event Management

#### Create Event
```http
POST /api/v1/events/
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "title": "Hair Health Summit",
    "theme": "Hair Restoration",
    "description": "Annual conference on hair health innovations",
    "start_date": "2025-08-15T09:00:00Z",
    "end_date": "2025-08-17T18:00:00Z",
    "location_name": "The Gwen Hotel",
    "location_address": "521 North Rush Street Chicago, IL 60611",
    "city": "Chicago",
    "state": "IL",
    "country": "USA",
    "postal_code": "60611",
    "website_url": "https://hairtechconference2025.com",
    "cover_image_url": "https://example.com/cover.jpg",
    "is_public": false
}
```

#### List Events
```http
GET /api/v1/events/?skip=0&limit=10&search=summit&city=Chicago
Authorization: Bearer <jwt_token>
```

#### Get Event Details
```http
GET /api/v1/events/{event_id}
Authorization: Bearer <jwt_token>
```

#### Update Event
```http
PUT /api/v1/events/{event_id}
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "title": "Updated Event Title",
    "theme": "Updated Theme"
}
```

#### Delete Event
```http
DELETE /api/v1/events/{event_id}
Authorization: Bearer <jwt_token>
```

#### Get Event Statistics
```http
GET /api/v1/events/stats
Authorization: Bearer <jwt_token>
```

### Deeds Module (Agenda & Expenses)

#### Create Agenda Item
```http
POST /api/v1/events/{event_id}/agenda
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "title": "Opening Remarks",
    "description": "Welcome and conference overview",
    "location": "Main Hall - Auditorium A",
    "day": 1,
    "start_time": "2025-08-15T09:00:00Z",
    "duration_minutes": 30
}
```

#### Get Event Agenda
```http
GET /api/v1/events/{event_id}/agenda?day=1&skip=0&limit=20
Authorization: Bearer <jwt_token>
```

#### Create Expense
```http
POST /api/v1/events/{event_id}/expenses
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "category": "Event Signup",
    "description": "Conference registration fee",
    "amount": 1299.00,
    "currency": "USD"
}
```

#### Get Event Expenses
```http
GET /api/v1/events/{event_id}/expenses?category=Event Signup&skip=0&limit=20
Authorization: Bearer <jwt_token>
```

### Zone Module (Media)

#### Create Media
```http
POST /api/v1/events/{event_id}/media
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "title": "Panel Discussion Photo",
    "description": "Keynote session on AI in dermatology",
    "file_url": "https://example.com/photo.jpg",
    "file_type": "image/jpeg",
    "file_size": 2048576,
    "tags": ["keynote", "main stage", "panel"]
}
```

#### Get Event Media
```http
GET /api/v1/events/{event_id}/media?file_type=image/jpeg&skip=0&limit=20
Authorization: Bearer <jwt_token>
```

### Plugs Module

#### Add Plug to Event
```http
POST /api/v1/events/{event_id}/plugs
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "plug_id": "123e4567-e89b-12d3-a456-426614174000",
    "notes": "Met during keynote session",
    "priority": "high"
}
```

#### Get Event Plugs
```http
GET /api/v1/events/{event_id}/plugs?plug_type=contact&skip=0&limit=20
Authorization: Bearer <jwt_token>
```

#### Remove Plug from Event
```http
DELETE /api/v1/events/{event_id}/plugs/{plug_id}
Authorization: Bearer <jwt_token>
```

## Pydantic Schemas

### Event Schemas

#### EventCreate
```python
class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    theme: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    location_name: Optional[str] = Field(None, max_length=128)
    location_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=64)
    state: Optional[str] = Field(None, max_length=64)
    country: Optional[str] = Field(None, max_length=64)
    postal_code: Optional[str] = Field(None, max_length=16)
    website_url: Optional[HttpUrl] = None
    cover_image_url: Optional[HttpUrl] = None
    is_public: bool = Field(False)
```

#### EventResponse
```python
class EventResponse(EventCreate):
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_days: int
    current_day: int
    is_happening_now: bool
    total_budget: float
    expenses_by_category: dict
```

### Agenda Schemas

#### EventAgendaCreate
```python
class EventAgendaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=128)
    day: int = Field(..., ge=1)
    start_time: datetime
    duration_minutes: int = Field(60, ge=1, le=1440)
```

### Expense Schemas

#### EventExpenseCreate
```python
class EventExpenseCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=256)
    amount: float = Field(..., ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)
```

### Media Schemas

#### EventMediaCreate
```python
class EventMediaCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    file_url: str
    file_type: str = Field(..., min_length=1, max_length=32)
    file_size: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
```

## Business Logic Features

### Event Management
- **Automatic Day Calculation**: Events automatically calculate total days and current day
- **Status Tracking**: Real-time "happening now" status based on current time
- **Budget Tracking**: Automatic calculation of total budget from expenses
- **Duplicate Prevention**: Prevents duplicate events with same title and start date

### Agenda Management (Deeds Module)
- **Day Validation**: Ensures agenda items don't exceed event duration
- **Time Management**: Automatic end time calculation based on duration
- **Flexible Duration**: Support for various time formats (hours, minutes)

### Expense Tracking (Deeds Module)
- **Category Management**: Flexible expense categorization
- **Currency Support**: Multi-currency support with USD default
- **Budget Analytics**: Automatic expense categorization and totals

### Media Management (Zone Module)
- **Tag System**: Flexible tagging for media categorization
- **File Type Support**: Support for various media types
- **Search Capabilities**: Tag-based search functionality

### Plug Integration
- **Many-to-Many Relationship**: Plugs can be associated with multiple events
- **Priority Management**: Priority levels for event-specific plug management
- **Notes System**: Event-specific notes for plugs

## Error Handling

### Validation Errors (400 Bad Request)
- Missing required fields
- Invalid data formats
- Business rule violations

### Business Logic Errors (422 Unprocessable Entity)
- Duplicate entries
- Invalid associations
- Constraint violations

### Not Found Errors (404 Not Found)
- Event not found
- Plug not found
- Access denied

## Security Features

### User Ownership
- All operations verify user ownership
- Users can only access their own events
- Plugs must belong to the user to be associated

### Data Validation
- Comprehensive Pydantic validation
- SQL injection prevention through SQLAlchemy ORM
- Input sanitization and type checking

## Performance Optimizations

### Database Indexing
- Primary keys on all tables
- Foreign key indexes for relationships
- Search indexes on frequently queried fields
- Composite indexes for complex queries

### Query Optimization
- Pagination for all list endpoints
- Efficient joins for related data
- Lazy loading for relationships
- Query result caching where appropriate

## Usage Examples

### Creating a Complete Event
```python
# 1. Create the event
event_data = EventCreate(
    title="Tech Conference 2025",
    theme="AI and Machine Learning",
    start_date=datetime(2025, 6, 15, 9, 0),
    end_date=datetime(2025, 6, 17, 18, 0),
    location_name="Convention Center",
    city="San Francisco",
    country="USA"
)
event = await event_service.create_event(user_id, event_data)

# 2. Add agenda items
agenda_data = EventAgendaCreate(
    title="Opening Keynote",
    day=1,
    start_time=datetime(2025, 6, 15, 9, 0),
    duration_minutes=60,
    location="Main Hall"
)
await event_service.create_agenda_item(user_id, event.id, agenda_data)

# 3. Add expenses
expense_data = EventExpenseCreate(
    category="Registration",
    amount=500.00,
    description="Early bird registration"
)
await event_service.create_expense(user_id, event.id, expense_data)

# 4. Add media
media_data = EventMediaCreate(
    title="Conference Photo",
    file_url="https://example.com/photo.jpg",
    file_type="image/jpeg",
    tags=["opening", "keynote"]
)
await event_service.create_media(user_id, event.id, media_data)

# 5. Associate plugs
plug_data = EventPlugCreate(
    plug_id=existing_plug_id,
    notes="Met during networking session",
    priority="high"
)
await event_service.add_plug_to_event(user_id, event.id, plug_data.plug_id, plug_data)
```

## Migration Commands

### Create Migration
```bash
docker exec the_plugs_api alembic revision --autogenerate -m "Add events module"
```

### Apply Migration
```bash
docker exec the_plugs_api alembic upgrade head
```

### Rollback Migration
```bash
docker exec the_plugs_api alembic downgrade -1
```

## Testing

### Unit Tests
- Model validation tests
- Service layer business logic tests
- Repository data access tests

### Integration Tests
- API endpoint tests
- Database integration tests
- Authentication and authorization tests

### End-to-End Tests
- Complete event workflow tests
- Cross-module integration tests
- Performance and load tests

## Future Enhancements

### Planned Features
- **Agenda Import**: Import agenda from external URLs
- **Real-time Updates**: WebSocket support for live updates
- **Advanced Analytics**: Detailed event analytics and reporting
- **Export Functionality**: Export events and data in various formats
- **Collaboration**: Multi-user event management
- **Templates**: Event templates for quick setup
- **Notifications**: Event reminders and updates

### Scalability Considerations
- **Database Sharding**: For large-scale deployments
- **Caching Layer**: Redis integration for improved performance
- **CDN Integration**: For media file delivery
- **Microservices**: Potential service separation for large deployments

## Conclusion

The Events Module provides a comprehensive solution for event management with a clean, scalable architecture. It follows FastAPI best practices and provides all the functionality shown in the mobile app screenshots. The implementation is production-ready and can be easily extended with additional features as needed.

The module successfully integrates with the existing Plugs system and provides a solid foundation for the complete event management platform.
