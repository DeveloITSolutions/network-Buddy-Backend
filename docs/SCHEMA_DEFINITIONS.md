# The Plugs - Detailed Schema Definitions

## Table Definitions

### Core Entities

#### 1. organizations
**Purpose**: Multi-tenant organization management
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_organizations_domain ON organizations(domain) WHERE NOT is_deleted;
CREATE INDEX idx_organizations_active ON organizations(is_active) WHERE NOT is_deleted;
```

#### 2. users
**Purpose**: User authentication and profile management
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    bio TEXT,
    avatar_url VARCHAR(500),
    job_title VARCHAR(100),
    company VARCHAR(100),
    linkedin_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_admin BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    CONSTRAINT users_unique_email_per_org UNIQUE(organization_id, email)
);

CREATE INDEX idx_users_organization ON users(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_users_email ON users(email) WHERE NOT is_deleted;
CREATE INDEX idx_users_active ON users(is_active, is_verified) WHERE NOT is_deleted;
```

#### 3. contacts
**Purpose**: Professional networking contact management
```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    company VARCHAR(100),
    job_title VARCHAR(100),
    linkedin_url VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    contact_type VARCHAR(20) CHECK (contact_type IN ('target', 'contact', 'plug')) DEFAULT 'target',
    status VARCHAR(30) CHECK (status IN ('new_client', 'existing_client', 'hot_lead', 'cold_lead')) DEFAULT 'cold_lead',
    priority VARCHAR(10) CHECK (priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
    business_type VARCHAR(50),
    network_type VARCHAR(50),
    industry VARCHAR(100),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
    last_interaction TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_contacts_organization ON contacts(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_contacts_created_by ON contacts(created_by) WHERE NOT is_deleted;
CREATE INDEX idx_contacts_type_status ON contacts(contact_type, status) WHERE NOT is_deleted;
CREATE INDEX idx_contacts_email ON contacts(email) WHERE NOT is_deleted AND email IS NOT NULL;
CREATE INDEX idx_contacts_company ON contacts(company) WHERE NOT is_deleted AND company IS NOT NULL;
CREATE INDEX idx_contacts_lead_score ON contacts(lead_score DESC) WHERE NOT is_deleted;
```

#### 4. contact_interactions
**Purpose**: Track networking activities and relationship building
```sql
CREATE TABLE contact_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    interaction_type VARCHAR(20) CHECK (interaction_type IN ('meeting', 'call', 'email', 'linkedin', 'event', 'follow_up')) NOT NULL,
    subject VARCHAR(255),
    description TEXT,
    outcome TEXT,
    interaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('completed', 'scheduled', 'cancelled')) DEFAULT 'completed',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_contact_interactions_contact ON contact_interactions(contact_id) WHERE NOT is_deleted;
CREATE INDEX idx_contact_interactions_user ON contact_interactions(user_id) WHERE NOT is_deleted;
CREATE INDEX idx_contact_interactions_date ON contact_interactions(interaction_date DESC) WHERE NOT is_deleted;
CREATE INDEX idx_contact_interactions_type ON contact_interactions(interaction_type) WHERE NOT is_deleted;
```

### Event Management

#### 5. events
**Purpose**: Event creation and management
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(20) CHECK (event_type IN ('conference', 'workshop', 'networking', 'meeting')) DEFAULT 'networking',
    status VARCHAR(20) CHECK (status IN ('draft', 'published', 'ongoing', 'completed', 'cancelled')) DEFAULT 'draft',
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    location VARCHAR(255),
    venue VARCHAR(255),
    venue_details JSONB DEFAULT '{}',
    budget DECIMAL(12,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    max_attendees INTEGER,
    current_attendees INTEGER DEFAULT 0,
    registration_url VARCHAR(500),
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID REFERENCES users(id),
    
    CONSTRAINT events_date_range CHECK (end_date > start_date),
    CONSTRAINT events_attendees_check CHECK (current_attendees >= 0 AND (max_attendees IS NULL OR current_attendees <= max_attendees))
);

CREATE INDEX idx_events_organization ON events(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_events_created_by ON events(created_by) WHERE NOT is_deleted;
CREATE INDEX idx_events_status ON events(status) WHERE NOT is_deleted;
CREATE INDEX idx_events_date_range ON events(start_date, end_date) WHERE NOT is_deleted;
CREATE INDEX idx_events_type ON events(event_type) WHERE NOT is_deleted;
```

#### 6. event_attendees
**Purpose**: Event participation tracking
```sql
CREATE TABLE event_attendees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) CHECK (status IN ('registered', 'confirmed', 'attended', 'no_show', 'cancelled')) DEFAULT 'registered',
    registration_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    check_in_time TIMESTAMP WITH TIME ZONE,
    check_out_time TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT event_attendees_unique UNIQUE(event_id, user_id),
    CONSTRAINT event_attendees_checkin_checkout CHECK (check_out_time IS NULL OR check_in_time IS NOT NULL)
);

CREATE INDEX idx_event_attendees_event ON event_attendees(event_id) WHERE NOT is_deleted;
CREATE INDEX idx_event_attendees_user ON event_attendees(user_id) WHERE NOT is_deleted;
CREATE INDEX idx_event_attendees_status ON event_attendees(status) WHERE NOT is_deleted;
```

#### 7. event_agenda_items
**Purpose**: Detailed event agenda management
```sql
CREATE TABLE event_agenda_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    agenda_type VARCHAR(20) CHECK (agenda_type IN ('presentation', 'break', 'networking', 'workshop')) DEFAULT 'presentation',
    location VARCHAR(255),
    speaker_id UUID REFERENCES users(id),
    sort_order INTEGER DEFAULT 0,
    status VARCHAR(20) CHECK (status IN ('scheduled', 'ongoing', 'completed', 'cancelled')) DEFAULT 'scheduled',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT agenda_time_range CHECK (end_time > start_time)
);

CREATE INDEX idx_agenda_items_event ON event_agenda_items(event_id, sort_order) WHERE NOT is_deleted;
CREATE INDEX idx_agenda_items_speaker ON event_agenda_items(speaker_id) WHERE NOT is_deleted;
CREATE INDEX idx_agenda_items_time ON event_agenda_items(start_time) WHERE NOT is_deleted;
```

### Financial Management

#### 8. expenses
**Purpose**: Financial tracking for events and activities
```sql
CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    event_id UUID REFERENCES events(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    category VARCHAR(50),
    expense_type VARCHAR(20) CHECK (expense_type IN ('travel', 'accommodation', 'catering', 'venue', 'marketing', 'other')) DEFAULT 'other',
    expense_date DATE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected', 'paid')) DEFAULT 'pending',
    receipt_url VARCHAR(500),
    notes TEXT,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_expenses_organization ON expenses(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_expenses_event ON expenses(event_id) WHERE NOT is_deleted;
CREATE INDEX idx_expenses_created_by ON expenses(created_by) WHERE NOT is_deleted;
CREATE INDEX idx_expenses_status ON expenses(status) WHERE NOT is_deleted;
CREATE INDEX idx_expenses_date ON expenses(expense_date DESC) WHERE NOT is_deleted;
CREATE INDEX idx_expenses_amount ON expenses(amount DESC) WHERE NOT is_deleted;
```

### Media Management

#### 9. media
**Purpose**: File and media storage management
```sql
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500),
    media_type VARCHAR(20) CHECK (media_type IN ('image', 'video', 'document', 'audio')) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) CHECK (status IN ('processing', 'ready', 'failed')) DEFAULT 'processing',
    related_event UUID REFERENCES events(id),
    related_contact UUID REFERENCES contacts(id),
    access_level VARCHAR(20) CHECK (access_level IN ('public', 'private', 'organization')) DEFAULT 'organization',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_media_organization ON media(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_media_uploaded_by ON media(uploaded_by) WHERE NOT is_deleted;
CREATE INDEX idx_media_type ON media(media_type) WHERE NOT is_deleted;
CREATE INDEX idx_media_related_event ON media(related_event) WHERE NOT is_deleted;
CREATE INDEX idx_media_related_contact ON media(related_contact) WHERE NOT is_deleted;
CREATE INDEX idx_media_access_level ON media(access_level) WHERE NOT is_deleted;
```

#### 10. media_collections
**Purpose**: Organized media groupings
```sql
CREATE TABLE media_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    collection_type VARCHAR(20) CHECK (collection_type IN ('event_photos', 'contact_media', 'general')) DEFAULT 'general',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_media_collections_organization ON media_collections(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_media_collections_created_by ON media_collections(created_by) WHERE NOT is_deleted;
```

#### 11. media_collection_items
**Purpose**: Media to collection mapping
```sql
CREATE TABLE media_collection_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES media_collections(id) ON DELETE CASCADE,
    media_id UUID NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT media_collection_items_unique UNIQUE(collection_id, media_id)
);

CREATE INDEX idx_media_collection_items_collection ON media_collection_items(collection_id, sort_order);
CREATE INDEX idx_media_collection_items_media ON media_collection_items(media_id);
```

### Communication & Notifications

#### 12. notifications
**Purpose**: Real-time user notifications
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(20) CHECK (notification_type IN ('info', 'success', 'warning', 'error', 'reminder')) DEFAULT 'info',
    channel VARCHAR(20) CHECK (channel IN ('in_app', 'email', 'sms', 'push')) DEFAULT 'in_app',
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read) WHERE NOT is_deleted;
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC) WHERE NOT is_deleted;
CREATE INDEX idx_notifications_expires_at ON notifications(expires_at) WHERE NOT is_deleted AND expires_at IS NOT NULL;
```

### System Integration

#### 13. integrations
**Purpose**: Third-party system integrations
```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider VARCHAR(50) CHECK (provider IN ('hubspot', 'mailchimp', 'zoom', 'teams')) NOT NULL,
    integration_type VARCHAR(20) CHECK (integration_type IN ('crm', 'email', 'video', 'calendar')) NOT NULL,
    credentials JSONB NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) CHECK (status IN ('connected', 'disconnected', 'error')) DEFAULT 'disconnected',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT integrations_unique_provider UNIQUE(organization_id, provider)
);

CREATE INDEX idx_integrations_organization ON integrations(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_integrations_provider ON integrations(provider) WHERE NOT is_deleted;
CREATE INDEX idx_integrations_status ON integrations(status) WHERE NOT is_deleted;
```

#### 14. integration_logs
**Purpose**: Integration operation tracking
```sql
CREATE TABLE integration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    operation VARCHAR(20) CHECK (operation IN ('sync', 'export', 'import', 'webhook')) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('success', 'failed', 'partial')) NOT NULL,
    message TEXT,
    request_data JSONB,
    response_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integration_logs_integration ON integration_logs(integration_id, started_at DESC);
CREATE INDEX idx_integration_logs_status ON integration_logs(status, started_at DESC);
CREATE INDEX idx_integration_logs_operation ON integration_logs(operation, started_at DESC);
```

### Analytics & Audit

#### 15. analytics_events
**Purpose**: User behavior and platform analytics
```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    event_name VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    properties JSONB DEFAULT '{}',
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analytics_events_organization ON analytics_events(organization_id, event_timestamp DESC);
CREATE INDEX idx_analytics_events_user ON analytics_events(user_id, event_timestamp DESC);
CREATE INDEX idx_analytics_events_name ON analytics_events(event_name, event_timestamp DESC);
CREATE INDEX idx_analytics_events_category ON analytics_events(event_category, event_timestamp DESC);
```

#### 16. audit_logs
**Purpose**: Complete audit trail for compliance
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) CHECK (action IN ('create', 'update', 'delete', 'restore')) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_organization ON audit_logs(organization_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
```

## Views and Functions

### Business Intelligence Views

```sql
-- Contact Performance View
CREATE VIEW contact_performance_summary AS
SELECT 
    c.organization_id,
    c.contact_type,
    c.status,
    COUNT(*) as total_contacts,
    AVG(c.lead_score) as avg_lead_score,
    COUNT(ci.id) as total_interactions,
    MAX(ci.interaction_date) as last_interaction_date
FROM contacts c
LEFT JOIN contact_interactions ci ON c.id = ci.contact_id AND NOT ci.is_deleted
WHERE NOT c.is_deleted
GROUP BY c.organization_id, c.contact_type, c.status;

-- Event Analytics View
CREATE VIEW event_analytics AS
SELECT 
    e.organization_id,
    e.event_type,
    e.status,
    COUNT(*) as event_count,
    AVG(e.current_attendees) as avg_attendees,
    SUM(exp.amount) as total_expenses,
    AVG(exp.amount) as avg_expense_per_event
FROM events e
LEFT JOIN expenses exp ON e.id = exp.event_id AND NOT exp.is_deleted
WHERE NOT e.is_deleted
GROUP BY e.organization_id, e.event_type, e.status;
```

---

*These schema definitions provide the complete data structure for The Plugs enterprise networking platform with proper constraints, indexes, and relationships.*
































