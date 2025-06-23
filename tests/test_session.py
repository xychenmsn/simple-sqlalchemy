"""
Tests for session management functionality
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from simple_sqlalchemy.session import session_scope, detach_object, SessionManager
from tests.conftest import User


class TestSessionScope:
    """Test session_scope context manager"""
    
    def test_session_scope_success(self, db_client):
        """Test successful session scope operation"""
        user_id = None
        
        with session_scope(db_client.session_factory) as session:
            assert isinstance(session, Session)
            
            user = User(name="Session Test", email="session@example.com")
            session.add(user)
            session.flush()
            user_id = user.id
            
            assert user_id is not None
        
        # Verify transaction was committed
        with session_scope(db_client.session_factory) as session:
            saved_user = session.query(User).filter(User.id == user_id).first()
            assert saved_user is not None
            assert saved_user.name == "Session Test"
    
    def test_session_scope_rollback(self, db_client):
        """Test session scope with exception (rollback)"""
        user_id = None
        
        try:
            with session_scope(db_client.session_factory) as session:
                user = User(name="Rollback Test", email="rollback@example.com")
                session.add(user)
                session.flush()
                user_id = user.id
                
                # Force an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # Verify transaction was rolled back
        with session_scope(db_client.session_factory) as session:
            saved_user = session.query(User).filter(User.id == user_id).first()
            assert saved_user is None
    
    def test_session_scope_nested_exception(self, db_client):
        """Test session scope with nested operations and exception"""
        user1_id = None
        user2_id = None
        
        # First, create a user successfully
        with session_scope(db_client.session_factory) as session:
            user1 = User(name="User 1", email="user1@example.com")
            session.add(user1)
            session.flush()
            user1_id = user1.id
        
        # Then try to create another user but fail
        try:
            with session_scope(db_client.session_factory) as session:
                user2 = User(name="User 2", email="user2@example.com")
                session.add(user2)
                session.flush()
                user2_id = user2.id
                
                raise ValueError("Second operation failed")
        except ValueError:
            pass
        
        # Verify first user exists, second doesn't
        with session_scope(db_client.session_factory) as session:
            user1 = session.query(User).filter(User.id == user1_id).first()
            user2 = session.query(User).filter(User.id == user2_id).first()
            
            assert user1 is not None
            assert user2 is None
    
    def test_session_scope_manual_rollback(self, db_client):
        """Test manual rollback within session scope"""
        user2_id = None

        with session_scope(db_client.session_factory) as session:
            user = User(name="Manual Rollback", email="manual@example.com")
            session.add(user)
            session.flush()
            user_id = user.id

            # Manual rollback
            session.rollback()

            # Add another user after rollback
            user2 = User(name="After Rollback", email="after@example.com")
            session.add(user2)
            session.flush()
            user2_id = user2.id

        # Verify second user was committed (first was rolled back but we can't easily test that)
        with session_scope(db_client.session_factory) as session:
            user2 = session.query(User).filter(User.id == user2_id).first()
            assert user2 is not None
            assert user2.name == "After Rollback"


class TestDetachObject:
    """Test detach_object functionality"""
    
    def test_detach_object_with_session(self, db_client, sample_user):
        """Test detaching object with explicit session"""
        with session_scope(db_client.session_factory) as session:
            user = session.query(User).filter(User.id == sample_user.id).first()
            assert user in session
            
            detached_user = detach_object(user, session)
            
            assert detached_user not in session
            assert detached_user.id == sample_user.id
            assert detached_user.name == sample_user.name
    
    def test_detach_object_without_session(self, db_client, sample_user):
        """Test detaching object without explicit session"""
        with session_scope(db_client.session_factory) as session:
            user = session.query(User).filter(User.id == sample_user.id).first()
            
            # Detach without passing session (should use object's session)
            detached_user = detach_object(user)
            
            assert detached_user not in session
            assert detached_user.id == sample_user.id
    
    def test_detach_none_object(self):
        """Test detaching None object"""
        result = detach_object(None)
        assert result is None
    
    def test_detach_already_detached_object(self, sample_user):
        """Test detaching already detached object"""
        # sample_user should already be detached from fixture
        result = detach_object(sample_user)
        
        assert result == sample_user
        assert result.id == sample_user.id
    
    def test_detach_object_preserves_data(self, db_client, sample_user):
        """Test that detaching preserves all object data"""
        with session_scope(db_client.session_factory) as session:
            user = session.query(User).filter(User.id == sample_user.id).first()
            
            # Store original values
            original_id = user.id
            original_name = user.name
            original_email = user.email
            original_created_at = user.created_at
            original_updated_at = user.updated_at
            
            detached_user = detach_object(user, session)
            
            # Verify all data is preserved
            assert detached_user.id == original_id
            assert detached_user.name == original_name
            assert detached_user.email == original_email
            assert detached_user.created_at == original_created_at
            assert detached_user.updated_at == original_updated_at


class TestSessionManager:
    """Test SessionManager functionality"""
    
    def test_session_manager_initialization(self, db_client):
        """Test SessionManager initialization"""
        manager = SessionManager(db_client.session_factory)
        
        assert manager.session_factory == db_client.session_factory
    
    def test_session_manager_session_scope(self, db_client):
        """Test SessionManager session_scope method"""
        manager = SessionManager(db_client.session_factory)
        
        with manager.session_scope() as session:
            assert isinstance(session, Session)
            
            user = User(name="Manager Test", email="manager@example.com")
            session.add(user)
            session.flush()
            user_id = user.id
        
        # Verify transaction was committed
        with manager.session_scope() as session:
            saved_user = session.query(User).filter(User.id == user_id).first()
            assert saved_user is not None
    
    def test_session_manager_session_factory(self, db_client):
        """Test SessionManager session factory access"""
        manager = SessionManager(db_client.session_factory)

        # SessionManager doesn't have get_session, but we can access the factory
        session = manager.session_factory()

        assert isinstance(session, Session)
        assert session.bind == db_client.engine

        session.close()
    
    def test_session_manager_detach_object(self, db_client, sample_user):
        """Test SessionManager detach_object method"""
        manager = SessionManager(db_client.session_factory)
        
        with manager.session_scope() as session:
            user = session.query(User).filter(User.id == sample_user.id).first()
            
            detached_user = manager.detach_object(user, session)
            
            assert detached_user not in session
            assert detached_user.id == sample_user.id


class TestSessionIntegration:
    """Test session integration with other components"""
    
    def test_session_with_crud_operations(self, db_client):
        """Test session management with CRUD operations"""
        from tests.conftest import UserCrud
        
        user_crud = UserCrud(db_client)
        
        # Create user (should handle session automatically)
        user = user_crud.create({
            "name": "CRUD Session Test",
            "email": "crud.session@example.com"
        })
        
        assert user.id is not None
        
        # Update user (should handle session automatically)
        updated_user = user_crud.update(user.id, {"name": "Updated CRUD"})
        
        assert updated_user.name == "Updated CRUD"
        
        # Get user (should handle session automatically)
        retrieved_user = user_crud.get_by_id(user.id)
        
        assert retrieved_user.name == "Updated CRUD"
    
    def test_concurrent_sessions(self, db_client):
        """Test multiple concurrent sessions"""
        # Create users in separate sessions
        user_ids = []
        
        for i in range(3):
            with session_scope(db_client.session_factory) as session:
                user = User(name=f"Concurrent User {i}", email=f"concurrent{i}@example.com")
                session.add(user)
                session.flush()
                user_ids.append(user.id)
        
        # Verify all users were created
        with session_scope(db_client.session_factory) as session:
            for user_id in user_ids:
                user = session.query(User).filter(User.id == user_id).first()
                assert user is not None
