String-Schema Operations
========================

String-schema operations are the recommended approach for 90% of use cases. They provide type-safe, validated results that are perfect for APIs and data validation.

Overview
--------

String-schema operations use a simple string-based schema definition to:

- Validate data types
- Ensure consistent output format
- Provide API-ready JSON-serializable results
- Offer better performance by fetching only needed fields

Schema Syntax
-------------

Schema strings use a simple, intuitive syntax:

.. code-block:: text

   "field_name:type, another_field:type?, third_field:type"

**Field Types:**

- ``int`` - Integer numbers
- ``float`` - Floating-point numbers
- ``string`` - Text strings
- ``text`` - Long text (same as string)
- ``bool`` - Boolean values
- ``email`` - Email addresses (validated)
- ``url`` - URLs (validated)
- ``datetime`` - Date and time values (automatically timezone-aware)
- ``date`` - Date values

**Optional Fields:**

Add ``?`` after the type to make a field optional:

.. code-block:: text

   "id:int, name:string, email:email?, bio:text?"

Basic Queries
-------------

**Simple Query**

.. code-block:: python

   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email",
       limit=10
   )
   # Returns: [{"id": 1, "name": "John", "email": "john@example.com"}, ...]

**With Filtering**

.. code-block:: python

   active_users = user_crud.query_with_schema(
       schema_str="id:int, name:string, active:bool",
       filters={"active": True},
       sort_by="name"
   )

**With Sorting**

.. code-block:: python

   recent_users = user_crud.query_with_schema(
       schema_str="id:int, name:string, created_at:datetime",
       sort_by="created_at",
       sort_desc=True,
       limit=5
   )
   # Returns: [{"id": 1, "name": "John", "created_at": "2025-08-13T12:22:13+00:00"}, ...]

Enhanced Filtering
------------------

String-schema operations support powerful filtering options:

**Equality and Null Checks**

.. code-block:: python

   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email?",
       filters={
           "active": True,              # Equality
           "email": None,               # IS NULL
           "phone": {"not": None}       # IS NOT NULL
       }
   )

**Comparisons**

.. code-block:: python

   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, age:int?",
       filters={
           "age": {">=": 18},           # age >= 18
           "score": {"<": 100},         # score < 100
           "rating": {"between": [1, 5]} # BETWEEN 1 AND 5
       }
   )

**Lists and Patterns**

.. code-block:: python

   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, status:string",
       filters={
           "status": ["active", "pending"],     # IN clause
           "department": {"not_in": ["HR"]},    # NOT IN
           "name": {"like": "%john%"},          # LIKE (case-sensitive)
           "email": {"ilike": "%@gmail.com"}    # ILIKE (case-insensitive)
       }
   )

Search Functionality
--------------------

Search across multiple fields with automatic text matching:

.. code-block:: python

   # Search in specific fields
   results = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email",
       search_query="john",
       search_fields=["name", "email"],
       filters={"active": True}
   )

   # Search with additional filtering
   results = user_crud.query_with_schema(
       schema_str="id:int, name:string, department:string",
       search_query="manager",
       search_fields=["name", "title", "department"],
       filters={
           "active": True,
           "department": {"not_in": ["Temp"]}
       }
   )

Pagination
----------

Built-in pagination with comprehensive metadata:

.. code-block:: python

   result = user_crud.paginated_query_with_schema(
       schema_str="id:int, name:string, email:email",
       page=1,
       per_page=20,
       filters={"active": True},
       sort_by="name"
   )

   print(f"Page {result['page']} of {result['total_pages']}")
   print(f"Total items: {result['total']}")
   print(f"Has next page: {result['has_next']}")
   
   for user in result['items']:
       print(f"- {user['name']}: {user['email']}")

**Pagination Response Format:**

.. code-block:: python

   {
       "items": [...],           # List of results
       "total": 150,            # Total number of items
       "page": 1,               # Current page (1-based)
       "per_page": 20,          # Items per page
       "total_pages": 8,        # Total number of pages
       "has_next": True,        # Has next page
       "has_prev": False        # Has previous page
   }

Aggregations
------------

Perform aggregations with schema validation:

.. code-block:: python

   # Count by category
   stats = post_crud.aggregate_with_schema(
       aggregations={
           "count": "count(id)",
           "avg_views": "avg(view_count)"
       },
       schema_str="category:string?, count:int, avg_views:float?",
       group_by=["category"]
   )

   # Complex aggregations
   user_stats = user_crud.aggregate_with_schema(
       aggregations={
           "total_users": "count(id)",
           "active_users": "sum(case when active = 1 then 1 else 0 end)",
           "avg_age": "avg(age)",
           "max_login": "max(last_login)"
       },
       schema_str="department:string?, total_users:int, active_users:int, avg_age:float?, max_login:datetime?",
       group_by=["department"],
       filters={"created_at": {">=": "2024-01-01"}}
   )

CRUD Operations
---------------

**Create Records**

.. code-block:: python

   # Create and return ID
   user_id = user_crud.create({
       "name": "John Doe",
       "email": "john@example.com",
       "active": True
   })

   # Create and return validated data
   user = user_crud.create(
       data={"name": "Jane Doe", "email": "jane@example.com"},
       return_schema="id:int, name:string, email:email, created_at:datetime"
   )

**Update Records**

.. code-block:: python

   # Update and return success boolean
   success = user_crud.update(user_id, {"name": "John Smith"})

   # Update and return validated data
   updated_user = user_crud.update(
       id=user_id,
       data={"name": "John Smith", "active": False},
       return_schema="id:int, name:string, active:bool, updated_at:datetime"
   )

**Delete Records**

.. code-block:: python

   # Delete record
   deleted = user_crud.delete(user_id)  # Returns True/False

Custom Schemas
--------------

Define reusable schemas for different contexts:

.. code-block:: python

   # Define named schemas
   user_crud.add_schema("basic", "id:int, name:string, email:email")
   user_crud.add_schema("full", "id:int, name:string, email:email, active:bool, created_at:datetime")
   user_crud.add_schema("api", "id:int, name:string, email:email, active:bool")

   # Use named schemas
   basic_users = user_crud.query_with_schema("basic", limit=10)
   full_users = user_crud.query_with_schema("full", filters={"active": True})
   api_users = user_crud.query_with_schema("api", page=1, per_page=20)

JSON Field Handling
-------------------

JSON fields are automatically serialized as strings for schema validation:

.. code-block:: python

   # Model with JSON field
   class Product(CommonBase):
       __tablename__ = 'products'
       name = Column(String(100))
       metadata = Column(JSON, default=lambda: {})

   # Query JSON fields (they become strings)
   products = product_crud.query_with_schema(
       schema_str="id:int, name:string, metadata:string"
   )

   # Parse JSON strings back to objects
   for product in products:
       import json
       metadata = json.loads(product['metadata']) if product['metadata'] else {}
       print(f"{product['name']}: {metadata}")

Performance Considerations
--------------------------

String-schema operations are optimized for performance:

**Fetch Only Needed Fields**

.. code-block:: python

   # Good: Only fetch required fields
   users = user_crud.query_with_schema("id:int, name:string", limit=100)

   # Avoid: Fetching all fields when you only need a few
   users = user_crud.get_multi(limit=100)  # Fetches all columns

**Use Pagination for Large Datasets**

.. code-block:: python

   # Good: Paginate large results
   result = user_crud.paginated_query_with_schema(
       "id:int, name:string",
       page=1,
       per_page=50
   )

   # Avoid: Loading all results at once
   all_users = user_crud.query_with_schema("id:int, name:string")  # No limit

**Optimize Filters**

.. code-block:: python

   # Good: Use indexed fields for filtering
   users = user_crud.query_with_schema(
       "id:int, name:string",
       filters={"id": {">=": 1000}},  # Indexed field
       limit=100
   )

   # Consider: Add database indexes for frequently filtered fields

Best Practices
--------------

1. **Use string-schema for APIs**: Perfect for JSON responses with automatic timezone handling
2. **Define reusable schemas**: Avoid repeating schema definitions
3. **Validate early**: Let schema validation catch type errors
4. **Paginate large results**: Always use pagination for user-facing lists
5. **Index filtered fields**: Add database indexes for performance
6. **Handle JSON carefully**: Remember JSON fields are serialized as strings
7. **Use optional fields**: Mark nullable fields as optional with ``?``

.. note::
   For advanced features like timezone handling, soft deletes, and performance optimization,
   see the :doc:`advanced_features` documentation.

Error Handling
--------------

String-schema operations provide clear error messages:

.. code-block:: python

   try:
       users = user_crud.query_with_schema(
           "id:int, nonexistent_field:string"
       )
   except ValueError as e:
       print(f"Schema validation error: {e}")

   try:
       result = user_crud.paginated_query_with_schema(
           "id:int, name:string",
           page=1,
           per_page=2000  # Exceeds maximum
       )
   except ValueError as e:
       print(f"Pagination error: {e}")  # "Per page must be <= 1000"
