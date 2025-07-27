# Simple SQLAlchemy

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 1.4+](https://img.shields.io/badge/sqlalchemy-1.4+-green.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simplified, enhanced SQLAlchemy package that combines the power of SQLAlchemy ORM with convenient string-schema validation for modern database operations.

## ⚡ Quick Start (90% Use Case)

Get started in 30 seconds with the most common database operations:

```python
from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from sqlalchemy import Column, String, Integer, Boolean

# 1. Setup database and model
db = DbClient("sqlite:///app.db")

class User(CommonBase):
    __tablename__ = 'users'
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    active = Column(Boolean, default=True)

CommonBase.metadata.create_all(db.engine)

# 2. Create CRUD operations
user_crud = BaseCrud(User, db)

# 3. Use it! - Returns validated dictionaries ready for APIs
users = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email?, active:bool",
    filters={"active": True},
    sort_by="name",
    limit=10
)
# Returns: [{"id": 1, "name": "John", "email": "john@example.com", "active": true}, ...]

# Paginated results for web APIs
paginated = user_crud.paginated_query_with_schema(
    schema_str="id:int, name:string, email:email?",
    page=1,
    per_page=20,
    filters={"active": True}
)
# Returns: {"items": [...], "total": 150, "page": 1, "per_page": 20, "has_next": true}

# Create users
user_id = user_crud.create({"name": "Alice", "email": "alice@example.com"})
# Returns: 123 (the new user ID)
```

**That's it!** You now have type-safe, validated database operations perfect for APIs.

## 🚀 Features

- **🎯 90% Convenience**: String-schema operations for common use cases
- **🔧 10% Power**: Full SQLAlchemy access when you need it
- **📊 Enhanced Filtering**: null/not-null, comparisons, lists, ranges
- **📄 Pagination**: Built-in pagination with metadata
- **🔍 Search**: Text search across multiple fields
- **📈 Aggregation**: Group by, count, sum, avg with schema validation
- **🔄 Hybrid Approach**: Mix SQLAlchemy models and validated dicts
- **🗃️ Database Agnostic**: SQLite, PostgreSQL, MySQL support
- **⚡ Zero Breaking Changes**: Enhances existing SQLAlchemy patterns

## 📦 Installation

```bash
pip install simple-sqlalchemy
```

For PostgreSQL vector support:

```bash
pip install simple-sqlalchemy[postgres]
```

## 🏗️ Core Architecture

### DbClient - Your Database Entry Point

The `DbClient` is your main interface to the database:

```python
from simple_sqlalchemy import DbClient

# Create database connection
db = DbClient("sqlite:///app.db")
# or
db = DbClient("postgresql://user:pass@localhost/db")

# Use context manager for automatic cleanup
with DbClient("sqlite:///app.db") as db:
    # Your database operations
    pass

# Advanced configuration
db = DbClient(
    "postgresql://user:pass@localhost/db",
    echo=True,  # Log SQL queries
    pool_size=10,  # Connection pool size
    max_overflow=20  # Max connections beyond pool_size
)
```

### BaseCrud - Enhanced CRUD Operations

`BaseCrud` provides both traditional SQLAlchemy operations and modern string-schema operations:

```python
from simple_sqlalchemy import BaseCrud

user_crud = BaseCrud(User, db)  # One instance per model
```

## 📋 String-Schema Operations (Recommended)

### Basic Queries

```python
# Simple query with schema validation
users = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email?, active:bool",
    filters={"active": True},
    sort_by="name",
    limit=50
)

# Enhanced filtering options
users = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email?, age:int?",
    filters={
        "active": True,                    # Equality
        "email": {"not": None},            # IS NOT NULL
        "age": {">=": 18, "<": 65},       # Comparisons
        "department": ["Engineering", "Product"],  # IN clause
        "created_at": {"between": ["2024-01-01", "2024-12-31"]}  # Range
    },
    search_query="john",                   # Text search
    search_fields=["name", "email"],       # Fields to search in
    sort_by="created_at",
    sort_desc=True
)
```

### Pagination

```python
# Perfect for web APIs
result = user_crud.paginated_query_with_schema(
    schema_str="id:int, name:string, email:email?, department:string?",
    page=1,
    per_page=20,
    filters={"active": True},
    search_query="alice",
    search_fields=["name", "email"]
)

print(f"Page {result['page']} of {result['total_pages']}")
print(f"Total users: {result['total']}")
print(f"Has next: {result['has_next']}")

for user in result['items']:
    print(f"- {user['name']}: {user['email']}")
```

### Aggregation

```python
# Department statistics
stats = user_crud.aggregate_with_schema(
    aggregations={
        "count": "count(id)",
        "avg_age": "avg(age)",
        "max_salary": "max(salary)"
    },
    schema_str="department:string?, count:int, avg_age:float?, max_salary:float?",
    group_by=["department"],
    filters={"active": True}
)

for stat in stats:
    dept = stat['department'] or 'No Department'
    print(f"{dept}: {stat['count']} users, avg age {stat['avg_age']:.1f}")
```

### CRUD Operations

```python
# Create (returns ID by default)
user_id = user_crud.create({
    "name": "John Doe",
    "email": "john@example.com",
    "active": True
})

# Create and get data back
user = user_crud.create(
    data={"name": "Jane Doe", "email": "jane@example.com"},
    return_schema="id:int, name:string, email:email, created_at:datetime"
)

# Update (returns boolean by default)
success = user_crud.update(user_id, {"name": "John Smith"})

# Update and get data back
updated_user = user_crud.update(
    id=user_id,
    data={"name": "John Smith"},
    return_schema="id:int, name:string, updated_at:datetime"
)

# Delete
deleted = user_crud.delete(user_id)  # Returns True/False
```

## 🔧 Traditional SQLAlchemy Operations

When you need the full power of SQLAlchemy (relationships, change tracking, model methods):

```python
# Get SQLAlchemy model instances
user = user_crud.get_by_id(123)  # Returns User instance
users = user_crud.get_multi(
    filters={
        "active": True,
        "email": {"not": None},  # Enhanced filtering still works!
        "department": ["Engineering", "Product"]
    },
    sort_by="name",
    limit=10
)

# Use SQLAlchemy features
user.posts.append(new_post)  # Relationships
user.send_welcome_email()    # Model methods
user.name = "New Name"       # Direct attribute access

# Save changes
updated_user = user_crud.update(user.id, {"name": user.name})

# Search across fields
search_results = user_crud.search(
    search_query="alice",
    search_fields=["name", "email"],
    filters={"active": True}
)

# Count with enhanced filtering
count = user_crud.count(filters={
    "active": True,
    "age": {">=": 25},
    "department": {"not_in": ["HR"]}
})
```

## 🔄 Hybrid Approach (Best of Both Worlds)

Mix SQLAlchemy power with schema validation:

```python
# Get SQLAlchemy instance for complex operations
user = user_crud.get_by_id(123)

# Use SQLAlchemy features
user.posts.append(new_post)
user.update_last_login()
user.calculate_metrics()

# Convert to validated dict for API response
api_response = user_crud.to_dict(user, "id:int, name:string, email:email, last_login:datetime")

# Or convert multiple instances
users = user_crud.get_multi(filters={"active": True})
api_users = user_crud.to_dict_list(users, "id:int, name:string, department:string?")
```

## 📊 Enhanced Filtering Reference

All filtering options work with both string-schema and traditional operations:

```python
filters = {
    # Equality
    "name": "John",
    "active": True,

    # Null checks
    "email": None,                    # IS NULL
    "phone": {"not": None},           # IS NOT NULL

    # Comparisons
    "age": {">=": 18},               # age >= 18
    "salary": {"<": 100000},         # salary < 100000
    "score": {"between": [80, 100]}, # BETWEEN 80 AND 100

    # Lists
    "status": ["active", "pending"], # IN ('active', 'pending')
    "department": {"not_in": ["HR", "Legal"]},  # NOT IN

    # String patterns
    "name": {"like": "%john%"},      # LIKE (case-sensitive)
    "email": {"ilike": "%@gmail.com"} # ILIKE (case-insensitive)
}
```

## 🔍 Advanced Features

### Complex Queries with SearchHelper

For complex custom queries that BaseCrud can't handle:

```python
from simple_sqlalchemy import SearchHelper

# Create search helper for complex queries
search_helper = db.create_search_helper(User)

# Custom query with complex JOINs
def complex_admin_query(session):
    return session.query(User).join(Role).join(Permission).filter(
        Permission.name == 'admin',
        User.last_login > datetime.now() - timedelta(days=30)
    ).group_by(User.id).having(func.count(Role.id) > 2)

# Execute with pagination
results = search_helper.paginated_search_with_count(
    query_func=complex_admin_query,
    page=1,
    per_page=20
)

# Batch processing for large datasets
def process_inactive_users(users_batch):
    for user in users_batch:
        user.send_reactivation_email()

search_helper.batch_process(
    query_func=lambda s: s.query(User).filter(User.active == False),
    process_func=process_inactive_users,
    batch_size=100
)
```

### Many-to-Many Relationships

```python
from simple_sqlalchemy import M2MHelper

# Setup many-to-many helper
user_roles = M2MHelper(
    db_client=db,
    source_model=User,
    target_model=Role,
    association_table='user_roles'  # Your association table
)

# Add relationships
user_roles.add_relationship(user_id=1, target_id=2)  # Add role to user
user_roles.add_relationships(user_id=1, target_ids=[2, 3, 4])  # Add multiple roles

# Query relationships
user_role_ids = user_roles.get_target_ids(source_id=1)  # Get user's role IDs
users_with_role = user_roles.get_source_ids(target_id=2)  # Get users with specific role

# Remove relationships
user_roles.remove_relationship(user_id=1, target_id=2)
user_roles.clear_relationships(source_id=1)  # Remove all roles from user
```

### PostgreSQL Vector Support

```python
from simple_sqlalchemy.postgres import VectorHelper

# Setup vector operations (requires pgvector extension)
vector_helper = VectorHelper(db, embedding_dim=384)

# Store embeddings
vector_helper.store_embedding(
    table_name='documents',
    record_id=123,
    embedding=[0.1, 0.2, 0.3, ...],  # 384-dimensional vector
    metadata={"title": "Document Title", "category": "tech"}
)

# Similarity search
similar_docs = vector_helper.similarity_search(
    table_name='documents',
    query_embedding=[0.1, 0.2, 0.3, ...],
    limit=10,
    threshold=0.8
)

# Batch operations
embeddings_data = [
    {"id": 1, "embedding": [0.1, 0.2, ...], "metadata": {"title": "Doc 1"}},
    {"id": 2, "embedding": [0.3, 0.4, ...], "metadata": {"title": "Doc 2"}},
]
vector_helper.batch_store_embeddings('documents', embeddings_data)
```

## 🧪 Testing and Development

### Test Utilities

```python
from simple_sqlalchemy.testing import TestDbClient, create_test_data

# Create test database
test_db = TestDbClient()  # Uses in-memory SQLite

# Create test data
test_users = create_test_data(User, count=10, overrides={
    "active": True,
    "department": "Engineering"
})

# Use in tests
def test_user_operations():
    user_crud = BaseCrud(User, test_db)
    users = user_crud.query_with_schema("id:int, name:string", filters={"active": True})
    assert len(users) == 10
```

### Custom Schema Definitions

```python
# Define reusable schemas
user_crud.add_schema("basic", "id:int, name:string, email:email?")
user_crud.add_schema("full", "id:int, name:string, email:email?, active:bool, created_at:datetime")
user_crud.add_schema("api", "id:int, name:string, email:email?, department:string?")

# Use predefined schemas
users = user_crud.query_with_schema("basic", filters={"active": True})
paginated = user_crud.paginated_query_with_schema("api", page=1, per_page=20)
```

## 🎯 Best Practices

### When to Use What

**Use String-Schema Operations (90% of cases):**

- API endpoints that return JSON
- Data validation and type safety
- Simple CRUD operations
- Pagination and search
- Aggregation queries

**Use Traditional SQLAlchemy (10% of cases):**

- Complex business logic in model methods
- Relationship manipulation (adding/removing related objects)
- Transaction management across multiple models
- Custom SQLAlchemy features (events, hybrid properties)

**Use SearchHelper for:**

- Complex JOINs across multiple tables
- Custom aggregations with HAVING clauses
- Batch processing of large datasets
- Statistical analysis functions

### Performance Tips

```python
# Good: Use schema to fetch only needed columns
users = user_crud.query_with_schema(
    "id:int, name:string",  # Only fetch id and name
    limit=100
)

# Avoid: Fetching all columns when you only need a few
users = user_crud.get_multi(limit=100)  # Fetches all columns

# Good: Use aggregation for counts
stats = user_crud.aggregate_with_schema(
    aggregations={"count": "count(id)"},
    schema_str="department:string, count:int",
    group_by=["department"]
)

# Good: Use pagination for large datasets
result = user_crud.paginated_query_with_schema(
    "id:int, name:string",
    page=1,
    per_page=50
)
```

## 🔧 Configuration

### Database Connection Options

```python
# SQLite with custom options
db = DbClient(
    "sqlite:///app.db",
    echo=True,  # Log SQL queries
    connect_args={"check_same_thread": False}
)

# PostgreSQL with connection pooling
db = DbClient(
    "postgresql://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)

# MySQL
db = DbClient(
    "mysql+pymysql://user:pass@localhost/db",
    echo=False,
    pool_size=5
)
```

### Environment-Based Configuration

```python
import os
from simple_sqlalchemy import DbClient

# Use environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
db = DbClient(DATABASE_URL)

# Different configs for different environments
if os.getenv("ENVIRONMENT") == "production":
    db = DbClient(DATABASE_URL, echo=False, pool_size=20)
elif os.getenv("ENVIRONMENT") == "development":
    db = DbClient(DATABASE_URL, echo=True, pool_size=5)
else:  # testing
    db = DbClient("sqlite:///:memory:", echo=False)
```

## 📚 Examples

Check out the `examples/` directory for comprehensive examples:

- `examples/enhanced_crud_examples.py` - Complete BaseCrud usage
- `examples/basic_usage.py` - Getting started examples
- `examples/advanced_usage.py` - Complex queries and relationships
- `examples/postgres_examples.py` - PostgreSQL-specific features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](https://simple-sqlalchemy.readthedocs.io/)
- [PyPI Package](https://pypi.org/project/simple-sqlalchemy/)
- [GitHub Repository](https://github.com/your-org/simple-sqlalchemy)
- [Issue Tracker](https://github.com/your-org/simple-sqlalchemy/issues)
