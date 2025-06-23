# Simple SQLAlchemy

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 1.4+](https://img.shields.io/badge/sqlalchemy-1.4+-green.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simplified, enhanced SQLAlchemy package that provides common patterns and utilities for database operations. Built to reduce boilerplate code and provide a consistent, powerful interface for database interactions.

## 🚀 Features

### Core Features (Database Agnostic)

- **🔧 DbClient**: Centralized database connection and session management
- **📊 BaseCrud**: Generic CRUD operations with advanced querying capabilities
- **🏗️ Base Models**: CommonBase with automatic timestamps, SoftDeleteMixin
- **🔍 Advanced Search**: Full-text search across multiple fields with filtering
- **📄 Pagination**: Built-in pagination with count optimization
- **🔄 Bulk Operations**: Efficient bulk updates, deletes, and field clearing
- **🔗 Relationship Helpers**: Many-to-many relationship management utilities
- **📈 Query Builders**: Complex query construction with reusable patterns

### PostgreSQL Features

- **🧮 Vector Support**: Native pgvector integration for embeddings (384+ dimensions)
- **🗃️ JSONB Operations**: Enhanced JSON field handling
- **⚡ Performance Utils**: Index management, VACUUM, table statistics
- **🔧 Schema Management**: Constraint handling, sequence management

### Developer Experience

- **🎯 Type Safety**: Full type hints with Generic support
- **📚 Rich Documentation**: Comprehensive examples and API documentation
- **🧪 Testing Ready**: Built-in test utilities and fixtures
- **🔌 Extensible**: Easy to extend and customize for specific needs

## 📦 Installation

### Basic Installation

```bash
pip install simple-sqlalchemy
```

### With PostgreSQL Support

```bash
pip install simple-sqlalchemy[postgres]
```

### Development Installation

```bash
pip install simple-sqlalchemy[dev]
```

### All Features

```bash
pip install simple-sqlalchemy[all]
```

## 🚀 Quick Start

### 1. Define Your Models

```python
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from simple_sqlalchemy import CommonBase, SoftDeleteMixin

class User(CommonBase):
    __tablename__ = 'users'

    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    posts = relationship("Post", back_populates="author")

class Post(CommonBase, SoftDeleteMixin):
    __tablename__ = 'posts'

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    author = relationship("User", back_populates="posts")
```

### 2. Create Database Client

```python
from simple_sqlalchemy import DbClient

# SQLite
db = DbClient("sqlite:///app.db")

# PostgreSQL
db = DbClient("postgresql://user:password@localhost/dbname")

# With custom engine options
db = DbClient("postgresql://user:password@localhost/dbname", {
    "pool_size": 10,
    "max_overflow": 20,
    "echo": True
})
```

### 3. Create CRUD Operations

```python
from simple_sqlalchemy import BaseCrud

class UserOps(BaseCrud[User]):
    def __init__(self, db_client):
        super().__init__(User, db_client)

    def get_by_email(self, email: str):
        return self.get_by_field("email", email)

    def search_users(self, query: str):
        return self.search(query, ["name", "email"])

class PostOps(BaseCrud[Post]):
    def __init__(self, db_client):
        super().__init__(Post, db_client)

    def get_by_author(self, author_id: int):
        return self.get_multi(filters={"author_id": author_id})
```

### 4. Use the CRUD Operations

```python
# Initialize
user_ops = UserOps(db)
post_ops = PostOps(db)

# Create
user = user_ops.create({
    "name": "John Doe",
    "email": "john@example.com"
})

# Read
users = user_ops.get_multi(limit=10, sort_by="name")
user = user_ops.get_by_email("john@example.com")

# Update
updated_user = user_ops.update(user.id, {"name": "John Smith"})

# Delete (soft delete for Post, hard delete for User)
post_ops.soft_delete(post_id)
user_ops.delete(user_id)

# Search
matching_users = user_ops.search_users("john")

# Pagination
paginated = user_ops.get_multi(skip=20, limit=10)
```

## 📖 Comprehensive Guide

### Base Models

#### CommonBase

Provides standard fields for all models:

- `id`: Auto-incrementing primary key
- `created_at`: Timestamp when record was created (UTC)
- `updated_at`: Timestamp when record was last updated (UTC)

```python
from simple_sqlalchemy import CommonBase

class Product(CommonBase):
    __tablename__ = 'products'

    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

# Automatically includes: id, created_at, updated_at
```

#### SoftDeleteMixin

Adds soft delete functionality:

- `deleted_at`: Timestamp when record was soft-deleted (NULL for active records)

```python
from simple_sqlalchemy import CommonBase, SoftDeleteMixin

class Article(CommonBase, SoftDeleteMixin):
    __tablename__ = 'articles'

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

# Automatically includes: id, created_at, updated_at, deleted_at
```

### Database Client (DbClient)

The `DbClient` manages database connections and provides session handling:

```python
from simple_sqlalchemy import DbClient

# Basic usage
db = DbClient("sqlite:///app.db")

# PostgreSQL with connection pooling
db = DbClient("postgresql://user:pass@localhost/db", {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "echo": False  # Set to True for SQL logging
})

# Session management
with db.session_scope() as session:
    user = session.query(User).first()
    # Automatically commits on success, rolls back on exception

# Get a session (manual management)
session = db.get_session()
try:
    # Your operations
    session.commit()
finally:
    session.close()

# Helper factories
m2m_helper = db.create_m2m_helper(User, Role, "roles", "users")
search_helper = db.create_search_helper(User)
```

### CRUD Operations (BaseCrud)

#### Basic CRUD

```python
class UserOps(BaseCrud[User]):
    def __init__(self, db_client):
        super().__init__(User, db_client)

user_ops = UserOps(db)

# Create
user = user_ops.create({
    "name": "John Doe",
    "email": "john@example.com"
})

# Read by ID
user = user_ops.get_by_id(1)

# Read multiple with filters
users = user_ops.get_multi(
    skip=0,           # Offset
    limit=10,         # Limit
    filters={"name": "John"},  # Field filters
    sort_by="created_at",      # Sort field
    sort_desc=True,            # Sort direction
    include_deleted=False      # Include soft-deleted records
)

# Update
updated_user = user_ops.update(1, {
    "name": "John Smith",
    "email": "john.smith@example.com"
})

# Delete (hard delete)
success = user_ops.delete(1)

# Soft delete (if model has SoftDeleteMixin)
soft_deleted_user = user_ops.soft_delete(1)

# Restore soft-deleted record
restored_user = user_ops.undelete(1)
```

#### Advanced Queries

```python
# Search across multiple fields
users = user_ops.search(
    search_query="john",
    search_fields=["name", "email"],
    limit=20
)

# Count records
total_users = user_ops.count()
active_users = user_ops.count(include_deleted=False)

# Check existence
exists = user_ops.exists_by_field("email", "john@example.com")

# Get by specific field
user = user_ops.get_by_field("email", "john@example.com")

# Get records with NULL/NOT NULL fields
unverified_users = user_ops.get_by_null_field("verified_at", is_null=True)
verified_users = user_ops.get_by_null_field("verified_at", is_null=False)

# Date range queries
recent_users = user_ops.get_by_date_range(
    date_field="created_at",
    days_back=7  # Last 7 days
)

# Custom date range
from datetime import datetime, timedelta
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()
monthly_users = user_ops.get_by_date_range(
    date_field="created_at",
    start_date=start_date,
    end_date=end_date
)

# Get distinct values
email_domains = user_ops.get_distinct_values("email_domain")
```

#### Bulk Operations

```python
# Bulk update fields
updated_count = user_ops.bulk_update_fields(
    update_data={"status": "active"},
    filters={"verified": True}
)

# Bulk clear fields (set to None)
cleared_count = user_ops.bulk_clear_fields(
    clear_data={"last_login": None, "session_token": None},
    filters={"status": "inactive"}
)

# Bulk soft delete
soft_deleted_count = user_ops.bulk_soft_delete(
    filters={"last_login": None}  # Users who never logged in
)

# Bulk restore
restored_count = user_ops.bulk_restore(
    filters={"email": "admin@example.com"}
)

# Delete all records (use with caution!)
deleted_count = user_ops.delete_all()
# Or with filters
deleted_count = user_ops.delete_all(filters={"status": "test"})
```

### Relationship Management (M2MHelper)

For many-to-many relationships:

```python
# Define models with M2M relationship
class User(CommonBase):
    __tablename__ = 'users'
    name = Column(String(100), nullable=False)
    roles = relationship("Role", secondary="user_roles", back_populates="users")

class Role(CommonBase):
    __tablename__ = 'roles'
    name = Column(String(50), nullable=False)
    users = relationship("User", secondary="user_roles", back_populates="roles")

# Create M2M helper
user_role_helper = db.create_m2m_helper(User, Role, "roles", "users")

# Add relationship
user_role_helper.add_relationship(user_id=1, target_id=2)

# Remove relationship
user_role_helper.remove_relationship(user_id=1, target_id=2)

# Get related records
user_roles = user_role_helper.get_related_for_source(user_id=1)
role_users = user_role_helper.get_sources_for_target(role_id=2)

# Count relationships
role_count = user_role_helper.count_related_for_source(user_id=1)
user_count = user_role_helper.count_sources_for_target(role_id=2)

# Check if relationship exists
exists = user_role_helper.relationship_exists(user_id=1, target_id=2)
```

### Advanced Search (SearchHelper)

For complex queries:

```python
search_helper = db.create_search_helper(User)

# Custom query with pagination
def build_complex_query(session):
    return session.query(User).filter(
        User.created_at > datetime.now() - timedelta(days=30),
        User.status == 'active'
    ).join(User.roles).filter(Role.name == 'admin')

result = search_helper.paginated_search_with_count(
    base_query_builder=build_complex_query,
    page=1,
    per_page=20,
    sort_by="created_at",
    sort_desc=True
)

# Result contains: items, total, page, per_page, total_pages
print(f"Found {result['total']} users, showing page {result['page']}")

# Execute custom query
def get_active_admins(session):
    return session.query(User).join(User.roles).filter(
        Role.name == 'admin',
        User.status == 'active'
    )

active_admins = search_helper.execute_custom_query(get_active_admins)

# Count with custom query
admin_count = search_helper.count_with_custom_query(get_active_admins)

# Batch processing for large datasets
def process_batch(users):
    for user in users:
        # Process each user
        print(f"Processing {user.name}")

total_processed = search_helper.batch_process(
    query_builder=get_active_admins,
    batch_size=1000,
    processor=process_batch
)
```

### Pagination Utilities

```python
from simple_sqlalchemy import PaginationHelper

# Calculate pagination info
pagination_info = PaginationHelper.calculate_pagination_info(
    page=2, per_page=10, total=95
)
print(f"Page {pagination_info.page} of {pagination_info.total_pages}")
print(f"Has previous: {pagination_info.has_prev}")
print(f"Has next: {pagination_info.has_next}")

# Build standardized response
response = PaginationHelper.build_pagination_response(
    items=users,
    page=2,
    per_page=10,
    total=95
)

# Validate pagination parameters
page, per_page = PaginationHelper.validate_pagination_params(
    page=0,  # Invalid, will be set to 1
    per_page=2000,  # Too large, will be capped
    max_per_page=1000,
    default_per_page=20
)

# Get page range for UI
page_numbers = PaginationHelper.get_page_range(
    current_page=5,
    total_pages=20,
    max_pages=10
)  # Returns [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Human-readable summary
summary = PaginationHelper.get_pagination_summary(
    page=3, per_page=20, total=95
)  # "Showing 41-60 of 95 items"
```

## 🐘 PostgreSQL Features

### Vector/Embedding Support

For AI/ML applications with vector embeddings:

```python
from simple_sqlalchemy import CommonBase
from simple_sqlalchemy.postgres import EmbeddingVector, embedding_column

class Document(CommonBase):
    __tablename__ = 'documents'

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # 384-dimensional embedding vector (default)
    embedding = Column(EmbeddingVector(384), nullable=True)

    # Alternative syntax
    # embedding = embedding_column(dimensions=384, nullable=True)

# Usage
doc_ops = DocumentOps(db)

# Store document with embedding
embedding_vector = [0.1, 0.2, 0.3, ...]  # 384 dimensions
document = doc_ops.create({
    "title": "AI Research Paper",
    "content": "This paper discusses...",
    "embedding": embedding_vector
})

# Query by embedding similarity (requires pgvector extension)
with db.session_scope() as session:
    similar_docs = session.query(Document).order_by(
        Document.embedding.cosine_distance(embedding_vector)
    ).limit(10).all()
```

### PostgreSQL Utilities

```python
from simple_sqlalchemy.postgres import PostgreSQLUtils

pg_utils = PostgreSQLUtils(db)

# Reset sequence after bulk operations
pg_utils.reset_sequence('users', 'id')

# Manage constraints
pg_utils.drop_constraint('posts', 'posts_author_id_fkey')
pg_utils.add_foreign_key_constraint(
    table_name='posts',
    constraint_name='posts_author_id_fkey',
    column_name='author_id',
    ref_table='users',
    ref_column='id'
)

# Get table information
constraints = pg_utils.get_table_constraints('users')
size_info = pg_utils.get_table_size('users')
print(f"Table size: {size_info['total_size']}")
print(f"Row count: {size_info['row_count']}")

# Index management
pg_utils.create_index(
    table_name='users',
    column_names=['email', 'status'],
    index_name='idx_users_email_status',
    unique=False,
    concurrent=True  # Non-blocking index creation
)

pg_utils.drop_index('idx_users_email_status', concurrent=True)

# Maintenance operations
pg_utils.vacuum_table('users', analyze=True)
```

## 🔧 Advanced Patterns

### Custom CRUD Extensions

```python
class UserOps(BaseCrud[User]):
    def __init__(self, db_client):
        super().__init__(User, db_client)

    def get_active_users(self, limit: int = 100):
        """Get users who are not soft-deleted and have logged in recently"""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=30)

        return self.get_multi(
            filters={"status": "active"},
            include_deleted=False,
            limit=limit
        )

    def search_by_role(self, role_name: str):
        """Search users by role using custom query"""
        def query_builder(session):
            return session.query(User).join(User.roles).filter(
                Role.name == role_name,
                User.deleted_at.is_(None)
            )

        search_helper = self.db_client.create_search_helper(User)
        return search_helper.execute_custom_query(query_builder)

    def get_user_statistics(self):
        """Get user statistics using aggregation"""
        def stats_query(session):
            return session.query(User).filter(User.deleted_at.is_(None))

        def calculate_stats(query):
            return {
                'total': query.count(),
                'active': query.filter(User.status == 'active').count(),
                'inactive': query.filter(User.status == 'inactive').count()
            }

        search_helper = self.db_client.create_search_helper(User)
        return search_helper.search_with_aggregation(stats_query, calculate_stats)
```

### Application-Specific Client

```python
class AppDbClient(DbClient):
    """Application-specific database client"""

    def __init__(self, db_url: str, engine_options=None):
        super().__init__(db_url, engine_options)

        # Initialize all operations
        self.users = UserOps(self)
        self.posts = PostOps(self)
        self.roles = RoleOps(self)

        # Create helpers
        self.user_roles = self.create_m2m_helper(User, Role, "roles", "users")

    def setup_database(self):
        """Initialize database schema"""
        CommonBase.metadata.create_all(self.engine)

    def get_dashboard_data(self):
        """Get data for application dashboard"""
        return {
            'total_users': self.users.count(),
            'active_users': self.users.count(filters={'status': 'active'}),
            'total_posts': self.posts.count(include_deleted=False),
            'recent_posts': self.posts.get_by_date_range('created_at', days_back=7)
        }

# Usage
app_db = AppDbClient("postgresql://user:pass@localhost/app")
app_db.setup_database()

# Use the integrated operations
user = app_db.users.create({"name": "John", "email": "john@example.com"})
app_db.user_roles.add_relationship(user.id, role_id)
dashboard = app_db.get_dashboard_data()
```

## 🧪 Testing

### Test Utilities

```python
import pytest
from simple_sqlalchemy import DbClient, CommonBase

@pytest.fixture
def test_db():
    """Test database fixture"""
    db = DbClient("sqlite:///:memory:")
    CommonBase.metadata.create_all(db.engine)
    yield db
    db.close()

@pytest.fixture
def user_ops(test_db):
    """User operations fixture"""
    return UserOps(test_db)

def test_user_creation(user_ops):
    """Test user creation"""
    user_data = {"name": "Test User", "email": "test@example.com"}
    user = user_ops.create(user_data)

    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.created_at is not None

def test_user_search(user_ops):
    """Test user search functionality"""
    # Create test users
    user_ops.create({"name": "John Doe", "email": "john@example.com"})
    user_ops.create({"name": "Jane Smith", "email": "jane@example.com"})

    # Search by name
    results = user_ops.search("john", ["name", "email"])
    assert len(results) == 1
    assert results[0].name == "John Doe"

def test_pagination(user_ops):
    """Test pagination functionality"""
    # Create multiple users
    for i in range(25):
        user_ops.create({"name": f"User {i}", "email": f"user{i}@example.com"})

    # Test pagination
    page1 = user_ops.get_multi(skip=0, limit=10)
    page2 = user_ops.get_multi(skip=10, limit=10)

    assert len(page1) == 10
    assert len(page2) == 10
    assert page1[0].id != page2[0].id
```

### Integration Testing

```python
def test_relationship_management(test_db):
    """Test M2M relationship management"""
    user_ops = UserOps(test_db)
    role_ops = RoleOps(test_db)

    # Create user and role
    user = user_ops.create({"name": "John", "email": "john@example.com"})
    role = role_ops.create({"name": "admin"})

    # Create M2M helper
    user_roles = test_db.create_m2m_helper(User, Role, "roles", "users")

    # Test relationship operations
    user_roles.add_relationship(user.id, role.id)
    assert user_roles.relationship_exists(user.id, role.id)

    user_role_list = user_roles.get_related_for_source(user.id)
    assert len(user_role_list) == 1
    assert user_role_list[0].name == "admin"

    user_roles.remove_relationship(user.id, role.id)
    assert not user_roles.relationship_exists(user.id, role.id)
```

## 🔄 Migration from common_lib

If you're migrating from `common_lib`, here's how to update your code:

### Import Changes

```python
# Old (common_lib)
from common_lib.db import DbClient, BaseCrud, CommonBase, SoftDeleteMixin
from common_lib.db.session import session_scope, detach_object

# New (simple-sqlalchemy)
from simple_sqlalchemy import DbClient, BaseCrud, CommonBase, SoftDeleteMixin
from simple_sqlalchemy import session_scope, detach_object
```

### Model Changes

```python
# Old
from common_lib.db.base import CommonBase, EmbeddingVector, SoftDeleteMixin

class MyModel(CommonBase, SoftDeleteMixin):
    embedding = Column(EmbeddingVector(384), nullable=True)

# New
from simple_sqlalchemy import CommonBase, SoftDeleteMixin
from simple_sqlalchemy.postgres import EmbeddingVector

class MyModel(CommonBase, SoftDeleteMixin):
    embedding = Column(EmbeddingVector(384), nullable=True)
```

### CRUD Operations

Most CRUD operations remain the same, but some method names have been standardized:

```python
# These methods work the same way
user_ops.create(data)
user_ops.get_by_id(id)
user_ops.get_multi(filters=filters)
user_ops.update(id, data)
user_ops.delete(id)
user_ops.search(query, fields)
user_ops.count(filters)

# Soft delete methods (if using SoftDeleteMixin)
user_ops.soft_delete(id)  # Same
user_ops.undelete(id)     # Same (was restore() in some versions)
```

## 📋 Best Practices

### 1. Model Design

```python
# ✅ Good: Use CommonBase for standard fields
class User(CommonBase):
    __tablename__ = 'users'
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)

# ✅ Good: Use SoftDeleteMixin for data you might need to recover
class Post(CommonBase, SoftDeleteMixin):
    __tablename__ = 'posts'
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

# ❌ Avoid: Don't use SoftDeleteMixin for lookup tables
class Category(CommonBase):  # No SoftDeleteMixin
    __tablename__ = 'categories'
    name = Column(String(50), nullable=False, unique=True)
```

### 2. CRUD Organization

```python
# ✅ Good: Extend BaseCrud with domain-specific methods
class UserOps(BaseCrud[User]):
    def get_by_email(self, email: str):
        return self.get_by_field("email", email)

    def get_active_users(self):
        return self.get_multi(filters={"status": "active"}, include_deleted=False)

    def search_users(self, query: str):
        return self.search(query, ["name", "email", "username"])

# ❌ Avoid: Don't put business logic in models
# Keep models as data containers, put logic in CRUD classes
```

### 3. Session Management

```python
# ✅ Good: Use session_scope for automatic transaction management
with db.session_scope() as session:
    user = session.query(User).first()
    user.last_login = datetime.now()
    # Automatically commits

# ✅ Good: Use CRUD operations for most database work
user = user_ops.get_by_id(1)
user_ops.update(1, {"last_login": datetime.now()})

# ❌ Avoid: Manual session management unless necessary
session = db.get_session()
try:
    # operations
    session.commit()
except:
    session.rollback()
finally:
    session.close()
```

### 4. Performance Optimization

```python
# ✅ Good: Use bulk operations for large datasets
user_ops.bulk_update_fields(
    update_data={"status": "inactive"},
    filters={"last_login": None}
)

# ✅ Good: Use pagination for large result sets
users = user_ops.get_multi(skip=offset, limit=page_size)

# ✅ Good: Use search helpers for complex queries
search_helper = db.create_search_helper(User)
result = search_helper.paginated_search_with_count(
    base_query_builder=complex_query_function,
    page=1,
    per_page=20
)

# ❌ Avoid: Loading all records at once
all_users = user_ops.get_multi(limit=0)  # Could be millions of records!
```

## 📚 API Reference

### Core Classes

#### `DbClient(db_url, engine_options=None)`

- **Purpose**: Database connection and session management
- **Methods**:
  - `session_scope()`: Context manager for transactions
  - `get_session()`: Get a new session (manual management)
  - `create_m2m_helper(source_model, target_model, source_attr, target_attr)`: Create M2M helper
  - `create_search_helper(model)`: Create search helper
  - `close()`: Close all connections

#### `BaseCrud[ModelType](model, db_client)`

- **Purpose**: Generic CRUD operations with advanced features
- **Basic Methods**:
  - `create(data: Dict) -> ModelType`
  - `get_by_id(id: int) -> Optional[ModelType]`
  - `get_multi(skip=0, limit=100, filters=None, sort_by="id", sort_desc=False) -> List[ModelType]`
  - `update(id: int, data: Dict) -> Optional[ModelType]`
  - `delete(id: int) -> bool`
- **Search Methods**:
  - `search(query: str, fields: List[str]) -> List[ModelType]`
  - `count(filters=None) -> int`
  - `exists_by_field(field: str, value: Any) -> bool`
  - `get_by_field(field: str, value: Any) -> Optional[ModelType]`
  - `get_distinct_values(field: str) -> List[Any]`
- **Bulk Methods**:
  - `bulk_update_fields(update_data: Dict, filters=None) -> int`
  - `bulk_clear_fields(clear_data: Dict, filters=None) -> int`
  - `delete_all(filters=None) -> int`
- **Soft Delete Methods** (if model has SoftDeleteMixin):
  - `soft_delete(id: int) -> Optional[ModelType]`
  - `undelete(id: int) -> Optional[ModelType]`
  - `bulk_soft_delete(filters=None) -> int`
  - `bulk_restore(filters=None) -> int`

#### `CommonBase`

- **Purpose**: Base model with standard fields
- **Fields**: `id`, `created_at`, `updated_at`

#### `SoftDeleteMixin`

- **Purpose**: Adds soft delete functionality
- **Fields**: `deleted_at`
- **Properties**: `is_deleted`, `is_active`
- **Methods**: `soft_delete()`, `restore()`

### Helper Classes

#### `M2MHelper(db_client, source_model, target_model, source_attr, target_attr)`

- **Methods**:
  - `add_relationship(source_id: int, target_id: int)`
  - `remove_relationship(source_id: int, target_id: int)`
  - `get_related_for_source(source_id: int) -> List`
  - `get_sources_for_target(target_id: int) -> List`
  - `relationship_exists(source_id: int, target_id: int) -> bool`

#### `SearchHelper(db_client, model)`

- **Methods**:
  - `paginated_search_with_count(query_builder, page=1, per_page=20) -> Dict`
  - `execute_custom_query(query_builder) -> List`
  - `count_with_custom_query(query_builder) -> int`
  - `batch_process(query_builder, batch_size=1000, processor=None) -> int`

#### `PaginationHelper` (Static Methods)

- **Methods**:
  - `calculate_pagination_info(page, per_page, total) -> PaginationInfo`
  - `build_pagination_response(items, page, per_page, total) -> Dict`
  - `validate_pagination_params(page, per_page) -> Tuple[int, int]`
  - `get_pagination_summary(page, per_page, total) -> str`

### PostgreSQL Features

#### `EmbeddingVector(dimensions=384)`

- **Purpose**: Custom type for vector embeddings
- **Usage**: `Column(EmbeddingVector(384), nullable=True)`

#### `PostgreSQLUtils(db_client)`

- **Methods**:
  - `reset_sequence(table_name, column_name="id") -> bool`
  - `create_index(table_name, column_names, index_name=None) -> bool`
  - `drop_index(index_name) -> bool`
  - `get_table_size(table_name) -> Dict`
  - `vacuum_table(table_name, analyze=True) -> bool`

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/simple-sqlalchemy/simple-sqlalchemy.git
cd simple-sqlalchemy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Running Tests

Simple SQLAlchemy includes a comprehensive test suite with **109 tests** covering all functionality using SQLite in-memory databases for fast, isolated testing.

```bash
# Run all tests
pytest tests/

# Run with coverage (current: 64%)
pytest tests/ --cov=simple_sqlalchemy --cov-report=term-missing

# Run using Makefile
make test          # Basic test run
make test-cov      # With coverage report
make test-fast     # Exclude slow tests
make test-integration  # Only integration tests

# Run using custom test runner
python run_tests.py --coverage --verbose

# Run specific test categories
pytest tests/test_crud.py -v           # CRUD operations
pytest tests/test_helpers.py -v        # Helper modules
pytest tests/test_integration.py -v    # Integration tests
pytest tests/test_base.py -v           # Base models and mixins
pytest tests/test_session.py -v        # Session management

# Run PostgreSQL-specific tests (requires PostgreSQL)
pytest -m postgres
```

**Test Features:**

- ✅ **109 comprehensive tests** covering all components
- ✅ **Fast execution** (< 1 second) using SQLite in-memory
- ✅ **No external dependencies** - works anywhere
- ✅ **Detailed coverage reporting** with HTML output
- ✅ **CI/CD ready** with multiple test runners

### Code Quality

```bash
# Format code
black simple_sqlalchemy tests

# Sort imports
isort simple_sqlalchemy tests

# Type checking
mypy simple_sqlalchemy

# Run all quality checks
pre-commit run --all-files
```

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit your changes: `git commit -m "Add feature"`
7. Push to your fork: `git push origin feature-name`
8. Create a Pull Request

### Guidelines

- **Code Style**: Follow PEP 8, use Black for formatting
- **Type Hints**: Add type hints to all public APIs
- **Documentation**: Update docstrings and README for new features
- **Tests**: Maintain 90%+ test coverage
- **Backwards Compatibility**: Don't break existing APIs without major version bump

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [SQLAlchemy](https://www.sqlalchemy.org/) ORM
- Inspired by Django's ORM and FastAPI's design patterns
- PostgreSQL vector support powered by [pgvector](https://github.com/pgvector/pgvector)

## 📞 Support

- **Documentation**: [Read the full docs](https://simple-sqlalchemy.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/simple-sqlalchemy/simple-sqlalchemy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/simple-sqlalchemy/simple-sqlalchemy/discussions)
- **Email**: contributors@simple-sqlalchemy.dev

---

**Simple SQLAlchemy** - Making database operations simple, powerful, and enjoyable! 🚀
