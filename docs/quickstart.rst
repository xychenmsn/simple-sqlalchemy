Quick Start Guide
=================

This guide will get you up and running with Simple SQLAlchemy in just a few minutes.

Installation
------------

Install Simple SQLAlchemy using pip:

.. code-block:: bash

   pip install simple-sqlalchemy

For PostgreSQL vector support:

.. code-block:: bash

   pip install simple-sqlalchemy[postgres]

Basic Setup
-----------

1. **Database Connection**

   Create a database connection using :class:`~simple_sqlalchemy.DbClient`:

   .. code-block:: python

      from simple_sqlalchemy import DbClient

      # SQLite (for development)
      db = DbClient("sqlite:///app.db")

      # PostgreSQL (for production)
      db = DbClient("postgresql://user:pass@localhost/db")

2. **Define Models**

   Use :class:`~simple_sqlalchemy.CommonBase` for your models:

   .. code-block:: python

      from simple_sqlalchemy import CommonBase
      from sqlalchemy import Column, String, Integer, Boolean

      class User(CommonBase):
          __tablename__ = 'users'
          
          name = Column(String(100), nullable=False)
          email = Column(String(100), unique=True)
          active = Column(Boolean, default=True)

      # Create tables
      CommonBase.metadata.create_all(db.engine)

3. **Create CRUD Operations**

   Use :class:`~simple_sqlalchemy.BaseCrud` for database operations:

   .. code-block:: python

      from simple_sqlalchemy import BaseCrud

      user_crud = BaseCrud(User, db)

String-Schema Operations (Recommended)
--------------------------------------

String-schema operations provide type-safe, validated results perfect for APIs:

**Query with Schema**

.. code-block:: python

   # Returns validated dictionaries
   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email?, active:bool",
       filters={"active": True},
       sort_by="name",
       limit=10
   )
   # Result: [{"id": 1, "name": "John", "email": "john@example.com", "active": true}, ...]

**Pagination**

.. code-block:: python

   # Perfect for web APIs
   result = user_crud.paginated_query_with_schema(
       schema_str="id:int, name:string, email:email?",
       page=1,
       per_page=20,
       filters={"active": True}
   )
   # Result: {"items": [...], "total": 150, "page": 1, "per_page": 20, "has_next": true}

**Enhanced Filtering**

.. code-block:: python

   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email?",
       filters={
           "active": True,                    # Equality
           "email": {"not": None},            # IS NOT NULL
           "id": {">=": 10, "<": 100},       # Comparisons
           "name": {"like": "%john%"},        # Pattern matching
           "status": ["active", "pending"]    # IN clause
       }
   )

**Search**

.. code-block:: python

   results = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email?",
       search_query="john",
       search_fields=["name", "email"],
       filters={"active": True}
   )

**CRUD Operations**

.. code-block:: python

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
   deleted = user_crud.delete(user_id)

Traditional SQLAlchemy Operations
---------------------------------

When you need the full power of SQLAlchemy (relationships, model methods, etc.):

.. code-block:: python

   # Get SQLAlchemy model instances
   user = user_crud.get_by_id(123)  # Returns User instance
   users = user_crud.get_multi(
       filters={"active": True},
       sort_by="name",
       limit=10
   )

   # Use SQLAlchemy features
   user.posts.append(new_post)  # Relationships
   user.send_welcome_email()    # Model methods
   user.name = "New Name"       # Direct attribute access

Hybrid Approach
---------------

Mix SQLAlchemy power with schema validation:

.. code-block:: python

   # Get SQLAlchemy instance for complex operations
   user = user_crud.get_by_id(123)

   # Use SQLAlchemy features
   user.posts.append(new_post)
   user.update_last_login()

   # Convert to validated dict for API response
   api_response = user_crud.to_dict(
       user, 
       "id:int, name:string, email:email, last_login:datetime"
   )

When to Use What
----------------

**Use String-Schema Operations (90% of cases):**

- API endpoints that return JSON
- Data validation and type safety
- Simple CRUD operations
- Pagination and search
- Aggregation queries

**Use Traditional SQLAlchemy (10% of cases):**

- Complex business logic in model methods
- Relationship manipulation
- Transaction management across multiple models
- Custom SQLAlchemy features (events, hybrid properties)

Next Steps
----------

- :doc:`string_schema` - Deep dive into string-schema operations
- :doc:`traditional_sqlalchemy` - Advanced SQLAlchemy features
- :doc:`advanced_features` - Performance and complex queries
- :doc:`examples` - Complete working examples
