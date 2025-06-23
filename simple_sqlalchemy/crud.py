"""
Base CRUD operations for simple-sqlalchemy
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import (
    Generic, TypeVar, Type, Optional, List, Dict, Any, Union, Callable
)
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.orm import Session, Query, load_only, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError

from .base import SoftDeleteMixin

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar("ModelType")


class BaseCrud(Generic[ModelType]):
    """
    Base class for CRUD operations with advanced features.
    
    Features:
    - Basic CRUD operations (Create, Read, Update, Delete)
    - Pagination and search
    - Filtering and sorting
    - Soft delete support
    - Bulk operations
    - Date range queries
    - Existence checks
    - Distinct value queries
    """
    
    def __init__(self, model: Type[ModelType], db_client):
        """
        Initialize BaseCrud.
        
        Args:
            model: SQLAlchemy model class
            db_client: Database client instance
        """
        self.model = model
        self.db_client = db_client
    
    # ===== Basic CRUD Operations =====
    
    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new record.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Created model instance
        """
        with self.db_client.session_scope() as session:
            # Filter out None values and invalid fields
            clean_data = {k: v for k, v in data.items() 
                         if v is not None and hasattr(self.model, k)}
            
            instance = self.model(**clean_data)
            session.add(instance)
            session.flush()  # Get the ID
            session.refresh(instance)
            
            # Detach from session before returning
            return self.db_client.detach_object(instance, session)
    
    def get_by_id(self, record_id: int, include_deleted: bool = False) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            record_id: Record ID
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Model instance or None
        """
        with self.db_client.session_scope() as session:
            query = session.query(self.model).filter(self.model.id == record_id)
            
            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))
            
            instance = query.first()
            return self.db_client.detach_object(instance, session) if instance else None
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        include_deleted: bool = False,
        options: Optional[List] = None
    ) -> List[ModelType]:
        """
        Get multiple records with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return (0 for all)
            filters: Dictionary of field filters
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            include_deleted: Whether to include soft-deleted records
            options: SQLAlchemy query options (e.g., joinedload, selectinload)
            
        Returns:
            List of model instances
        """
        with self.db_client.session_scope() as session:
            query = session.query(self.model)
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))
            
            # Apply sorting
            if hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                query = query.order_by(desc(sort_column) if sort_desc else asc(sort_column))
            
            # Apply query options
            if options:
                for option in options:
                    query = query.options(option)
            
            # Apply pagination
            if skip > 0:
                query = query.offset(skip)
            if limit > 0:
                query = query.limit(limit)
            
            instances = query.all()
            return [self.db_client.detach_object(instance, session) for instance in instances]
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a record.
        
        Args:
            record_id: Record ID
            data: Dictionary of field updates
            
        Returns:
            Updated model instance or None
        """
        with self.db_client.session_scope() as session:
            query = session.query(self.model).filter(self.model.id == record_id)
            
            # Handle soft delete
            if self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))
            
            instance = query.first()
            if not instance:
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            session.flush()
            session.refresh(instance)
            
            return self.db_client.detach_object(instance, session)
    
    def delete(self, record_id: int) -> bool:
        """
        Hard delete a record.
        
        Args:
            record_id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.db_client.session_scope() as session:
            instance = session.query(self.model).filter(self.model.id == record_id).first()
            if not instance:
                return False
            
            session.delete(instance)
            return True
    
    # ===== Soft Delete Operations =====
    
    def soft_delete(self, record_id: int) -> Optional[ModelType]:
        """
        Soft delete a record (if model supports it).
        
        Args:
            record_id: Record ID
            
        Returns:
            Soft-deleted model instance or None
        """
        if not self._has_soft_delete():
            raise ValueError(f"Model {self.model.__name__} does not support soft delete")
        
        return self.update(record_id, {"deleted_at": datetime.now(timezone.utc)})
    
    def undelete(self, record_id: int) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        
        Args:
            record_id: Record ID
            
        Returns:
            Restored model instance or None
        """
        if not self._has_soft_delete():
            raise ValueError(f"Model {self.model.__name__} does not support soft delete")
        
        with self.db_client.session_scope() as session:
            instance = session.query(self.model).filter(
                and_(
                    self.model.id == record_id,
                    self.model.deleted_at.isnot(None)
                )
            ).first()
            
            if not instance:
                return None
            
            instance.deleted_at = None
            session.flush()
            session.refresh(instance)
            
            return self.db_client.detach_object(instance, session)
    
    # ===== Helper Methods =====
    
    def _has_soft_delete(self) -> bool:
        """Check if model supports soft delete"""
        return (hasattr(self.model, 'deleted_at') or 
                issubclass(self.model, SoftDeleteMixin))
    
    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """Apply filters to query"""
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query

    # ===== Search and Count Operations =====

    def search(
        self,
        search_query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        include_deleted: bool = False,
        options: Optional[List] = None
    ) -> List[ModelType]:
        """
        Search records across multiple fields.

        Args:
            search_query: Text to search for
            search_fields: List of field names to search in
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Additional filters to apply
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            include_deleted: Whether to include soft-deleted records
            options: SQLAlchemy query options

        Returns:
            List of matching model instances
        """
        with self.db_client.session_scope() as session:
            query = session.query(self.model)

            # Apply search filter
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    field_attr = getattr(self.model, field)
                    search_conditions.append(field_attr.ilike(f"%{search_query}%"))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

            # Apply additional filters
            if filters:
                query = self._apply_filters(query, filters)

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            # Apply sorting
            if hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                query = query.order_by(desc(sort_column) if sort_desc else asc(sort_column))

            # Apply query options
            if options:
                for option in options:
                    query = query.options(option)

            # Apply pagination
            if skip > 0:
                query = query.offset(skip)
            if limit > 0:
                query = query.limit(limit)

            instances = query.all()
            return [self.db_client.detach_object(instance, session) for instance in instances]

    def count(self, filters: Optional[Dict[str, Any]] = None, include_deleted: bool = False) -> int:
        """
        Count records with optional filters.

        Args:
            filters: Dictionary of field filters
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of matching records
        """
        with self.db_client.session_scope() as session:
            query = session.query(func.count(self.model.id))

            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            return query.scalar() or 0

    # ===== Specialized Query Methods =====

    def exists_by_field(self, field: str, value: Any, include_deleted: bool = False) -> bool:
        """
        Check if a record exists with a specific field value.

        Args:
            field: Field name to check
            value: Value to check for
            include_deleted: Whether to include soft-deleted records

        Returns:
            True if record exists, False otherwise
        """
        if not hasattr(self.model, field):
            return False

        with self.db_client.session_scope() as session:
            query = session.query(self.model.id).filter(getattr(self.model, field) == value)

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            return query.first() is not None

    def get_by_field(self, field: str, value: Any, include_deleted: bool = False) -> Optional[ModelType]:
        """
        Get a record by a specific field value.

        Args:
            field: Field name to search by
            value: Value to search for
            include_deleted: Whether to include soft-deleted records

        Returns:
            Model instance or None
        """
        if not hasattr(self.model, field):
            return None

        with self.db_client.session_scope() as session:
            query = session.query(self.model).filter(getattr(self.model, field) == value)

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            instance = query.first()
            return self.db_client.detach_object(instance, session) if instance else None

    def get_by_null_field(
        self,
        field: str,
        is_null: bool = True,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        sort_by: str = "id"
    ) -> List[ModelType]:
        """
        Get records where a field is NULL or NOT NULL.

        Args:
            field: Field name to check
            is_null: True to get NULL records, False to get NOT NULL records
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records
            sort_by: Field to sort by

        Returns:
            List of matching model instances
        """
        if not hasattr(self.model, field):
            return []

        with self.db_client.session_scope() as session:
            query = session.query(self.model)

            # Apply NULL/NOT NULL filter
            field_attr = getattr(self.model, field)
            if is_null:
                query = query.filter(field_attr.is_(None))
            else:
                query = query.filter(field_attr.isnot(None))

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            # Apply sorting
            if hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                query = query.order_by(asc(sort_column))

            # Apply pagination
            if skip > 0:
                query = query.offset(skip)
            if limit > 0:
                query = query.limit(limit)

            instances = query.all()
            return [self.db_client.detach_object(instance, session) for instance in instances]

    def get_by_date_range(
        self,
        date_field: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_back: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> List[ModelType]:
        """
        Get records within a date range.

        Args:
            date_field: Name of the date field to filter on
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            days_back: Number of days back from now (alternative to start_date)
            filters: Additional filters to apply
            limit: Maximum number of records to return

        Returns:
            List of matching model instances
        """
        if not hasattr(self.model, date_field):
            return []

        with self.db_client.session_scope() as session:
            query = session.query(self.model)

            # Apply date range filter
            date_attr = getattr(self.model, date_field)

            if days_back is not None:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
                query = query.filter(date_attr >= cutoff_date)
            else:
                if start_date:
                    query = query.filter(date_attr >= start_date)
                if end_date:
                    query = query.filter(date_attr <= end_date)

            # Apply additional filters
            if filters:
                query = self._apply_filters(query, filters)

            # Handle soft delete
            if self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            # Apply limit
            if limit > 0:
                query = query.limit(limit)

            instances = query.all()
            return [self.db_client.detach_object(instance, session) for instance in instances]

    def get_distinct_values(self, field: str, include_deleted: bool = False) -> List[Any]:
        """
        Get distinct values for a field.

        Args:
            field: Field name to get distinct values for
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of distinct values
        """
        if not hasattr(self.model, field):
            return []

        with self.db_client.session_scope() as session:
            field_attr = getattr(self.model, field)
            query = session.query(field_attr).distinct()

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            # Filter out None values
            query = query.filter(field_attr.isnot(None))

            results = query.all()
            return [result[0] for result in results]

    # ===== Bulk Operations =====

    def bulk_update_fields(
        self,
        update_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Bulk update fields for multiple records.

        Args:
            update_data: Dictionary of field updates
            filters: Filters to determine which records to update
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of records updated
        """
        with self.db_client.session_scope() as session:
            query = session.query(self.model)

            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)

            # Handle soft delete
            if not include_deleted and self._has_soft_delete():
                query = query.filter(self.model.deleted_at.is_(None))

            # Perform bulk update
            result = query.update(update_data, synchronize_session=False)
            return result

    def bulk_clear_fields(
        self,
        clear_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Bulk clear (set to None) fields for multiple records.

        Args:
            clear_data: Dictionary of fields to clear (values should be None)
            filters: Filters to determine which records to update
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of records updated
        """
        return self.bulk_update_fields(clear_data, filters, include_deleted)

    def delete_all(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Delete all records (hard delete).

        Args:
            filters: Optional filters to limit which records to delete

        Returns:
            Number of records deleted
        """
        with self.db_client.session_scope() as session:
            query = session.query(self.model)

            # Apply filters if provided
            if filters:
                query = self._apply_filters(query, filters)

            # Count records before deletion
            count = query.count()

            # Delete records
            query.delete(synchronize_session=False)

            return count

    def bulk_soft_delete(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Bulk soft delete records.

        Args:
            filters: Filters to determine which records to soft delete

        Returns:
            Number of records soft deleted
        """
        if not self._has_soft_delete():
            raise ValueError(f"Model {self.model.__name__} does not support soft delete")

        return self.bulk_update_fields(
            {"deleted_at": datetime.now(timezone.utc)},
            filters,
            include_deleted=False
        )

    def bulk_restore(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Bulk restore soft-deleted records.

        Args:
            filters: Filters to determine which records to restore

        Returns:
            Number of records restored
        """
        if not self._has_soft_delete():
            raise ValueError(f"Model {self.model.__name__} does not support soft delete")

        with self.db_client.session_scope() as session:
            query = session.query(self.model).filter(self.model.deleted_at.isnot(None))

            # Apply additional filters
            if filters:
                query = self._apply_filters(query, filters)

            # Restore records
            result = query.update({"deleted_at": None}, synchronize_session=False)
            return result
