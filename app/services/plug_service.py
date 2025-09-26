"""
Service layer for plug (target/contact) business logic.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.plug import Plug, PlugType
from app.repositories.plug_repository import PlugRepository
from app.schemas.plug import PlugStats
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

    # Core CRUD Operations
    async def create_plug(self, user_id: UUID, plug_data: Dict[str, Any]) -> Plug:
        """
        Create a new plug (target or contact).
        
        Args:
            user_id: Owner user ID
            plug_data: Plug creation data
            
        Returns:
            Created plug
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate business rules
            await self._validate_plug_creation(user_id, plug_data)
            
            # Create plug through repository
            plug = await self.repository.create_plug(user_id, plug_data)
            
            logger.info(f"Created plug {plug.id} for user {user_id}")
            return plug
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating plug for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to create plug",
                error_code="PLUG_CREATION_FAILED",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def update_plug(
        self,
        user_id: UUID,
        plug_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Plug]:
        """
        Update an existing plug.
        
        Args:
            user_id: Owner user ID
            plug_id: Plug ID
            update_data: Update data
            
        Returns:
            Updated plug or None if not found
            
        Raises:
            ValidationError: If data is invalid
            BusinessLogicError: If business rules are violated
        """
        try:
            # Verify ownership and existence
            plug = await self._verify_user_plug_ownership(user_id, plug_id)
            if not plug:
                return None
            
            # Validate business rules
            await self._validate_plug_update(plug, update_data)
            
            # Update through repository
            updated_plug = await self.repository.update(plug_id, update_data)
            
            logger.info(f"Updated plug {plug_id} for user {user_id}")
            return updated_plug
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating plug {plug_id} for user {user_id}: {e}")
            raise BusinessLogicError(
                "Failed to update plug",
                error_code="PLUG_UPDATE_FAILED",
                details={"plug_id": str(plug_id), "user_id": str(user_id), "error": str(e)}
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

    # Query Operations
    async def get_user_plugs(
        self,
        user_id: UUID,
        plug_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        search_term: Optional[str] = None,
        network_type: Optional[str] = None
    ) -> Tuple[List[Plug], int]:
        """
        Get paginated list of user's plugs with filtering and optional search.
        
        Args:
            user_id: Owner user ID
            plug_type: Filter by plug type (target/contact)
            skip: Number of records to skip
            limit: Maximum number of records
            search_term: Optional search term for text search
            network_type: Filter by network type (new_client, existing_client, etc.)
            
        Returns:
            Tuple of (plugs list, total count)
        """
        try:
            # Convert string to enum if provided
            plug_type_enum = None
            if plug_type:
                try:
                    plug_type_enum = PlugType(plug_type.lower())
                except ValueError:
                    raise ValidationError(
                        f"Invalid plug type: {plug_type}",
                        error_code="INVALID_PLUG_TYPE"
                    )
            
            # Validate network_type if provided
            if network_type:
                await self._validate_network_type(network_type)
            
            # Use search if search term provided, otherwise use regular list
            if search_term:
                # Validate search term
                if len(search_term.strip()) < 2:
                    raise ValidationError(
                        "Search term must be at least 2 characters",
                        error_code="INVALID_SEARCH_TERM"
                    )
                plugs, total_count = await self.repository.search_user_plugs(
                    user_id=user_id,
                    search_term=search_term.strip(),
                    plug_type=plug_type_enum,
                    skip=skip,
                    limit=limit
                )
            elif network_type:
                # Use network type filtering
                plugs, total_count = await self.repository.get_user_plugs_by_network_type(
                    user_id=user_id,
                    network_type=network_type,
                    plug_type=plug_type_enum,
                    skip=skip,
                    limit=limit
                )
            else:
                plugs, total_count = await self.repository.get_user_plugs(
                    user_id=user_id,
                    plug_type=plug_type_enum,
                    skip=skip,
                    limit=limit
                )
            
            return plugs, total_count
            
        except ValidationError:
            raise
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
        plug_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Plug], int]:
        """
        Search user's plugs by term.
        
        Args:
            user_id: Owner user ID
            search_term: Search term
            plug_type: Filter by plug type (target/contact)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (matching plugs list, total count)
        """
        try:
            # Validate search term
            if not search_term or len(search_term.strip()) < 2:
                raise ValidationError(
                    "Search term must be at least 2 characters",
                    error_code="INVALID_SEARCH_TERM"
                )
            
            # Convert string to enum if provided
            plug_type_enum = None
            if plug_type:
                try:
                    plug_type_enum = PlugType(plug_type.lower())
                except ValueError:
                    raise ValidationError(
                        f"Invalid plug type: {plug_type}",
                        error_code="INVALID_PLUG_TYPE"
                    )
            
            return await self.repository.search_user_plugs(
                user_id=user_id,
                search_term=search_term.strip(),
                plug_type=plug_type_enum,
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

    async def get_plug_stats(self, user_id: UUID) -> PlugStats:
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

    # Conversion Operations
    async def convert_target_to_contact(
        self,
        user_id: UUID,
        target_id: UUID,
        conversion_data: Dict[str, Any]
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
            
            # Perform conversion through repository
            contact = await self.repository.convert_target_to_contact(target_id, conversion_data)
            
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

    async def _validate_plug_creation(self, user_id: UUID, plug_data: Dict[str, Any]) -> None:
        """Validate plug creation business rules."""
        # Check for duplicate plugs based on email if provided
        if plug_data.get("email"):
            existing_plugs = await self.repository.find_by({
                "user_id": user_id,
                "email": plug_data["email"]
            }, limit=1)
            
            if existing_plugs:
                raise ValidationError(
                    "Plug with this email already exists",
                    error_code="DUPLICATE_PLUG_EMAIL"
                )

    async def _validate_plug_update(self, plug: Plug, update_data: Dict[str, Any]) -> None:
        """Validate plug update business rules."""
        # Check for duplicate email if being updated
        if update_data.get("email") and update_data["email"] != plug.email:
            existing_plugs = await self.repository.find_by({
                "user_id": plug.user_id,
                "email": update_data["email"]
            }, limit=1)
            
            # Exclude current plug from check
            existing_plugs = [p for p in existing_plugs if p.id != plug.id]
            
            if existing_plugs:
                raise ValidationError(
                    "Plug with this email already exists",
                    error_code="DUPLICATE_PLUG_EMAIL"
                )

    async def _validate_target_conversion(
        self,
        target: Plug,
        conversion_data: Dict[str, Any]
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

    async def _validate_network_type(self, network_type: str) -> None:
        """Validate network type value."""
        from app.models.plug import NetworkType
        
        # Check if it's a valid enum value
        valid_enum_values = [nt.value for nt in NetworkType]
        
        # Convert to lowercase for comparison
        network_type_lower = network_type.lower().replace(' ', '_')
        
        if network_type_lower not in valid_enum_values:
            # Allow custom network types but validate format
            if len(network_type.strip()) < 2:
                raise ValidationError(
                    "Network type must be at least 2 characters",
                    error_code="INVALID_NETWORK_TYPE"
                )
            # Custom network type is allowed
