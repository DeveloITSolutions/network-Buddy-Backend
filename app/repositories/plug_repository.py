"""
Repository for plug (target/contact) operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError, NotFoundError, ValidationError
from app.models.plug import Plug, PlugType, NetworkType, BusinessType, Priority
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

    # Specialized Creation Methods
    async def create_target(self, user_id: UUID, target_data: Dict[str, Any]) -> Plug:
        """
        Create a new target plug.
        
        Args:
            user_id: Owner user ID
            target_data: Target data dictionary
            
        Returns:
            Created target plug
            
        Raises:
            ValidationError: If target data is invalid
            DatabaseError: If creation fails
        """
        try:
            # Ensure target type and user association
            target_data.update({
                "user_id": user_id,
                "plug_type": PlugType.TARGET,
                "is_contact": False
            })
            
            # Validate minimum required fields for target
            if not target_data.get("first_name") or not target_data.get("last_name"):
                raise ValidationError(
                    "First name and last name are required for targets",
                    error_code="MISSING_REQUIRED_FIELDS"
                )
            
            return await self.create(target_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating target for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to create target",
                error_code="TARGET_CREATE_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def create_contact(self, user_id: UUID, contact_data: Dict[str, Any]) -> Plug:
        """
        Create a new contact plug.
        
        Args:
            user_id: Owner user ID
            contact_data: Contact data dictionary
            
        Returns:
            Created contact plug
            
        Raises:
            ValidationError: If contact data is invalid
            DatabaseError: If creation fails
        """
        try:
            # Ensure contact type and user association
            contact_data.update({
                "user_id": user_id,
                "plug_type": PlugType.CONTACT,
                "is_contact": True
            })
            
            # Set default values for contact-specific fields
            if "priority" not in contact_data:
                contact_data["priority"] = Priority.MEDIUM
            if "network_type" not in contact_data:
                contact_data["network_type"] = NetworkType.NEW_CLIENT
            
            # Validate minimum required fields for contact
            if not contact_data.get("first_name") or not contact_data.get("last_name"):
                raise ValidationError(
                    "First name and last name are required for contacts",
                    error_code="MISSING_REQUIRED_FIELDS"
                )
            
            # Validate that contact has some form of contact information
            if not any([contact_data.get("email"), contact_data.get("primary_number")]):
                raise ValidationError(
                    "Contact must have either email or phone number",
                    error_code="MISSING_CONTACT_INFO"
                )
            
            return await self.create(contact_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating contact for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to create contact",
                error_code="CONTACT_CREATE_ERROR",
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
    ) -> List[Plug]:
        """
        Get all plugs for a specific user.
        
        Args:
            user_id: User ID
            plug_type: Filter by plug type (targets or contacts)
            skip: Number of records to skip
            limit: Maximum number of records
            filters: Additional filters
            
        Returns:
            List of user's plugs
        """
        try:
            # Build base filters
            base_filters = {"user_id": user_id}
            
            if plug_type:
                base_filters["plug_type"] = plug_type
            
            # Merge with additional filters
            if filters:
                base_filters.update(filters)
            
            return await self.get_multi(
                skip=skip,
                limit=limit,
                filters=base_filters,
                order_by="-created_at"
            )
            
        except Exception as e:
            logger.error(f"Error getting plugs for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to get user plugs",
                error_code="USER_PLUGS_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def count_user_plugs(
        self,
        user_id: UUID,
        plug_type: Optional[PlugType] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count plugs for a specific user.
        
        Args:
            user_id: User ID
            plug_type: Filter by plug type
            filters: Additional filters
            
        Returns:
            Number of matching plugs
        """
        try:
            # Build base filters
            base_filters = {"user_id": user_id}
            
            if plug_type:
                base_filters["plug_type"] = plug_type
            
            # Merge with additional filters
            if filters:
                base_filters.update(filters)
            
            return await self.count(filters=base_filters)
            
        except Exception as e:
            logger.error(f"Error counting plugs for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to count user plugs",
                error_code="USER_PLUGS_COUNT_ERROR",
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
    ) -> List[Plug]:
        """
        Search plugs by name, company, or email for a specific user.
        
        Args:
            user_id: User ID
            search_term: Search term to match against name, company, email
            plug_type: Filter by plug type
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of matching plugs
        """
        try:
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
            
            results = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(results)} plugs matching search term '{search_term}' for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching plugs for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to search user plugs",
                error_code="SEARCH_PLUGS_ERROR",
                details={"user_id": str(user_id), "search_term": search_term, "error": str(e)}
            )

    async def get_plugs_by_tags(
        self,
        user_id: UUID,
        tags: List[str],
        match_all: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Plug]:
        """
        Get plugs that have specific tags.
        
        Args:
            user_id: User ID
            tags: List of tags to search for
            match_all: If True, requires all tags; if False, requires any tag
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of plugs with matching tags
        """
        try:
            query = self.db.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False,
                    self.model.tags.isnot(None)
                )
            )
            
            if match_all:
                # All tags must be present
                for tag in tags:
                    query = query.filter(self.model.tags.contains([tag]))
            else:
                # Any tag must be present
                tag_conditions = [self.model.tags.contains([tag]) for tag in tags]
                query = query.filter(or_(*tag_conditions))
            
            results = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(results)} plugs with tags {tags} for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting plugs by tags for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to get plugs by tags",
                error_code="PLUGS_BY_TAGS_ERROR",
                details={"user_id": str(user_id), "tags": tags, "error": str(e)}
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
            
            # Contacts by business type
            business_type_stats = self.db.query(
                self.model.business_type,
                func.count(self.model.id)
            ).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.plug_type == PlugType.CONTACT,
                    self.model.is_deleted == False
                )
            ).group_by(self.model.business_type).all()
            
            contacts_by_business_type = {str(bt): count for bt, count in business_type_stats if bt}
            
            # Targets by priority (only contacts have priority, but let's check targets that were converted)
            priority_stats = self.db.query(
                self.model.priority,
                func.count(self.model.id)
            ).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False,
                    self.model.priority.isnot(None)
                )
            ).group_by(self.model.priority).all()
            
            targets_by_priority = {str(p): count for p, count in priority_stats if p}
            
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
                "targets_by_priority": targets_by_priority,
                "contacts_by_network_type": contacts_by_network_type,
                "contacts_by_business_type": contacts_by_business_type,
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

    # Bulk Operations
    async def bulk_convert_targets_to_contacts(
        self,
        target_ids: List[UUID],
        conversion_data: Dict[str, Any]
    ) -> List[Plug]:
        """
        Convert multiple targets to contacts.
        
        Args:
            target_ids: List of target IDs to convert
            conversion_data: Common data to apply to all conversions
            
        Returns:
            List of converted contacts
            
        Raises:
            ValidationError: If any target cannot be converted
            DatabaseError: If conversion fails
        """
        try:
            converted_contacts = []
            
            for target_id in target_ids:
                contact = await self.convert_target_to_contact(target_id, conversion_data)
                if contact:
                    converted_contacts.append(contact)
            
            logger.debug(f"Bulk converted {len(converted_contacts)} targets to contacts")
            return converted_contacts
            
        except Exception as e:
            logger.error(f"Error in bulk target conversion: {e}")
            raise DatabaseError(
                "Failed to bulk convert targets to contacts",
                error_code="BULK_CONVERSION_ERROR",
                details={"target_count": len(target_ids), "error": str(e)}
            )
