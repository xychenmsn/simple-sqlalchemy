# Migration Guide

This guide helps you migrate from `common_lib` to `simple-sqlalchemy`.

## Overview

`simple-sqlalchemy` is a standalone package extracted from `common_lib` that provides the same database functionality with improved design and additional features.

## Installation

### Remove common_lib dependency

```bash
# Remove from requirements.txt or pyproject.toml
# common_lib>=x.x.x

# Add simple-sqlalchemy
pip install simple-sqlalchemy[postgres]  # If using PostgreSQL features
```

### Update package configuration

```toml
# pyproject.toml
[project]
dependencies = [
    # Remove: "common_lib>=x.x.x"
    "simple-sqlalchemy[postgres]>=0.1.0",
    # ... other dependencies
]
```

## Import Changes

### Basic Imports

```python
# Before (common_lib)
from common_lib.db import DbClient, BaseCrud, CommonBase, SoftDeleteMixin
from common_lib.db.session import session_scope, detach_object
from common_lib.db.base import EmbeddingVector, metadata_obj

# After (simple-sqlalchemy)
from simple_sqlalchemy import DbClient, BaseCrud, CommonBase, SoftDeleteMixin
from simple_sqlalchemy import session_scope, detach_object, metadata_obj
from simple_sqlalchemy.postgres import EmbeddingVector  # PostgreSQL-specific
```

### Helper Imports

```python
# Before (common_lib)
# These were typically created internally by DbClient

# After (simple-sqlalchemy)
from simple_sqlalchemy import M2MHelper, SearchHelper, PaginationHelper
```

## Code Changes

### 1. Model Definitions

Models remain largely the same:

```python
# Before and After - No changes needed
from simple_sqlalchemy import CommonBase, SoftDeleteMixin
from simple_sqlalchemy.postgres import EmbeddingVector

class User(CommonBase):
    __tablename__ = 'users'
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

class Post(CommonBase, SoftDeleteMixin):
    __tablename__ = 'posts'
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(EmbeddingVector(384), nullable=True)
```

### 2. Database Client

```python
# Before (common_lib)
from common_lib.db import DbClient

db = DbClient(db_url, engine_options)

# After (simple-sqlalchemy) - Same interface
from simple_sqlalchemy import DbClient

db = DbClient(db_url, engine_options)
```

### 3. CRUD Operations

Most CRUD operations remain the same:

```python
# Before and After - Same interface
class UserOps(BaseCrud[User]):
    def __init__(self, db_client):
        super().__init__(User, db_client)

user_ops = UserOps(db)

# All these methods work the same way
user = user_ops.create(data)
user = user_ops.get_by_id(id)
users = user_ops.get_multi(filters=filters)
user = user_ops.update(id, data)
success = user_ops.delete(id)
```

### 4. Session Management

```python
# Before and After - Same interface
with db.session_scope() as session:
    # Your database operations
    pass

# Detaching objects
detached_user = db.detach_object(user, session)
```

## New Features Available

### 1. Enhanced Search Capabilities

```python
# New in simple-sqlalchemy
search_helper = db.create_search_helper(User)

# Paginated search with count
result = search_helper.paginated_search_with_count(
    base_query_builder=custom_query_function,
    page=1,
    per_page=20
)

# Custom queries
users = search_helper.execute_custom_query(query_builder)
```

### 2. Improved M2M Relationship Management

```python
# New explicit M2M helper
user_roles = db.create_m2m_helper(User, Role, "roles", "users")

# Clear API for relationship management
user_roles.add_relationship(user_id, role_id)
user_roles.remove_relationship(user_id, role_id)
roles = user_roles.get_related_for_source(user_id)
```

### 3. Pagination Utilities

```python
# New pagination helpers
from simple_sqlalchemy import PaginationHelper

pagination_info = PaginationHelper.calculate_pagination_info(
    page=2, per_page=10, total=95
)

response = PaginationHelper.build_pagination_response(
    items=users, page=2, per_page=10, total=95
)
```

### 4. PostgreSQL Utilities

```python
# New PostgreSQL-specific utilities
from simple_sqlalchemy.postgres import PostgreSQLUtils

pg_utils = PostgreSQLUtils(db)
pg_utils.reset_sequence('users', 'id')
pg_utils.create_index('users', ['email'], unique=True)
size_info = pg_utils.get_table_size('users')
```

## Breaking Changes

### 1. Import Paths

The main breaking change is import paths. Update all imports as shown above.

### 2. PostgreSQL Features

PostgreSQL-specific features are now in a separate module:

```python
# Before
from common_lib.db.base import EmbeddingVector

# After
from simple_sqlalchemy.postgres import EmbeddingVector
```

### 3. Helper Access

Helpers are now explicitly created rather than accessed as properties:

```python
# Before (if this pattern was used)
# m2m_helper = db.some_internal_helper

# After
m2m_helper = db.create_m2m_helper(User, Role, "roles", "users")
search_helper = db.create_search_helper(User)
```

## Step-by-Step Migration

### Step 1: Update Dependencies

1. Remove `common_lib` from your dependencies
2. Add `simple-sqlalchemy[postgres]` (or just `simple-sqlalchemy` if not using PostgreSQL)

### Step 2: Update Imports

1. Find all imports from `common_lib.db`
2. Replace with equivalent `simple_sqlalchemy` imports
3. Move PostgreSQL-specific imports to `simple_sqlalchemy.postgres`

### Step 3: Test Your Application

1. Run your test suite to ensure everything works
2. Check for any import errors or missing functionality
3. Update any custom code that relied on internal `common_lib` APIs

### Step 4: Leverage New Features (Optional)

1. Consider using the new helper classes for cleaner code
2. Explore pagination utilities for better UX
3. Use PostgreSQL utilities for better database management

## Troubleshooting

### Import Errors

```python
# Error: ModuleNotFoundError: No module named 'common_lib'
# Solution: Update imports to simple_sqlalchemy

# Error: ImportError: cannot import name 'EmbeddingVector'
# Solution: Import from simple_sqlalchemy.postgres
from simple_sqlalchemy.postgres import EmbeddingVector
```

### Missing PostgreSQL Features

```bash
# Error: PostgreSQL features not available
# Solution: Install with PostgreSQL support
pip install simple-sqlalchemy[postgres]
```

### Method Not Found

```python
# Error: AttributeError: 'BaseCrud' object has no attribute 'some_method'
# Solution: Check if method was renamed or moved to a helper class
# Consult the API reference in README.md
```

## Getting Help

If you encounter issues during migration:

1. Check the [API Reference](../README.md#api-reference) for method signatures
2. Look at the [examples](../examples/) for usage patterns
3. Open an issue on GitHub with your specific migration problem
4. Join our discussions for community help

## Benefits After Migration

After migrating to `simple-sqlalchemy`, you'll have:

- ✅ **Better Type Safety**: Full type hints throughout
- ✅ **Improved Performance**: Optimized queries and bulk operations
- ✅ **Enhanced Features**: New helpers and utilities
- ✅ **Better Documentation**: Comprehensive docs and examples
- ✅ **Active Development**: Dedicated package with focused development
- ✅ **PostgreSQL Optimization**: Specialized PostgreSQL features
- ✅ **Testing Support**: Built-in test utilities
