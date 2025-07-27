Core API
========

This section documents the core classes and functions of Simple SQLAlchemy.

DbClient
--------

.. autoclass:: simple_sqlalchemy.DbClient
   :members:
   :undoc-members:
   :show-inheritance:

   The main database client that manages connections and sessions.

   **Example:**

   .. code-block:: python

      from simple_sqlalchemy import DbClient

      # SQLite connection
      db = DbClient("sqlite:///app.db")

      # PostgreSQL with connection pooling
      db = DbClient(
          "postgresql://user:pass@localhost/db",
          pool_size=10,
          max_overflow=20
      )

      # Use as context manager
      with DbClient("sqlite:///app.db") as db:
          # Your database operations
          pass

CommonBase
----------

.. autoclass:: simple_sqlalchemy.CommonBase
   :members:
   :undoc-members:
   :show-inheritance:

   Base class for all database models. Provides common fields and functionality.

   **Example:**

   .. code-block:: python

      from simple_sqlalchemy import CommonBase
      from sqlalchemy import Column, String, Boolean

      class User(CommonBase):
          __tablename__ = 'users'
          
          name = Column(String(100), nullable=False)
          email = Column(String(100), unique=True)
          active = Column(Boolean, default=True)

      # Create tables
      CommonBase.metadata.create_all(db.engine)

   **Automatic Fields:**

   All models inheriting from CommonBase automatically get:

   - ``id``: Primary key (Integer, auto-increment)
   - ``created_at``: Creation timestamp (DateTime)
   - ``updated_at``: Last update timestamp (DateTime)

BaseCrud
--------

.. autoclass:: simple_sqlalchemy.BaseCrud
   :members:
   :undoc-members:
   :show-inheritance:

   Enhanced CRUD operations with both string-schema and traditional SQLAlchemy support.

   **Example:**

   .. code-block:: python

      from simple_sqlalchemy import BaseCrud

      user_crud = BaseCrud(User, db)

      # String-schema operations (recommended)
      users = user_crud.query_with_schema(
          "id:int, name:string, email:email",
          filters={"active": True}
      )

      # Traditional SQLAlchemy operations
      user = user_crud.get_by_id(123)

String-Schema Operations
~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: simple_sqlalchemy.BaseCrud.query_with_schema

   Query with schema validation and return validated dictionaries.

   **Parameters:**

   - ``schema_str`` (str): Schema definition (e.g., "id:int, name:string, email:email?")
   - ``filters`` (dict, optional): Filter conditions
   - ``search_query`` (str, optional): Text search query
   - ``search_fields`` (list, optional): Fields to search in
   - ``sort_by`` (str, optional): Field to sort by
   - ``sort_desc`` (bool, optional): Sort in descending order
   - ``limit`` (int, optional): Maximum number of results
   - ``offset`` (int, optional): Number of results to skip

   **Returns:**

   List of validated dictionaries matching the schema.

.. automethod:: simple_sqlalchemy.BaseCrud.paginated_query_with_schema

   Query with pagination and schema validation.

   **Parameters:**

   - ``schema_str`` (str): Schema definition
   - ``page`` (int): Page number (1-based)
   - ``per_page`` (int): Items per page (max 1000)
   - ``filters`` (dict, optional): Filter conditions
   - ``search_query`` (str, optional): Text search query
   - ``search_fields`` (list, optional): Fields to search in
   - ``sort_by`` (str, optional): Field to sort by
   - ``sort_desc`` (bool, optional): Sort in descending order

   **Returns:**

   Dictionary with pagination metadata:

   .. code-block:: python

      {
          "items": [...],           # List of results
          "total": 150,            # Total number of items
          "page": 1,               # Current page
          "per_page": 20,          # Items per page
          "total_pages": 8,        # Total number of pages
          "has_next": True,        # Has next page
          "has_prev": False        # Has previous page
      }

.. automethod:: simple_sqlalchemy.BaseCrud.aggregate_with_schema

   Perform aggregations with schema validation.

   **Parameters:**

   - ``aggregations`` (dict): Aggregation functions (e.g., {"count": "count(id)", "avg_age": "avg(age)"})
   - ``schema_str`` (str): Schema for results
   - ``group_by`` (list, optional): Fields to group by
   - ``filters`` (dict, optional): Filter conditions
   - ``having`` (dict, optional): HAVING conditions

   **Returns:**

   List of aggregation results as validated dictionaries.

.. automethod:: simple_sqlalchemy.BaseCrud.create

   Create a new record.

   **Parameters:**

   - ``data`` (dict): Data to create
   - ``return_schema`` (str, optional): Schema for return data

   **Returns:**

   - If ``return_schema`` is provided: Validated dictionary
   - Otherwise: ID of created record

.. automethod:: simple_sqlalchemy.BaseCrud.update

   Update an existing record.

   **Parameters:**

   - ``id`` (int): ID of record to update
   - ``data`` (dict): Data to update
   - ``return_schema`` (str, optional): Schema for return data

   **Returns:**

   - If ``return_schema`` is provided: Validated dictionary
   - Otherwise: Boolean indicating success

.. automethod:: simple_sqlalchemy.BaseCrud.delete

   Delete a record.

   **Parameters:**

   - ``id`` (int): ID of record to delete

   **Returns:**

   Boolean indicating success.

Traditional SQLAlchemy Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: simple_sqlalchemy.BaseCrud.get_by_id

   Get a single record by ID.

   **Returns:**

   SQLAlchemy model instance or None.

.. automethod:: simple_sqlalchemy.BaseCrud.get_multi

   Get multiple records with filtering.

   **Parameters:**

   - ``filters`` (dict, optional): Filter conditions
   - ``sort_by`` (str, optional): Field to sort by
   - ``sort_desc`` (bool, optional): Sort in descending order
   - ``limit`` (int, optional): Maximum number of results
   - ``offset`` (int, optional): Number of results to skip

   **Returns:**

   List of SQLAlchemy model instances.

.. automethod:: simple_sqlalchemy.BaseCrud.search

   Search across multiple fields.

   **Parameters:**

   - ``search_query`` (str): Text to search for
   - ``search_fields`` (list): Fields to search in
   - ``filters`` (dict, optional): Additional filter conditions
   - ``limit`` (int, optional): Maximum number of results

   **Returns:**

   List of SQLAlchemy model instances.

.. automethod:: simple_sqlalchemy.BaseCrud.count

   Count records matching filters.

   **Parameters:**

   - ``filters`` (dict, optional): Filter conditions

   **Returns:**

   Integer count of matching records.

Utility Methods
~~~~~~~~~~~~~~~

.. automethod:: simple_sqlalchemy.BaseCrud.to_dict

   Convert SQLAlchemy instance to validated dictionary.

   **Parameters:**

   - ``instance``: SQLAlchemy model instance
   - ``schema_str`` (str): Schema definition

   **Returns:**

   Validated dictionary.

.. automethod:: simple_sqlalchemy.BaseCrud.to_dict_list

   Convert list of SQLAlchemy instances to validated dictionaries.

   **Parameters:**

   - ``instances`` (list): List of SQLAlchemy model instances
   - ``schema_str`` (str): Schema definition

   **Returns:**

   List of validated dictionaries.

.. automethod:: simple_sqlalchemy.BaseCrud.add_schema

   Add a named schema for reuse.

   **Parameters:**

   - ``name`` (str): Schema name
   - ``schema_str`` (str): Schema definition

   **Example:**

   .. code-block:: python

      user_crud.add_schema("basic", "id:int, name:string, email:email")
      user_crud.add_schema("full", "id:int, name:string, email:email, active:bool, created_at:datetime")

      # Use named schemas
      users = user_crud.query_with_schema("basic")
      detailed_users = user_crud.query_with_schema("full")
