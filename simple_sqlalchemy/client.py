"""
Core database client for simple-sqlalchemy
"""

import logging
from typing import Optional, Dict, Any, Type, TypeVar
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .session import session_scope, detach_object, SessionManager
from .helpers.m2m import M2MHelper
from .helpers.search import SearchHelper

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DbClient:
    """
    Core database client that provides connection management and session handling.
    
    Features:
    - Database connection management
    - Session factory and context managers
    - Helper factory methods for M2M and search operations
    - Extensible design for application-specific clients
    """
    
    def __init__(self, db_url: str, engine_options: Optional[Dict[str, Any]] = None):
        """
        Initialize database client.
        
        Args:
            db_url: Database connection URL
            engine_options: Optional SQLAlchemy engine configuration
        """
        self.db_url = db_url
        self.engine_options = engine_options or {}
        
        # Set up default engine options
        default_options = {
            'echo': False,
            'pool_pre_ping': True,
        }
        
        # Handle SQLite in-memory databases
        if db_url.startswith('sqlite:///:memory:'):
            default_options.update({
                'poolclass': StaticPool,
                'connect_args': {'check_same_thread': False}
            })
        
        # Merge user options with defaults
        final_options = {**default_options, **self.engine_options}
        
        # Create engine and session factory
        self.engine: Engine = create_engine(db_url, **final_options)
        self.session_factory = sessionmaker(bind=self.engine)
        
        # Create session manager
        self.session_manager = SessionManager(self.session_factory)
        
        logger.info(f"DbClient initialized with database: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Return database URL with password masked for logging"""
        if '://' in self.db_url:
            scheme, rest = self.db_url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                if ':' in credentials:
                    user, _ = credentials.split(':', 1)
                    return f"{scheme}://{user}:***@{host_part}"
        return self.db_url
    
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Returns:
            Context manager that yields a database session
            
        Example:
            with db_client.session_scope() as session:
                user = User(name="John")
                session.add(user)
                # Automatically commits on success, rolls back on exception
        """
        return session_scope(self.session_factory)
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Note: Caller is responsible for closing the session.
        Consider using session_scope() for automatic session management.
        
        Returns:
            New database session
        """
        return self.session_factory()
    
    def detach_object(self, obj: Any, session: Optional[Session] = None) -> Any:
        """
        Detach an SQLAlchemy object from its session.
        
        Args:
            obj: SQLAlchemy model instance to detach
            session: Optional session to expunge from
            
        Returns:
            The detached object
        """
        return detach_object(obj, session)
    
    def create_m2m_helper(self, source_model: Type[T], target_model: Type[T], 
                         source_attr: str, target_attr: str) -> M2MHelper:
        """
        Create a many-to-many relationship helper.
        
        Args:
            source_model: Source model class
            target_model: Target model class  
            source_attr: Attribute name on source model for the relationship
            target_attr: Attribute name on target model for the relationship
            
        Returns:
            M2MHelper instance for managing the relationship
        """
        return M2MHelper(
            db_client=self,
            source_model=source_model,
            target_model=target_model,
            source_attr=source_attr,
            target_attr=target_attr
        )
    
    def create_search_helper(self, model: Type[T]) -> SearchHelper:
        """
        Create a search helper for complex queries.
        
        Args:
            model: Model class to create search helper for
            
        Returns:
            SearchHelper instance for the model
        """
        return SearchHelper(db_client=self, model=model)
    
    def close(self):
        """Close the database engine and all connections"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("Database connections closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __repr__(self):
        return f"<DbClient(url='{self._safe_url()}')>"
