"""
PostgreSQL-specific features for simple-sqlalchemy
"""

try:
    from .types import EmbeddingVector
    from .utils import PostgreSQLUtils
    __all__ = ["EmbeddingVector", "PostgreSQLUtils"]
except ImportError as e:
    # PostgreSQL dependencies not available
    import warnings
    warnings.warn(f"PostgreSQL features not available: {e}")
    __all__ = []
