"""
Simple SQLAlchemy - Enhanced SQLAlchemy utilities and patterns

A simplified, enhanced SQLAlchemy package that provides common patterns
and utilities for database operations.
"""

__version__ = "0.1.0"

# Core imports
from .client import DbClient
from .crud import BaseCrud
from .base import CommonBase, SoftDeleteMixin, metadata_obj
from .session import session_scope, detach_object

# Helper imports
from .helpers.m2m import M2MHelper
from .helpers.search import SearchHelper
from .helpers.pagination import PaginationHelper

# Optional string-schema helper
try:
    from .helpers.string_schema import StringSchemaHelper
    __all_string_schema = ["StringSchemaHelper"]
except ImportError:
    __all_string_schema = []

__all__ = [
    # Core classes
    "DbClient",
    "BaseCrud",
    "CommonBase",
    "SoftDeleteMixin",
    "metadata_obj",

    # Session utilities
    "session_scope",
    "detach_object",

    # Helpers
    "M2MHelper",
    "SearchHelper",
    "PaginationHelper",
] + __all_string_schema

# PostgreSQL-specific imports (optional)
try:
    from .postgres.types import EmbeddingVector
    from .postgres.utils import PostgreSQLUtils
    __all__.extend(["EmbeddingVector", "PostgreSQLUtils"])
except ImportError:
    # PostgreSQL dependencies not available
    pass
