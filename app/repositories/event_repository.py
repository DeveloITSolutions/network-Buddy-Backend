"""
Repository for event operations.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError, ValidationError
from app.models.event import Event, EventAgenda, EventExpense, EventMedia, EventPlug
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class EventRepository(BaseRepository[Event]):
    """
    Repository for event operations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize event repository."""
        super().__init__(db, Event)

    # Event CRUD Operations
    async def create_event(self, user_id: UUID, event_data: Dict[str, Any]) -> Event:
        """
        Create a new event.
        
        Args:
            user_id: Owner user ID
            event_data: Event data dictionary
            
        Returns:
            Created event
            
        Raises:
            ValidationError: If event data is invalid
            DatabaseError: If creation fails
        """
        try:
            # Ensure user association
            event_data.update({"user_id": user_id})
            
            # Validate required fields
            if not event_data.get("title"):
                raise ValidationError(
                    "Event title is required",
                    error_code="MISSING_REQUIRED_FIELDS"
                )
            
            if not event_data.get("start_date") or not event_data.get("end_date"):
                raise ValidationError(
                    "Start date and end date are required",
                    error_code="MISSING_REQUIRED_FIELDS"
                )
            
            return await self.create(event_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating event for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to create event",
                error_code="EVENT_CREATE_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def get_user_events(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Event], int]:
        """
        Get all events for a specific user with count.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            filters: Additional filters
            
        Returns:
            Tuple of (events list, total count)
        """
        try:
            # Build base filters
            base_filters = {"user_id": user_id}
            
            # Merge with additional filters
            if filters:
                base_filters.update(filters)
            
            # Get events
            events = await self.get_multi(
                skip=skip,
                limit=limit,
                filters=base_filters,
                order_by="-created_at"
            )
            
            # Get total count
            total_count = await self.count(filters=base_filters)
            
            return events, total_count
            
        except Exception as e:
            logger.error(f"Error getting events for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to get user events",
                error_code="USER_EVENTS_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )

    async def search_user_events(
        self,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Event], int]:
        """
        Search events by title, theme, or location for a specific user.
        
        Args:
            user_id: User ID
            search_term: Search term to match against title, theme, location
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (matching events list, total count)
        """
        try:
            # Build search query
            query = self.db.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False,
                    or_(
                        self.model.title.ilike(f"%{search_term}%"),
                        self.model.theme.ilike(f"%{search_term}%"),
                        self.model.location_name.ilike(f"%{search_term}%"),
                        self.model.city.ilike(f"%{search_term}%"),
                        self.model.country.ilike(f"%{search_term}%")
                    )
                )
            )
            
            # Get total count
            total_count = query.count()
            
            # Get paginated results
            results = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(results)} events matching search term '{search_term}' for user {user_id}")
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching events for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to search user events",
                error_code="SEARCH_EVENTS_ERROR",
                details={"user_id": str(user_id), "search_term": search_term, "error": str(e)}
            )

    async def get_user_event_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about user's events.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with event statistics
        """
        try:
            # Base query for user's non-deleted events
            base_query = self.db.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False
                )
            )
            
            # Total counts
            total_events = base_query.count()
            active_events = base_query.filter(self.model.is_active == True).count()
            
            # Upcoming events (start date in future)
            now = datetime.utcnow()
            upcoming_events = base_query.filter(self.model.start_date > now).count()
            past_events = base_query.filter(self.model.end_date < now).count()
            
            # Events by month (current year)
            current_year = now.year
            events_by_month = {}
            for month in range(1, 13):
                month_events = base_query.filter(
                    and_(
                        func.extract('year', self.model.start_date) == current_year,
                        func.extract('month', self.model.start_date) == month
                    )
                ).count()
                events_by_month[str(month)] = month_events
            
            # Events by city
            city_stats = self.db.query(
                self.model.city,
                func.count(self.model.id)
            ).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False,
                    self.model.city.isnot(None)
                )
            ).group_by(self.model.city).all()
            
            events_by_city = {city: count for city, count in city_stats if city}
            
            # Events by country
            country_stats = self.db.query(
                self.model.country,
                func.count(self.model.id)
            ).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False,
                    self.model.country.isnot(None)
                )
            ).group_by(self.model.country).all()
            
            events_by_country = {country: count for country, count in country_stats if country}
            
            # Total budget across all events
            total_budget = self.db.query(
                func.sum(EventExpense.amount)
            ).join(Event).filter(
                and_(
                    Event.user_id == user_id,
                    Event.is_deleted == False,
                    EventExpense.is_deleted == False
                )
            ).scalar() or 0
            
            stats = {
                "total_events": total_events,
                "active_events": active_events,
                "upcoming_events": upcoming_events,
                "past_events": past_events,
                "total_budget": float(total_budget),
                "events_by_month": events_by_month,
                "events_by_city": events_by_city,
                "events_by_country": events_by_country
            }
            
            logger.debug(f"Generated event stats for user {user_id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting event stats for user {user_id}: {e}")
            raise DatabaseError(
                "Failed to get event statistics",
                error_code="EVENT_STATS_ERROR",
                details={"user_id": str(user_id), "error": str(e)}
            )


class EventAgendaRepository(BaseRepository[EventAgenda]):
    """
    Repository for event agenda operations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize event agenda repository."""
        super().__init__(db, EventAgenda)

    async def get_event_agendas(
        self,
        event_id: UUID,
        day: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventAgenda], int]:
        """
        Get agenda items for a specific event.
        
        Args:
            event_id: Event ID
            day: Filter by specific day (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (agenda items list, total count)
        """
        try:
            # Build filters
            filters = {"event_id": event_id}
            if day is not None:
                filters["day"] = day
            
            # Get agenda items
            agendas = await self.get_multi(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by="day, start_time"
            )
            
            # Get total count
            total_count = await self.count(filters=filters)
            
            return agendas, total_count
            
        except Exception as e:
            logger.error(f"Error getting agendas for event {event_id}: {e}")
            raise DatabaseError(
                "Failed to get event agendas",
                error_code="EVENT_AGENDAS_ERROR",
                details={"event_id": str(event_id), "error": str(e)}
            )


class EventExpenseRepository(BaseRepository[EventExpense]):
    """
    Repository for event expense operations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize event expense repository."""
        super().__init__(db, EventExpense)

    async def get_event_expenses(
        self,
        event_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventExpense], int]:
        """
        Get expenses for a specific event.
        
        Args:
            event_id: Event ID
            category: Filter by category (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (expenses list, total count)
        """
        try:
            # Build filters
            filters = {"event_id": event_id}
            if category:
                filters["category"] = category
            
            # Get expenses
            expenses = await self.get_multi(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by="-created_at"
            )
            
            # Get total count
            total_count = await self.count(filters=filters)
            
            return expenses, total_count
            
        except Exception as e:
            logger.error(f"Error getting expenses for event {event_id}: {e}")
            raise DatabaseError(
                "Failed to get event expenses",
                error_code="EVENT_EXPENSES_ERROR",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def get_expense_categories(self, event_id: UUID) -> List[str]:
        """
        Get unique expense categories for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            List of unique categories
        """
        try:
            categories = self.db.query(self.model.category).filter(
                and_(
                    self.model.event_id == event_id,
                    self.model.is_deleted == False
                )
            ).distinct().all()
            
            return [cat[0] for cat in categories if cat[0]]
            
        except Exception as e:
            logger.error(f"Error getting expense categories for event {event_id}: {e}")
            raise DatabaseError(
                "Failed to get expense categories",
                error_code="EXPENSE_CATEGORIES_ERROR",
                details={"event_id": str(event_id), "error": str(e)}
            )


class EventMediaRepository(BaseRepository[EventMedia]):
    """
    Repository for event media operations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize event media repository."""
        super().__init__(db, EventMedia)

    async def get_event_media(
        self,
        event_id: UUID,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """
        Get media for a specific event.
        
        Args:
            event_id: Event ID
            file_type: Filter by file type (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (media list, total count)
        """
        try:
            # Build filters
            filters = {"event_id": event_id}
            if file_type:
                filters["file_type"] = file_type
            
            # Get media
            media = await self.get_multi(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by="-created_at"
            )
            
            # Get total count
            total_count = await self.count(filters=filters)
            
            return media, total_count
            
        except Exception as e:
            logger.error(f"Error getting media for event {event_id}: {e}")
            raise DatabaseError(
                "Failed to get event media",
                error_code="EVENT_MEDIA_ERROR",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def search_media_by_tags(
        self,
        event_id: UUID,
        tags: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventMedia], int]:
        """
        Search media by tags for a specific event.
        
        Args:
            event_id: Event ID
            tags: List of tags to search for
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (matching media list, total count)
        """
        try:
            # Build search query
            query = self.db.query(self.model).filter(
                and_(
                    self.model.event_id == event_id,
                    self.model.is_deleted == False,
                    self.model.tags.isnot(None)
                )
            )
            
            # Search for any of the provided tags
            tag_conditions = [self.model.tags.ilike(f"%{tag}%") for tag in tags]
            query = query.filter(or_(*tag_conditions))
            
            # Get total count
            total_count = query.count()
            
            # Get paginated results
            results = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(results)} media items matching tags {tags} for event {event_id}")
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching media by tags for event {event_id}: {e}")
            raise DatabaseError(
                "Failed to search media by tags",
                error_code="MEDIA_TAG_SEARCH_ERROR",
                details={"event_id": str(event_id), "tags": tags, "error": str(e)}
            )


class EventPlugRepository(BaseRepository[EventPlug]):
    """
    Repository for event-plug association operations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize event-plug repository."""
        super().__init__(db, EventPlug)

    async def add_plug_to_event(
        self,
        event_id: UUID,
        plug_id: UUID,
        association_data: Optional[Dict[str, Any]] = None
    ) -> EventPlug:
        """
        Add a plug to an event.
        
        Args:
            event_id: Event ID
            plug_id: Plug ID
            association_data: Additional association data
            
        Returns:
            Created event-plug association
            
        Raises:
            ValidationError: If association data is invalid
            DatabaseError: If creation fails
        """
        try:
            # Check if association already exists
            existing = await self.find_by({
                "event_id": event_id,
                "plug_id": plug_id
            }, limit=1)
            
            if existing:
                raise ValidationError(
                    "Plug is already associated with this event",
                    error_code="DUPLICATE_EVENT_PLUG"
                )
            
            # Prepare data
            data = {
                "event_id": event_id,
                "plug_id": plug_id,
                **(association_data or {})
            }
            
            return await self.create(data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding plug {plug_id} to event {event_id}: {e}")
            raise DatabaseError(
                "Failed to add plug to event",
                error_code="ADD_PLUG_TO_EVENT_ERROR",
                details={"event_id": str(event_id), "plug_id": str(plug_id), "error": str(e)}
            )

    async def get_event_plugs(
        self,
        event_id: UUID,
        plug_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventPlug], int]:
        """
        Get plugs associated with an event.
        
        Args:
            event_id: Event ID
            plug_type: Filter by plug type (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (event-plug associations list, total count)
        """
        try:
            # Build query with join to plugs table
            query = self.db.query(self.model).join(
                self.model.plug
            ).filter(
                and_(
                    self.model.event_id == event_id,
                    self.model.is_deleted == False
                )
            )
            
            if plug_type:
                query = query.filter(self.model.plug.has(plug_type=plug_type))
            
            # Get total count
            total_count = query.count()
            
            # Get paginated results
            results = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error getting plugs for event {event_id}: {e}")
            raise DatabaseError(
                "Failed to get event plugs",
                error_code="EVENT_PLUGS_ERROR",
                details={"event_id": str(event_id), "error": str(e)}
            )

    async def remove_plug_from_event(self, event_id: UUID, plug_id: UUID) -> bool:
        """
        Remove a plug from an event.
        
        Args:
            event_id: Event ID
            plug_id: Plug ID
            
        Returns:
            True if removed, False if not found
        """
        try:
            # Find the association
            association = await self.find_by({
                "event_id": event_id,
                "plug_id": plug_id
            }, limit=1)
            
            if not association:
                return False
            
            # Soft delete the association
            return await self.delete(association[0].id, soft=True)
            
        except Exception as e:
            logger.error(f"Error removing plug {plug_id} from event {event_id}: {e}")
            raise DatabaseError(
                "Failed to remove plug from event",
                error_code="REMOVE_PLUG_FROM_EVENT_ERROR",
                details={"event_id": str(event_id), "plug_id": str(plug_id), "error": str(e)}
            )

