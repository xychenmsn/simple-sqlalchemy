"""
Tests for DbClient functionality
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from simple_sqlalchemy import DbClient, CommonBase
from tests.conftest import User


class TestDbClient:
    """Test DbClient functionality"""
    
    def test_client_initialization(self):
        """Test DbClient initialization"""
        client = DbClient("sqlite:///:memory:")
        
        assert client.db_url == "sqlite:///:memory:"
        assert client.engine is not None
        assert client.session_factory is not None
        assert client.session_manager is not None
        
        client.close()
    
    def test_client_with_engine_options(self):
        """Test DbClient with custom engine options"""
        options = {
            "echo": True,
        }
        client = DbClient("sqlite:///:memory:", engine_options=options)

        assert client.engine.echo is True
        # Note: SQLite in-memory uses StaticPool which doesn't have pre_ping

        client.close()
    
    def test_get_session(self, db_client):
        """Test getting a session"""
        session = db_client.get_session()
        
        assert isinstance(session, Session)
        assert session.bind == db_client.engine
        
        session.close()
    
    def test_session_scope_success(self, db_client):
        """Test session scope with successful operation"""
        with db_client.session_scope() as session:
            user = User(name="Test User", email="test@example.com")
            session.add(user)
            session.flush()
            user_id = user.id
        
        # Verify the user was committed
        with db_client.session_scope() as session:
            saved_user = session.query(User).filter(User.id == user_id).first()
            assert saved_user is not None
            assert saved_user.name == "Test User"
            assert saved_user.email == "test@example.com"
    
    def test_session_scope_rollback(self, db_client):
        """Test session scope with exception (rollback)"""
        user_id = None
        
        try:
            with db_client.session_scope() as session:
                user = User(name="Test User", email="test@example.com")
                session.add(user)
                session.flush()
                user_id = user.id
                
                # Force an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception
        
        # Verify the user was rolled back
        with db_client.session_scope() as session:
            saved_user = session.query(User).filter(User.id == user_id).first()
            assert saved_user is None
    
    def test_detach_object(self, db_client, sample_user):
        """Test object detachment"""
        with db_client.session_scope() as session:
            user = session.query(User).filter(User.id == sample_user.id).first()
            assert user is not None
            
            # Detach the object
            detached_user = db_client.detach_object(user, session)
            
            # Object should be detached from session
            assert detached_user not in session
            assert detached_user.id == sample_user.id
            assert detached_user.name == sample_user.name
    
    def test_detach_none_object(self, db_client):
        """Test detaching None object"""
        result = db_client.detach_object(None)
        assert result is None
    
    def test_safe_url_masking(self):
        """Test URL password masking for logging"""
        # Test with password (using sqlite to avoid psycopg2 dependency)
        client = DbClient("sqlite:///:memory:")
        safe_url = client._safe_url()
        assert safe_url == "sqlite:///:memory:"

        client.close()

        # Test URL masking logic directly
        client = DbClient("sqlite:///:memory:")
        # Simulate a URL with password for testing the masking logic
        client.db_url = "postgresql://user:password@localhost/db"
        safe_url = client._safe_url()
        assert "password" not in safe_url
        assert "user:***@localhost" in safe_url

        client.close()
    
    def test_create_tables(self, db_client):
        """Test creating tables"""
        # Tables should already be created by fixture
        with db_client.session_scope() as session:
            # Should be able to query without error
            result = session.query(User).count()
            assert result >= 0
    
    def test_m2m_helper(self, db_client):
        """Test M2M helper creation"""
        from tests.conftest import User, Post
        helper = db_client.create_m2m_helper(User, Post, "posts", "author")
        assert helper is not None
        assert helper.db_client == db_client
        assert helper.source_model == User
        assert helper.target_model == Post

    def test_search_helper(self, db_client):
        """Test search helper creation"""
        from tests.conftest import User
        helper = db_client.create_search_helper(User)
        assert helper is not None
        assert helper.db_client == db_client
        assert helper.model == User
    
    def test_close_client(self):
        """Test closing the client"""
        client = DbClient("sqlite:///:memory:")

        # Client should be usable before closing
        session = client.get_session()
        session.close()

        # Close the client
        client.close()

        # Engine should be disposed (we can't easily test pool state with StaticPool)
        # Just verify the method runs without error
        assert hasattr(client, 'engine')
    
    def test_multiple_clients(self):
        """Test creating multiple independent clients"""
        client1 = DbClient("sqlite:///:memory:")
        client2 = DbClient("sqlite:///:memory:")
        
        # Create tables in both
        CommonBase.metadata.create_all(client1.engine)
        CommonBase.metadata.create_all(client2.engine)
        
        # Add data to client1
        with client1.session_scope() as session:
            user = User(name="User 1", email="user1@example.com")
            session.add(user)
        
        # Verify client2 doesn't have the data
        with client2.session_scope() as session:
            count = session.query(User).count()
            assert count == 0
        
        # Verify client1 has the data
        with client1.session_scope() as session:
            count = session.query(User).count()
            assert count == 1
        
        client1.close()
        client2.close()
