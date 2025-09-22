"""
Base service class with common functionality following SOLID principles.
"""
import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any, Dict
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.exceptions import ValidationError, NotFoundError
from app.config.redis import get_cache_manager

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Model type
S = TypeVar('S')  # Schema type


class BaseService(ABC, Generic[T]):
    """
    Abstract base service class providing common functionality.
    
    Follows SOLID principles:
    - Single Responsibility: Each service handles one domain
    - Open/Closed: Extensible through inheritance
    - Liskov Substitution: Derived classes are substitutable
    - Interface Segregation: Focused interfaces
    - Dependency Inversion: Depends on abstractions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = get_cache_manager()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_model_class(self) -> type[T]:
        """Get the model class for this service."""
        pass
    
    def get_by_id(self, id: str, include_deleted: bool = False) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            id: Entity ID
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Entity if found, None otherwise
        """
        query = self.db.query(self.get_model_class()).filter(
            self.get_model_class().id == id
        )
        
        if not include_deleted:
            query = query.filter(self.get_model_class().is_deleted == False)
        
        return query.first()
    
    def get_by_field(self, field_name: str, value: Any, include_deleted: bool = False) -> Optional[T]:
        """
        Get entity by field value.
        
        Args:
            field_name: Field name to search by
            value: Field value
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Entity if found, None otherwise
        """
        query = self.db.query(self.get_model_class()).filter(
            getattr(self.get_model_class(), field_name) == value
        )
        
        if not include_deleted:
            query = query.filter(self.get_model_class().is_deleted == False)
        
        return query.first()
    
    def create(self, data: Dict[str, Any]) -> T:
        """
        Create new entity.
        
        Args:
            data: Entity data
            
        Returns:
            Created entity
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            entity = self.get_model_class()(**data)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            
            self.logger.info(f"Created {self.get_model_class().__name__} with ID: {entity.id}")
            return entity
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create {self.get_model_class().__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create {self.get_model_class().__name__.lower()}"
            )
    
    def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        Update entity by ID.
        
        Args:
            id: Entity ID
            data: Update data
            
        Returns:
            Updated entity if found, None otherwise
            
        Raises:
            HTTPException: If update fails
        """
        try:
            entity = self.get_by_id(id)
            if not entity:
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            # Update timestamp
            entity.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(entity)
            
            self.logger.info(f"Updated {self.get_model_class().__name__} with ID: {id}")
            return entity
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update {self.get_model_class().__name__} {id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update {self.get_model_class().__name__.lower()}"
            )
    
    def soft_delete(self, id: str) -> bool:
        """
        Soft delete entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            entity = self.get_by_id(id)
            if not entity:
                return False
            
            entity.soft_delete()
            self.db.commit()
            
            self.logger.info(f"Soft deleted {self.get_model_class().__name__} with ID: {id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to soft delete {self.get_model_class().__name__} {id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete {self.get_model_class().__name__.lower()}"
            )
    
    def restore(self, id: str) -> bool:
        """
        Restore soft-deleted entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if restored, False if not found
        """
        try:
            entity = self.get_by_id(id, include_deleted=True)
            if not entity or not entity.is_deleted:
                return False
            
            entity.restore()
            self.db.commit()
            
            self.logger.info(f"Restored {self.get_model_class().__name__} with ID: {id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to restore {self.get_model_class().__name__} {id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restore {self.get_model_class().__name__.lower()}"
            )
    
    def _handle_validation_error(self, error: ValidationError) -> None:
        """Handle validation errors consistently."""
        self.logger.warning(f"Validation error: {error}")
        raise error
    
    def _handle_not_found_error(self, error: NotFoundError) -> None:
        """Handle not found errors consistently."""
        self.logger.warning(f"Not found error: {error}")
        raise error
    
    def _handle_generic_error(self, error: Exception, operation: str) -> None:
        """Handle generic errors consistently."""
        self.logger.error(f"Error during {operation}: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {operation}"
        )
