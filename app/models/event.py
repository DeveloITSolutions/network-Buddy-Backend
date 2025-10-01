"""
Event model for managing events and their associated modules.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, String, Text, 
    UniqueConstraint, CheckConstraint, Numeric
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Event(BaseModel):
    """
    Event model representing a conference, summit, or gathering.
    
    Events contain multiple modules:
    - Deeds: Agenda and expense management
    - Plugs: Associated contacts/targets
    - Zone: Media content
    - Tea: Additional features
    """
    
    __tablename__ = "events"
    
    # Basic event information
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True
    )
    
    theme: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Event timing
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Location information
    location_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True
    )
    
    location_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    
    state: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    
    country: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True
    )
    
    # Geographic coordinates (from Google Maps)
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 8),
        nullable=True,
        index=True
    )
    
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(11, 8),
        nullable=True,
        index=True
    )
    
    # Additional location metadata (Google Places data)
    location_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )
    
    # Event details
    website_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True
    )
    
    cover_image_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True
    )
    
    # Event status and settings
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="events")
    
    # Event modules
    agendas: Mapped[List["EventAgenda"]] = relationship(
        "EventAgenda",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventAgenda.day, EventAgenda.start_time"
    )
    
    expenses: Mapped[List["EventExpense"]] = relationship(
        "EventExpense",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventExpense.created_at.desc()"
    )
    
    media: Mapped[List["EventMedia"]] = relationship(
        "EventMedia",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventMedia.created_at.desc()"
    )
    
    media_zones: Mapped[List["EventMediaZone"]] = relationship(
        "EventMediaZone",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventMediaZone.created_at.desc()"
    )
    
    # Event-Plug associations (many-to-many)
    event_plugs: Mapped[List["EventPlug"]] = relationship(
        "EventPlug",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="check_end_after_start"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="check_longitude_range"),
        UniqueConstraint("user_id", "title", "start_date", name="unique_user_event"),
    )
    
    @property
    def total_days(self) -> int:
        """Calculate total number of event days."""
        if not self.start_date or not self.end_date:
            return 0
        return (self.end_date.date() - self.start_date.date()).days + 1
    
    @property
    def current_day(self) -> int:
        """Get current day of the event (1-based)."""
        if not self.start_date or not self.end_date:
            return 0
        
        now = datetime.now(self.start_date.tzinfo)
        if now < self.start_date:
            return 0
        elif now > self.end_date:
            return self.total_days
        else:
            return (now.date() - self.start_date.date()).days + 1
    
    @property
    def is_happening_now(self) -> bool:
        """Check if event is currently happening."""
        if not self.start_date or not self.end_date:
            return False
        
        now = datetime.now(self.start_date.tzinfo)
        return self.start_date <= now <= self.end_date
    
    @property
    def total_budget(self) -> float:
        """Calculate total budget from all expenses."""
        return sum(expense.amount for expense in self.expenses if not expense.is_deleted)
    
    @property
    def expenses_by_category(self) -> dict:
        """Get expenses grouped by category."""
        categories = {}
        for expense in self.expenses:
            if not expense.is_deleted:
                category = expense.category
                if category not in categories:
                    categories[category] = 0
                categories[category] += expense.amount
        return categories
    
    @property
    def has_coordinates(self) -> bool:
        """Check if event has valid coordinates."""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def coordinates(self) -> Optional[tuple]:
        """Get coordinates as a tuple (latitude, longitude)."""
        if self.has_coordinates:
            return (float(self.latitude), float(self.longitude))
        return None
    
    def set_coordinates(self, latitude: float, longitude: float, metadata: Optional[dict] = None) -> None:
        """
        Set event coordinates with validation.
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            metadata: Optional location metadata from Google Places
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        
        self.latitude = latitude
        self.longitude = longitude
        if metadata:
            self.location_metadata = metadata
    
    def get_google_maps_url(self) -> Optional[str]:
        """Generate Google Maps URL for the event location."""
        if not self.has_coordinates:
            return None
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
    
    def get_display_address(self) -> str:
        """Get formatted address for display."""
        address_parts = []
        if self.location_name:
            address_parts.append(self.location_name)
        if self.location_address:
            address_parts.append(self.location_address)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.country:
            address_parts.append(self.country)
        if self.postal_code:
            address_parts.append(self.postal_code)
        
        return ", ".join(address_parts) if address_parts else "Location not specified"
    
    @property
    def google_maps_url(self) -> Optional[str]:
        """Get Google Maps URL for the event location."""
        return self.get_google_maps_url()
    
    @property
    def display_address(self) -> str:
        """Get formatted address for display."""
        return self.get_display_address()
    
    @property
    def plug_counts(self) -> dict:
        """Get count of plugs by type (targets and contacts)."""
        from app.models.plug import PlugType
        
        target_count = 0
        contact_count = 0
        
        for event_plug in self.event_plugs:
            if not event_plug.is_deleted and event_plug.plug and not event_plug.plug.is_deleted:
                if event_plug.plug.plug_type == PlugType.TARGET:
                    target_count += 1
                elif event_plug.plug.plug_type == PlugType.CONTACT:
                    contact_count += 1
        
        return {
            "targets": target_count,
            "contacts": contact_count
        }


class EventAgenda(BaseModel):
    """
    Agenda items for events (Deeds module).
    """
    
    __tablename__ = "event_agendas"
    
    # Basic agenda information
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    location: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True
    )
    
    # Timing
    day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )
    
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False
    )
    
    # Event relationship
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="agendas")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("day > 0", name="check_positive_day"),
        CheckConstraint("duration_minutes > 0", name="check_positive_duration"),
    )
    
    @property
    def end_time(self) -> datetime:
        """Calculate end time based on start time and duration."""
        from datetime import timedelta
        return self.start_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def duration_display(self) -> str:
        """Get human-readable duration."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"


class EventExpense(BaseModel):
    """
    Expense tracking for events (Deeds module).
    """
    
    __tablename__ = "event_expenses"
    
    # Expense details
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True
    )
    
    amount: Mapped[float] = mapped_column(
        nullable=False,
        index=True
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    
    # Event relationship
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="expenses")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_non_negative_amount"),
    )


class EventMediaZone(BaseModel):
    """
    Zone metadata for grouped media uploads.
    Stores title, description, and tags once for the entire zone.
    """
    
    __tablename__ = "event_media_zones"
    
    # Zone metadata - stored once per zone
    title: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="Zone title applied to all media in this zone"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Zone description applied to all media in this zone"
    )
    
    tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated tags applied to all media in this zone"
    )
    
    # Event relationship
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="media_zones")
    media_files: Mapped[List["EventMedia"]] = relationship(
        "EventMedia",
        back_populates="zone",
        foreign_keys="EventMedia.zone_id",
        cascade="all, delete-orphan"
    )
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list."""
        self.tags = ",".join(tags) if tags else None


class EventMedia(BaseModel):
    """
    Media files for events (Zone module).
    Individual files with only file-specific data (no duplicated metadata).
    """
    
    __tablename__ = "event_media"
    
    # File-specific information only
    file_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="S3 URL for the media file"
    )
    
    s3_key: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        index=True,
        comment="S3 object key"
    )
    
    file_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="MIME type of the file"
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="File size in bytes"
    )
    
    # Zone relationship - links to zone metadata
    zone_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("event_media_zones.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Reference to zone metadata (title, description, tags)"
    )
    
    # Legacy batch_id for backward compatibility (deprecated, use zone_id)
    batch_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Deprecated: Use zone_id instead"
    )
    
    # Event relationship
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="media")
    zone: Mapped[Optional["EventMediaZone"]] = relationship(
        "EventMediaZone",
        back_populates="media_files",
        foreign_keys=[zone_id]
    )


class EventPlug(BaseModel):
    """
    Association table for Event-Plug relationships.
    """
    
    __tablename__ = "event_plugs"
    
    # Relationships
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    plug_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("plugs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Additional relationship data
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    priority: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="event_plugs")
    plug: Mapped["Plug"] = relationship("Plug")
    
    # Plug media relationship
    plug_media: Mapped[List["EventPlugMedia"]] = relationship(
        "EventPlugMedia",
        back_populates="event_plug",
        cascade="all, delete-orphan",
        order_by="EventPlugMedia.created_at.desc()"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("event_id", "plug_id", name="unique_event_plug"),
    )


class EventPlugMedia(BaseModel):
    """
    Media content (snaps/voice recordings) for specific plugs within events.
    Simple model with only essential fields for S3 file storage.
    """
    
    __tablename__ = "event_plug_media"
    
    # S3 file information
    file_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )
    
    s3_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True
    )
    
    file_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )
    
    # Media category: 'snap' for images, 'voice' for audio recordings
    media_category: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True
    )
    
    # Event and plug relationships
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    plug_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("plugs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    event_plug_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("event_plugs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event")
    plug: Mapped["Plug"] = relationship("Plug")
    event_plug: Mapped["EventPlug"] = relationship("EventPlug", back_populates="plug_media")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "media_category IN ('snap', 'voice')", 
            name="check_media_category"
        ),
    )
