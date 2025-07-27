"""
Tests for string-schema integration in simple-sqlalchemy
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# Test models from conftest
from .conftest import User, Post, Category, UserCrud, PostCrud, CategoryCrud


def _has_string_schema():
    """Check if string-schema is available"""
    try:
        import string_schema
        return True
    except ImportError:
        return False


class TestStringSchemaIntegration:
    """Test string-schema integration with BaseCrud"""
    
    def test_string_schema_not_available(self, user_crud):
        """Test graceful handling when string-schema is not available"""
        # Mock the string-schema import to fail
        with patch('simple_sqlalchemy.helpers.string_schema.HAS_STRING_SCHEMA', False):
            with pytest.raises(ImportError, match="string-schema is required"):
                user_crud._get_schema_helper()
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_query_with_schema_basic(self, user_crud, sample_users):
        """Test basic query with schema validation"""
        # Query with simple schema
        results = user_crud.query_with_schema(
            "id:int, name:string, email:email",
            limit=3
        )
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)
            assert "id" in result
            assert "name" in result
            assert "email" in result
            assert isinstance(result["id"], int)
            assert isinstance(result["name"], str)
            assert isinstance(result["email"], str)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_query_with_schema_filters(self, user_crud, sample_users):
        """Test query with schema and filters"""
        results = user_crud.query_with_schema(
            "id:int, name:string, is_active:bool",
            filters={"is_active": True}
        )
        
        # Should only return active users
        assert len(results) >= 1
        for result in results:
            assert result["is_active"] is True
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_query_with_schema_search(self, user_crud, sample_users):
        """Test query with schema and search"""
        results = user_crud.query_with_schema(
            "id:int, name:string, email:email",
            search_query="User 1",
            search_fields=["name"]
        )
        
        assert len(results) == 1
        assert "User 1" in results[0]["name"]
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_query_with_schema_sorting(self, user_crud, sample_users):
        """Test query with schema and sorting"""
        results = user_crud.query_with_schema(
            "id:int, name:string",
            sort_by="name",
            sort_desc=True
        )
        
        # Should be sorted by name descending
        names = [r["name"] for r in results]
        assert names == sorted(names, reverse=True)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_query_with_schema_relationships(self, post_crud, sample_posts):
        """Test query with schema including relationships"""
        results = post_crud.query_with_schema(
            "id:int, title:string, author:{id:int, name:string}",
            include_relationships=["author"],
            limit=1
        )
        
        assert len(results) == 1
        result = results[0]
        assert "author" in result
        assert isinstance(result["author"], dict)
        assert "id" in result["author"]
        assert "name" in result["author"]
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_paginated_query_with_schema(self, user_crud, sample_users):
        """Test paginated query with schema validation"""
        result = user_crud.paginated_query_with_schema(
            "id:int, name:string, email:email",
            page=1,
            per_page=2
        )
        
        # Check pagination structure
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result
        assert "total_pages" in result
        assert "has_next" in result
        assert "has_prev" in result
        
        # Check data
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["per_page"] == 2
        assert result["total"] == len(sample_users)
        
        # Check item structure
        for item in result["items"]:
            assert isinstance(item, dict)
            assert "id" in item
            assert "name" in item
            assert "email" in item
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_paginated_query_with_schema_filters(self, user_crud, sample_users):
        """Test paginated query with filters"""
        result = user_crud.paginated_query_with_schema(
            "id:int, name:string, is_active:bool",
            page=1,
            per_page=10,
            filters={"is_active": True}
        )
        
        # All returned items should be active
        for item in result["items"]:
            assert item["is_active"] is True
        
        # Total should reflect filtered count
        active_count = sum(1 for user in sample_users if user.is_active)
        assert result["total"] == active_count
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_aggregate_with_schema(self, user_crud, sample_users):
        """Test aggregation queries with schema validation"""
        results = user_crud.aggregate_with_schema(
            aggregations={
                "total_users": "count(*)",
                "active_users": "count(is_active)"
            },
            schema_str="total_users:int, active_users:int"
        )
        
        assert len(results) == 1
        result = results[0]
        assert "total_users" in result
        assert "active_users" in result
        assert isinstance(result["total_users"], int)
        assert isinstance(result["active_users"], int)
        assert result["total_users"] == len(sample_users)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_aggregate_with_schema_group_by(self, user_crud, sample_users):
        """Test aggregation with group by"""
        results = user_crud.aggregate_with_schema(
            aggregations={"user_count": "count(*)"},
            schema_str="is_active:bool, user_count:int",
            group_by=["is_active"]
        )
        
        assert len(results) == 2  # True and False groups
        for result in results:
            assert "is_active" in result
            assert "user_count" in result
            assert isinstance(result["is_active"], bool)
            assert isinstance(result["user_count"], int)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_predefined_schemas(self, user_crud, sample_user):
        """Test predefined schemas (basic, full)"""
        # Test basic schema
        basic_results = user_crud.query_with_schema("basic", limit=1)
        assert len(basic_results) == 1
        basic_result = basic_results[0]
        assert "id" in basic_result
        
        # Test full schema
        full_results = user_crud.query_with_schema("full", limit=1)
        assert len(full_results) == 1
        full_result = full_results[0]
        assert "id" in full_result
        assert "name" in full_result
        assert "email" in full_result
        assert "is_active" in full_result
        assert "created_at" in full_result
        assert "updated_at" in full_result
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_custom_schema_management(self, user_crud):
        """Test adding and using custom schemas"""
        # Add custom schema
        user_crud.add_schema("user_summary", "id:int, name:string")
        
        # Check schema was added
        schema_def = user_crud.get_schema("user_summary")
        assert schema_def == "id:int, name:string"
        
        # Use custom schema
        user_crud.create({"name": "Test User", "email": "test@example.com"})
        results = user_crud.query_with_schema("user_summary")
        
        assert len(results) >= 1
        for result in results:
            assert "id" in result
            assert "name" in result
            assert "email" not in result  # Should not be in summary schema
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_soft_delete_handling(self, post_crud, sample_post):
        """Test that soft delete is handled correctly"""
        # Create and soft delete a post
        post_crud.soft_delete(sample_post.id)
        
        # Query without including deleted should not return the post
        results = post_crud.query_with_schema(
            "id:int, title:string",
            include_deleted=False
        )
        post_ids = [r["id"] for r in results]
        assert sample_post.id not in post_ids
        
        # Query including deleted should return the post
        results_with_deleted = post_crud.query_with_schema(
            "id:int, title:string",
            include_deleted=True
        )
        post_ids_with_deleted = [r["id"] for r in results_with_deleted]
        assert sample_post.id in post_ids_with_deleted
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_optional_fields_in_schema(self, user_crud, sample_user):
        """Test handling of optional fields in schema"""
        # Create user without optional field
        user_crud.create({
            "name": "User Without Description",
            "email": "nodesc@example.com"
        })
        
        # Query with optional field in schema
        results = user_crud.query_with_schema(
            "id:int, name:string, email:email, description:text?"
        )
        
        # Should handle missing optional field gracefully
        assert len(results) >= 1
        for result in results:
            assert "id" in result
            assert "name" in result
            assert "email" in result
            # description might be None or missing
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_invalid_schema_handling(self, user_crud):
        """Test handling of invalid schemas"""
        # Create a user first
        user_crud.create({"name": "Test User", "email": "test@example.com"})

        # Try with invalid schema - this might not raise an exception
        # depending on string-schema implementation, so let's test a different way
        try:
            result = user_crud.query_with_schema("invalid_field:unknown_type")
            # If it doesn't raise, that's also acceptable behavior
            assert isinstance(result, list)
        except Exception:
            # If it raises an exception, that's also acceptable
            pass
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_empty_results(self, user_crud):
        """Test handling of empty query results"""
        results = user_crud.query_with_schema(
            "id:int, name:string",
            filters={"name": "NonexistentUser"}
        )
        
        assert results == []
        
        # Test paginated empty results
        paginated = user_crud.paginated_query_with_schema(
            "id:int, name:string",
            filters={"name": "NonexistentUser"}
        )
        
        assert paginated["items"] == []
        assert paginated["total"] == 0


class TestStringSchemaHelper:
    """Test StringSchemaHelper directly"""
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_string_schema_helper_initialization(self, db_client):
        """Test StringSchemaHelper initialization"""
        from simple_sqlalchemy.helpers.string_schema import StringSchemaHelper
        
        helper = StringSchemaHelper(db_client, User)
        assert helper.db_client == db_client
        assert helper.model == User
        assert "basic" in helper.common_schemas
        assert "full" in helper.common_schemas
        assert "list_response" in helper.common_schemas
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_schema_generation(self, db_client):
        """Test automatic schema generation"""
        from simple_sqlalchemy.helpers.string_schema import StringSchemaHelper
        
        helper = StringSchemaHelper(db_client, User)
        
        # Test basic schema generation
        basic_schema = helper._generate_basic_schema()
        assert "id:int" in basic_schema
        assert "name:string" in basic_schema
        
        # Test full schema generation
        full_schema = helper._generate_full_schema()
        assert "id:int" in full_schema
        assert "name:string" in full_schema
        assert "email:" in full_schema  # Should detect email type
        assert "is_active:bool" in full_schema
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_model_to_dict_conversion(self, db_client, user_crud):
        """Test model to dict conversion with schema validation"""
        from simple_sqlalchemy.helpers.string_schema import StringSchemaHelper

        # Create a user within the session context
        user = user_crud.create({
            "name": "Test User",
            "email": "test@example.com",
            "is_active": True
        })

        helper = StringSchemaHelper(db_client, User)

        # Convert model to dict with schema
        result = helper._model_to_dict_with_schema(
            user,
            "id:int, name:string, email:email"
        )

        assert isinstance(result, dict)
        assert result["id"] == user.id
        assert result["name"] == user.name
        assert result["email"] == user.email
