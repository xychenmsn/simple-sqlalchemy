Helpers API
===========

This section documents the helper classes and utilities provided by Simple SQLAlchemy.

SearchHelper
------------

.. autoclass:: simple_sqlalchemy.helpers.search.SearchHelper
   :members:
   :undoc-members:
   :show-inheritance:

   Advanced search helper for complex custom queries that can't be handled by basic CRUD operations.

   **Example:**

   .. code-block:: python

      from simple_sqlalchemy.helpers.search import SearchHelper

      # Create search helper
      search_helper = db.create_search_helper(User)

      # Custom query function
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

   **Methods:**

   .. automethod:: simple_sqlalchemy.helpers.search.SearchHelper.paginated_search_with_count

      Execute a custom query function with pagination and count.

      **Parameters:**

      - ``query_func`` (callable): Function that takes a session and returns a query
      - ``page`` (int): Page number (1-based)
      - ``per_page`` (int): Items per page

      **Returns:**

      Dictionary with pagination metadata and results.

   .. automethod:: simple_sqlalchemy.helpers.search.SearchHelper.batch_process

      Process query results in batches to handle large datasets efficiently.

      **Parameters:**

      - ``query_func`` (callable): Function that takes a session and returns a query
      - ``process_func`` (callable): Function to process each batch
      - ``batch_size`` (int): Size of each batch

      **Example:**

      .. code-block:: python

         def process_inactive_users(users_batch):
             for user in users_batch:
                 user.send_reactivation_email()

         search_helper.batch_process(
             query_func=lambda s: s.query(User).filter(User.active == False),
             process_func=process_inactive_users,
             batch_size=100
         )

M2MHelper
---------

.. autoclass:: simple_sqlalchemy.helpers.m2m.M2MHelper
   :members:
   :undoc-members:
   :show-inheritance:

   Helper for managing many-to-many relationships with enhanced functionality.

   **Example:**

   .. code-block:: python

      from simple_sqlalchemy.helpers.m2m import M2MHelper

      # Setup many-to-many helper
      user_roles = M2MHelper(
          db_client=db,
          source_model=User,
          target_model=Role,
          association_table='user_roles'
      )

      # Add relationships
      user_roles.add_relationship(user_id=1, target_id=2)
      user_roles.add_relationships(user_id=1, target_ids=[2, 3, 4])

      # Query relationships
      user_role_ids = user_roles.get_target_ids(source_id=1)
      users_with_role = user_roles.get_source_ids(target_id=2)

   **Methods:**

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.add_relationship

      Add a single many-to-many relationship.

      **Parameters:**

      - ``source_id`` (int): ID of the source record
      - ``target_id`` (int): ID of the target record

      **Returns:**

      Boolean indicating success.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.add_relationships

      Add multiple many-to-many relationships for a single source.

      **Parameters:**

      - ``source_id`` (int): ID of the source record
      - ``target_ids`` (list): List of target IDs

      **Returns:**

      Number of relationships added.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.remove_relationship

      Remove a single many-to-many relationship.

      **Parameters:**

      - ``source_id`` (int): ID of the source record
      - ``target_id`` (int): ID of the target record

      **Returns:**

      Boolean indicating success.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.clear_relationships

      Remove all relationships for a source record.

      **Parameters:**

      - ``source_id`` (int): ID of the source record

      **Returns:**

      Number of relationships removed.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.get_target_ids

      Get all target IDs for a source record.

      **Parameters:**

      - ``source_id`` (int): ID of the source record

      **Returns:**

      List of target IDs.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.get_source_ids

      Get all source IDs for a target record.

      **Parameters:**

      - ``target_id`` (int): ID of the target record

      **Returns:**

      List of source IDs.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.relationship_exists

      Check if a relationship exists.

      **Parameters:**

      - ``source_id`` (int): ID of the source record
      - ``target_id`` (int): ID of the target record

      **Returns:**

      Boolean indicating if relationship exists.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.count_targets_for_source

      Count target records for a source.

      **Parameters:**

      - ``source_id`` (int): ID of the source record

      **Returns:**

      Integer count of target records.

   .. automethod:: simple_sqlalchemy.helpers.m2m.M2MHelper.count_sources_for_target

      Count source records for a target.

      **Parameters:**

      - ``target_id`` (int): ID of the target record

      **Returns:**

      Integer count of source records.

StringSchemaHelper
------------------

.. autoclass:: simple_sqlalchemy.helpers.string_schema.StringSchemaHelper
   :members:
   :undoc-members:
   :show-inheritance:

   Internal helper for string-schema operations. Usually accessed through BaseCrud methods.

   **Schema Syntax:**

   - ``field_name:type`` - Required field
   - ``field_name:type?`` - Optional field
   - Multiple fields separated by commas

   **Supported Types:**

   - ``int`` - Integer numbers
   - ``float`` - Floating-point numbers
   - ``string`` - Text strings
   - ``text`` - Long text (same as string)
   - ``bool`` - Boolean values
   - ``email`` - Email addresses (validated)
   - ``url`` - URLs (validated)
   - ``datetime`` - Date and time values
   - ``date`` - Date values

   **Methods:**

   .. automethod:: simple_sqlalchemy.helpers.string_schema.StringSchemaHelper.query_with_schema

      Execute a query with schema validation.

   .. automethod:: simple_sqlalchemy.helpers.string_schema.StringSchemaHelper.paginated_query_with_schema

      Execute a paginated query with schema validation.

   .. automethod:: simple_sqlalchemy.helpers.string_schema.StringSchemaHelper.aggregate_with_schema

      Execute aggregation queries with schema validation.

Utility Functions
-----------------

.. autofunction:: simple_sqlalchemy.helpers.utils.validate_schema

   Validate a schema string format.

   **Parameters:**

   - ``schema_str`` (str): Schema string to validate

   **Returns:**

   Boolean indicating if schema is valid.

   **Raises:**

   - ``ValueError``: If schema format is invalid

.. autofunction:: simple_sqlalchemy.helpers.utils.parse_filters

   Parse and validate filter dictionary.

   **Parameters:**

   - ``filters`` (dict): Filter conditions

   **Returns:**

   Parsed and validated filters.

   **Supported Filter Formats:**

   .. code-block:: python

      {
          "field": "value",                    # Equality
          "field": None,                       # IS NULL
          "field": {"not": None},              # IS NOT NULL
          "field": {">=": 10},                 # Greater than or equal
          "field": {"<": 100},                 # Less than
          "field": {"between": [1, 10]},       # BETWEEN
          "field": ["val1", "val2"],           # IN clause
          "field": {"not_in": ["val1"]},       # NOT IN
          "field": {"like": "%pattern%"},      # LIKE
          "field": {"ilike": "%pattern%"}      # ILIKE (case-insensitive)
      }

Error Classes
-------------

.. autoexception:: simple_sqlalchemy.exceptions.SchemaValidationError

   Raised when schema validation fails.

.. autoexception:: simple_sqlalchemy.exceptions.FilterValidationError

   Raised when filter validation fails.

.. autoexception:: simple_sqlalchemy.exceptions.DatabaseError

   Base class for database-related errors.
