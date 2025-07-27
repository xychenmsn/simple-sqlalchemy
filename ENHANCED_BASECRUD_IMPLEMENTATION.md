# Enhanced BaseCrud Implementation Plan

## Overview

This document outlines the implementation of an enhanced `BaseCrud` class that combines the best of SQLAlchemy ORM with string-schema validation. The approach is pragmatic: keep SQLAlchemy as the primary ORM while adding convenient string-schema operations for API consistency and type safety.

## Core Philosophy

1. **Don't fight SQLAlchemy** - Keep it as the primary ORM
2. **Add string-schema as optional output** - 90% convenience, 10% power user features
3. **Database agnostic** - Works with SQLite, PostgreSQL, MySQL (no database-specific features)
4. **No breaking changes** - All existing code continues to work
5. **Gradual adoption** - Users can migrate at their own pace

## Enhanced BaseCrud API

### Traditional SQLAlchemy Methods (Unchanged)
```python
# These methods remain exactly the same
def get_by_id(self, id: int) -> Optional[ModelType]
def get_multi(self, **kwargs) -> List[ModelType]
def create(self, data: Dict) -> ModelType
def update(self, instance: ModelType) -> ModelType
def delete(self, id: int) -> bool
def search(self, search_query: str, **kwargs) -> List[ModelType]
def count(self, **kwargs) -> int
def bulk_create(self, data: List[Dict]) -> List[ModelType]
def bulk_update(self, filters: Dict, data: Dict) -> int
```

### New String-Schema Methods
```python
def query_with_schema(self, schema_str: str, **kwargs) -> List[Dict[str, Any]]:
    """Query with string-schema validation - same API as StringSchemaHelper"""

def paginated_query_with_schema(
    self, 
    schema_str: str, 
    page: int = 1, 
    per_page: int = 10, 
    **kwargs
) -> Dict[str, Any]:
    """
    Paginated query with schema validation.
    
    Returns:
        {
            "items": List[Dict],
            "total": int,
            "page": int,
            "per_page": int,
            "total_pages": int,
            "has_next": bool,
            "has_prev": bool
        }
    """

def aggregate_with_schema(
    self,
    aggregations: Dict[str, str],
    schema_str: str,
    group_by: Optional[List[str]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """Aggregation queries with schema validation"""

def to_dict(self, instance: ModelType, schema: str) -> Dict[str, Any]:
    """Convert SQLAlchemy instance to validated dict"""

def to_dict_list(self, instances: List[ModelType], schema: str) -> List[Dict[str, Any]]:
    """Convert list of instances to validated dicts"""
```

### Enhanced Filtering (Database-Agnostic)
```python
filters = {
    "name": "John",                           # Equality
    "active": True,                           # Boolean
    "email": None,                            # IS NULL
    "phone": {"not": None},                   # IS NOT NULL
    "age": {">=": 18},                        # Comparison operators
    "salary": {"<": 100000},                  # Less than
    "created_at": {"between": [start, end]},  # BETWEEN (if supported)
    "status": ["active", "pending"],          # IN clause
    "department": {"not_in": ["HR", "Legal"]} # NOT IN clause
}
```

## Implementation Strategy

### Phase 1: DRY Refactoring of Current BaseCrud
Apply the DRY principles we used for StringSchemaHelper:

```python
class BaseCrud(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db_client):
        self.model = model
        self.db_client = db_client
        self._schema_helper = StringSchemaHelper(db_client, model)
    
    # DRY helper methods (internal)
    def _apply_filters(self, query, filters) -> Query:
        """Enhanced filtering with null/not-null/comparison support"""
    
    def _apply_search(self, query, search_query, search_fields) -> Query:
        """Text search across multiple fields"""
    
    def _apply_sorting(self, query, sort_by, sort_desc) -> Query:
        """Sorting logic"""
    
    def _apply_pagination(self, query, limit, skip) -> Query:
        """Pagination logic"""
    
    def _apply_soft_delete_filter(self, query, include_deleted) -> Query:
        """Soft delete filtering"""
    
    def _build_base_query(self, session, **options) -> Query:
        """Master query builder using all helpers"""
```

### Phase 2: Add String-Schema Integration
```python
class BaseCrud(Generic[ModelType]):
    # String-schema methods delegate to internal helper
    def query_with_schema(self, schema_str: str, **kwargs):
        return self._schema_helper.query_with_schema(schema_str, **kwargs)
    
    def paginated_query_with_schema(self, schema_str: str, **kwargs):
        return self._schema_helper.paginated_query_with_schema(schema_str, **kwargs)
    
    def aggregate_with_schema(self, aggregations: Dict, schema_str: str, **kwargs):
        return self._schema_helper.aggregate_with_schema(aggregations, schema_str, **kwargs)
    
    # Conversion utilities
    def to_dict(self, instance: ModelType, schema: str) -> Dict:
        return self._schema_helper._model_to_dict_with_schema(instance, schema)
    
    def to_dict_list(self, instances: List[ModelType], schema: str) -> List[Dict]:
        return [self.to_dict(instance, schema) for instance in instances]
```

### Phase 3: Enhanced Filtering Implementation
```python
def _apply_filters(self, query, filters):
    """Enhanced filtering - database agnostic"""
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
                if value.get('not') is None:
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
                # Simple equality
                query = query.filter(field_attr == value)
    
    return query
```

## Usage Examples

### Traditional SQLAlchemy (Unchanged)
```python
user_crud = BaseCrud(User, db_client)

# Get model instance - use SQLAlchemy features
user = user_crud.get_by_id(123)
posts = user.posts  # Use relationships
user.name = "New Name"  # Direct manipulation
user.send_welcome_email()  # Model methods

# Traditional queries
users = user_crud.get_multi(
    filters={"active": True, "department": "Engineering"},
    sort_by="created_at",
    limit=50
)
```

### String-Schema Operations (New)
```python
# Query with schema validation
users_dict = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email, created_at:datetime",
    filters={
        "active": True,
        "email": {"not": None},
        "department": ["Engineering", "Product"]
    },
    search_query="john",
    search_fields=["name", "email"],
    sort_by="created_at",
    limit=50
)

# Paginated results
paginated = user_crud.paginated_query_with_schema(
    schema_str="id:int, name:string, email:email",
    page=1,
    per_page=20,
    filters={"active": True}
)

# Aggregation
stats = user_crud.aggregate_with_schema(
    aggregations={"count": "count(id)", "avg_age": "avg(age)"},
    schema_str="department:string, count:int, avg_age:float",
    group_by=["department"]
)
```

### Hybrid Approach (Best of Both Worlds)
```python
# Get SQLAlchemy instance for complex operations
user = user_crud.get_by_id(123)
user.update_last_login()
user.posts.append(new_post)

# Convert to dict for API response
api_response = user_crud.to_dict(user, "id:int, name:string, email:email, last_login:datetime")

# Or get multiple and convert
users = user_crud.get_multi(filters={"active": True})
api_users = user_crud.to_dict_list(users, "id:int, name:string, email:email")
```

## Benefits

### 1. No Breaking Changes
- All existing `BaseCrud` code continues to work unchanged
- Users can migrate gradually
- No forced architectural changes

### 2. Best of Both Worlds
- Use SQLAlchemy when you need ORM features (relationships, change tracking, model methods)
- Use string-schema when you need API consistency and type safety
- Convert between them as needed

### 3. Database Compatibility
- Works with SQLite, PostgreSQL, MySQL
- No database-specific features
- Standard SQL operations only

### 4. Enhanced Functionality
- Better filtering with null/not-null/comparison operators
- DRY code eliminates duplication
- All StringSchemaHelper convenience methods available
- Flexible conversion utilities

### 5. Simple Migration Path
```python
# Current code (unchanged)
users = user_crud.get_multi(filters={"active": True})

# Add string-schema when ready
users_dict = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email",
    filters={"active": True}
)

# Or convert existing results
users_dict = user_crud.to_dict_list(users, "id:int, name:string, email:email")
```

## Implementation Files

### Files to Modify
1. `simple_sqlalchemy/crud.py` - Enhance existing BaseCrud class
2. `simple_sqlalchemy/helpers/string_schema.py` - Keep as internal helper
3. `simple_sqlalchemy/__init__.py` - Update exports if needed

### Files to Create
1. `simple_sqlalchemy/examples/enhanced_crud_examples.py` - Usage examples
2. `simple_sqlalchemy/tests/test_enhanced_crud.py` - Comprehensive tests

## Testing Strategy

### 1. Backward Compatibility Tests
- Ensure all existing BaseCrud functionality works unchanged
- Test with existing codebases

### 2. New Feature Tests
- Test all string-schema methods
- Test enhanced filtering
- Test conversion utilities

### 3. Database Compatibility Tests
- Test with SQLite, PostgreSQL, MySQL
- Ensure no database-specific features break compatibility

### 4. Integration Tests
- Test hybrid usage patterns
- Test performance with large datasets

## Success Criteria

1. **Zero breaking changes** - All existing code works
2. **Feature parity** - All StringSchemaHelper features available
3. **Database compatibility** - Works with SQLite/PostgreSQL/MySQL
4. **Performance** - No significant performance regression
5. **Documentation** - Clear examples and migration guide

## Timeline

- **Week 1**: DRY refactoring of current BaseCrud
- **Week 2**: Add string-schema integration
- **Week 3**: Enhanced filtering implementation
- **Week 4**: Testing and documentation
- **Week 5**: Examples and migration guide

This approach provides a pragmatic evolution of simple-sqlalchemy that enhances functionality without breaking existing code or fighting against SQLAlchemy's strengths.
