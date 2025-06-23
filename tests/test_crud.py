"""
Tests for BaseCrud functionality
"""

import pytest
from datetime import datetime, timezone

from simple_sqlalchemy import BaseCrud
from tests.conftest import User, Post, Category


class TestBaseCrud:
    """Test BaseCrud functionality"""
    
    def test_create_record(self, user_crud):
        """Test creating a new record"""
        data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "is_active": True
        }
        
        user = user_crud.create(data)
        
        assert user.id is not None
        assert user.name == "Jane Doe"
        assert user.email == "jane@example.com"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_create_with_none_values(self, user_crud):
        """Test creating record with None values (should be filtered out)"""
        data = {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "is_active": None,  # Should be filtered out
            "invalid_field": "should be ignored"  # Should be filtered out
        }
        
        user = user_crud.create(data)
        
        assert user.name == "John Smith"
        assert user.email == "john.smith@example.com"
        assert user.is_active is True  # Default value
    
    def test_get_by_id(self, user_crud, sample_user):
        """Test getting record by ID"""
        user = user_crud.get_by_id(sample_user.id)
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.name == sample_user.name
        assert user.email == sample_user.email
    
    def test_get_by_id_not_found(self, user_crud):
        """Test getting non-existent record"""
        user = user_crud.get_by_id(99999)
        assert user is None
    
    def test_get_by_field(self, user_crud, sample_user):
        """Test getting record by field"""
        user = user_crud.get_by_field("email", sample_user.email)
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email
    
    def test_get_by_field_not_found(self, user_crud):
        """Test getting record by field that doesn't exist"""
        user = user_crud.get_by_field("email", "nonexistent@example.com")
        assert user is None
    
    def test_get_multi_no_filters(self, user_crud, sample_users):
        """Test getting multiple records without filters"""
        users = user_crud.get_multi()
        
        assert len(users) >= len(sample_users)
        assert all(isinstance(user, User) for user in users)
    
    def test_get_multi_with_filters(self, user_crud, sample_users):
        """Test getting multiple records with filters"""
        active_users = user_crud.get_multi(filters={"is_active": True})
        
        assert len(active_users) > 0
        assert all(user.is_active for user in active_users)
    
    def test_get_multi_with_limit(self, user_crud, sample_users):
        """Test getting multiple records with limit"""
        users = user_crud.get_multi(limit=2)
        
        assert len(users) == 2
    
    def test_get_multi_with_offset(self, user_crud, sample_users):
        """Test getting multiple records with offset"""
        all_users = user_crud.get_multi()
        offset_users = user_crud.get_multi(skip=1)

        assert len(offset_users) == len(all_users) - 1
    
    def test_get_multi_with_order_by(self, user_crud, sample_users):
        """Test getting multiple records with ordering"""
        users_asc = user_crud.get_multi(sort_by="name", sort_desc=False)
        users_desc = user_crud.get_multi(sort_by="name", sort_desc=True)

        assert len(users_asc) == len(users_desc)
        if len(users_asc) > 1:
            assert users_asc[0].name != users_desc[0].name
    
    def test_update_record(self, user_crud, sample_user):
        """Test updating a record"""
        update_data = {
            "name": "Updated Name",
            "is_active": False
        }
        
        updated_user = user_crud.update(sample_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.id == sample_user.id
        assert updated_user.name == "Updated Name"
        assert updated_user.is_active is False
        assert updated_user.email == sample_user.email  # Unchanged
    
    def test_update_nonexistent_record(self, user_crud):
        """Test updating non-existent record"""
        updated_user = user_crud.update(99999, {"name": "New Name"})
        assert updated_user is None
    
    def test_delete_record(self, user_crud, sample_user):
        """Test hard deleting a record"""
        result = user_crud.delete(sample_user.id)
        assert result is True
        
        # Verify record is deleted
        deleted_user = user_crud.get_by_id(sample_user.id)
        assert deleted_user is None
    
    def test_delete_nonexistent_record(self, user_crud):
        """Test deleting non-existent record"""
        result = user_crud.delete(99999)
        assert result is False
    
    def test_soft_delete(self, post_crud, sample_post):
        """Test soft deleting a record"""
        soft_deleted_post = post_crud.soft_delete(sample_post.id)
        
        assert soft_deleted_post is not None
        assert soft_deleted_post.id == sample_post.id
        assert soft_deleted_post.deleted_at is not None
        
        # Verify record is not returned in normal queries
        post = post_crud.get_by_id(sample_post.id)
        assert post is None
        
        # But can be found when including deleted
        post_with_deleted = post_crud.get_by_id(sample_post.id, include_deleted=True)
        assert post_with_deleted is not None
    
    def test_soft_delete_unsupported_model(self, user_crud, sample_user):
        """Test soft delete on model that doesn't support it"""
        with pytest.raises(ValueError, match="does not support soft delete"):
            user_crud.soft_delete(sample_user.id)
    
    def test_restore_soft_deleted(self, post_crud, sample_post):
        """Test restoring a soft-deleted record"""
        # First soft delete
        post_crud.soft_delete(sample_post.id)

        # Then restore (method is called 'undelete')
        restored_post = post_crud.undelete(sample_post.id)

        assert restored_post is not None
        assert restored_post.id == sample_post.id
        assert restored_post.deleted_at is None

        # Verify record is available in normal queries
        post = post_crud.get_by_id(sample_post.id)
        assert post is not None
    
    def test_count_records(self, user_crud, sample_users):
        """Test counting records"""
        total_count = user_crud.count()
        active_count = user_crud.count(filters={"is_active": True})
        
        assert total_count >= len(sample_users)
        assert active_count <= total_count
        assert active_count > 0
    
    def test_exists(self, user_crud, sample_user):
        """Test checking if record exists"""
        exists = user_crud.exists_by_field("id", sample_user.id)
        assert exists is True

        not_exists = user_crud.exists_by_field("id", 99999)
        assert not_exists is False
    
    def test_bulk_create(self, user_crud):
        """Test bulk creating records (using individual creates)"""
        data_list = [
            {"name": "Bulk User 1", "email": "bulk1@example.com"},
            {"name": "Bulk User 2", "email": "bulk2@example.com"},
            {"name": "Bulk User 3", "email": "bulk3@example.com"}
        ]

        # Since there's no bulk_create method, create individually
        users = []
        for data in data_list:
            user = user_crud.create(data)
            users.append(user)

        assert len(users) == 3
        assert all(user.id is not None for user in users)
        assert users[0].name == "Bulk User 1"
        assert users[1].name == "Bulk User 2"
        assert users[2].name == "Bulk User 3"
    
    def test_bulk_update(self, user_crud, sample_users):
        """Test bulk updating records"""
        # Use bulk_update_fields method with filters
        update_data = {"is_active": False}

        # Update all users (no specific filters)
        updated_count = user_crud.bulk_update_fields(update_data)

        assert updated_count >= 3  # Should update at least the sample users

        # Verify updates for sample users
        for user in sample_users[:3]:
            updated_user = user_crud.get_by_id(user.id)
            assert updated_user.is_active is False
    
    def test_get_distinct_values(self, user_crud, sample_users):
        """Test getting distinct values"""
        distinct_active_values = user_crud.get_distinct_values("is_active")
        
        assert len(distinct_active_values) == 2  # True and False
        assert True in distinct_active_values
        assert False in distinct_active_values
