"""
String Schema helper for simple-sqlalchemy

Provides string-schema integration for database operations, allowing
schema-first database queries with automatic validation and response formatting.
"""

import logging
from typing import Dict, Any, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_, or_, func, desc, asc

try:
    from string_schema import validate_to_dict, string_to_json_schema, string_to_model
    HAS_STRING_SCHEMA = True
except ImportError:
    HAS_STRING_SCHEMA = False

from .pagination import PaginationHelper

logger = logging.getLogger(__name__)

T = TypeVar('T')


class StringSchemaHelper:
    """
    Helper class for string-schema integration with simple-sqlalchemy.
    
    Provides methods to query database using string schemas for validation
    and response formatting, eliminating the need for heavy Pydantic models.
    """
    
    def __init__(self, db_client, model: Type[T]):
        """
        Initialize StringSchemaHelper.
        
        Args:
            db_client: Database client instance
            model: SQLAlchemy model class
        """
        if not HAS_STRING_SCHEMA:
            raise ImportError(
                "string-schema is required for StringSchemaHelper. "
                "Install with: pip install string-schema"
            )
        
        self.db_client = db_client
        self.model = model
        
        # Predefined common schemas
        self.common_schemas = {
            "basic": self._generate_basic_schema(),
            "full": self._generate_full_schema(),
            "list_response": "items:[dict], total:int, page:int, per_page:int, total_pages:int, has_next:bool, has_prev:bool",
        }
    
    def _generate_basic_schema(self) -> str:
        """Generate a basic schema with common fields."""
        fields = ["id:int"]
        
        # Add common fields if they exist
        for field_name, field_type in [
            ("name", "string"), ("title", "string"), ("email", "email"),
            ("created_at", "datetime"), ("updated_at", "datetime")
        ]:
            if hasattr(self.model, field_name):
                fields.append(f"{field_name}:{field_type}")
        
        return ", ".join(fields)
    
    def _generate_full_schema(self) -> str:
        """Generate a full schema with all model fields."""
        fields = []
        
        for column in self.model.__table__.columns:
            field_name = column.name
            
            # Map SQLAlchemy types to string-schema types
            try:
                python_type = column.type.python_type
                if python_type == int:
                    field_type = "int"
                elif python_type == float:
                    field_type = "number"
                elif python_type == bool:
                    field_type = "bool"
                elif python_type == str:
                    if "email" in field_name.lower():
                        field_type = "email"
                    elif "url" in field_name.lower():
                        field_type = "url"
                    elif hasattr(column.type, 'length') and column.type.length and column.type.length > 500:
                        field_type = "text"
                    else:
                        field_type = "string"
                else:
                    field_type = "string"  # Default fallback
            except (NotImplementedError, AttributeError):
                # Handle types that don't have python_type or other issues
                column_type_str = str(column.type).lower()
                if "integer" in column_type_str or "int" in column_type_str:
                    field_type = "int"
                elif "float" in column_type_str or "numeric" in column_type_str or "decimal" in column_type_str:
                    field_type = "number"
                elif "boolean" in column_type_str or "bool" in column_type_str:
                    field_type = "bool"
                elif "datetime" in column_type_str or "timestamp" in column_type_str:
                    field_type = "datetime"
                elif "json" in column_type_str:
                    field_type = "dict"  # Use dict for JSON fields
                elif "text" in column_type_str:
                    field_type = "text"
                else:
                    field_type = "string"  # Default fallback
            
            # Add optional marker if nullable
            if column.nullable and not column.primary_key:
                field_type += "?"
            
            fields.append(f"{field_name}:{field_type}")
        
        return ", ".join(fields)
    
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
        
        Args:
            schema_str: String schema definition or schema name
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
        """
        schema = self._resolve_schema(schema_str)
        
        with self.db_client.session_scope() as session:
            # Build base query
            query = session.query(self.model)
            
            # Add eager loading for relationships
            if include_relationships:
                for rel in include_relationships:
                    if hasattr(self.model, rel):
                        query = query.options(selectinload(getattr(self.model, rel)))
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        field_attr = getattr(self.model, field)
                        if isinstance(value, list):
                            query = query.filter(field_attr.in_(value))
                        elif value is None:
                            query = query.filter(field_attr.is_(None))
                        else:
                            query = query.filter(field_attr == value)
            
            # Apply search
            if search_query and search_fields:
                search_conditions = []
                for field in search_fields:
                    if hasattr(self.model, field):
                        search_conditions.append(
                            getattr(self.model, field).ilike(f"%{search_query}%")
                        )
                if search_conditions:
                    query = query.filter(or_(*search_conditions))
            
            # Handle soft delete
            if hasattr(self.model, 'deleted_at') and not include_deleted:
                query = query.filter(self.model.deleted_at.is_(None))
            
            # Apply sorting
            if hasattr(self.model, sort_by):
                sort_field = getattr(self.model, sort_by)
                query = query.order_by(desc(sort_field) if sort_desc else asc(sort_field))
            
            # Apply pagination
            if skip > 0:
                query = query.offset(skip)
            if limit:
                query = query.limit(limit)
            
            # Execute query
            results = query.all()
            
            # Convert to dictionaries and validate against schema
            return [self._model_to_dict_with_schema(result, schema) for result in results]
    
    def paginated_query_with_schema(
        self,
        schema_str: str,
        page: int = 1,
        per_page: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Paginated query with string schema validation.
        
        Args:
            schema_str: String schema definition or schema name
            page: Page number (1-based)
            per_page: Number of items per page
            **kwargs: Additional arguments for query_with_schema
            
        Returns:
            Dictionary with items and pagination info, validated against schemas
        """
        # Validate pagination parameters
        page, per_page = PaginationHelper.validate_pagination_params(
            page=page, per_page=per_page, max_per_page=1000, default_per_page=10
        )
        
        # Calculate skip
        skip = (page - 1) * per_page
        
        # Get total count for pagination
        with self.db_client.session_scope() as session:
            count_query = session.query(self.model)
            
            # Apply same filters as main query for accurate count
            if kwargs.get('filters'):
                for field, value in kwargs['filters'].items():
                    if hasattr(self.model, field):
                        field_attr = getattr(self.model, field)
                        if isinstance(value, list):
                            count_query = count_query.filter(field_attr.in_(value))
                        elif value is None:
                            count_query = count_query.filter(field_attr.is_(None))
                        else:
                            count_query = count_query.filter(field_attr == value)
            
            # Apply search filters to count
            if kwargs.get('search_query') and kwargs.get('search_fields'):
                search_conditions = []
                for field in kwargs['search_fields']:
                    if hasattr(self.model, field):
                        search_conditions.append(
                            getattr(self.model, field).ilike(f"%{kwargs['search_query']}%")
                        )
                if search_conditions:
                    count_query = count_query.filter(or_(*search_conditions))
            
            # Handle soft delete in count
            if hasattr(self.model, 'deleted_at') and not kwargs.get('include_deleted', False):
                count_query = count_query.filter(self.model.deleted_at.is_(None))
            
            total = count_query.count()
        
        # Get items
        items = self.query_with_schema(
            schema_str=schema_str,
            limit=per_page,
            skip=skip,
            **kwargs
        )
        
        # Build pagination response
        response = PaginationHelper.build_pagination_response(
            items=items,
            page=page,
            per_page=per_page,
            total=total,
            include_pagination_info=True
        )

        # Return response directly (items are already validated by query_with_schema)
        return response
    
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
            schema_str: Schema to validate results against
            group_by: List of fields to group by
            filters: Filters to apply
            include_deleted: Include soft-deleted records
            
        Returns:
            List of aggregation results as dictionaries
        """
        schema = self._resolve_schema(schema_str)
        
        with self.db_client.session_scope() as session:
            # Build aggregation query
            select_items = []
            
            # Add group by fields
            if group_by:
                for field in group_by:
                    if hasattr(self.model, field):
                        select_items.append(getattr(self.model, field).label(field))
            
            # Add aggregations
            for alias, agg_expr in aggregations.items():
                if agg_expr.startswith("count("):
                    if "*" in agg_expr:
                        select_items.append(func.count().label(alias))
                    else:
                        field = agg_expr.split("(")[1].split(")")[0]
                        if hasattr(self.model, field):
                            select_items.append(func.count(getattr(self.model, field)).label(alias))
                elif agg_expr.startswith("avg("):
                    field = agg_expr.split("(")[1].split(")")[0]
                    if hasattr(self.model, field):
                        select_items.append(func.avg(getattr(self.model, field)).label(alias))
                elif agg_expr.startswith("sum("):
                    field = agg_expr.split("(")[1].split(")")[0]
                    if hasattr(self.model, field):
                        select_items.append(func.sum(getattr(self.model, field)).label(alias))
                elif agg_expr.startswith("max("):
                    field = agg_expr.split("(")[1].split(")")[0]
                    if hasattr(self.model, field):
                        select_items.append(func.max(getattr(self.model, field)).label(alias))
                elif agg_expr.startswith("min("):
                    field = agg_expr.split("(")[1].split(")")[0]
                    if hasattr(self.model, field):
                        select_items.append(func.min(getattr(self.model, field)).label(alias))
            
            query = session.query(*select_items)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        field_attr = getattr(self.model, field)
                        if isinstance(value, list):
                            query = query.filter(field_attr.in_(value))
                        elif value is None:
                            query = query.filter(field_attr.is_(None))
                        else:
                            query = query.filter(field_attr == value)
            
            # Handle soft delete
            if hasattr(self.model, 'deleted_at') and not include_deleted:
                query = query.filter(self.model.deleted_at.is_(None))
            
            # Apply group by
            if group_by:
                for field in group_by:
                    if hasattr(self.model, field):
                        query = query.group_by(getattr(self.model, field))
            
            results = query.all()
            
            # Convert to dictionaries
            result_dicts = []
            for result in results:
                result_dict = {}
                for i, item in enumerate(select_items):
                    result_dict[item.name] = result[i]
                result_dicts.append(result_dict)
            
            # Validate against schema
            return [validate_to_dict(item, schema) for item in result_dicts]
    
    def _resolve_schema(self, schema_str: str) -> str:
        """Resolve schema string - either return predefined schema or the string itself."""
        return self.common_schemas.get(schema_str, schema_str)
    
    def _model_to_dict_with_schema(self, model_instance, schema: str) -> Dict[str, Any]:
        """Convert SQLAlchemy model instance to dictionary and validate against schema."""
        # Convert model to dictionary
        model_dict = {}
        
        # Get basic attributes
        for column in model_instance.__table__.columns:
            model_dict[column.name] = getattr(model_instance, column.name)
        
        # Get relationship attributes if they're loaded (avoid lazy loading)
        for rel_name in model_instance.__mapper__.relationships.keys():
            try:
                # Check if the relationship is already loaded to avoid DetachedInstanceError
                if hasattr(model_instance, rel_name):
                    # Use __dict__ to check if relationship is loaded without triggering lazy load
                    if rel_name in model_instance.__dict__:
                        rel_value = model_instance.__dict__[rel_name]
                        if rel_value is not None:
                            if isinstance(rel_value, list):
                                # Handle one-to-many or many-to-many relationships
                                model_dict[rel_name] = [
                                    {col.name: getattr(item, col.name) for col in item.__table__.columns}
                                    for item in rel_value
                                ]
                            else:
                                # Handle many-to-one relationships
                                model_dict[rel_name] = {
                                    col.name: getattr(rel_value, col.name)
                                    for col in rel_value.__table__.columns
                                }
            except Exception:
                # Skip relationships that can't be accessed (e.g., detached instances)
                continue
        
        # Add computed fields if they exist (like cluster_size)
        # Only check attributes that are already in __dict__ to avoid lazy loading
        for attr_name, value in model_instance.__dict__.items():
            if not attr_name.startswith('_') and attr_name not in model_dict:
                # Check if it's not a column attribute (computed field)
                if not hasattr(self.model, attr_name) or attr_name not in [col.name for col in self.model.__table__.columns]:
                    try:
                        model_dict[attr_name] = value
                    except:
                        pass  # Skip problematic attributes
        
        # Validate against schema
        return validate_to_dict(model_dict, schema)
    
    def add_custom_schema(self, name: str, schema: str):
        """Add a custom schema to the predefined schemas."""
        self.common_schemas[name] = schema
    
    def get_schema(self, name: str) -> str:
        """Get a predefined schema by name."""
        return self.common_schemas.get(name, "")
