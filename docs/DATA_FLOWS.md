# The Plugs - Data Flows and Business Logic

## Overview

This document outlines the data flows and business logic for **The Plugs** platform based on the Figma UI designs. Each flow corresponds to specific user journeys and interactions shown in the mockups.

## 1. Authentication Flow

### 1.1 User Registration & Login (Screens 2.1-2.3)

**Flow**: Registration → Email Verification → Login → Dashboard

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant EmailService
    participant RedisCache

    User->>API: POST /auth/register
    API->>Database: Create user record (unverified)
    API->>EmailService: Send verification email
    API->>RedisCache: Store OTP with expiration
    API-->>User: Registration success + OTP sent

    User->>API: POST /auth/verify-email
    API->>RedisCache: Validate OTP
    API->>Database: Update user.is_verified = true
    API-->>User: Email verified

    User->>API: POST /auth/login
    API->>Database: Validate credentials
    API->>RedisCache: Store JWT tokens
    API-->>User: JWT tokens + user profile
```

**Database Operations**:
1. Insert into `users` table with `is_verified=false`
2. Store OTP in Redis with 10-minute expiration
3. Update `users.is_verified=true` on successful verification
4. Update `users.last_login` on successful login

### 1.2 Password Reset Flow (Screen 2.2)

**Flow**: Request Reset → Email Verification → New Password → Login

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant EmailService
    participant RedisCache

    User->>API: POST /auth/forgot-password
    API->>Database: Verify user exists
    API->>EmailService: Send reset email
    API->>RedisCache: Store reset token
    API-->>User: Reset email sent

    User->>API: POST /auth/reset-password
    API->>RedisCache: Validate reset token
    API->>Database: Update password_hash
    API-->>User: Password reset success
```

## 2. Dashboard Flow

### 2.1 Dashboard Data Loading (Screen 3)

**Data Components**:
- User statistics (Events: 16, Leads: 24, Contacts: 56, Media Drops: 88)
- Upcoming events
- Recent plugs/contacts
- Latest media drops

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant CacheService

    User->>API: GET /dashboard
    API->>CacheService: Check cached stats
    alt Cache Miss
        API->>Database: Query aggregated stats
        API->>CacheService: Cache for 5 minutes
    end
    API->>Database: Get recent events
    API->>Database: Get recent contacts
    API->>Database: Get recent media
    API-->>User: Dashboard data
```

**Database Queries**:
```sql
-- User statistics
SELECT 
    COUNT(CASE WHEN type = 'event' THEN 1 END) as events_count,
    COUNT(CASE WHEN type = 'contact' AND status = 'hot_lead' THEN 1 END) as leads_count,
    COUNT(CASE WHEN type = 'contact' THEN 1 END) as contacts_count,
    COUNT(CASE WHEN type = 'media' THEN 1 END) as media_count
FROM (
    SELECT 'event' as type, null as status FROM events WHERE organization_id = ? AND NOT is_deleted
    UNION ALL
    SELECT 'contact' as type, status FROM contacts WHERE organization_id = ? AND NOT is_deleted
    UNION ALL
    SELECT 'media' as type, null as status FROM media WHERE organization_id = ? AND NOT is_deleted
) stats;

-- Recent events
SELECT * FROM events 
WHERE organization_id = ? AND NOT is_deleted 
ORDER BY start_date ASC LIMIT 5;

-- Recent contacts
SELECT * FROM contacts 
WHERE organization_id = ? AND NOT is_deleted 
ORDER BY created_at DESC LIMIT 10;
```

## 3. Networking/Contact Management Flow

### 3.1 Contact Listing & Filtering (Screens 4.1-4.2)

**Flow**: View Targets/Contacts → Filter by Status → View Details

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database

    User->>API: GET /contacts?type=targets&status=new_client
    API->>Database: Query filtered contacts
    API-->>User: Paginated contact list

    User->>API: GET /contacts/{id}
    API->>Database: Get contact details + interactions
    API-->>User: Contact profile with history
```

**Database Operations**:
```sql
-- Filtered contact listing
SELECT c.*, COUNT(ci.id) as interaction_count,
       MAX(ci.interaction_date) as last_interaction
FROM contacts c
LEFT JOIN contact_interactions ci ON c.id = ci.contact_id AND NOT ci.is_deleted
WHERE c.organization_id = ? AND c.contact_type = ? 
  AND (? IS NULL OR c.status = ?)
  AND NOT c.is_deleted
GROUP BY c.id
ORDER BY c.updated_at DESC
LIMIT ? OFFSET ?;
```

### 3.2 Contact Conversion Flow (Screens 4.3-4.8)

**Flow**: Target → Contact → Plug → Lead Conversion

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant AnalyticsService

    User->>API: PUT /contacts/{id}/convert
    Note over API: Target → Contact
    API->>Database: Update contact_type, status
    API->>AnalyticsService: Track conversion event
    API-->>User: Contact converted

    User->>API: POST /contacts/{id}/interactions
    API->>Database: Create interaction record
    API->>Database: Update contact.last_interaction
    API->>Database: Update contact.lead_score
    API-->>User: Interaction logged

    User->>API: PUT /contacts/{id}/submit-plug
    API->>Database: Update status to 'plug'
    API->>Database: Create notification for team
    API-->>User: Plug submitted
```

### 3.3 Contact Profile Management (Screens 4.3-4.4)

**Data Structure**:
- Basic info (name, email, company, role)
- Professional details (LinkedIn, industry, business type)
- Networking classification (network type, priority)
- Interaction history
- Notes and metadata

```sql
-- Get complete contact profile
SELECT 
    c.*,
    u.first_name || ' ' || u.last_name as created_by_name,
    COUNT(ci.id) as total_interactions,
    MAX(ci.interaction_date) as last_interaction_date,
    STRING_AGG(DISTINCT ci.interaction_type, ', ') as interaction_types
FROM contacts c
JOIN users u ON c.created_by = u.id
LEFT JOIN contact_interactions ci ON c.id = ci.contact_id AND NOT ci.is_deleted
WHERE c.id = ? AND c.organization_id = ? AND NOT c.is_deleted
GROUP BY c.id, u.first_name, u.last_name;
```

## 4. Event Management Flow

### 4.1 Event Creation & Management (Screens 5.1-5.6)

**Flow**: Create Event → Add Agenda → Manage Attendees → Track Analytics

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant NotificationService

    User->>API: POST /events
    API->>Database: Create event record
    API-->>User: Event created

    User->>API: POST /events/{id}/agenda
    API->>Database: Create agenda items
    API-->>User: Agenda updated

    User->>API: POST /events/{id}/attendees
    API->>Database: Create attendee records
    API->>NotificationService: Send event invitations
    API-->>User: Attendees added
```

**Database Operations**:
```sql
-- Create event with agenda
INSERT INTO events (organization_id, created_by, title, description, start_date, end_date, ...)
VALUES (?, ?, ?, ?, ?, ?, ...);

-- Add agenda items
INSERT INTO event_agenda_items (organization_id, event_id, created_by, title, start_time, end_time, ...)
VALUES (?, ?, ?, ?, ?, ?, ...);

-- Register attendees
INSERT INTO event_attendees (organization_id, event_id, user_id, status)
VALUES (?, ?, ?, 'registered');
```

### 4.2 Event Analytics & Tracking (Screens 5.5-5.6)

**Metrics Tracked**:
- Attendance rates
- Check-in/check-out times
- Agenda participation
- Budget vs actual expenses

```sql
-- Event analytics query
SELECT 
    e.id,
    e.title,
    e.max_attendees,
    e.current_attendees,
    COUNT(CASE WHEN ea.status = 'attended' THEN 1 END) as actual_attendees,
    COUNT(CASE WHEN ea.status = 'no_show' THEN 1 END) as no_shows,
    SUM(exp.amount) as total_expenses,
    e.budget,
    (SUM(exp.amount) / NULLIF(e.budget, 0)) * 100 as budget_utilization
FROM events e
LEFT JOIN event_attendees ea ON e.id = ea.event_id AND NOT ea.is_deleted
LEFT JOIN expenses exp ON e.id = exp.event_id AND NOT exp.is_deleted
WHERE e.id = ? AND e.organization_id = ?
GROUP BY e.id;
```

## 5. Expense Management Flow

### 5.1 Expense Tracking (Screens 5.7-5.10)

**Flow**: Create Expense → Categorize → Submit for Approval → Track Status

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant FileStorage
    participant ApprovalService

    User->>API: POST /expenses
    Note over API: Include receipt upload
    API->>FileStorage: Store receipt file
    API->>Database: Create expense record
    API-->>User: Expense created

    User->>API: PUT /expenses/{id}/submit
    API->>Database: Update status to 'pending'
    API->>ApprovalService: Notify approvers
    API-->>User: Submitted for approval

    Note over ApprovalService: Manager approves
    ApprovalService->>API: PUT /expenses/{id}/approve
    API->>Database: Update status, approved_by, approved_at
    API-->>User: Expense approved
```

**Database Operations**:
```sql
-- Create expense with file reference
INSERT INTO expenses (
    organization_id, created_by, event_id, title, description,
    amount, currency, category, expense_type, expense_date,
    receipt_url, status
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending');

-- Approve expense
UPDATE expenses 
SET status = 'approved', approved_by = ?, approved_at = NOW()
WHERE id = ? AND organization_id = ?;
```

## 6. Media Management Flow

### 6.1 Media Upload & Organization (Screens 5.11-5.17)

**Flow**: Upload Media → Process/Optimize → Organize in Collections → Associate with Events/Contacts

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant FileStorage
    participant MediaProcessor

    User->>API: POST /media/upload
    API->>FileStorage: Store original file
    API->>Database: Create media record (status: processing)
    API->>MediaProcessor: Queue for processing
    API-->>User: Upload initiated

    MediaProcessor->>FileStorage: Generate thumbnails/optimized versions
    MediaProcessor->>Database: Update media status to 'ready'
    MediaProcessor->>API: Notify processing complete

    User->>API: POST /media/collections
    API->>Database: Create collection
    API-->>User: Collection created

    User->>API: POST /media/collections/{id}/items
    API->>Database: Add media to collection
    API-->>User: Media organized
```

### 6.2 Media Associations (Screens 5.12-5.16)

**Associations**:
- Event photos/videos
- Contact profile images
- General media library
- Snap collections (fleeting content)

```sql
-- Associate media with event
UPDATE media 
SET related_event = ?, access_level = 'organization'
WHERE id = ? AND organization_id = ?;

-- Create media collection for event
INSERT INTO media_collections (organization_id, created_by, name, collection_type)
VALUES (?, ?, 'Event Photos - ' || ?, 'event_photos');

-- Add media to collection
INSERT INTO media_collection_items (collection_id, media_id, sort_order)
VALUES (?, ?, ?);
```

## 7. Integration & Sync Flow

### 7.1 HubSpot Sync (Screens 5.22-5.23)

**Flow**: Configure Integration → Sync Contacts → Export Data → Monitor Status

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    participant HubSpotAPI
    participant BackgroundJob

    User->>API: POST /integrations/hubspot/configure
    API->>Database: Store credentials (encrypted)
    API->>HubSpotAPI: Test connection
    API-->>User: Integration configured

    User->>API: POST /integrations/hubspot/sync
    API->>BackgroundJob: Queue sync job
    API-->>User: Sync initiated

    BackgroundJob->>Database: Get contacts to sync
    BackgroundJob->>HubSpotAPI: Sync contact data
    BackgroundJob->>Database: Log sync results
    BackgroundJob->>API: Notify completion
```

**Database Operations**:
```sql
-- Store integration configuration
INSERT INTO integrations (
    organization_id, provider, integration_type, 
    credentials, settings, status
) VALUES (?, 'hubspot', 'crm', ?, ?, 'connected');

-- Log sync operation
INSERT INTO integration_logs (
    organization_id, integration_id, operation, status,
    started_at, records_processed, records_failed
) VALUES (?, ?, 'sync', 'success', ?, ?, ?);
```

### 7.2 CSV Export Flow (Screen 5.22)

**Export Types**:
- Contact lists with interaction history
- Event attendee lists
- Expense reports
- Media inventory

```sql
-- Export contacts with interaction summary
SELECT 
    c.first_name, c.last_name, c.email, c.company, c.job_title,
    c.contact_type, c.status, c.priority, c.lead_score,
    COUNT(ci.id) as total_interactions,
    MAX(ci.interaction_date) as last_interaction,
    STRING_AGG(ci.interaction_type, ', ') as interaction_types
FROM contacts c
LEFT JOIN contact_interactions ci ON c.id = ci.contact_id AND NOT ci.is_deleted
WHERE c.organization_id = ? AND NOT c.is_deleted
GROUP BY c.id
ORDER BY c.last_name, c.first_name;
```

## 8. Notification & Communication Flow

### 8.1 Real-time Notifications

**Notification Types**:
- Event reminders
- Contact interaction updates
- Expense approval status
- System alerts

```mermaid
sequenceDiagram
    participant System
    participant API
    participant Database
    participant NotificationService
    participant User

    System->>API: Trigger notification event
    API->>Database: Create notification record
    API->>NotificationService: Send via channels (in-app, email, push)
    NotificationService-->>User: Deliver notification

    User->>API: GET /notifications
    API->>Database: Get user notifications
    API-->>User: Notification list

    User->>API: PUT /notifications/{id}/read
    API->>Database: Mark as read
    API-->>User: Notification updated
```

## Performance Optimization

### Caching Strategy
- Dashboard statistics: 5-minute cache
- User profile data: 30-minute cache
- Event lists: 10-minute cache
- Media thumbnails: 24-hour cache

### Database Optimization
- Composite indexes on `(organization_id, created_at)`
- Full-text search indexes on contact/event names
- Partitioning for analytics and audit tables
- Read replicas for reporting queries

### Background Processing
- Media processing (thumbnails, optimization)
- Email notifications
- Data synchronization
- Analytics aggregation

---

*This data flow documentation provides comprehensive coverage of all user journeys and system interactions shown in the Figma designs.*
