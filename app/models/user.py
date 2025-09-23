"""
User model for authentication and user management.
"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from .base import BaseModel

if TYPE_CHECKING:
    from .plug import Plug


class User(BaseModel):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="User email address (unique)"
    )
    
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User password"
    )
    
    # Profile fields
    first_name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="User first name"
    )
    
    last_name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="User last name"
    )
    
    # Optional profile fields
    profile_picture: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        doc="User profile picture URL"
    )
    
    primary_number: Mapped[str] = mapped_column(
        String(18),
        nullable=True,
        doc="Primary phone number"
    )
    
    secondary_number: Mapped[str] = mapped_column(
        String(18),
        nullable=True,
        doc="Secondary phone number"
    )
    
    # Required fields
    timezone: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="UTC",
        doc="User timezone"
    )
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="User active status"
    )
    
    # Relationships
    plugs: Mapped[List["Plug"]] = relationship(
        "Plug",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's plugs (targets and contacts)"
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return self.full_name
    
    def can_login(self) -> bool:
        """Check if user can log in."""
        return self.is_active and not self.is_deleted
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = self._get_current_utc_time()
    
    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.updated_at = self._get_current_utc_time()
    
    def _get_current_utc_time(self):
        """Get current UTC time using common utility."""
        from app.utils.datetime import get_current_utc_time
        return get_current_utc_time()
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"


