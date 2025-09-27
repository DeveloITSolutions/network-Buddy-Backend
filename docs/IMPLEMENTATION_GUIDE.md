# The Plugs - Database Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the database schema based on the Figma designs and ERD documentation. It includes migration scripts, model definitions, and validation procedures.

## Prerequisites

- PostgreSQL 14+ database server
- Python 3.11+ with SQLAlchemy 2.0+
- Alembic for database migrations
- Redis for caching and session storage

## Implementation Phases

### Phase 1: Core Foundation (Week 1-2)

#### 1.1 Base Models and Mixins
```python
# app/models/base.py - Already implemented
# app/models/mixins.py - Already implemented
```

#### 1.2 Organizations and Users
**Priority**: Critical - Foundation for multi-tenancy

```sql
-- Migration: 001_create_organizations_and_users.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_crypto";

-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- Indexes
CREATE INDEX idx_organizations_domain ON organizations(domain) WHERE NOT is_deleted;
CREATE INDEX idx_users_organization ON users(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_users_email ON users(email) WHERE NOT is_deleted;
```

### Phase 2: Professional Networking (Week 3-4)

#### 2.1 Contacts and Interactions
**Priority**: High - Core business functionality

```sql
-- Migration: 002_create_contacts_and_interactions.sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

CREATE TABLE contact_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- Indexes
CREATE INDEX idx_contacts_organization ON contacts(organization_id) WHERE NOT is_deleted;
CREATE INDEX idx_contacts_type_status ON contacts(contact_type, status) WHERE NOT is_deleted;
CREATE INDEX idx_contact_interactions_contact ON contact_interactions(contact_id) WHERE NOT is_deleted;
```

### Phase 3: Event Management (Week 5-6)

#### 3.1 Events, Attendees, and Agenda
**Priority**: High - Key platform feature

```sql
-- Migration: 003_create_events_system.sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    
    CONSTRAINT events_date_range CHECK (end_date > start_date)
);

-- Event attendees and agenda tables...
-- [Full SQL provided in SCHEMA_DEFINITIONS.md]
```

### Phase 4: Media & Financial (Week 7-8)

#### 4.1 Media Management
**Priority**: Medium - Content organization

#### 4.2 Expense Tracking
**Priority**: Medium - Financial features

### Phase 5: Integration & Analytics (Week 9-10)

#### 5.1 Third-party Integrations
**Priority**: Low - Enhancement features

#### 5.2 Analytics and Audit
**Priority**: Medium - Business intelligence

## SQLAlchemy Model Implementation

### User Model Example
```python
# app/models/user.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .mixins import TenantEntityMixin

class User(BaseModel, TenantEntityMixin):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    # Profile fields
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    company: Mapped[Optional[str]] = mapped_column(String(100))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    created_contacts = relationship("Contact", foreign_keys="Contact.created_by", back_populates="creator")
    created_events = relationship("Event", foreign_keys="Event.created_by", back_populates="creator")
    uploaded_media = relationship("Media", foreign_keys="Media.uploaded_by", back_populates="uploader")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

### Contact Model Example
```python
# app/models/contact.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .mixins import TenantEntityMixin

class Contact(BaseModel, TenantEntityMixin):
    """Contact model for professional networking."""
    
    __tablename__ = "contacts"
    
    # Creator relationship
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # Basic information
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    company: Mapped[Optional[str]] = mapped_column(String(100))
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Classification
    contact_type: Mapped[str] = mapped_column(String(20), default="target")
    status: Mapped[str] = mapped_column(String(30), default="cold_lead")
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    business_type: Mapped[Optional[str]] = mapped_column(String(50))
    network_type: Mapped[Optional[str]] = mapped_column(String(50))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Networking data
    notes: Mapped[Optional[str]] = mapped_column(Text)
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_contacts")
    interactions = relationship("ContactInteraction", back_populates="contact", cascade="all, delete-orphan")
    related_media = relationship("Media", foreign_keys="Media.related_contact", back_populates="contact")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

## API Endpoint Implementation

### Contact Management Endpoints
```python
# app/api/v1/contacts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.services.contact_service import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    contact_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List contacts with filtering and pagination."""
    contact_service = ContactService(db)
    contacts = await contact_service.list_contacts(
        organization_id=current_user.organization_id,
        contact_type=contact_type,
        status=status,
        skip=skip,
        limit=limit
    )
    return contacts

@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new contact."""
    contact_service = ContactService(db)
    contact = await contact_service.create_contact(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        contact_data=contact_data
    )
    return contact

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get contact details with interaction history."""
    contact_service = ContactService(db)
    contact = await contact_service.get_contact_with_interactions(
        contact_id=contact_id,
        organization_id=current_user.organization_id
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_contact_model.py
import pytest
from app.models.contact import Contact
from app.models.user import User
from app.models.organization import Organization

def test_contact_creation(db_session, sample_organization, sample_user):
    """Test contact creation with required fields."""
    contact = Contact(
        organization_id=sample_organization.id,
        created_by=sample_user.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        contact_type="target"
    )
    db_session.add(contact)
    db_session.commit()
    
    assert contact.id is not None
    assert contact.full_name == "John Doe"
    assert contact.lead_score == 0
    assert contact.contact_type == "target"

def test_contact_lead_score_validation(db_session):
    """Test lead score constraints."""
    with pytest.raises(IntegrityError):
        contact = Contact(lead_score=150)  # Should fail (max 100)
        db_session.add(contact)
        db_session.commit()
```

### Integration Tests
```python
# tests/integration/test_contact_api.py
import pytest
from fastapi.testclient import TestClient

def test_create_contact_endpoint(client: TestClient, auth_headers):
    """Test contact creation via API."""
    contact_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "company": "Tech Corp",
        "contact_type": "target"
    }
    
    response = client.post(
        "/api/v1/contacts/",
        json=contact_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["contact_type"] == "target"
    assert data["lead_score"] == 0

def test_list_contacts_with_filters(client: TestClient, auth_headers):
    """Test contact listing with filters."""
    response = client.get(
        "/api/v1/contacts/?contact_type=plug&status=hot_lead",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

## Deployment Checklist

### Database Setup
- [ ] PostgreSQL 14+ installed and configured
- [ ] Database user created with appropriate permissions
- [ ] Extensions enabled (uuid-ossp, pg_crypto)
- [ ] Connection pooling configured
- [ ] Backup strategy implemented

### Migration Process
- [ ] Alembic configured with proper environment settings
- [ ] Migration scripts tested in staging environment
- [ ] Rollback procedures documented
- [ ] Data seeding scripts prepared

### Performance Optimization
- [ ] Indexes created on frequently queried columns
- [ ] Query performance analyzed and optimized
- [ ] Connection pooling tuned for expected load
- [ ] Caching strategy implemented

### Security
- [ ] Database credentials secured
- [ ] Row-level security policies defined
- [ ] SSL/TLS encryption enabled
- [ ] Audit logging configured

### Monitoring
- [ ] Database monitoring tools configured
- [ ] Performance metrics collection setup
- [ ] Alert thresholds defined
- [ ] Log aggregation implemented

## Maintenance Procedures

### Regular Tasks
1. **Weekly**: Analyze slow queries and optimize
2. **Monthly**: Review and clean up soft-deleted records
3. **Quarterly**: Database performance review and tuning
4. **Annually**: Major version upgrades and schema review

### Backup & Recovery
- Automated daily backups with point-in-time recovery
- Cross-region backup replication for disaster recovery
- Regular restore testing procedures
- Documentation of recovery procedures

---

*This implementation guide provides the complete roadmap for building The Plugs database infrastructure following enterprise best practices.*



















