"""
Enhanced CRUD operations for simple-sqlalchemy with string-schema integration
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
    Enhanced CRUD operations with SQLAlchemy ORM and string-schema integration.

    Features:
    - Traditional SQLAlchemy operations (returns model instances)
    - String-schema operations (returns validated dicts)
    - Enhanced filtering with null/not-null/comparison operators
    - DRY architecture with reusable query building
    - Database-agnostic design (SQLite, PostgreSQL, MySQL)
    - Conversion utilities between models and dicts

    Usage:
        # Traditional SQLAlchemy
        user = user_crud.get_by_id(123)  # Returns User instance
        users = user_crud.get_multi(filters={"active": True})

        # String-schema operations
        user_dict = user_crud.query_with_schema("id:int, name:string", filters={"active": True})
        paginated = user_crud.paginated_query_with_schema("id:int, name:string", page=1)

        # Conversion utilities
        user_dict = user_crud.to_dict(user, "id:int, name:string, email:email")
    """

    def __init__(self, model: Type[ModelType], db_client):
        """
        Initialize Enhanced BaseCrud.

        Args:
            model: SQLAlchemy model class
            db_client: Database client instance
        """
        self.model = model
        self.db_client = db_client

        # Initialize string-schema helper for schema operations
        self._schema_helper = None  # Lazy loaded to avoid circular imports

    def _get_schema_helper(self):
        """Get or create string schema helper for this model."""
        if self._schema_helper is None:
            try:
                from .helpers.string_schema import StringSchemaHelper
                self._schema_helper = StringSchemaHelper(self.db_client, self.model)
            except ImportError:
                raise ImportError(
                    "string-schema is required for schema-based operations. "
                    "Install with: pip install string-schema"
                )
        return self._schema_helper

    # ===== DRY Helper Methods (Internal) =====

    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """
        Apply enhanced filters to query - database agnostic.

        Supports:
        - Equality: {"field": "value"}
        - Null checks: {"field": None}, {"field": {"not": None}}
        - Comparisons: {"field": {">=": value, "<": value}}
        - Lists: {"field": ["val1", "val2"]}, {"field": {"not_in": ["val1", "val2"]}}
        - String operations: {"field": {"like": "%pattern%", "ilike": "%pattern%"}}
        - Range: {"field": {"between": [start, end]}}
        """
        if not filters:
            return query

        for field, value in filters.items():
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)

                if isinstance(value, list):
                    # IN clause
                    query = query.filter(field_attr.in_(value))
                elif value is None:
                    # IS NULL
                    query = query.filter(field_attr.is_(None))
                elif isinstance(value, dict):
                    # Handle special operators
                    if 'not' in value and value.get('not') is None:
                        query = query.filter(field_attr.is_not(None))
                    elif '>=' in value:
                        query = query.filter(field_attr >= value['>='])
                    elif '<=' in value:
                        query = query.filter(field_attr <= value['<='])
                    elif '>' in value:
                        query = query.filter(field_attr > value['>'])
                    elif '<' in value:
                        query = query.filter(field_attr < value['<'])
                    elif 'between' in value:
                        start, end = value['between']
                        query = query.filter(field_attr.between(start, end))
                    elif 'not_in' in value:
                        query = query.filter(~field_attr.in_(value['not_in']))
                    elif 'like' in value:
                        query = query.filter(field_attr.like(value['like']))
                    elif 'ilike' in value:
                        query = query.filter(field_attr.ilike(value['ilike']))
                    else:
                        # Invalid dict format - raise error instead of trying to use as equality
                        raise ValueError(f"Invalid filter format for field '{field}': {value}. "
                                       f"Supported dict operators: 'not', '>=', '<=', '>', '<', 'between', 'not_in', 'like', 'ilike'")
                else:
                    # Simple equality
                    query = query.filter(field_attr == value)

        return query

    def _apply_search(self, query: Query, search_query: str, search_fields: List[str]) -> Query:
        """Apply text search across multiple fields."""
        if not search_query or not search_fields:
            return query

        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                search_conditions.append(field_attr.ilike(f"%{search_query}%"))

        if search_conditions:
            query = query.filter(or_(*search_conditions))

        return query

    def _apply_soft_delete_filter(self, query: Query, include_deleted: bool) -> Query:
        """Filter out soft-deleted records when applicable."""
        if not include_deleted and self._has_soft_delete():
            query = query.filter(self.model.deleted_at.is_(None))
        return query

    def _apply_sorting(self, query: Query, sort_by: str, sort_desc: bool = False) -> Query:
        """Apply sorting to query."""
        if hasattr(self.model, sort_by):
            sort_column = getattr(self.model, sort_by)
            query = query.order_by(desc(sort_column) if sort_desc else asc(sort_column))
        return query

    def _apply_pagination(self, query: Query, limit: Optional[int], skip: int) -> Query:
        """Apply pagination to query."""
        if skip > 0:
            query = query.offset(skip)
        if limit and limit > 0:
            query = query.limit(limit)
        return query

    def _apply_eager_loading(self, query: Query, options: Optional[List]) -> Query:
        """Apply SQLAlchemy query options for eager loading."""
        if options:
            for option in options:
                query = query.options(option)
        return query

    def _build_base_query(
        self,
        session: Session,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        limit: Optional[int] = None,
        skip: int = 0,
        include_deleted: bool = False,
        options: Optional[List] = None
    ) -> Query:
        """
        Build complete SQLAlchemy query using all DRY helpers.

        This is the master query builder that orchestrates all filtering,
        searching, sorting, pagination, and eager loading operations.
        """
        query = session.query(self.model)

        # Apply all query modifications using DRY helpers
        query = self._apply_filters(query, filters)
        query = self._apply_search(query, search_query, search_fields)
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = self._apply_sorting(query, sort_by, sort_desc)
        query = self._apply_pagination(query, limit, skip)
        query = self._apply_eager_loading(query, options)

        return query

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
        Get multiple records with enhanced filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return (0 for all)
            filters: Enhanced dictionary of field filters (see _apply_filters for supported formats)
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            include_deleted: Whether to include soft-deleted records
            options: SQLAlchemy query options (e.g., joinedload, selectinload)

        Returns:
            List of model instances

        Example:
            users = user_crud.get_multi(
                filters={
                    "active": True,
                    "email": {"not": None},
                    "department": ["Engineering", "Product"],
                    "created_at": {">=": "2024-01-01"}
                },
                sort_by="created_at",
                limit=50
            )
        """
        with self.db_client.session_scope() as session:
            # Use DRY query builder
            query = self._build_base_query(
                session=session,
                filters=filters,
                sort_by=sort_by,
                sort_desc=sort_desc,
                limit=limit,
                skip=skip,
                include_deleted=include_deleted,
                options=options
            )

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
        Search records across multiple fields with enhanced filtering.

        Args:
            search_query: Text to search for
            search_fields: List of field names to search in
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Enhanced dictionary of additional filters to apply
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            include_deleted: Whether to include soft-deleted records
            options: SQLAlchemy query options

        Returns:
            List of matching model instances

        Example:
            users = user_crud.search(
                search_query="john",
                search_fields=["name", "email"],
                filters={
                    "active": True,
                    "department": ["Engineering", "Product"]
                },
                limit=20
            )
        """
        with self.db_client.session_scope() as session:
            # Use DRY query builder
            query = self._build_base_query(
                session=session,
                filters=filters,
                search_query=search_query,
                search_fields=search_fields,
                sort_by=sort_by,
                sort_desc=sort_desc,
                limit=limit,
                skip=skip,
                include_deleted=include_deleted,
                options=options
            )

            instances = query.all()
            return [self.db_client.detach_object(instance, session) for instance in instances]

    def count(self, filters: Optional[Dict[str, Any]] = None, include_deleted: bool = False) -> int:
        """
        Count records with enhanced filtering.

        Args:
            filters: Enhanced dictionary of field filters
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of matching records

        Example:
            count = user_crud.count(filters={
                "active": True,
                "email": {"not": None},
                "created_at": {">=": "2024-01-01"}
            })
        """
        with self.db_client.session_scope() as session:
            query = session.query(func.count(self.model.id))

            # Apply enhanced filters and soft delete using DRY helpers
            query = self._apply_filters(query, filters)
            query = self._apply_soft_delete_filter(query, include_deleted)

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
            query = session.query(self.model.id)

            # Use DRY helpers
            query = self._apply_filters(query, {field: value})
            query = self._apply_soft_delete_filter(query, include_deleted)

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
            # Use DRY query builder
            query = self._build_base_query(
                session=session,
                filters={field: value},
                include_deleted=include_deleted,
                limit=1
            )

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

        Note: This method is now redundant with enhanced filtering.
        You can use get_multi(filters={"field": None}) or get_multi(filters={"field": {"not": None}})

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

        # Use enhanced filtering instead of manual query building
        if is_null:
            filters = {field: None}
        else:
            filters = {field: {"not": None}}

        return self.get_multi(
            filters=filters,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted,
            sort_by=sort_by
        )

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

    # ===== String Schema Integration =====

    def query_with_schema(
        self,
        schema_str: str,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        limit: Optional[int] = None,
        skip: int = 0,
        include_relationships: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query database and return results validated against string schema.

        This method provides a schema-first approach to database queries,
        automatically validating results against string-schema definitions.

        Args:
            schema_str: String schema definition (e.g., "id:int, name:string, email:email")
                       or predefined schema name ("basic", "full")
            filters: Enhanced dictionary of field filters
            search_query: Text search query
            search_fields: Fields to search in
            sort_by: Field to sort by
            sort_desc: Sort descending if True
            limit: Maximum number of results
            skip: Number of results to skip
            include_relationships: List of relationship names to eager load
            include_deleted: Include soft-deleted records

        Returns:
            List of dictionaries matching the schema

        Example:
            # Using custom schema with enhanced filtering
            articles = article_crud.query_with_schema(
                schema_str="id:int, title:string, created_at:datetime",
                filters={
                    "status": "published",
                    "created_at": {">=": "2024-01-01"},
                    "author_id": {"not": None}
                },
                search_query="AI",
                search_fields=["title", "body"],
                sort_by="created_at",
                sort_desc=True,
                limit=20
            )
        """
        helper = self._get_schema_helper()
        return helper.query_with_schema(
            schema_str=schema_str,
            filters=filters,
            search_query=search_query,
            search_fields=search_fields,
            sort_by=sort_by,
            sort_desc=sort_desc,
            limit=limit,
            skip=skip,
            include_relationships=include_relationships,
            include_deleted=include_deleted
        )

    def get_one_with_schema(
        self,
        schema_str: str,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        include_relationships: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single record with schema validation.

        This method is perfect for the 90% use case where you need to fetch
        a single record with validated, API-ready results.

        Args:
            schema_str: String schema definition (e.g., "id:int, name:string, email:email")
                       or predefined schema name ("basic", "full")
            filters: Enhanced dictionary of field filters
            search_query: Text search query
            search_fields: Fields to search in
            sort_by: Field to sort by (if multiple matches)
            sort_desc: Sort descending if True
            include_relationships: List of relationship names to eager load
            include_deleted: Include soft-deleted records

        Returns:
            Single validated dictionary or None if not found

        Example:
            # Get user by ID
            user = user_crud.get_one_with_schema(
                "id:int, name:string, email:email, active:bool",
                filters={"id": 123}
            )

            # Get latest published article
            article = article_crud.get_one_with_schema(
                "id:int, title:string, published_at:datetime",
                filters={"status": "published"},
                sort_by="published_at",
                sort_desc=True
            )
        """
        results = self.query_with_schema(
            schema_str=schema_str,
            filters=filters,
            search_query=search_query,
            search_fields=search_fields,
            sort_by=sort_by,
            sort_desc=sort_desc,
            limit=1,
            include_relationships=include_relationships,
            include_deleted=include_deleted
        )
        return results[0] if results else None

    def get_scalar_with_schema(
        self,
        field: str,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        include_deleted: bool = False
    ) -> Any:
        """
        Get a single field value with optional filtering.

        This method is perfect for getting scalar values like counts, names,
        or specific field values without fetching entire records.

        Args:
            field: Field name to retrieve (e.g., "name", "email") or
                  aggregation function (e.g., "count(*)", "sum(price)")
            filters: Enhanced dictionary of field filters
            search_query: Text search query
            search_fields: Fields to search in
            sort_by: Field to sort by (if multiple matches)
            sort_desc: Sort descending if True
            include_deleted: Include soft-deleted records

        Returns:
            Single field value or None if not found

        Example:
            # Get user name by ID
            name = user_crud.get_scalar_with_schema("name", filters={"id": 123})

            # Get count of active users
            count = user_crud.get_scalar_with_schema("count(*)", filters={"active": True})

            # Get highest price
            max_price = product_crud.get_scalar_with_schema("max(price)")
        """
        # Handle aggregation functions
        if "(" in field and ")" in field:
            # This is an aggregation like count(*), sum(price), etc.
            result = self.aggregate_with_schema(
                aggregations={"result": field},
                schema_str="result:float?",  # Use flexible type for aggregations
                filters=filters,
                include_deleted=include_deleted
            )
            return result[0]["result"] if result else None
        else:
            # Regular field - determine appropriate type
            field_type = "string?"  # Default to nullable string

            # Try to infer type from model if possible
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                if hasattr(column.property, 'columns'):
                    col_type = column.property.columns[0].type
                    if hasattr(col_type, 'python_type'):
                        python_type = col_type.python_type
                        if python_type == int:
                            field_type = "int?"
                        elif python_type == float:
                            field_type = "float?"
                        elif python_type == bool:
                            field_type = "bool?"
                        elif python_type == datetime:
                            field_type = "datetime?"

            result = self.get_one_with_schema(
                f"{field}:{field_type}",
                filters=filters,
                search_query=search_query,
                search_fields=search_fields,
                sort_by=sort_by,
                sort_desc=sort_desc,
                include_deleted=include_deleted
            )
            return result[field] if result else None

    def paginated_query_with_schema(
        self,
        schema_str: str,
        page: int = 1,
        per_page: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Paginated query with string schema validation.

        Provides paginated results with automatic schema validation,
        eliminating the need for separate response models.

        Args:
            schema_str: String schema definition or predefined schema name
            page: Page number (1-based)
            per_page: Number of items per page
            **kwargs: Additional arguments for query_with_schema

        Returns:
            Dictionary with items and pagination info, all validated against schemas

        Example:
            result = article_crud.paginated_query_with_schema(
                schema_str="id:int, title:string, body:text, created_at:datetime",
                page=1,
                per_page=20,
                filters={
                    "category_id": 1,
                    "status": "published",
                    "created_at": {">=": "2024-01-01"}
                },
                search_query="technology",
                search_fields=["title", "body"]
            )
            # Returns: {
            #   "items": [...],
            #   "total": 100,
            #   "page": 1,
            #   "per_page": 20,
            #   "has_next": true,
            #   ...
            # }
        """
        helper = self._get_schema_helper()
        return helper.paginated_query_with_schema(
            schema_str=schema_str,
            page=page,
            per_page=per_page,
            **kwargs
        )

    def aggregate_with_schema(
        self,
        aggregations: Dict[str, str],
        schema_str: str,
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Perform aggregation queries with schema validation.

        Args:
            aggregations: Dict of {alias: "function(field)"}
                         e.g., {"count": "count(*)", "avg_size": "avg(size)"}
            schema_str: Schema to validate results against
            group_by: List of fields to group by
            filters: Enhanced filters to apply
            include_deleted: Include soft-deleted records

        Returns:
            List of aggregation results as dictionaries

        Example:
            stats = article_crud.aggregate_with_schema(
                aggregations={"total": "count(*)", "avg_length": "avg(length)"},
                schema_str="category_id:int, total:int, avg_length:float",
                group_by=["category_id"],
                filters={
                    "published": True,
                    "created_at": {">=": "2024-01-01"}
                }
            )
        """
        helper = self._get_schema_helper()
        return helper.aggregate_with_schema(
            aggregations=aggregations,
            schema_str=schema_str,
            group_by=group_by,
            filters=filters,
            include_deleted=include_deleted
        )

    def query_with_schema(
        self,
        schema_str: str,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        limit: Optional[int] = None,
        skip: int = 0,
        include_relationships: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query database and return results validated against string schema.

        This method provides a schema-first approach to database queries,
        automatically validating results against string-schema definitions.

        Args:
            schema_str: String schema definition (e.g., "id:int, name:string, email:email")
                       or predefined schema name ("basic", "full")
            filters: Dictionary of field filters
            search_query: Text search query
            search_fields: Fields to search in
            sort_by: Field to sort by
            sort_desc: Sort descending if True
            limit: Maximum number of results
            skip: Number of results to skip
            include_relationships: List of relationship names to eager load
            include_deleted: Include soft-deleted records

        Returns:
            List of dictionaries matching the schema

        Example:
            # Using predefined schema
            articles = article_ops.query_with_schema("basic", filters={"category_id": 1})

            # Using custom schema
            articles = article_ops.query_with_schema(
                "id:int, title:string, created_at:datetime",
                search_query="AI",
                search_fields=["title", "body"]
            )
        """
        helper = self._get_schema_helper()
        return helper.query_with_schema(
            schema_str=schema_str,
            filters=filters,
            search_query=search_query,
            search_fields=search_fields,
            sort_by=sort_by,
            sort_desc=sort_desc,
            limit=limit,
            skip=skip,
            include_relationships=include_relationships,
            include_deleted=include_deleted
        )

    def paginated_query_with_schema(
        self,
        schema_str: str,
        page: int = 1,
        per_page: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Paginated query with string schema validation.

        Provides paginated results with automatic schema validation,
        eliminating the need for separate response models.

        Args:
            schema_str: String schema definition or predefined schema name
            page: Page number (1-based)
            per_page: Number of items per page
            **kwargs: Additional arguments for query_with_schema

        Returns:
            Dictionary with items and pagination info, all validated against schemas

        Example:
            result = article_ops.paginated_query_with_schema(
                "id:int, title:string, body:text, created_at:datetime",
                page=1,
                per_page=20,
                filters={"category_id": 1},
                search_query="technology",
                search_fields=["title", "body"]
            )
            # Returns: {
            #   "items": [...],
            #   "total": 100,
            #   "page": 1,
            #   "per_page": 20,
            #   "has_next": true,
            #   ...
            # }
        """
        helper = self._get_schema_helper()
        return helper.paginated_query_with_schema(
            schema_str=schema_str,
            page=page,
            per_page=per_page,
            **kwargs
        )

    def aggregate_with_schema(
        self,
        aggregations: Dict[str, str],
        schema_str: str,
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Perform aggregation queries with schema validation.

        Args:
            aggregations: Dict of {alias: "function(field)"}
                         e.g., {"count": "count(*)", "avg_size": "avg(size)"}
            schema_str: Schema to validate results against
            group_by: List of fields to group by
            filters: Filters to apply
            include_deleted: Include soft-deleted records

        Returns:
            List of aggregation results as dictionaries

        Example:
            stats = article_ops.aggregate_with_schema(
                aggregations={"total": "count(*)", "avg_length": "avg(length)"},
                schema_str="category_id:int, total:int, avg_length:number",
                group_by=["category_id"],
                filters={"published": True}
            )
        """
        helper = self._get_schema_helper()
        return helper.aggregate_with_schema(
            aggregations=aggregations,
            schema_str=schema_str,
            group_by=group_by,
            filters=filters,
            include_deleted=include_deleted
        )

    def to_dict(self, instance: ModelType, schema: str) -> Dict[str, Any]:
        """
        Convert SQLAlchemy model instance to validated dictionary.

        This allows you to work with SQLAlchemy instances for complex operations
        and then convert to validated dicts for API responses.

        Args:
            instance: SQLAlchemy model instance
            schema: String schema definition for validation

        Returns:
            Validated dictionary matching the schema

        Example:
            # Get SQLAlchemy instance for complex operations
            user = user_crud.get_by_id(123)
            user.update_last_login()
            user.posts.append(new_post)

            # Convert to dict for API response
            api_response = user_crud.to_dict(user, "id:int, name:string, email:email, last_login:datetime")
        """
        helper = self._get_schema_helper()
        return helper._model_to_dict_with_schema(instance, schema)

    def to_dict_list(self, instances: List[ModelType], schema: str) -> List[Dict[str, Any]]:
        """
        Convert list of SQLAlchemy instances to validated dictionaries.

        Args:
            instances: List of SQLAlchemy model instances
            schema: String schema definition for validation

        Returns:
            List of validated dictionaries

        Example:
            # Get SQLAlchemy instances
            users = user_crud.get_multi(filters={"active": True})

            # Convert to dicts for API response
            api_users = user_crud.to_dict_list(users, "id:int, name:string, email:email")
        """
        helper = self._get_schema_helper()
        return [helper._model_to_dict_with_schema(instance, schema) for instance in instances]

    def add_schema(self, name: str, schema: str):
        """
        Add a custom schema definition for this model.

        Args:
            name: Schema name for later reference
            schema: String schema definition

        Example:
            article_crud.add_schema("summary", "id:int, title:string, summary:text?")
            articles = article_crud.query_with_schema("summary")
        """
        helper = self._get_schema_helper()
        helper.add_custom_schema(name, schema)

    def get_schema(self, name: str) -> str:
        """
        Get a predefined schema by name.

        Args:
            name: Schema name

        Returns:
            Schema definition string
        """
        helper = self._get_schema_helper()
        return helper.get_schema(name)
