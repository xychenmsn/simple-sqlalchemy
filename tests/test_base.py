"""
Tests for base models and mixins
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer

from simple_sqlalchemy import CommonBase, SoftDeleteMixin, metadata_obj
from simple_sqlalchemy.base import TimestampMixin
from tests.conftest import User, Post


class TestCommonBase:
    """Test CommonBase functionality"""
    
    def test_common_base_fields(self, sample_user):
        """Test that CommonBase provides required fields"""
        assert hasattr(sample_user, 'id')
        assert hasattr(sample_user, 'created_at')
        assert hasattr(sample_user, 'updated_at')
        
        assert sample_user.id is not None
        assert sample_user.created_at is not None
        assert sample_user.updated_at is not None
        assert isinstance(sample_user.created_at, datetime)
        assert isinstance(sample_user.updated_at, datetime)
    
    def test_auto_timestamps(self, user_crud):
        """Test automatic timestamp creation"""
        before_create = datetime.now(timezone.utc)

        user = user_crud.create({
            "name": "Timestamp Test",
            "email": "timestamp@example.com"
        })

        after_create = datetime.now(timezone.utc)

        # Convert to UTC if needed for comparison
        user_created_at = user.created_at
        user_updated_at = user.updated_at
        if user_created_at.tzinfo is None:
            user_created_at = user_created_at.replace(tzinfo=timezone.utc)
        if user_updated_at.tzinfo is None:
            user_updated_at = user_updated_at.replace(tzinfo=timezone.utc)

        assert before_create <= user_created_at <= after_create
        assert before_create <= user_updated_at <= after_create
        # Timestamps should be very close (within 1 second) on creation
        time_diff = abs((user.created_at - user.updated_at).total_seconds())
        assert time_diff < 1.0
    
    def test_updated_at_on_update(self, user_crud, sample_user):
        """Test that updated_at changes on update"""
        original_updated_at = sample_user.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        updated_user = user_crud.update(sample_user.id, {"name": "Updated Name"})
        
        assert updated_user.updated_at > original_updated_at
        assert updated_user.created_at == sample_user.created_at  # Should not change
    
    def test_repr_method(self, sample_user):
        """Test __repr__ method"""
        repr_str = repr(sample_user)
        assert "User" in repr_str
        assert str(sample_user.id) in repr_str
        assert repr_str.startswith("<")
        assert repr_str.endswith(">")
    
    def test_metadata_object(self):
        """Test shared metadata object"""
        assert metadata_obj is not None
        assert CommonBase.metadata == metadata_obj
        
        # Test that models use the shared metadata
        assert User.__table__.metadata == metadata_obj
        assert Post.__table__.metadata == metadata_obj


class TestSoftDeleteMixin:
    """Test SoftDeleteMixin functionality"""
    
    def test_soft_delete_fields(self, sample_post):
        """Test that SoftDeleteMixin provides required fields"""
        assert hasattr(sample_post, 'deleted_at')
        assert sample_post.deleted_at is None  # Should be None initially
    
    def test_soft_delete_method(self, sample_post):
        """Test soft_delete method"""
        before_delete = datetime.now(timezone.utc)
        sample_post.soft_delete()
        after_delete = datetime.now(timezone.utc)
        
        assert sample_post.deleted_at is not None
        assert before_delete <= sample_post.deleted_at <= after_delete
    
    def test_restore_method(self, sample_post):
        """Test restore method"""
        # First soft delete
        sample_post.soft_delete()
        assert sample_post.deleted_at is not None
        
        # Then restore
        sample_post.restore()
        assert sample_post.deleted_at is None
    
    def test_is_deleted_property(self, sample_post):
        """Test is_deleted property"""
        assert sample_post.is_deleted is False
        
        sample_post.soft_delete()
        assert sample_post.is_deleted is True
        
        sample_post.restore()
        assert sample_post.is_deleted is False
    
    def test_is_active_property(self, sample_post):
        """Test is_active property"""
        assert sample_post.is_active is True
        
        sample_post.soft_delete()
        assert sample_post.is_active is False
        
        sample_post.restore()
        assert sample_post.is_active is True


class TestTimestampMixin:
    """Test TimestampMixin functionality"""
    
    def test_timestamp_mixin_standalone(self, db_client):
        """Test TimestampMixin can be used standalone"""
        from sqlalchemy.orm import declarative_base

        # Create a proper base for the test model
        TestBase = declarative_base()

        # Create a test model with only TimestampMixin
        class TimestampOnlyModel(TestBase, TimestampMixin):
            __tablename__ = 'timestamp_only_test'

            id = Column(Integer, primary_key=True)
            name = Column(String(100))

        # Create table
        TimestampOnlyModel.__table__.create(db_client.engine, checkfirst=True)

        # Test that it has timestamp fields
        assert hasattr(TimestampOnlyModel, 'created_at')
        assert hasattr(TimestampOnlyModel, 'updated_at')

        # Test creating an instance
        with db_client.session_scope() as session:
            instance = TimestampOnlyModel(name="Test")
            session.add(instance)
            session.flush()

            assert instance.created_at is not None
            assert instance.updated_at is not None
            assert isinstance(instance.created_at, datetime)
            assert isinstance(instance.updated_at, datetime)


class TestModelInheritance:
    """Test model inheritance patterns"""
    
    def test_user_inheritance(self):
        """Test User model inheritance"""
        assert issubclass(User, CommonBase)
        assert hasattr(User, 'id')
        assert hasattr(User, 'created_at')
        assert hasattr(User, 'updated_at')
        assert hasattr(User, 'name')
        assert hasattr(User, 'email')
        assert hasattr(User, 'is_active')
    
    def test_post_inheritance(self):
        """Test Post model inheritance with SoftDeleteMixin"""
        assert issubclass(Post, CommonBase)
        assert hasattr(Post, 'id')
        assert hasattr(Post, 'created_at')
        assert hasattr(Post, 'updated_at')
        assert hasattr(Post, 'deleted_at')
        assert hasattr(Post, 'title')
        assert hasattr(Post, 'content')
        assert hasattr(Post, 'author_id')
    
    def test_multiple_inheritance_order(self):
        """Test that multiple inheritance works correctly"""
        # Post inherits from both CommonBase and SoftDeleteMixin
        mro = Post.__mro__
        
        # Should have proper method resolution order
        assert CommonBase in mro
        assert SoftDeleteMixin in mro
        
        # Should have all methods available
        post_instance = Post(
            title="Test",
            content="Content",
            author_id=1
        )
        
        # CommonBase methods
        assert hasattr(post_instance, '__repr__')
        
        # SoftDeleteMixin methods
        assert hasattr(post_instance, 'soft_delete')
        assert hasattr(post_instance, 'restore')
        assert hasattr(post_instance, 'is_deleted')
        assert hasattr(post_instance, 'is_active')


class TestTableNames:
    """Test table naming conventions"""
    
    def test_explicit_table_names(self):
        """Test that models have explicit table names"""
        assert User.__tablename__ == 'test_users'
        assert Post.__tablename__ == 'test_posts'
    
    def test_table_creation(self, db_client):
        """Test that tables are created correctly"""
        # Tables should exist (created by fixtures)
        inspector = db_client.engine.dialect.get_table_names(db_client.engine.connect())
        
        assert 'test_users' in inspector
        assert 'test_posts' in inspector
