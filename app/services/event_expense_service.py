"""
Event expense service for expense operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.models.event import Event, EventExpense
from app.repositories.event_repository import EventExpenseRepository
from app.schemas.event import EventExpenseCreate, EventExpenseUpdate
from app.services.decorators import handle_service_errors, require_event_ownership
from app.services.event_base_service import EventBaseService

logger = logging.getLogger(__name__)


class EventExpenseService(EventBaseService):
    """
    Service for event expense operations.
    """

    def __init__(self, db: Session):
        """Initialize event expense service."""
        super().__init__(db)
        self.expense_repo = EventExpenseRepository(db)

    @handle_service_errors("create expense", "EXPENSE_CREATION_FAILED")
    @require_event_ownership
    async def create_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_data: EventExpenseCreate
    ) -> EventExpense:
        """
        Create a new expense for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            expense_data: Expense creation data
            
        Returns:
            Created expense
        """
        # Convert schema to dict
        expense_dict = expense_data.model_dump(exclude_unset=True)
        expense_dict["event_id"] = event_id
        
        # Create expense
        expense = await self.expense_repo.create(expense_dict)
        
        logger.info(f"Created expense {expense.id} for event {event_id}")
        return expense

    @handle_service_errors("get event expenses", "EVENT_EXPENSES_RETRIEVAL_FAILED")
    @require_event_ownership
    async def get_event_expenses(
        self,
        user_id: UUID,
        event_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EventExpense], int]:
        """
        Get expenses for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            category: Filter by category (optional)
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (expenses list, total count)
        """
        return await self.expense_repo.get_event_expenses(
            event_id=event_id,
            category=category,
            skip=skip,
            limit=limit
        )

    @handle_service_errors("get expense categories", "EXPENSE_CATEGORIES_RETRIEVAL_FAILED")
    @require_event_ownership
    async def get_expense_categories(self, user_id: UUID, event_id: UUID) -> List[str]:
        """
        Get unique expense categories for an event.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            
        Returns:
            List of unique categories
        """
        return await self.expense_repo.get_expense_categories(event_id)

    @handle_service_errors("update expense", "EXPENSE_UPDATE_FAILED")
    @require_event_ownership
    async def update_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_id: UUID,
        update_data: EventExpenseUpdate
    ) -> Optional[EventExpense]:
        """
        Update an expense.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            expense_id: Expense ID
            update_data: Update data
            
        Returns:
            Updated expense or None if not found
        """
        # Verify expense belongs to event
        expense = await self.expense_repo.get(expense_id)
        if not expense or expense.event_id != event_id:
            return None
        
        # Convert schema to dict
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Update expense
        updated_expense = await self.expense_repo.update(expense_id, update_dict)
        
        logger.info(f"Updated expense {expense_id} for event {event_id}")
        return updated_expense

    @handle_service_errors("delete expense", "EXPENSE_DELETION_FAILED")
    @require_event_ownership
    async def delete_expense(
        self,
        user_id: UUID,
        event_id: UUID,
        expense_id: UUID
    ) -> bool:
        """
        Delete an expense.
        
        Args:
            user_id: Owner user ID
            event_id: Event ID
            expense_id: Expense ID
            
        Returns:
            True if deleted, False if not found
        """
        # Verify expense belongs to event
        expense = await self.expense_repo.get(expense_id)
        if not expense or expense.event_id != event_id:
            return False
        
        # Delete expense
        return await self.expense_repo.delete(expense_id, soft=True)






