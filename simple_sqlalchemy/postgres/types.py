"""
PostgreSQL-specific types for simple-sqlalchemy
"""

from typing import List, Optional, Any
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import ARRAY, REAL

try:
    # Try to import pgvector if available
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback to array of floats
    Vector = None


class EmbeddingVector(TypeDecorator):
    """
    A custom SQLAlchemy type for storing embedding vectors.
    
    Uses pgvector.Vector if available, otherwise falls back to PostgreSQL ARRAY.
    """
    
    impl = Text
    cache_ok = True
    
    def __init__(self, dimensions: int = 384):
        """
        Initialize EmbeddingVector type.
        
        Args:
            dimensions: Number of dimensions in the vector
        """
        self.dimensions = dimensions
        
        if PGVECTOR_AVAILABLE and Vector is not None:
            # Use pgvector if available
            self.impl = Vector(dimensions)
        else:
            # Fallback to PostgreSQL ARRAY of REAL
            self.impl = ARRAY(REAL)
        
        super().__init__()
    
    def load_dialect_impl(self, dialect):
        """Load the appropriate dialect implementation"""
        if dialect.name == 'postgresql':
            if PGVECTOR_AVAILABLE and Vector is not None:
                return dialect.type_descriptor(Vector(self.dimensions))
            else:
                return dialect.type_descriptor(ARRAY(REAL))
        else:
            # For non-PostgreSQL databases, use JSON or TEXT
            return dialect.type_descriptor(Text)
    
    def process_bind_param(self, value: Optional[List[float]], dialect) -> Optional[Any]:
        """Process value before sending to database"""
        if value is None:
            return None
        
        if dialect.name == 'postgresql':
            if PGVECTOR_AVAILABLE and Vector is not None:
                # pgvector handles the conversion
                return value
            else:
                # Convert to PostgreSQL array format
                return value
        else:
            # For other databases, convert to JSON string
            import json
            return json.dumps(value)
    
    def process_result_value(self, value: Optional[Any], dialect) -> Optional[List[float]]:
        """Process value when loading from database"""
        if value is None:
            return None
        
        if dialect.name == 'postgresql':
            if PGVECTOR_AVAILABLE and Vector is not None:
                # pgvector returns the list directly
                return value
            else:
                # PostgreSQL array returns as list
                return list(value) if value else None
        else:
            # For other databases, parse JSON string
            if isinstance(value, str):
                import json
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return None
            return value


# Convenience function for creating embedding columns
def embedding_column(dimensions: int = 384, nullable: bool = True, **kwargs):
    """
    Create an embedding vector column.
    
    Args:
        dimensions: Number of dimensions in the vector
        nullable: Whether the column can be NULL
        **kwargs: Additional column arguments
    
    Returns:
        SQLAlchemy Column with EmbeddingVector type
    """
    from sqlalchemy import Column
    return Column(EmbeddingVector(dimensions), nullable=nullable, **kwargs)
