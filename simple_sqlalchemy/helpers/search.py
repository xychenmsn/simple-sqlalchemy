"""
Search helper for complex queries in simple-sqlalchemy
"""

import logging
from typing import Type, TypeVar, Dict, Any, List, Callable, Optional
from sqlalchemy.orm import Session, Query
from sqlalchemy import desc, asc, func

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SearchHelper:
    """
    Helper class for building complex search queries.
    
    Provides utilities for advanced querying, pagination with counts,
    and custom query building.
    """
    
    def __init__(self, db_client, model: Type[T]):
        """
        Initialize SearchHelper.
        
        Args:
            db_client: Database client instance
            model: Model class to search
        """
        self.db_client = db_client
        self.model = model
    
    def paginated_search_with_count(
        self,
        base_query_builder: Callable[[Session], Query],
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "id",
        sort_desc: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a paginated search with total count.
        
        Args:
            base_query_builder: Function that takes a session and returns a base query
            page: Page number (1-based)
            per_page: Number of items per page
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            
        Returns:
            Dictionary with items, total, page, per_page, and total_pages
        """
        with self.db_client.session_scope() as session:
            # Build base query
            base_query = base_query_builder(session)
            
            # Get total count (without pagination)
            count_query = base_query.statement.with_only_columns(func.count()).order_by(None)
            total = session.execute(count_query).scalar()
            
            # Apply sorting
            if hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                base_query = base_query.order_by(desc(sort_column) if sort_desc else asc(sort_column))
            
            # Apply pagination
            offset = (page - 1) * per_page
            paginated_query = base_query.offset(offset).limit(per_page)
            
            # Execute query
            items = paginated_query.all()
            
            # Detach objects
            detached_items = [self.db_client.detach_object(item, session) for item in items]
            
            # Calculate total pages
            total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
            
            return {
                "items": detached_items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
    
    def execute_custom_query(
        self,
        query_builder: Callable[[Session], Query],
        detach_objects: bool = True
    ) -> List[T]:
        """
        Execute a custom query.
        
        Args:
            query_builder: Function that takes a session and returns a query
            detach_objects: Whether to detach objects from session
            
        Returns:
            List of model instances
        """
        with self.db_client.session_scope() as session:
            query = query_builder(session)
            results = query.all()
            
            if detach_objects:
                return [self.db_client.detach_object(result, session) for result in results]
            else:
                return results
    
    def execute_custom_query_single(
        self,
        query_builder: Callable[[Session], Query],
        detach_object: bool = True
    ) -> Optional[T]:
        """
        Execute a custom query that returns a single result.
        
        Args:
            query_builder: Function that takes a session and returns a query
            detach_object: Whether to detach object from session
            
        Returns:
            Single model instance or None
        """
        with self.db_client.session_scope() as session:
            query = query_builder(session)
            result = query.first()
            
            if result and detach_object:
                return self.db_client.detach_object(result, session)
            else:
                return result
    
    def count_with_custom_query(
        self,
        query_builder: Callable[[Session], Query]
    ) -> int:
        """
        Count results from a custom query.
        
        Args:
            query_builder: Function that takes a session and returns a query
            
        Returns:
            Number of matching records
        """
        with self.db_client.session_scope() as session:
            base_query = query_builder(session)
            count_query = base_query.statement.with_only_columns(func.count()).order_by(None)
            return session.execute(count_query).scalar() or 0
    
    def search_with_aggregation(
        self,
        query_builder: Callable[[Session], Query],
        aggregation_func: Callable[[Query], Any]
    ) -> Any:
        """
        Execute a search query with aggregation.
        
        Args:
            query_builder: Function that takes a session and returns a base query
            aggregation_func: Function that takes a query and returns aggregated result
            
        Returns:
            Aggregation result
        """
        with self.db_client.session_scope() as session:
            base_query = query_builder(session)
            return aggregation_func(base_query)
    
    def batch_process(
        self,
        query_builder: Callable[[Session], Query],
        batch_size: int = 1000,
        processor: Callable[[List[T]], None] = None
    ) -> int:
        """
        Process query results in batches.
        
        Args:
            query_builder: Function that takes a session and returns a query
            batch_size: Number of records to process in each batch
            processor: Function to process each batch (optional)
            
        Returns:
            Total number of records processed
        """
        total_processed = 0
        offset = 0
        
        while True:
            with self.db_client.session_scope() as session:
                base_query = query_builder(session)
                batch_query = base_query.offset(offset).limit(batch_size)
                batch_results = batch_query.all()
                
                if not batch_results:
                    break
                
                if processor:
                    # Detach objects before processing
                    detached_batch = [self.db_client.detach_object(item, session) for item in batch_results]
                    processor(detached_batch)
                
                total_processed += len(batch_results)
                offset += batch_size
                
                # Break if we got fewer results than batch_size (last batch)
                if len(batch_results) < batch_size:
                    break
        
        return total_processed
    
    def exists_with_custom_query(
        self,
        query_builder: Callable[[Session], Query]
    ) -> bool:
        """
        Check if any records exist matching a custom query.
        
        Args:
            query_builder: Function that takes a session and returns a query
            
        Returns:
            True if any records exist, False otherwise
        """
        with self.db_client.session_scope() as session:
            base_query = query_builder(session)
            # Use exists() for efficiency
            exists_query = session.query(base_query.exists())
            return exists_query.scalar()
    
    def get_field_statistics(
        self,
        field: str,
        query_builder: Optional[Callable[[Session], Query]] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a numeric field.
        
        Args:
            field: Field name to get statistics for
            query_builder: Optional query builder to filter records
            
        Returns:
            Dictionary with min, max, avg, count statistics
        """
        if not hasattr(self.model, field):
            return {}
        
        with self.db_client.session_scope() as session:
            if query_builder:
                base_query = query_builder(session)
            else:
                base_query = session.query(self.model)
            
            field_attr = getattr(self.model, field)
            
            stats = base_query.with_entities(
                func.min(field_attr).label('min'),
                func.max(field_attr).label('max'),
                func.avg(field_attr).label('avg'),
                func.count(field_attr).label('count')
            ).first()
            
            return {
                'min': stats.min,
                'max': stats.max,
                'avg': float(stats.avg) if stats.avg else None,
                'count': stats.count
            }
