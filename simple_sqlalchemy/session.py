"""
Session management utilities for simple-sqlalchemy
"""

import logging
from contextlib import contextmanager
from typing import Optional, Any, Generator
from sqlalchemy.orm import Session, make_transient
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


@contextmanager
def session_scope(session_factory) -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.
    
    This is a context manager that provides a database session with automatic
    transaction management. It commits on success and rolls back on exceptions.
    
    Args:
        session_factory: SQLAlchemy session factory (sessionmaker instance)
        
    Yields:
        Session: Database session
        
    Example:
        with session_scope(session_factory) as session:
            user = User(name="John")
            session.add(user)
            # Automatically commits on success, rolls back on exception
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Session rollback due to exception: {e}")
        raise
    finally:
        session.close()


def detach_object(obj: Any, session: Optional[Session] = None) -> Any:
    """
    Detach an SQLAlchemy object from its session.
    
    This makes the object independent of any session, allowing it to be
    used outside of the session context. Useful for returning objects
    from functions that manage their own sessions.
    
    Args:
        obj: SQLAlchemy model instance to detach
        session: Optional session to expunge from (if not provided, uses obj.session)
        
    Returns:
        The detached object
        
    Example:
        with session_scope(session_factory) as session:
            user = session.query(User).first()
            detached_user = detach_object(user, session)
        # detached_user can now be used outside the session
    """
    if obj is None:
        return obj
    
    try:
        # If session is provided, use it; otherwise try to get from object
        if session is not None:
            session.expunge(obj)
        elif hasattr(obj, '_sa_instance_state') and obj._sa_instance_state.session:
            obj._sa_instance_state.session.expunge(obj)
        else:
            # Object might already be detached or transient
            make_transient(obj)
    except (AttributeError, SQLAlchemyError) as e:
        logger.warning(f"Could not detach object {obj}: {e}")
        # Try alternative approach
        try:
            make_transient(obj)
        except SQLAlchemyError:
            logger.warning(f"Could not make object transient: {obj}")
    
    return obj


def detach_all(objects: list, session: Optional[Session] = None) -> list:
    """
    Detach multiple SQLAlchemy objects from their session.
    
    Args:
        objects: List of SQLAlchemy model instances to detach
        session: Optional session to expunge from
        
    Returns:
        List of detached objects
    """
    if not objects:
        return objects
    
    return [detach_object(obj, session) for obj in objects]


class SessionManager:
    """
    Helper class for managing database sessions.
    
    Provides utilities for session management and object detachment.
    """
    
    def __init__(self, session_factory):
        """
        Initialize SessionManager.
        
        Args:
            session_factory: SQLAlchemy session factory (sessionmaker instance)
        """
        self.session_factory = session_factory
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope using this manager's session factory.
        
        Yields:
            Session: Database session
        """
        with session_scope(self.session_factory) as session:
            yield session
    
    def detach_object(self, obj: Any, session: Optional[Session] = None) -> Any:
        """
        Detach an object using this manager.
        
        Args:
            obj: SQLAlchemy model instance to detach
            session: Optional session to expunge from
            
        Returns:
            The detached object
        """
        return detach_object(obj, session)
    
    def detach_all(self, objects: list, session: Optional[Session] = None) -> list:
        """
        Detach multiple objects using this manager.
        
        Args:
            objects: List of SQLAlchemy model instances to detach
            session: Optional session to expunge from
            
        Returns:
            List of detached objects
        """
        return detach_all(objects, session)
