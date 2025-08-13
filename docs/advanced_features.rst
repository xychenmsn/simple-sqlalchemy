Advanced Features
=================

This section covers advanced features and behaviors of simple-sqlalchemy that help you build robust, production-ready applications.

Timezone Handling
-----------------

Simple-sqlalchemy automatically handles timezone conversion for datetime fields to ensure consistent, timezone-aware API responses.

**Automatic UTC Conversion**

All datetime fields are automatically converted to UTC timezone format when returned through string-schema operations:

.. code-block:: python

   # Model with datetime fields
   class Article(CommonBase):
       __tablename__ = 'articles'
       title = Column(String(255))
       # created_at and updated_at are automatically added by CommonBase

   # Query with datetime fields
   articles = article_crud.query_with_schema(
       "id:int, title:string, created_at:datetime, updated_at:datetime"
   )

   # Results automatically include timezone information
   print(articles[0]['created_at'])  # "2025-08-13T12:22:13+00:00"

**How It Works**

1. **Database Storage**: Datetime values are stored in UTC (recommended practice)
2. **Naive Datetime Handling**: If a datetime lacks timezone info, it's assumed to be UTC
3. **ISO Format Output**: All datetime fields are returned in ISO 8601 format with timezone
4. **Frontend Compatibility**: JavaScript automatically handles timezone conversion for display

**Benefits**

- ✅ **Consistent API Responses**: All datetime fields include timezone information
- ✅ **Global Application Support**: Works correctly across all timezones
- ✅ **Industry Best Practice**: Follows UTC storage + timezone-aware API pattern
- ✅ **Zero Configuration**: Works automatically for all datetime fields
- ✅ **Performance Optimized**: Minimal overhead with maximum benefit

**Example Output**

.. code-block:: python

   # Before: Naive datetime (problematic for frontend)
   {
       "id": 1,
       "title": "Sample Article",
       "created_at": "2025-08-13T12:22:13"  # Missing timezone info
   }

   # After: Timezone-aware datetime (frontend-friendly)
   {
       "id": 1,
       "title": "Sample Article", 
       "created_at": "2025-08-13T12:22:13+00:00"  # Clear UTC timezone
   }

**Frontend Integration**

JavaScript automatically handles timezone conversion:

.. code-block:: javascript

   // Frontend receives timezone-aware datetime
   const article = await fetch('/api/articles/1').then(r => r.json());
   
   // JavaScript Date constructor handles timezone conversion
   const createdAt = new Date(article.created_at);
   
   // Displays in user's local timezone
   console.log(createdAt.toLocaleString()); // "8/13/2025, 8:22:13 AM" (EDT)

**Manual Timezone Handling (Not Recommended)**

If you need custom timezone handling, you can still access raw datetime objects through traditional SQLAlchemy operations:

.. code-block:: python

   # Traditional SQLAlchemy (returns raw datetime objects)
   articles = article_crud.get_multi(limit=10)
   
   # Manual timezone conversion if needed
   for article in articles:
       if article.created_at.tzinfo is None:
           article.created_at = article.created_at.replace(tzinfo=timezone.utc)

**Database Timezone Configuration**

For optimal timezone handling, configure your database to store datetime in UTC:

.. code-block:: python

   # PostgreSQL: Use timezone-aware datetime columns
   from sqlalchemy import DateTime
   
   class MyModel(CommonBase):
       __tablename__ = 'my_table'
       event_time = Column(DateTime(timezone=True))  # Timezone-aware
   
   # SQLite: Timezone info is handled by simple-sqlalchemy automatically
   # MySQL: Use DATETIME columns, simple-sqlalchemy handles timezone conversion

Soft Delete Support
-------------------

Simple-sqlalchemy provides built-in soft delete functionality through the ``SoftDeleteMixin``.

**Basic Usage**

.. code-block:: python

   from simple_sqlalchemy import CommonBase, SoftDeleteMixin
   
   class User(CommonBase, SoftDeleteMixin):
       __tablename__ = 'users'
       name = Column(String(100))
       email = Column(String(100))

   # Soft delete a user
   user = user_crud.get_by_id(1)
   user.soft_delete()
   db.session.commit()

   # Check if deleted
   print(user.is_deleted)  # True
   print(user.is_active)   # False

   # Restore a user
   user.restore()
   db.session.commit()

**Query Filtering**

By default, soft-deleted records are excluded from queries:

.. code-block:: python

   # Excludes soft-deleted records by default
   active_users = user_crud.query_with_schema(
       "id:int, name:string, email:email"
   )

   # Include soft-deleted records explicitly
   all_users = user_crud.query_with_schema(
       "id:int, name:string, email:email",
       include_deleted=True
   )

**Soft Delete Schema Fields**

Include soft delete information in your schemas:

.. code-block:: python

   users_with_status = user_crud.query_with_schema(
       "id:int, name:string, email:email, deleted_at:datetime?",
       include_deleted=True
   )

   for user in users_with_status:
       if user['deleted_at']:
           print(f"User {user['name']} was deleted at {user['deleted_at']}")

Enhanced Filtering
------------------

Simple-sqlalchemy provides powerful filtering capabilities beyond basic equality checks.

**Null and Not-Null Filtering**

.. code-block:: python

   # Find users without email
   users_no_email = user_crud.query_with_schema(
       "id:int, name:string, email:email?",
       filters={"email": None}  # IS NULL
   )

   # Find users with email
   users_with_email = user_crud.query_with_schema(
       "id:int, name:string, email:email",
       filters={"email": {"not": None}}  # IS NOT NULL
   )

**Range and Comparison Filtering**

.. code-block:: python

   # Age-based filtering
   adult_users = user_crud.query_with_schema(
       "id:int, name:string, age:int",
       filters={
           "age": {">=": 18},           # Greater than or equal
           "score": {"<": 100},         # Less than
           "rating": {"between": [1, 5]} # Between range
       }
   )

**List and Pattern Filtering**

.. code-block:: python

   # Status filtering
   active_users = user_crud.query_with_schema(
       "id:int, name:string, status:string",
       filters={
           "status": ["active", "pending"],     # IN clause
           "department": {"not_in": ["temp"]},  # NOT IN clause
           "name": {"like": "%john%"},          # LIKE pattern
           "email": {"ilike": "%@gmail.com"}    # Case-insensitive LIKE
       }
   )

**Date Range Filtering**

.. code-block:: python

   from datetime import datetime, timedelta

   # Recent articles
   recent_articles = article_crud.query_with_schema(
       "id:int, title:string, created_at:datetime",
       filters={
           "created_at": {
               ">=": (datetime.now() - timedelta(days=7)).isoformat()
           }
       }
   )

Performance Optimization
------------------------

**Field Selection**

Only fetch the fields you need to improve query performance:

.. code-block:: python

   # Good: Fetch only required fields
   user_list = user_crud.query_with_schema(
       "id:int, name:string",  # Only 2 fields
       limit=1000
   )

   # Avoid: Fetching all fields when unnecessary
   user_list = user_crud.get_multi(limit=1000)  # All fields

**Pagination Best Practices**

Always paginate large result sets:

.. code-block:: python

   # Recommended pagination size
   result = user_crud.paginated_query_with_schema(
       "id:int, name:string, email:email",
       page=1,
       per_page=50,  # Good balance of performance and UX
       sort_by="created_at",
       sort_desc=True
   )

**Index Optimization**

Add database indexes for frequently filtered and sorted fields:

.. code-block:: python

   class User(CommonBase):
       __tablename__ = 'users'
       name = Column(String(100))
       email = Column(String(100), index=True)      # Indexed for filtering
       status = Column(String(20), index=True)      # Indexed for filtering
       created_at = Column(DateTime, index=True)    # Indexed for sorting

Error Handling and Validation
-----------------------------

**Schema Validation Errors**

Handle schema validation errors gracefully:

.. code-block:: python

   try:
       users = user_crud.query_with_schema(
           "id:int, invalid_field:string"  # Field doesn't exist
       )
   except ValueError as e:
       logger.error(f"Schema validation failed: {e}")
       # Return appropriate error response

**Pagination Validation**

.. code-block:: python

   try:
       result = user_crud.paginated_query_with_schema(
           "id:int, name:string",
           page=1,
           per_page=2000  # Exceeds maximum allowed
       )
   except ValueError as e:
       logger.error(f"Pagination error: {e}")
       # Handle pagination limits

**Database Connection Errors**

.. code-block:: python

   from sqlalchemy.exc import SQLAlchemyError

   try:
       users = user_crud.query_with_schema("id:int, name:string")
   except SQLAlchemyError as e:
       logger.error(f"Database error: {e}")
       # Handle database connectivity issues

JSON Field Handling
-------------------

JSON fields require special consideration in string-schema operations.

**Automatic JSON Serialization**

JSON fields are automatically converted to strings for schema validation:

.. code-block:: python

   class Product(CommonBase):
       __tablename__ = 'products'
       name = Column(String(100))
       metadata = Column(JSON, default=lambda: {})

   # JSON fields become strings in schema results
   products = product_crud.query_with_schema(
       "id:int, name:string, metadata:string"
   )

   # Parse JSON strings back to objects
   for product in products:
       import json
       metadata = json.loads(product['metadata']) if product['metadata'] else {}

**Working with JSON Data**

.. code-block:: python

   # Create with JSON data
   product_id = product_crud.create({
       "name": "Laptop",
       "metadata": {"brand": "Dell", "specs": {"ram": "16GB", "cpu": "Intel i7"}}
   })

   # Query and parse JSON
   product = product_crud.get_one_with_schema(
       "id:int, name:string, metadata:string",
       filters={"id": product_id}
   )

   import json
   metadata = json.loads(product['metadata'])
   print(f"Brand: {metadata['brand']}")
   print(f"RAM: {metadata['specs']['ram']}")

Migration and Compatibility
---------------------------

**Upgrading from Traditional SQLAlchemy**

Simple-sqlalchemy is designed to be fully compatible with existing SQLAlchemy code:

.. code-block:: python

   # Existing SQLAlchemy code continues to work
   users = session.query(User).filter(User.active == True).all()

   # Gradually migrate to string-schema operations
   users = user_crud.query_with_schema(
       "id:int, name:string, email:email",
       filters={"active": True}
   )

**Mixed Usage Patterns**

You can mix traditional SQLAlchemy and string-schema operations:

.. code-block:: python

   # Complex query with SQLAlchemy
   complex_query = session.query(User).join(Department).filter(
       Department.budget > 100000
   ).subquery()

   # Use results with string-schema for API response
   api_users = user_crud.query_with_schema(
       "id:int, name:string, department_name:string",
       custom_query=complex_query
   )

Best Practices Summary
----------------------

1. **Use string-schema for APIs**: Perfect for JSON responses with automatic timezone handling
2. **Leverage automatic timezone conversion**: No manual timezone handling needed
3. **Implement soft deletes**: Use ``SoftDeleteMixin`` for audit trails
4. **Optimize with field selection**: Only fetch needed fields
5. **Always paginate**: Use pagination for user-facing lists
6. **Handle JSON carefully**: Remember JSON fields are serialized as strings
7. **Add appropriate indexes**: Index frequently filtered and sorted fields
8. **Validate inputs**: Let schema validation catch errors early
9. **Handle errors gracefully**: Provide meaningful error messages
10. **Mix approaches when needed**: Combine SQLAlchemy power with string-schema convenience
