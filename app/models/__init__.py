"""
Database models package.

This package contains all SQLAlchemy models and mixins for the application.
"""

from .base import BaseModel
from .mixins import (
    AuditMixin,
    AuditableEntityMixin,
    BaseEntityMixin,
    FullEntityMixin,
    MetadataMixin,
    SoftDeleteMixin,
    TenantEntityMixin,
    TenantMixin,
    TimestampMixin,
)
from .user import User
from .plug import Plug, PlugType, NetworkType, BusinessType, Priority
from .event import Event, EventAgenda, EventExpense, EventMedia, EventPlug, EventPlugMedia

__all__ = [
    # Base model
    "BaseModel",
    # Individual mixins
    "TimestampMixin",
    "SoftDeleteMixin", 
    "AuditMixin",
    "TenantMixin",
    "MetadataMixin",
    # Mixin combinations
    "BaseEntityMixin",
    "AuditableEntityMixin",
    "TenantEntityMixin",
    "FullEntityMixin",
    # Models
    "User",
    "Plug",
    "Event",
    "EventAgenda", 
    "EventExpense",
    "EventMedia",
    "EventPlug",
    "EventPlugMedia",
    # Enums
    "PlugType",
    "NetworkType", 
    "BusinessType",
    "Priority",
]