#!/usr/bin/env python3
"""
PostgreSQL Features Example

This example demonstrates PostgreSQL-specific features:
- Vector operations with pgvector extension
- Advanced PostgreSQL data types
- Full-text search capabilities
- JSON/JSONB operations
- Array operations
- Performance optimizations for PostgreSQL

Note: This example requires PostgreSQL with pgvector extension.
Install with: pip install simple-sqlalchemy[postgres]
"""

import os
from simple_sqlalchemy import DbClient, CommonBase, BaseCrud

# Check if PostgreSQL features are available
try:
    from simple_sqlalchemy.postgres import VectorHelper
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    print("⚠️ PostgreSQL features not available. Install with: pip install simple-sqlalchemy[postgres]")

if HAS_POSTGRES:
    from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
    from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
    from datetime import datetime
    import uuid
    import numpy as np


def run_postgresql_demo():
    """Run PostgreSQL-specific features demo"""
    if not HAS_POSTGRES:
        print("Skipping PostgreSQL demo - dependencies not available")
        return
    
    # Setup PostgreSQL connection
    # Note: Update connection string for your PostgreSQL instance
    postgres_url = os.getenv(
        "POSTGRES_URL", 
        "postgresql://user:password@localhost:5432/simple_sqlalchemy_demo"
    )
    
    print("=== PostgreSQL Features Demo ===")
    print(f"Connecting to: {postgres_url.replace('password', '***')}")
    
    try:
        db = DbClient(postgres_url)
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("Please ensure PostgreSQL is running and connection details are correct")
        return
    
    
    # Define Models with PostgreSQL-specific Types
    class Document(CommonBase):
        __tablename__ = 'documents'
        
        title = Column(String(200), nullable=False)
        content = Column(Text, nullable=False)
        tags = Column(ARRAY(String), default=lambda: [])  # PostgreSQL array
        metadata = Column(JSONB, default=lambda: {})      # JSONB for better performance
        document_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
        active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.now)
    
    
    class EmbeddingStore(CommonBase):
        __tablename__ = 'embeddings'
        
        document_id = Column(Integer, nullable=False)
        content_hash = Column(String(64), nullable=False)
        embedding_metadata = Column(JSONB, default=lambda: {})
        created_at = Column(DateTime, default=datetime.now)
    
    
    try:
        CommonBase.metadata.create_all(db.engine)
        print("✅ Created tables with PostgreSQL-specific types")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return
    
    
    # Create CRUD instances
    doc_crud = BaseCrud(Document, db)
    embedding_crud = BaseCrud(EmbeddingStore, db)
    
    
    # 1. PostgreSQL Array Operations
    print("\n=== 1. PostgreSQL Array Operations ===")
    
    # Create documents with array fields
    docs_data = [
        {
            "title": "Machine Learning Basics",
            "content": "Introduction to machine learning concepts and algorithms...",
            "tags": ["ml", "python", "data-science", "beginner"],
            "metadata": {
                "author": "Alice Johnson",
                "category": "tutorial",
                "difficulty": "beginner",
                "estimated_time": 30
            }
        },
        {
            "title": "Advanced Neural Networks",
            "content": "Deep dive into neural network architectures and training...",
            "tags": ["ml", "neural-networks", "deep-learning", "advanced"],
            "metadata": {
                "author": "Bob Smith",
                "category": "advanced",
                "difficulty": "expert",
                "estimated_time": 120
            }
        },
        {
            "title": "Python Web Development",
            "content": "Building web applications with Python frameworks...",
            "tags": ["python", "web", "flask", "django"],
            "metadata": {
                "author": "Charlie Brown",
                "category": "web-dev",
                "difficulty": "intermediate",
                "estimated_time": 60
            }
        }
    ]
    
    doc_ids = []
    for doc_data in docs_data:
        doc_id = doc_crud.create(doc_data)
        doc_ids.append(doc_id)
    
    print(f"✅ Created {len(doc_ids)} documents with array and JSONB fields")
    
    
    # Query with array operations
    # Note: PostgreSQL array operations require raw SQL for complex queries
    with db.session_scope() as session:
        # Find documents with specific tags
        ml_docs = session.query(Document).filter(
            Document.tags.any('ml')  # PostgreSQL array contains
        ).all()
        
        print(f"Documents tagged with 'ml': {len(ml_docs)}")
        for doc in ml_docs:
            print(f"  - '{doc.title}' tags: {doc.tags}")
    
    
    # 2. JSONB Operations
    print("\n=== 2. JSONB Operations ===")
    
    # Query JSONB fields with schema
    advanced_docs = doc_crud.query_with_schema(
        schema_str="id:int, title:string, metadata:string",  # JSONB serialized as string
        # Note: PostgreSQL JSONB queries require raw SQL for complex operations
        limit=10
    )
    
    print("Documents with JSONB metadata:")
    for doc in advanced_docs:
        import json
        metadata = json.loads(doc['metadata']) if doc['metadata'] else {}
        author = metadata.get('author', 'Unknown')
        difficulty = metadata.get('difficulty', 'Unknown')
        print(f"  - '{doc['title']}' by {author} ({difficulty})")
    
    
    # 3. Vector Operations (if pgvector is available)
    print("\n=== 3. Vector Operations ===")
    
    try:
        # Create vector helper
        vector_helper = VectorHelper(db, embedding_dim=384)
        print("✅ Vector helper initialized")
        
        # Generate sample embeddings (in real use, these would come from a model)
        sample_embeddings = [
            np.random.rand(384).tolist(),  # ML document embedding
            np.random.rand(384).tolist(),  # Neural networks embedding
            np.random.rand(384).tolist(),  # Web dev embedding
        ]
        
        # Store embeddings
        for i, (doc_id, embedding) in enumerate(zip(doc_ids, sample_embeddings)):
            doc = doc_crud.get_by_id(doc_id)
            vector_helper.store_embedding(
                table_name='document_vectors',
                record_id=doc_id,
                embedding=embedding,
                metadata={
                    "title": doc.title,
                    "tags": doc.tags,
                    "content_length": len(doc.content)
                }
            )
        
        print("✅ Stored document embeddings")
        
        # Similarity search
        query_embedding = np.random.rand(384).tolist()
        similar_docs = vector_helper.similarity_search(
            table_name='document_vectors',
            query_embedding=query_embedding,
            limit=2,
            threshold=0.0  # Low threshold for demo
        )
        
        print("Similar documents (vector search):")
        for result in similar_docs:
            print(f"  - Record {result['record_id']}: similarity {result['similarity']:.3f}")
            print(f"    Title: {result['metadata']['title']}")
        
        # Batch embedding operations
        batch_data = [
            {
                "id": doc_ids[0],
                "embedding": sample_embeddings[0],
                "metadata": {"batch": True, "type": "ml"}
            }
        ]
        
        vector_helper.batch_store_embeddings('document_vectors_batch', batch_data)
        print("✅ Batch embedding storage complete")
        
    except Exception as e:
        print(f"⚠️ Vector operations not available: {e}")
        print("Ensure pgvector extension is installed in PostgreSQL")
    
    
    # 4. Full-Text Search (PostgreSQL native)
    print("\n=== 4. Full-Text Search ===")
    
    # PostgreSQL full-text search requires raw SQL for best performance
    with db.session_scope() as session:
        try:
            # Create full-text search query
            search_results = session.execute("""
                SELECT id, title, 
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) as rank
                FROM documents 
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT 5
            """, {"query": "machine learning python"}).fetchall()
            
            print("Full-text search results for 'machine learning python':")
            for result in search_results:
                doc = doc_crud.get_by_id(result.id)
                print(f"  - '{doc.title}' (rank: {result.rank:.3f})")
                
        except Exception as e:
            print(f"⚠️ Full-text search not available: {e}")
    
    
    # 5. Advanced PostgreSQL Aggregations
    print("\n=== 5. Advanced PostgreSQL Aggregations ===")
    
    # Complex aggregations with PostgreSQL functions
    try:
        with db.session_scope() as session:
            # Aggregate with array operations
            tag_stats = session.execute("""
                SELECT 
                    unnest(tags) as tag,
                    COUNT(*) as doc_count,
                    AVG(CAST(metadata->>'estimated_time' AS INTEGER)) as avg_time
                FROM documents 
                WHERE active = true
                GROUP BY unnest(tags)
                ORDER BY doc_count DESC
            """).fetchall()
            
            print("Tag statistics:")
            for stat in tag_stats:
                avg_time = stat.avg_time or 0
                print(f"  - '{stat.tag}': {stat.doc_count} docs, avg time: {avg_time:.1f} min")
                
    except Exception as e:
        print(f"⚠️ Advanced aggregations failed: {e}")
    
    
    # 6. Performance Optimizations
    print("\n=== 6. Performance Optimizations ===")
    
    # Create indexes for better performance (in real app, do this in migrations)
    try:
        with db.session_scope() as session:
            # GIN index for JSONB
            session.execute("CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata)")
            
            # GIN index for arrays
            session.execute("CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN (tags)")
            
            # Full-text search index
            session.execute("CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents USING GIN (to_tsvector('english', content))")
            
            session.commit()
            print("✅ Created performance indexes")
            
    except Exception as e:
        print(f"⚠️ Index creation failed: {e}")
    
    
    # 7. Connection Pooling and Performance
    print("\n=== 7. Connection Pooling ===")
    
    # Demonstrate connection pooling configuration
    optimized_db = DbClient(
        postgres_url,
        pool_size=10,           # Number of connections to maintain
        max_overflow=20,        # Additional connections when needed
        pool_timeout=30,        # Timeout for getting connection
        pool_recycle=3600,      # Recycle connections after 1 hour
        echo=False              # Disable SQL logging for performance
    )
    
    print("✅ Configured optimized connection pool")
    print("  - Pool size: 10 connections")
    print("  - Max overflow: 20 connections")
    print("  - Pool timeout: 30 seconds")
    print("  - Connection recycle: 1 hour")
    
    
    print("\n🎉 PostgreSQL Features Complete!")
    print("\nPostgreSQL-specific features demonstrated:")
    print("✅ Array operations and queries")
    print("✅ JSONB storage and operations")
    print("✅ Vector embeddings with pgvector")
    print("✅ Full-text search capabilities")
    print("✅ Advanced aggregations")
    print("✅ Performance indexes")
    print("✅ Connection pooling optimization")
    print("\nPostgreSQL provides powerful features for modern applications!")


def run_sqlite_fallback():
    """Run a simplified demo for SQLite when PostgreSQL is not available"""
    print("=== SQLite Fallback Demo ===")
    print("Running simplified demo with SQLite (PostgreSQL features not available)")

    import os
    import time
    from sqlalchemy import Column, String, Boolean, Text

    # Use a unique database name to avoid conflicts
    db_name = f"postgres_fallback_{int(time.time())}.db"
    db = DbClient(f"sqlite:///{db_name}")
    print(f"✅ Connected to database: {db_name}")

    # Simple model without PostgreSQL-specific types
    class SimpleDocument(CommonBase):
        __tablename__ = 'simple_documents'

        title = Column(String(200), nullable=False)
        content = Column(Text, nullable=False)
        tags = Column(String(500))  # Store as comma-separated string
        doc_metadata = Column(Text)     # Store as JSON string (renamed to avoid conflict)
        active = Column(Boolean, default=True)
    
    CommonBase.metadata.create_all(db.engine)
    doc_crud = BaseCrud(SimpleDocument, db)
    
    # Create sample document
    doc_id = doc_crud.create({
        "title": "Sample Document",
        "content": "This is a sample document for the fallback demo",
        "tags": "sample,demo,sqlite",
        "doc_metadata": '{"author": "Demo User", "category": "example"}'
    })

    # Query with schema
    docs = doc_crud.query_with_schema(
        schema_str="id:int, title:string, tags:string, doc_metadata:string"
    )

    print("Sample documents:")
    for doc in docs:
        print(f"  - '{doc['title']}' tags: {doc['tags']}")
    
    print("\n✅ SQLite fallback demo complete")
    print("For full PostgreSQL features, install: pip install simple-sqlalchemy[postgres]")
    print("Then run: python examples/05_postgresql_features.py --postgres")

    # Cleanup
    print(f"\n🧹 Cleaning up database file: {db_name}")
    try:
        os.remove(db_name)
        print("✅ Database file removed")
    except:
        print("⚠️ Could not remove database file")


if __name__ == "__main__":
    # Always run SQLite fallback for safety unless explicitly requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--postgres" and HAS_POSTGRES:
        print("🐘 Running PostgreSQL demo (requires PostgreSQL server)")
        run_postgresql_demo()
    else:
        print("🗃️ Running SQLite fallback demo (safe for all environments)")
        run_sqlite_fallback()
