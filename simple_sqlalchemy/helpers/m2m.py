"""
Many-to-many relationship helper for simple-sqlalchemy
"""

import logging
from typing import Type, TypeVar, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')


class M2MHelper:
    """
    Helper class for managing many-to-many relationships.
    
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
        Initialize M2M helper.
        
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
    
    def add_relationship(self, source_id: int, target_id: int) -> Optional[T]:
        """
        Add a many-to-many relationship between two records.
        
        Args:
            source_id: ID of the source record
            target_id: ID of the target record
            
        Returns:
            Updated source model instance or None
        """
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
        """
        Remove a many-to-many relationship between two records.
        
        Args:
            source_id: ID of the source record
            target_id: ID of the target record
            
        Returns:
            Updated source model instance or None
        """
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
        """
        Get all target records related to a source record.
        
        Args:
            source_id: ID of the source record
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of related target model instances
        """
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
    
    def get_sources_for_target(
        self,
        target_id: int,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[T]:
        """
        Get all source records related to a target record.
        
        Args:
            target_id: ID of the target record
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of related source model instances
        """
        with self.db_client.session_scope() as session:
            target = session.query(self.target_model).filter(
                self.target_model.id == target_id
            ).first()
            
            if not target:
                return []
            
            # Get the relationship collection
            target_collection = getattr(target, self.target_attr)
            
            # Filter out soft-deleted records if needed
            if not include_deleted and hasattr(self.source_model, 'deleted_at'):
                related_items = [item for item in target_collection if item.deleted_at is None]
            else:
                related_items = list(target_collection)
            
            # Apply pagination
            if skip > 0 or limit > 0:
                related_items = related_items[skip:skip + limit] if limit > 0 else related_items[skip:]
            
            return [self.db_client.detach_object(item, session) for item in related_items]
    
    def count_related_for_source(self, source_id: int) -> int:
        """
        Count target records related to a source record.
        
        Args:
            source_id: ID of the source record
            
        Returns:
            Number of related target records
        """
        with self.db_client.session_scope() as session:
            source = session.query(self.source_model).filter(
                self.source_model.id == source_id
            ).first()
            
            if not source:
                return 0
            
            source_collection = getattr(source, self.source_attr)
            return len(source_collection)
    
    def count_sources_for_target(self, target_id: int, include_deleted: bool = False) -> int:
        """
        Count source records related to a target record.
        
        Args:
            target_id: ID of the target record
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Number of related source records
        """
        with self.db_client.session_scope() as session:
            target = session.query(self.target_model).filter(
                self.target_model.id == target_id
            ).first()
            
            if not target:
                return 0
            
            target_collection = getattr(target, self.target_attr)
            
            # Filter out soft-deleted records if needed
            if not include_deleted and hasattr(self.source_model, 'deleted_at'):
                return len([item for item in target_collection if item.deleted_at is None])
            else:
                return len(target_collection)
    
    def relationship_exists(self, source_id: int, target_id: int) -> bool:
        """
        Check if a relationship exists between two records.
        
        Args:
            source_id: ID of the source record
            target_id: ID of the target record
            
        Returns:
            True if relationship exists, False otherwise
        """
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
