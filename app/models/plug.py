"""
Plug model for target and contact management.
"""
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class PlugType(str, Enum):
    """Plug type enumeration."""
    TARGET = "target"
    CONTACT = "contact"


class NetworkType(str, Enum):
    """Network type enumeration - basic options, custom values via metadata."""
    NEW_CLIENT = "new_client"
    EXISTING_CLIENT = "existing_client"
    NEW_PARTNERSHIP = "new_partnership"
    EXISTING_PARTNERSHIP = "existing_partnership"
    VENDOR = "vendor"
    INVESTOR = "investor"
    MENTOR = "mentor"
    OTHER = "other"


class BusinessType(str, Enum):
    """Business type enumeration - basic options, custom values via metadata."""
    DERM_CLINIC = "derm_clinic"
    PHARMA_BIOTECH = "pharma_biotech"
    HOSPITAL_HEALTH_SYSTEM = "hospital_health_system"
    WELLNESS_CONSUMER_HEALTH = "wellness_consumer_health"
    CRO = "cro"
    PAYER = "payer"
    SALON = "salon"
    OTHER = "other"


class Priority(str, Enum):
    """Priority level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Plug(BaseModel):
    """
    Plug model representing both targets and contacts in the networking system.
    
    A plug can be either:
    - TARGET: Incomplete contact information, represents a potential connection
    - CONTACT: Complete contact information, represents an established connection
    
    Business Logic:
    - Targets are incomplete plugs that can be converted to contacts
    - Contacts have complete information and additional fields
    """
    
    __tablename__ = "plugs"
    
    # Foreign key to user who owns this plug
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this plug"
    )
    
    # Plug type - determines if this is a target or contact
    plug_type: Mapped[PlugType] = mapped_column(
        SQLEnum(PlugType),
        nullable=False,
        default=PlugType.TARGET,
        index=True,
        doc="Type of plug: target or contact"
    )
    
    # Basic contact information (optional per client request)
    first_name: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="Contact's first name"
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="Contact's last name"
    )
    
    # Optional contact information
    job_title: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Contact's job title"
    )
    
    profile_picture: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Profile picture URL"
    )
    
    company: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Company name"
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Contact's email address"
    )
    
    primary_number: Mapped[Optional[str]] = mapped_column(
        String(18),
        nullable=True,
        doc="Primary phone number"
    )
    
    secondary_number: Mapped[Optional[str]] = mapped_column(
        String(18),
        nullable=True,
        doc="Secondary phone number"
    )
    
    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="LinkedIn profile URL"
    )
    
    # Additional fields for contacts (only used when plug_type is CONTACT)
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Notes about the contact"
    )
    
    # Flexible custom data field for additional information
    custom_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Flexible custom data for network/business types and additional fields"
    )
    
    # HubSpot integration field
    hubspot_pipeline_stage: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="HubSpot pipeline stage for contacts"
    )
    
    network_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Type of network relationship (can be enum value or custom string)"
    )
    
    business_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Type of business (can be enum value or custom string)"
    )
    
    connect_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for connecting"
    )
    
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        doc="Tags associated with the contact"
    )
    
    priority: Mapped[Optional[Priority]] = mapped_column(
        SQLEnum(Priority),
        nullable=True,
        default=Priority.MEDIUM,
        doc="Priority level for the contact"
    )
    
    is_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this plug has been converted to a contact"
    )
    
    # Relationships
    user = relationship("User", back_populates="plugs")
    
    @property
    def full_name(self) -> str:
        """Get contact's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return self.full_name
    
    @property
    def is_target(self) -> bool:
        """Check if this plug is a target."""
        return self.plug_type == PlugType.TARGET
    
    @property
    def is_complete_contact(self) -> bool:
        """Check if this plug is a complete contact."""
        return self.plug_type == PlugType.CONTACT and self.is_contact
    
    def convert_to_contact(self) -> None:
        """Convert target to contact with complete information."""
        if self.plug_type == PlugType.TARGET:
            self.plug_type = PlugType.CONTACT
            self.is_contact = True
            # Set default values for contact-specific fields if not set
            if self.priority is None:
                self.priority = Priority.MEDIUM
            if self.network_type is None:
                self.network_type = NetworkType.NEW_CLIENT
    
    def revert_to_target(self) -> None:
        """Revert contact back to target (if needed)."""
        self.plug_type = PlugType.TARGET
        self.is_contact = False
        # Clear contact-specific fields
        self.notes = None
        self.connect_reason = None
        self.tags = None
    
    def is_complete_for_contact(self) -> bool:
        """
        Check if plug has minimum required information to be converted to contact.
        For conversion, we need at least: name, email or phone number.
        """
        has_contact_info = bool(self.email or self.primary_number)
        return bool(self.first_name and self.last_name and has_contact_info)
    
    def __repr__(self) -> str:
        """String representation of Plug."""
        return f"<Plug(id={self.id}, name={self.full_name}, type={self.plug_type})>"
