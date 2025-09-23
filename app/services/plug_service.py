"""
Service layer for plug (target/contact) business logic.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.plug import Plug, PlugType, NetworkType, BusinessType, Priority
from app.repositories.plug_repository import PlugRepository
from app.schemas.plug import (
    TargetCreate, TargetUpdate, ContactCreate, ContactUpdate,
    TargetToContactConversion, PlugFilters, PlugStats
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PlugService(BaseService[Plug]):
    """
    Service for plug business logic handling targets and contacts.
    
    Implements SOLID principles:
    - Single Responsibility: Handles plug-related business logic
    - Open/Closed: Extensible for new plug types
    - Liskov Substitution: Adheres to base service contract
    - Interface Segregation: Focused methods for specific operations
    - Dependency Inversion: Depends on repository abstraction
    """

    def __init__(self, db: Session):
        """Initialize plug service with dependencies."""
        super().__init__(db)
        self.repository = PlugRepository(db)

    def get_model_class(self) -> type[Plug]:
        """Get the Plug model class."""
        return Plug

    # Target Operations
    async def create_target(self, user_id: UUID, target_data: TargetCreate) -> Plug:
        """
        Create a new target with business validation.
        
        Args:
            user_id: Owner user ID
            target_data: Target creation data
            
        Returns:
            Created target
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate business rules
            await self._validate_target_creation(user_id, target_data)
            
            # Convert schema to dict
            target_dict = target_data.model_dump(exclude_unset=True)
            
            # Create target through repository
            target = await self.repository.create_target(user_id, target_dict)
            
            logger.info(f"Created target {target.id} for user {user_id}")
            return target
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating target for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to create target",
                error_code="TARGET_CREATION_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def update_target(
        self,
        user_id: UUID,
        target_id: UUID,
        update_data: TargetUpdate
    ) -> Optional[Plug]:
        """
        Update an existing target.
        
        Args:
            user_id: Owner user ID
            target_id: Target ID
            update_data: Update data
            
        Returns:
            Updated target or None if not found
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify ownership and existence
            target = await self._verify_user_plug_ownership(user_id, target_id)
            if not target:
                return None
            
            # Verify it's a target
            if target.plug_type != PlugType.TARGET:
                raise ValidationError(
                    "Can only update targets with this endpoint",
                    error_code="INVALID_PLUG_TYPE"
                )
            
            # Validate business rules
            await self._validate_target_update(target, update_data)
            
            # Convert schema to dict, excluding unset fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Update through repository
            updated_target = await self.repository.update(target_id, update_dict)
            
            logger.info(f"Updated target {target_id} for user {user_id}")
            return updated_target
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating target {target_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to update target",
                error_code="TARGET_UPDATE_FAILED",
                details={"target_id": str(target_id), "user_id": str(user_id), "error": str(e)}
            )

    # Contact Operations
    async def create_contact(self, user_id: UUID, contact_data: ContactCreate) -> Plug:
        """
        Create a new contact with business validation.
        
        Args:
            user_id: Owner user ID
            contact_data: Contact creation data
            
        Returns:
            Created contact
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate business rules
            await self._validate_contact_creation(user_id, contact_data)
            
            # Convert schema to dict
            contact_dict = contact_data.model_dump(exclude_unset=True)
            
            # Create contact through repository
            contact = await self.repository.create_contact(user_id, contact_dict)
            
            logger.info(f"Created contact {contact.id} for user {user_id}")
            return contact
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating contact for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to create contact",
                error_code="CONTACT_CREATION_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def update_contact(
        self,
        user_id: UUID,
        contact_id: UUID,
        update_data: ContactUpdate
    ) -> Optional[Plug]:
        """
        Update an existing contact.
        
        Args:
            user_id: Owner user ID
            contact_id: Contact ID
            update_data: Update data
            
        Returns:
            Updated contact or None if not found
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify ownership and existence
            contact = await self._verify_user_plug_ownership(user_id, contact_id)
            if not contact:
                return None
            
            # Verify it's a contact
            if contact.plug_type != PlugType.CONTACT:
                raise ValidationError(
                    "Can only update contacts with this endpoint",
                    error_code="INVALID_PLUG_TYPE"
                )
            
            # Validate business rules
            await self._validate_contact_update(contact, update_data)
            
            # Convert schema to dict, excluding unset fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Update through repository
            updated_contact = await self.repository.update(contact_id, update_dict)
            
            logger.info(f"Updated contact {contact_id} for user {user_id}")
            return updated_contact
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating contact {contact_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to update contact",
                error_code="CONTACT_UPDATE_FAILED",
                details={"contact_id": str(contact_id), "user_id": str(user_id), "error": str(e)}
            )

    # Conversion Operations
    async def convert_target_to_contact(
        self,
        user_id: UUID,
        target_id: UUID,
        conversion_data: TargetToContactConversion
    ) -> Optional[Plug]:
        """
        Convert a target to a contact with additional information.
        
        Args:
            user_id: Owner user ID
            target_id: Target ID
            conversion_data: Conversion data
            
        Returns:
            Converted contact or None if target not found
            
        Raises:
            ValidationError: If conversion is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify ownership and existence
            target = await self._verify_user_plug_ownership(user_id, target_id)
            if not target:
                return None
            
            # Validate conversion eligibility
            await self._validate_target_conversion(target, conversion_data)
            
            # Convert schema to dict
            conversion_dict = conversion_data.model_dump(exclude_unset=True)
            
            # Perform conversion through repository
            contact = await self.repository.convert_target_to_contact(target_id, conversion_dict)
            
            logger.info(f"Converted target {target_id} to contact for user {user_id}")
            return contact
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error converting target {target_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to convert target to contact",
                error_code="TARGET_CONVERSION_FAILED",
                details={"target_id": str(target_id), "user_id": str(user_id), "error": str(e)}
            )

    # Query Operations
    async def get_user_plug(self, user_id: UUID, plug_id: UUID) -> Optional[Plug]:
        """
        Get a specific plug for a user.
        
        Args:
            user_id: Owner user ID
            plug_id: Plug ID
            
        Returns:
            Plug if found and owned by user, None otherwise
        """
        try:
            return await self._verify_user_plug_ownership(user_id, plug_id)
        except Exception as e:
            logger.error(f"Error getting plug {plug_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to get plug",
                error_code="PLUG_RETRIEVAL_FAILED",
                details={"plug_id": str(plug_id), "user_id": str(user_id), "error": str(e)}
            )

    async def get_user_plugs(
        self,
        user_id: UUID,
        filters: Optional[PlugFilters] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Plug], int]:
        """
        Get paginated list of user's plugs with filtering.
        
        Args:
            user_id: Owner user ID
            filters: Filter criteria
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (plugs list, total count)
        """
        try:
            # Build filter dictionary
            filter_dict = {}
            if filters:
                # Convert filters to repository format
                filter_dict = await self._build_filter_dict(filters)
            
            # Get plugs and count
            plugs = await self.repository.get_user_plugs(
                user_id=user_id,
                plug_type=filters.plug_type if filters else None,
                skip=skip,
                limit=limit,
                filters=filter_dict
            )
            
            total_count = await self.repository.count_user_plugs(
                user_id=user_id,
                plug_type=filters.plug_type if filters else None,
                filters=filter_dict
            )
            
            return plugs, total_count
            
        except Exception as e:
            logger.error(f"Error getting plugs for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to get user plugs",
                error_code="USER_PLUGS_RETRIEVAL_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def search_user_plugs(
        self,
        user_id: UUID,
        search_term: str,
        plug_type: Optional[PlugType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Plug]:
        """
        Search user's plugs by term.
        
        Args:
            user_id: Owner user ID
            search_term: Search term
            plug_type: Filter by plug type
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of matching plugs
        """
        try:
            # Validate search term
            if not search_term or len(search_term.strip()) < 2:
                raise ValidationError(
                    "Search term must be at least 2 characters",
                    error_code="INVALID_SEARCH_TERM"
                )
            
            return await self.repository.search_user_plugs(
                user_id=user_id,
                search_term=search_term.strip(),
                plug_type=plug_type,
                skip=skip,
                limit=limit
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error searching plugs for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to search user plugs",
                error_code="PLUG_SEARCH_FAILED",
                details={"user_id": str(user_id), "search_term": search_term, "error": str(e)}
            )

    async def delete_plug(self, user_id: UUID, plug_id: UUID) -> bool:
        """
        Delete a user's plug (soft delete).
        
        Args:
            user_id: Owner user ID
            plug_id: Plug ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Verify ownership
            plug = await self._verify_user_plug_ownership(user_id, plug_id)
            if not plug:
                return False
            
            # Perform soft delete
            return await self.repository.delete(plug_id, soft=True)
            
        except Exception as e:
            logger.error(f"Error deleting plug {plug_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to delete plug",
                error_code="PLUG_DELETION_FAILED",
                details={"plug_id": str(plug_id), "user_id": str(user_id), "error": str(e)}
            )

    async def get_user_plug_stats(self, user_id: UUID) -> PlugStats:
        """
        Get statistics about user's plugs.
        
        Args:
            user_id: User ID
            
        Returns:
            Plug statistics
        """
        try:
            stats_data = await self.repository.get_user_plug_stats(user_id)
            return PlugStats(**stats_data)
            
        except Exception as e:
            logger.error(f"Error getting plug stats for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to get plug statistics",
                error_code="PLUG_STATS_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

    # Private Validation Methods
    async def _verify_user_plug_ownership(self, user_id: UUID, plug_id: UUID) -> Optional[Plug]:
        """Verify that the plug belongs to the user."""
        plug = await self.repository.get(plug_id)
        if plug and plug.user_id != user_id:
            raise ValidationError(
                "Plug not found or access denied",
                error_code="PLUG_ACCESS_DENIED"
            )
        return plug

    async def _validate_target_creation(self, user_id: UUID, target_data: TargetCreate) -> None:
        """Validate target creation business rules."""
        # Check for duplicate targets based on name and company
        if target_data.company:
            existing_targets = await self.repository.find_by({
                "user_id": user_id,
                "first_name": target_data.first_name,
                "last_name": target_data.last_name,
                "company": target_data.company,
                "plug_type": PlugType.TARGET
            }, limit=1)
            
            if existing_targets:
                raise ValidationError(
                    "Target with this name and company already exists",
                    error_code="DUPLICATE_TARGET"
                )

    async def _validate_target_update(self, target: Plug, update_data: TargetUpdate) -> None:
        """Validate target update business rules."""
        # Additional validation can be added here
        pass

    async def _validate_contact_creation(self, user_id: UUID, contact_data: ContactCreate) -> None:
        """Validate contact creation business rules."""
        # Check for duplicate contacts based on email
        if contact_data.email:
            existing_contacts = await self.repository.find_by({
                "user_id": user_id,
                "email": contact_data.email,
                "plug_type": PlugType.CONTACT
            }, limit=1)
            
            if existing_contacts:
                raise ValidationError(
                    "Contact with this email already exists",
                    error_code="DUPLICATE_CONTACT_EMAIL"
                )

    async def _validate_contact_update(self, contact: Plug, update_data: ContactUpdate) -> None:
        """Validate contact update business rules."""
        # Check for duplicate email if being updated
        if update_data.email and update_data.email != contact.email:
            existing_contacts = await self.repository.find_by({
                "user_id": contact.user_id,
                "email": update_data.email,
                "plug_type": PlugType.CONTACT
            }, limit=1)
            
            # Exclude current contact from check
            existing_contacts = [c for c in existing_contacts if c.id != contact.id]
            
            if existing_contacts:
                raise ValidationError(
                    "Contact with this email already exists",
                    error_code="DUPLICATE_CONTACT_EMAIL"
                )

    async def _validate_target_conversion(
        self,
        target: Plug,
        conversion_data: TargetToContactConversion
    ) -> None:
        """Validate target to contact conversion business rules."""
        if target.plug_type != PlugType.TARGET:
            raise ValidationError(
                "Only targets can be converted to contacts",
                error_code="INVALID_CONVERSION_SOURCE"
            )
        
        if not target.is_complete_for_contact():
            raise ValidationError(
                "Target needs at least name and contact info for conversion",
                error_code="INCOMPLETE_TARGET_DATA"
            )

    async def _build_filter_dict(self, filters: PlugFilters) -> Dict[str, Any]:
        """Build filter dictionary from PlugFilters schema."""
        filter_dict = {}
        
        if filters.network_type:
            filter_dict["network_type"] = filters.network_type
        if filters.business_type:
            filter_dict["business_type"] = filters.business_type
        if filters.priority:
            filter_dict["priority"] = filters.priority
        if filters.is_contact is not None:
            filter_dict["is_contact"] = filters.is_contact
        
        # Handle search term as ilike filter
        if filters.search:
            # This will be handled differently in the repository layer
            filter_dict["search_term"] = filters.search
        
        return filter_dict
