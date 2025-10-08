# Boolean Filter Fix for PostgreSQL

## Problem

The `query_with_schema` method in `simple-sqlalchemy` didn't properly handle boolean filters with PostgreSQL. When using filters like `{"is_dirty": True}`, PostgreSQL would fail because it requires strict boolean type handling.

### Error Example
```python
# This would fail or return incorrect results
dirty_clusters = db.cluster_ops.query_with_schema(
    CLUSTER_FULL, 
    filters={"is_dirty": True}, 
    limit=None
)
```

## Root Cause

In `simple_sqlalchemy/helpers/string_schema.py`, the `_apply_filters` method used a generic equality comparison:

```python
query = query.filter(field_attr == value)
```

This doesn't work properly for boolean values in PostgreSQL, which requires explicit boolean comparison using SQLAlchemy's `.is_()` method.

## Solution

Added special handling for boolean values in the `_apply_filters` method:

```python
elif isinstance(value, bool):
    # Special handling for boolean values to work with PostgreSQL
    # Use is_() for proper boolean comparison
    query = query.filter(field_attr.is_(value))
```

### File Changed
- `simple-sqlalchemy/simple_sqlalchemy/helpers/string_schema.py` (line 153-156)

## Testing

```python
from src.db import db

# Test Boolean True filter
dirty = db.cluster_ops.query_with_schema(
    'id:int, is_dirty:bool', 
    filters={'is_dirty': True}, 
    limit=3
)
print(f'Found {len(dirty)} dirty clusters')
# Output: Found 3 dirty clusters

# Test Boolean False filter  
clean = db.cluster_ops.query_with_schema(
    'id:int, is_dirty:bool', 
    filters={'is_dirty': False}, 
    limit=3
)
print(f'Found {len(clean)} clean clusters')
# Output: Found 1 clean clusters
```

## Impact

This fix enables proper boolean filtering across all projects using `simple-sqlalchemy`:
- ✅ `news` project - `get_dirty_clusters()` now works correctly
- ✅ Any other project using boolean filters with PostgreSQL
- ✅ Backward compatible - doesn't break existing code

## Benefits

1. **Simpler Code** - No need for workarounds like SearchHelper for boolean filters
2. **Consistent API** - Boolean filters work the same as other filter types
3. **PostgreSQL Compatible** - Proper boolean handling for PostgreSQL databases
4. **Better Performance** - Direct filter application instead of custom queries

