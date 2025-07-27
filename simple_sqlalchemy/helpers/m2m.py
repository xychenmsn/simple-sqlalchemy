"""
Many-to-many relationship helper for simple-sqlalchemy
"""

import logging
from typing import Type, TypeVar, List, Optional, Tuple, Any, Protocol
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, exists, Column
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')


class M2MStrategy(ABC):
    """Abstract base class for M2M operation strategies"""

    def __init__(self, db_client, source_model: Type[T], target_model: Type[U],
                 source_attr: str, target_attr: str):
        self.db_client = db_client
        self.source_model = source_model
        self.target_model = target_model
        self.source_attr = source_attr
        self.target_attr = target_attr

    @abstractmethod
    def add_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        pass

    @abstractmethod
    def remove_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        pass

    @abstractmethod
    def get_related_for_source(self, source_id: int, skip: int = 0, limit: int = 100) -> List[U]:
        pass

    @abstractmethod
    def get_sources_for_target(self, target_id: int, skip: int = 0, limit: int = 100) -> List[T]:
        pass

    @abstractmethod
    def count_related_for_source(self, source_id: int) -> int:
        pass

    @abstractmethod
    def count_sources_for_target(self, target_id: int) -> int:
        pass

    @abstractmethod
    def relationship_exists(self, source_id: int, target_id: int) -> bool:
        pass


class EfficientM2MStrategy(M2MStrategy):
    """Efficient M2M strategy using direct SQL queries"""

    def __init__(self, db_client, source_model: Type[T], target_model: Type[U],
                 source_attr: str, target_attr: str):
        super().__init__(db_client, source_model, target_model, source_attr, target_attr)

        # Cache association table info at initialization
        table_info = _get_association_table_info(source_model, source_attr)
        if table_info is None:
            raise ValueError("Cannot create EfficientM2MStrategy: association table info not available")

        self.association_table, self.source_fk_col, self.target_fk_col = table_info
        logger.debug(f"EfficientM2MStrategy initialized for {source_model.__name__} -> {target_model.__name__}")

    def relationship_exists(self, source_id: int, target_id: int) -> bool:
        """Check if relationship exists using SQL EXISTS"""
        with self.db_client.session_scope() as session:
            try:
                exists_query = session.query(
                    exists().where(
                        and_(
                            self.source_fk_col == source_id,
                            self.target_fk_col == target_id
                        )
                    )
                ).scalar()

                return bool(exists_query)

            except SQLAlchemyError as e:
                logger.error(f"Error in efficient relationship_exists: {e}")
                raise

    def add_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """Add relationship with efficient duplicate check"""
        with self.db_client.session_scope() as session:
            try:
                # First verify both records exist (lightweight check)
                source_exists = session.query(
                    session.query(self.source_model).filter(
                        self.source_model.id == source_id
                    ).exists()
                ).scalar()

                target_exists = session.query(
                    session.query(self.target_model).filter(
                        self.target_model.id == target_id
                    ).exists()
                ).scalar()

                if not source_exists or not target_exists:
                    logger.warning(f"Source or target not found: source_id={source_id}, target_id={target_id}")
                    return None

                # Check if relationship already exists
                if self.relationship_exists(source_id, target_id):
                    # Relationship exists, just return the source object
                    source = session.query(self.source_model).filter(
                        self.source_model.id == source_id
                    ).first()
                    return self.db_client.detach_object(source, session)

                # Insert into association table directly
                session.execute(
                    self.association_table.insert().values(
                        **{
                            self.source_fk_col.name: source_id,
                            self.target_fk_col.name: target_id
                        }
                    )
                )
                session.flush()

                # Return the updated source object
                source = session.query(self.source_model).filter(
                    self.source_model.id == source_id
                ).first()

                return self.db_client.detach_object(source, session)

            except SQLAlchemyError as e:
                logger.error(f"Error adding M2M relationship: {e}")
                return None

    def remove_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """Remove relationship using direct SQL DELETE"""
        with self.db_client.session_scope() as session:
            try:
                # Delete from association table directly
                result = session.execute(
                    self.association_table.delete().where(
                        and_(
                            self.source_fk_col == source_id,
                            self.target_fk_col == target_id
                        )
                    )
                )

                if result.rowcount == 0:
                    logger.info(f"No relationship found to remove: source_id={source_id}, target_id={target_id}")

                session.flush()

                # Return the source object
                source = session.query(self.source_model).filter(
                    self.source_model.id == source_id
                ).first()

                if not source:
                    return None

                return self.db_client.detach_object(source, session)

            except SQLAlchemyError as e:
                logger.error(f"Error removing M2M relationship: {e}")
                return None

    def get_related_for_source(self, source_id: int, skip: int = 0, limit: int = 100) -> List[U]:
        """Get related records using efficient JOIN with pagination"""
        with self.db_client.session_scope() as session:
            try:
                # Direct JOIN query with pagination
                query = session.query(self.target_model).join(
                    self.association_table,
                    self.target_model.id == self.target_fk_col
                ).filter(
                    self.source_fk_col == source_id
                )

                # Apply pagination at SQL level
                if skip > 0:
                    query = query.offset(skip)
                if limit > 0:
                    query = query.limit(limit)

                related_items = query.all()

                return [self.db_client.detach_object(item, session) for item in related_items]

            except SQLAlchemyError as e:
                logger.error(f"Error getting related records: {e}")
                return []

    def get_sources_for_target(self, target_id: int, skip: int = 0, limit: int = 100) -> List[T]:
        """Get source records using efficient JOIN"""
        with self.db_client.session_scope() as session:
            try:
                # Direct JOIN query
                query = session.query(self.source_model).join(
                    self.association_table,
                    self.source_model.id == self.source_fk_col
                ).filter(
                    self.target_fk_col == target_id
                )

                # Apply pagination at SQL level
                if skip > 0:
                    query = query.offset(skip)
                if limit > 0:
                    query = query.limit(limit)

                related_items = query.all()

                return [self.db_client.detach_object(item, session) for item in related_items]

            except SQLAlchemyError as e:
                logger.error(f"Error getting source records: {e}")
                return []

    def count_related_for_source(self, source_id: int) -> int:
        """Count related records using efficient SQL COUNT"""
        with self.db_client.session_scope() as session:
            try:
                count = session.query(func.count()).select_from(
                    self.association_table
                ).filter(
                    self.source_fk_col == source_id
                ).scalar()

                return count or 0

            except SQLAlchemyError as e:
                logger.error(f"Error counting related records: {e}")
                return 0

    def count_sources_for_target(self, target_id: int) -> int:
        """Count source records using efficient SQL COUNT"""
        with self.db_client.session_scope() as session:
            try:
                # Simple count on association table
                count = session.query(func.count()).select_from(
                    self.association_table
                ).filter(
                    self.target_fk_col == target_id
                ).scalar()

                return count or 0

            except SQLAlchemyError as e:
                logger.error(f"Error counting source records: {e}")
                return 0


class OriginalM2MStrategy(M2MStrategy):
    """Original M2M strategy using SQLAlchemy relationship loading"""

    def __init__(self, db_client, source_model: Type[T], target_model: Type[U],
                 source_attr: str, target_attr: str):
        super().__init__(db_client, source_model, target_model, source_attr, target_attr)
        logger.debug(f"OriginalM2MStrategy initialized for {source_model.__name__} -> {target_model.__name__}")

    def add_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """Add a many-to-many relationship between two records."""
        with self.db_client.session_scope() as session:
            try:
                # Get source and target instances
                source = session.query(self.source_model).filter(
                    self.source_model.id == source_id
                ).first()
                target = session.query(self.target_model).filter(
                    self.target_model.id == target_id
                ).first()

                if not source or not target:
                    logger.warning(f"Source or target not found: source_id={source_id}, target_id={target_id}")
                    return None

                # Get the relationship collection
                source_collection = getattr(source, self.source_attr)

                # Check if relationship already exists
                if target not in source_collection:
                    source_collection.append(target)
                    session.flush()
                    session.refresh(source)

                return self.db_client.detach_object(source, session)

            except SQLAlchemyError as e:
                logger.error(f"Error adding M2M relationship: {e}")
                return None

    def remove_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """Remove a many-to-many relationship between two records."""
        with self.db_client.session_scope() as session:
            try:
                # Get source and target instances
                source = session.query(self.source_model).filter(
                    self.source_model.id == source_id
                ).first()
                target = session.query(self.target_model).filter(
                    self.target_model.id == target_id
                ).first()

                if not source or not target:
                    logger.warning(f"Source or target not found: source_id={source_id}, target_id={target_id}")
                    return None

                # Get the relationship collection
                source_collection = getattr(source, self.source_attr)

                # Remove relationship if it exists
                if target in source_collection:
                    source_collection.remove(target)
                    session.flush()
                    session.refresh(source)

                return self.db_client.detach_object(source, session)

            except SQLAlchemyError as e:
                logger.error(f"Error removing M2M relationship: {e}")
                return None

    def get_related_for_source(self, source_id: int, skip: int = 0, limit: int = 100) -> List[U]:
        """Get all target records related to a source record."""
        with self.db_client.session_scope() as session:
            source = session.query(self.source_model).filter(
                self.source_model.id == source_id
            ).first()

            if not source:
                return []

            # Get the relationship collection
            source_collection = getattr(source, self.source_attr)

            # Apply pagination
            if skip > 0 or limit > 0:
                related_items = source_collection[skip:skip + limit] if limit > 0 else source_collection[skip:]
            else:
                related_items = list(source_collection)

            return [self.db_client.detach_object(item, session) for item in related_items]

    def get_sources_for_target(self, target_id: int, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all source records related to a target record."""
        with self.db_client.session_scope() as session:
            target = session.query(self.target_model).filter(
                self.target_model.id == target_id
            ).first()

            if not target:
                return []

            # Get the relationship collection
            target_collection = getattr(target, self.target_attr)
            related_items = list(target_collection)

            # Apply pagination
            if skip > 0 or limit > 0:
                related_items = related_items[skip:skip + limit] if limit > 0 else related_items[skip:]

            return [self.db_client.detach_object(item, session) for item in related_items]

    def count_related_for_source(self, source_id: int) -> int:
        """Count target records related to a source record."""
        with self.db_client.session_scope() as session:
            source = session.query(self.source_model).filter(
                self.source_model.id == source_id
            ).first()

            if not source:
                return 0

            source_collection = getattr(source, self.source_attr)
            return len(source_collection)

    def count_sources_for_target(self, target_id: int) -> int:
        """Count source records related to a target record."""
        with self.db_client.session_scope() as session:
            target = session.query(self.target_model).filter(
                self.target_model.id == target_id
            ).first()

            if not target:
                return 0

            target_collection = getattr(target, self.target_attr)
            return len(target_collection)

    def relationship_exists(self, source_id: int, target_id: int) -> bool:
        """Check if a relationship exists between two records."""
        with self.db_client.session_scope() as session:
            source = session.query(self.source_model).filter(
                self.source_model.id == source_id
            ).first()
            target = session.query(self.target_model).filter(
                self.target_model.id == target_id
            ).first()

            if not source or not target:
                return False

            source_collection = getattr(source, self.source_attr)
            return target in source_collection


def create_m2m_strategy(db_client, source_model: Type[T], target_model: Type[U],
                       source_attr: str, target_attr: str) -> M2MStrategy:
    """
    Factory function to create the appropriate M2M strategy based on relationship complexity.

    Returns:
        EfficientM2MStrategy for simple relationships, OriginalM2MStrategy for complex ones
    """
    try:
        # Check if we can use the efficient strategy
        if _can_use_efficient_query(source_model, target_model, source_attr):
            logger.info(f"Using EfficientM2MStrategy for {source_model.__name__} -> {target_model.__name__}")
            return EfficientM2MStrategy(db_client, source_model, target_model, source_attr, target_attr)
        else:
            logger.info(f"Using OriginalM2MStrategy for {source_model.__name__} -> {target_model.__name__}")
            return OriginalM2MStrategy(db_client, source_model, target_model, source_attr, target_attr)
    except Exception as e:
        logger.warning(f"Failed to create EfficientM2MStrategy, falling back to OriginalM2MStrategy: {e}")
        return OriginalM2MStrategy(db_client, source_model, target_model, source_attr, target_attr)


class M2MHelper:
    """
    Helper class for managing many-to-many relationships.

    Automatically selects the most efficient strategy based on relationship complexity.
    Provides utilities for adding, removing, and querying M2M relationships
    between two model classes.
    """

    def __init__(
        self,
        db_client,
        source_model: Type[T],
        target_model: Type[U],
        source_attr: str,
        target_attr: str
    ):
        """
        Initialize M2M helper with automatic strategy selection.

        Args:
            db_client: Database client instance
            source_model: Source model class
            target_model: Target model class
            source_attr: Attribute name on source model for the relationship
            target_attr: Attribute name on target model for the relationship
        """
        self.db_client = db_client
        self.source_model = source_model
        self.target_model = target_model
        self.source_attr = source_attr
        self.target_attr = target_attr

        # Select the appropriate strategy at initialization
        self._strategy = create_m2m_strategy(
            db_client, source_model, target_model, source_attr, target_attr
        )

    @property
    def strategy_type(self) -> str:
        """Return the type of strategy being used"""
        return type(self._strategy).__name__
    
    def add_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """
        Add a many-to-many relationship between two records.

        Args:
            source_id: ID of the source record
            target_id: ID of the target record

        Returns:
            Updated source model instance or None
        """
        return self._strategy.add_relationship(source_id, target_id)
    
    def remove_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """
        Remove a many-to-many relationship between two records.

        Args:
            source_id: ID of the source record
            target_id: ID of the target record

        Returns:
            Updated source model instance or None
        """
        return self._strategy.remove_relationship(source_id, target_id)
    
    def get_related_for_source(self, source_id: int, skip: int = 0, limit: int = 100) -> List[U]:
        """
        Get all target records related to a source record.

        Args:
            source_id: ID of the source record
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of related target model instances
        """
        return self._strategy.get_related_for_source(source_id, skip, limit)
    
    def get_sources_for_target(
        self,
        target_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        Get all source records related to a target record.

        Args:
            target_id: ID of the target record
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of related source model instances
        """
        return self._strategy.get_sources_for_target(target_id, skip, limit)

    def count_related_for_source(self, source_id: int) -> int:
        """
        Count target records related to a source record.

        Args:
            source_id: ID of the source record

        Returns:
            Number of related target records
        """
        return self._strategy.count_related_for_source(source_id)

    def count_sources_for_target(self, target_id: int) -> int:
        """
        Count source records related to a target record.

        Args:
            target_id: ID of the target record

        Returns:
            Number of related source records
        """
        return self._strategy.count_sources_for_target(target_id)
    
    def relationship_exists(self, source_id: int, target_id: int) -> bool:
        """
        Check if a relationship exists between two records.

        Args:
            source_id: ID of the source record
            target_id: ID of the target record

        Returns:
            True if relationship exists, False otherwise
        """
        return self._strategy.relationship_exists(source_id, target_id)

    # Backward compatibility methods (deprecated)
    def relationship_exists_fast(self, source_id: int, target_id: int) -> bool:
        """Deprecated: Use relationship_exists() instead. Kept for backward compatibility."""
        logger.warning("relationship_exists_fast is deprecated. Use relationship_exists() instead.")
        return self.relationship_exists(source_id, target_id)

    def count_sources_for_target_fast(self, target_id: int, include_deleted: bool = False) -> int:
        """Deprecated: Use count_sources_for_target() instead. Kept for backward compatibility."""
        logger.warning("count_sources_for_target_fast is deprecated. Use count_sources_for_target() instead.")
        return self.count_sources_for_target(target_id)






# Utility functions for efficient M2M operations
def _get_association_table_info(source_model: Type, source_attr: str) -> Optional[Tuple[Any, Column, Column]]:
    """
    Extract association table and foreign key columns from a relationship.

    Returns:
        Tuple of (association_table, source_fk_column, target_fk_column) or None if not applicable
    """
    try:
        # Get the relationship property
        relationship_prop = getattr(source_model, source_attr).property

        # Check if it's a many-to-many relationship with secondary table
        if not hasattr(relationship_prop, 'secondary') or relationship_prop.secondary is None:
            return None

        association_table = relationship_prop.secondary

        # Find the foreign key columns
        source_fk_col = None
        target_fk_col = None

        for col in association_table.columns:
            if col.foreign_keys:
                fk = list(col.foreign_keys)[0]
                if fk.column.table == source_model.__table__:
                    source_fk_col = col
                elif hasattr(relationship_prop, 'mapper') and fk.column.table == relationship_prop.mapper.class_.__table__:
                    target_fk_col = col

        if source_fk_col is None or target_fk_col is None:
            return None

        return association_table, source_fk_col, target_fk_col

    except Exception as e:
        logger.debug(f"Could not extract association table info: {e}")
        return None


def _can_use_efficient_query(source_model: Type, target_model: Type, source_attr: str) -> bool:
    """
    Check if we can use efficient SQL queries for this relationship.

    Returns True if:
    - It's a standard M2M relationship with secondary table
    - Association table has only foreign key columns (no extra metadata)
    - Foreign key columns can be auto-detected
    """
    try:
        table_info = _get_association_table_info(source_model, source_attr)
        if table_info is None:
            return False

        association_table, source_fk_col, target_fk_col = table_info

        # Check if table has only the two foreign key columns
        # If it has more columns, it might have metadata we need to preserve
        fk_columns = {source_fk_col.name, target_fk_col.name}
        all_columns = {col.name for col in association_table.columns}

        # Allow for additional columns that are commonly used for metadata
        # but don't affect the core relationship logic
        allowed_extra_columns = {'created_at', 'updated_at', 'assigned_at', 'tagged_at'}
        extra_columns = all_columns - fk_columns

        # If there are extra columns beyond the allowed metadata columns,
        # fall back to the safe method
        if extra_columns and not extra_columns.issubset(allowed_extra_columns):
            logger.debug(f"Association table has complex columns: {extra_columns}")
            return False

        return True

    except Exception as e:
        logger.debug(f"Cannot use efficient query: {e}")
        return False
