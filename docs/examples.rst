Examples
========

This section provides comprehensive examples demonstrating all features of Simple SQLAlchemy.

All examples are available in the ``examples/`` directory and can be run independently.

Quick Start Example
-------------------

**File:** ``examples/01_quick_start.py``

The 90% use case - everything you need to get started quickly:

.. code-block:: python

   from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
   from sqlalchemy import Column, String, Boolean

   # Setup
   db = DbClient("sqlite:///quickstart.db")

   class User(CommonBase):
       __tablename__ = 'users'
       name = Column(String(100), nullable=False)
       email = Column(String(100), unique=True)
       active = Column(Boolean, default=True)

   CommonBase.metadata.create_all(db.engine)
   user_crud = BaseCrud(User, db)

   # String-schema operations (API-ready)
   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email?, active:bool",
       filters={"active": True},
       sort_by="name"
   )

**Perfect for:** New users, API development, most common use cases

String-Schema Operations
------------------------

**File:** ``examples/02_string_schema_operations.py``

Deep dive into string-schema operations with comprehensive examples:

- Schema validation and type safety
- Custom schema definitions  
- JSON field handling
- Complex filtering with schema validation
- Performance considerations

.. code-block:: python

   # Custom schemas
   product_crud.add_schema("basic", "id:int, name:string, price:float")
   product_crud.add_schema("full", "id:int, name:string, price:float, category:string?")

   # Use predefined schemas
   products = product_crud.query_with_schema("basic", limit=10)

**Perfect for:** API endpoints, data validation, type safety

Traditional SQLAlchemy
-----------------------

**File:** ``examples/03_traditional_sqlalchemy.py``

When you need the full power of SQLAlchemy:

- Working with model instances and relationships
- Complex business logic in model methods
- Transaction management
- Change tracking and model state

.. code-block:: python

   # Get SQLAlchemy instances
   author = author_crud.get_by_id(author_id)
   
   # Use model methods
   author.send_welcome_email()
   book_count = author.get_published_books_count()
   
   # Work with relationships
   for book in author.books:
       book.publish()

**Perfect for:** Complex business logic, domain models, ORM features

Advanced Features
-----------------

**File:** ``examples/04_advanced_features.py``

Advanced features for complex applications:

- SearchHelper for complex custom queries
- M2MHelper for many-to-many relationships
- Batch processing and performance optimization
- Custom aggregations and statistical queries

.. code-block:: python

   # Complex queries with SearchHelper
   search_helper = db.create_search_helper(User)
   
   def complex_query(session):
       return session.query(User).join(Role).filter(
           Role.name == 'admin'
       ).group_by(User.id)
   
   results = search_helper.paginated_search_with_count(
       query_func=complex_query,
       page=1,
       per_page=20
   )

**Perfect for:** Performance-critical apps, complex queries, large datasets

PostgreSQL Features
-------------------

**File:** ``examples/05_postgresql_features.py``

PostgreSQL-specific features:

- Vector operations with pgvector extension
- Advanced PostgreSQL data types (ARRAY, JSONB, UUID)
- Full-text search capabilities
- Performance optimizations

.. code-block:: python

   # Vector operations
   vector_helper = VectorHelper(db, embedding_dim=384)
   
   vector_helper.store_embedding(
       table_name='documents',
       record_id=123,
       embedding=[0.1, 0.2, 0.3, ...],
       metadata={"title": "Document Title"}
   )
   
   # Similarity search
   similar_docs = vector_helper.similarity_search(
       table_name='documents',
       query_embedding=[0.1, 0.2, 0.3, ...],
       limit=10
   )

**Perfect for:** PostgreSQL users, vector search, advanced data types

Real-World Application
----------------------

**File:** ``examples/06_real_world_application.py``

Complete blog application example:

- User authentication and authorization
- Content management with categories
- Comment system with moderation
- Search and filtering
- API endpoints simulation

.. code-block:: python

   # Service layer pattern
   class BlogService:
       @staticmethod
       def create_post(author_id, title, content, category_id=None):
           # Business logic
           slug = title.lower().replace(' ', '-')
           excerpt = content[:200] + "..."
           
           return post_crud.create({
               "title": title,
               "slug": slug,
               "content": content,
               "excerpt": excerpt,
               "author_id": author_id,
               "category_id": category_id
           })

**Perfect for:** Understanding real-world usage, application architecture

Running Examples
----------------

All examples are self-contained and can be run directly:

.. code-block:: bash

   # Start with the quick start
   python examples/01_quick_start.py
   
   # Try string-schema operations
   python examples/02_string_schema_operations.py
   
   # Explore traditional SQLAlchemy
   python examples/03_traditional_sqlalchemy.py
   
   # Advanced features
   python examples/04_advanced_features.py
   
   # PostgreSQL features (requires PostgreSQL)
   python examples/05_postgresql_features.py
   
   # Real-world application
   python examples/06_real_world_application.py

Learning Path
-------------

**Beginner (New to simple-sqlalchemy)**

1. ``01_quick_start.py`` - Learn the basics
2. ``02_string_schema_operations.py`` - Master string-schema
3. ``06_real_world_application.py`` - See it in action

**Intermediate (Familiar with SQLAlchemy)**

1. ``01_quick_start.py`` - See the differences
2. ``03_traditional_sqlalchemy.py`` - When to use traditional approach
3. ``04_advanced_features.py`` - Advanced patterns

**Advanced (Building complex applications)**

1. ``04_advanced_features.py`` - Advanced patterns
2. ``05_postgresql_features.py`` - Database-specific features
3. ``06_real_world_application.py`` - Architecture patterns

Use Case Guide
--------------

**Building APIs**
- Primary: ``01_quick_start.py`` + ``02_string_schema_operations.py``
- Advanced: ``04_advanced_features.py`` (for complex queries)

**Enterprise Applications**
- Start: ``03_traditional_sqlalchemy.py`` (business logic)
- Scale: ``04_advanced_features.py`` (performance)
- Deploy: ``05_postgresql_features.py`` (production database)

**Data Analysis**
- Query: ``04_advanced_features.py`` (aggregations)
- Search: ``05_postgresql_features.py`` (full-text search)
- Process: ``04_advanced_features.py`` (batch processing)

**Microservices**
- Core: ``01_quick_start.py`` (simple services)
- Schema: ``02_string_schema_operations.py`` (API contracts)
- Scale: ``04_advanced_features.py`` (performance)

Example Output
--------------

Each example produces detailed output showing:

- ✅ Successful operations
- 📊 Data and statistics
- 🎯 Key concepts demonstrated
- 💡 Best practices and tips

For example, the quick start produces:

.. code-block:: text

   === 1. Database Setup ===
   ✅ Connected to database
   
   === 2. Model Definition ===
   ✅ Models defined and tables created
   
   === 3. CRUD Setup ===
   ✅ CRUD operations ready
   
   === 4. Creating Sample Data ===
   ✅ Created users: 1, 2, 3
   ✅ Created posts: 1, 2, 3
   
   === 5. String-Schema Queries (Recommended) ===
   Active users:
     - Alice Johnson (alice@example.com) - Active: True
     - Bob Smith (bob@example.com) - Active: True

Getting Help
------------

1. **Start with:** ``01_quick_start.py`` - Covers 90% of use cases
2. **Check:** Relevant example for your use case
3. **Read:** This documentation
4. **Ask:** GitHub issues for specific questions

The examples are designed to be:

- **Self-contained** - Run independently
- **Well-commented** - Explain every step
- **Realistic** - Show real-world usage patterns
- **Progressive** - Build from simple to complex
