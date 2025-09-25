"""
Repository for plug (target/contact) operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError, ValidationError
from app.models.plug import Plug, PlugType, NetworkType, Priority
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PlugRepository(BaseRepository[Plug]):
    """
    Repository for plug operations providing specialized methods for targets and contacts.
    
    Extends BaseRepository with plug-specific functionality:
    - Target and contact filtering
    - Search capabilities
    - Conversion tracking
    - Statistics and analytics
    """

    def __init__(self, db: Session) -> None:
        """Initialize plug repository."""
        super().__init__(db, Plug)

    # Creation Methods
    async def create_plug(self, user_id: UUID, plug_data: Dict[str, Any]) -> Plug:
        """
        Create a new plug (target or contact).
        
        Args:
            user_id: Owner user ID
            plug_data: Plug data dictionary
            
        Returns:
            Created plug
            
        Raises:
            ValidationError: If plug data is invalid
            DatabaseError: If creation fails
        """
        try:
            # Ensure user association
            plug_data.update({"user_id": user_id})
            
            # Validate minimum required fields
            if not plug_data.get("first_name") or not plug_data.get("last_name"):
                raise ValidationError(
                    "First name and last name are required",
                    error_code="MISSING_REQUIRED_FIELDS"
                )
            
            return await self.create(plug_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating plug for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to create plug",
                error_code="PLUG_CREATE_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )

    # Conversion Methods
    async def convert_target_to_contact(
        self,
        target_id: UUID,
        conversion_data: Dict[str, Any]
    ) -> Optional[Plug]:
        """
        Convert a target to a contact with additional information.
        
        Args:
            target_id: Target plug ID
            conversion_data: Additional contact data
            
        Returns:
            Converted contact plug or None if target not found
            
        Raises:
            ValidationError: If target cannot be converted or data is invalid
            DatabaseError: If conversion fails
        """
        try:
            # Get the target
            target = await self.get(target_id)
            if not target:
                return None
            
            # Verify it's a target
            if target.plug_type != PlugType.TARGET:
                raise ValidationError(
                    "Only targets can be converted to contacts",
                    error_code="INVALID_CONVERSION_SOURCE"
                )
            
            # Check if target has minimum info for conversion
            if not target.is_complete_for_contact():
                raise ValidationError(
                    "Target needs at least name and contact info (email or phone) for conversion",
                    error_code="INCOMPLETE_TARGET_DATA"
                )
            
            # Prepare update data for conversion
            update_data = {
                "plug_type": PlugType.CONTACT,
                "is_contact": True,
                **conversion_data
            }
            
            # Set defaults for required contact fields
            if "priority" not in update_data:
                update_data["priority"] = Priority.MEDIUM
            if "network_type" not in update_data:
                update_data["network_type"] = NetworkType.NEW_CLIENT
            
            # Update the target to become a contact
            return await self.update(target_id, update_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error converting target {target_id} to contact: {e}")
            raise DatabaseError(
                "Failed to convert target to contact",
                error_code="CONVERSION_ERROR",
                details={"target_id": str(target_id), "error": str(e)}
            )

    # User-specific Queries
    async def get_user_plugs(
        self,
        user_id: UUID,
        plug_type: Optional[PlugType] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Plug], int]:
        """
        Get all plugs for a specific user with count.
        
        Args:
            user_id: User ID
            plug_type: Filter by plug type (targets or contacts)
            skip: Number of records to skip
            limit: Maximum number of records
            filters: Additional filters
            
        Returns:
            Tuple of (plugs list, total count)
        """
        try:
            # Build base filters
            base_filters = {"user_id": user_id}
            
            if plug_type:
                base_filters["plug_type"] = plug_type
            
            # Merge with additional filters
            if filters:
                base_filters.update(filters)
            
            # Get plugs
            plugs = await self.get_multi(
                skip=skip,
                limit=limit,
                filters=base_filters,
                order_by="-created_at"
            )
            
            # Get total count
            total_count = await self.count(filters=base_filters)
            
            return plugs, total_count
            
        except Exception as e:
            logger.error(f"Error getting plugs for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to get user plugs",
                error_code="USER_PLUGS_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )

    # Search Methods
    async def search_user_plugs(
        self,
        user_id: UUID,
        search_term: str,
        plug_type: Optional[PlugType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Plug], int]:
        """
        Search plugs by name, company, or email for a specific user.
        
        Args:
            user_id: User ID
            search_term: Search term to match against name, company, email
            plug_type: Filter by plug type
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (matching plugs list, total count)
        """
        try:
            # Build search query
            query = self.db.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False,
                    or_(
                        func.concat(self.model.first_name, ' ', self.model.last_name).ilike(f"%{search_term}%"),
                        self.model.company.ilike(f"%{search_term}%"),
                        self.model.email.ilike(f"%{search_term}%"),
                        self.model.job_title.ilike(f"%{search_term}%")
                    )
                )
            )
            
            if plug_type:
                query = query.filter(self.model.plug_type == plug_type)
            
            # Get total count
            total_count = query.count()
            
            # Get paginated results
            results = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(results)} plugs matching search term '{search_term}' for user {user_id}")
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching plugs for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to search user plugs",
                error_code="SEARCH_PLUGS_ERROR",
                details={"user_id": str(user_id), "search_term": search_term, "error": str(e)}
            )

    # Statistics Methods
    async def get_user_plug_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about user's plugs.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with plug statistics
        """
        try:
            # Base query for user's non-deleted plugs
            base_query = self.db.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False
                )
            )
            
            # Total counts
            total_plugs = base_query.count()
            total_targets = base_query.filter(self.model.plug_type == PlugType.TARGET).count()
            total_contacts = base_query.filter(self.model.plug_type == PlugType.CONTACT).count()
            
            # Contacts by network type
            network_type_stats = self.db.query(
                self.model.network_type,
                func.count(self.model.id)
            ).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.plug_type == PlugType.CONTACT,
                    self.model.is_deleted == False
                )
            ).group_by(self.model.network_type).all()
            
            contacts_by_network_type = {str(nt): count for nt, count in network_type_stats if nt}
            
            # Recent conversions (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_conversions = self.db.query(func.count(self.model.id)).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.plug_type == PlugType.CONTACT,
                    self.model.updated_at >= thirty_days_ago,
                    self.model.is_deleted == False
                )
            ).scalar() or 0
            
            stats = {
                "total_plugs": total_plugs,
                "total_targets": total_targets,
                "total_contacts": total_contacts,
                "contacts_by_network_type": contacts_by_network_type,
                "recent_conversions": recent_conversions
            }
            
            logger.debug(f"Generated plug stats for user {user_id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting plug stats for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to get plug statistics",
                error_code="PLUG_STATS_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )
