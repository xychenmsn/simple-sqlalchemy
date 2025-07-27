# Simple SQLAlchemy Examples

This directory contains comprehensive examples demonstrating all features of simple-sqlalchemy. Each example is self-contained and can be run independently.

## 📚 Example Overview

### 🚀 [01_quick_start.py](01_quick_start.py) - **Start Here!**
**The 90% use case** - Everything you need to get started quickly:
- Database setup with DbClient
- Model definition with CommonBase
- String-schema operations (API-ready results)
- Basic CRUD with validation
- Pagination for web APIs
- Search functionality
- Enhanced filtering

**Perfect for:** New users, API development, most common use cases

### 📋 [02_string_schema_operations.py](02_string_schema_operations.py)
**Deep dive into string-schema operations:**
- Schema validation and type safety
- Custom schema definitions
- JSON field handling
- Complex filtering with schema validation
- Performance considerations
- CRUD with return schemas

**Perfect for:** API endpoints, data validation, type safety

### 🔧 [03_traditional_sqlalchemy.py](03_traditional_sqlalchemy.py)
**When you need the full power of SQLAlchemy:**
- Working with model instances and relationships
- Complex business logic in model methods
- Transaction management
- Change tracking and model state
- Relationship manipulation

**Perfect for:** Complex business logic, domain models, ORM features

### 🎯 [04_advanced_features.py](04_advanced_features.py)
**Advanced features for complex applications:**
- SearchHelper for complex custom queries
- M2MHelper for many-to-many relationships
- Batch processing and performance optimization
- Custom aggregations and statistical queries
- Advanced session management
- Error handling and edge cases

**Perfect for:** Performance-critical apps, complex queries, large datasets

### 🐘 [05_postgresql_features.py](05_postgresql_features.py)
**PostgreSQL-specific features:**
- Vector operations with pgvector extension
- Advanced PostgreSQL data types (ARRAY, JSONB, UUID)
- Full-text search capabilities
- JSON/JSONB operations
- Performance optimizations
- Connection pooling

**Perfect for:** PostgreSQL users, vector search, advanced data types

### 🌐 [06_real_world_application.py](06_real_world_application.py)
**Complete blog application example:**
- User authentication and authorization
- Content management with categories
- Comment system with moderation
- Search and filtering
- API endpoints simulation
- Performance considerations
- Error handling and validation

**Perfect for:** Understanding real-world usage, application architecture

## 🏃‍♂️ Running the Examples

### Prerequisites
```bash
# Install simple-sqlalchemy
pip install simple-sqlalchemy

# For PostgreSQL features (optional)
pip install simple-sqlalchemy[postgres]
```

### Run Examples
```bash
# Start with the quick start example
python examples/01_quick_start.py

# Try string-schema operations
python examples/02_string_schema_operations.py

# Explore traditional SQLAlchemy features
python examples/03_traditional_sqlalchemy.py

# Advanced features
python examples/04_advanced_features.py

# PostgreSQL features (requires PostgreSQL)
python examples/05_postgresql_features.py

# Real-world application
python examples/06_real_world_application.py
```

## 📖 Learning Path

### 🟢 **Beginner** (New to simple-sqlalchemy)
1. **Start here:** `01_quick_start.py` - Learn the basics
2. **Then:** `02_string_schema_operations.py` - Master string-schema
3. **Finally:** `06_real_world_application.py` - See it in action

### 🟡 **Intermediate** (Familiar with SQLAlchemy)
1. **Start here:** `01_quick_start.py` - See the differences
2. **Then:** `03_traditional_sqlalchemy.py` - When to use traditional approach
3. **Next:** `04_advanced_features.py` - Advanced patterns
4. **Finally:** `06_real_world_application.py` - Complete application

### 🔴 **Advanced** (Building complex applications)
1. **Review:** `04_advanced_features.py` - Advanced patterns
2. **Explore:** `05_postgresql_features.py` - Database-specific features
3. **Study:** `06_real_world_application.py` - Architecture patterns

## 🎯 Use Case Guide

### 📱 **Building APIs**
- Primary: `01_quick_start.py` + `02_string_schema_operations.py`
- Advanced: `04_advanced_features.py` (for complex queries)

### 🏢 **Enterprise Applications**
- Start: `03_traditional_sqlalchemy.py` (business logic)
- Scale: `04_advanced_features.py` (performance)
- Deploy: `05_postgresql_features.py` (production database)

### 🔍 **Data Analysis**
- Query: `04_advanced_features.py` (aggregations)
- Search: `05_postgresql_features.py` (full-text search)
- Process: `04_advanced_features.py` (batch processing)

### 🚀 **Microservices**
- Core: `01_quick_start.py` (simple services)
- Schema: `02_string_schema_operations.py` (API contracts)
- Scale: `04_advanced_features.py` (performance)

## 💡 Key Concepts Demonstrated

### **90% Use Case - String-Schema Operations**
```python
# API-ready results with validation
users = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email",
    filters={"active": True},
    sort_by="name"
)
# Returns: [{"id": 1, "name": "John", "email": "john@example.com"}, ...]
```

### **10% Use Case - Traditional SQLAlchemy**
```python
# Complex business logic
user = user_crud.get_by_id(123)  # SQLAlchemy instance
user.send_welcome_email()       # Model method
user.posts.append(new_post)     # Relationship manipulation
```

### **Hybrid Approach - Best of Both Worlds**
```python
# Use SQLAlchemy for complex operations
user = user_crud.get_by_id(123)
user.update_last_login()

# Convert to API-ready format
api_response = user_crud.to_dict(user, "id:int, name:string, last_login:datetime")
```

## 🔧 Database Support

### **SQLite** (Default)
- ✅ All basic features
- ✅ String-schema operations
- ✅ Enhanced filtering
- ✅ Aggregations
- ❌ Vector operations
- ❌ Advanced PostgreSQL types

### **PostgreSQL** (Recommended for Production)
- ✅ All SQLite features
- ✅ Vector operations (with pgvector)
- ✅ ARRAY, JSONB, UUID types
- ✅ Full-text search
- ✅ Advanced aggregations
- ✅ Connection pooling

### **MySQL** (Basic Support)
- ✅ All basic features
- ✅ String-schema operations
- ✅ Enhanced filtering
- ❌ PostgreSQL-specific features

## 🚨 Common Patterns

### **Error Handling**
```python
try:
    result = user_crud.query_with_schema("id:int, name:string")
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Database error: {e}")
```

### **Performance Optimization**
```python
# Good: Fetch only needed fields
users = user_crud.query_with_schema("id:int, name:string", limit=100)

# Avoid: Fetching all fields when you only need a few
users = user_crud.get_multi(limit=100)  # Fetches all columns
```

### **Pagination**
```python
result = user_crud.paginated_query_with_schema(
    "id:int, name:string",
    page=1,
    per_page=20
)
# Returns: {"items": [...], "total": 150, "page": 1, "has_next": true}
```

## 📞 Getting Help

1. **Start with:** `01_quick_start.py` - Covers 90% of use cases
2. **Check:** Relevant example for your use case
3. **Read:** Main documentation
4. **Ask:** GitHub issues for specific questions

## 🤝 Contributing Examples

Have a great example? We'd love to include it! Please:

1. Follow the existing example structure
2. Include comprehensive comments
3. Demonstrate real-world usage
4. Test with SQLite (for compatibility)
5. Submit a pull request

---

**Happy coding with simple-sqlalchemy!** 🎉
