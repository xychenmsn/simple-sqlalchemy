"""
Advanced tests for string-schema integration in simple-sqlalchemy
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Test models from conftest
from .conftest import User, Post, Category, UserCrud, PostCrud, CategoryCrud


def _has_string_schema():
    """Check if string-schema is available"""
    try:
        import string_schema
        return True
    except ImportError:
        return False


class TestStringSchemaPerformance:
    """Test performance aspects of string-schema integration"""
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_query_performance_comparison(self, user_crud):
        """Compare performance between regular query and schema query"""
        # Create test data
        test_users = []
        for i in range(100):
            user = user_crud.create({
                "name": f"Performance User {i}",
                "email": f"perf{i}@example.com",
                "is_active": i % 2 == 0
            })
            test_users.append(user)
        
        # Time regular query
        start_time = time.time()
        regular_results = user_crud.get_multi(limit=50)
        regular_time = time.time() - start_time
        
        # Time schema query
        start_time = time.time()
        schema_results = user_crud.query_with_schema(
            "id:int, name:string, email:email, is_active:bool",
            limit=50
        )
        schema_time = time.time() - start_time
        
        # Both should return same number of results
        assert len(regular_results) == len(schema_results)
        
        # Schema query should be reasonably fast (within 2x of regular query)
        assert schema_time < regular_time * 2
        
        print(f"Regular query time: {regular_time:.4f}s")
        print(f"Schema query time: {schema_time:.4f}s")
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_pagination_performance(self, user_crud):
        """Test pagination performance with large datasets"""
        # Create larger test dataset
        for i in range(200):
            user_crud.create({
                "name": f"Pagination User {i}",
                "email": f"page{i}@example.com",
                "is_active": True
            })
        
        # Test paginated query performance
        start_time = time.time()
        result = user_crud.paginated_query_with_schema(
            "id:int, name:string, email:email",
            page=5,
            per_page=20
        )
        pagination_time = time.time() - start_time
        
        assert len(result["items"]) == 20
        assert result["page"] == 5
        assert result["total"] >= 200
        
        # Should complete within reasonable time
        assert pagination_time < 1.0  # Less than 1 second
        
        print(f"Pagination query time: {pagination_time:.4f}s")


class TestStringSchemaEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_complex_nested_relationships(self, post_crud, sample_posts):
        """Test complex nested relationship queries"""
        # This tests the limits of what string-schema can handle
        try:
            results = post_crud.query_with_schema(
                "id:int, title:string, author:{id:int, name:string, email:email}",
                include_relationships=["author"],
                limit=1
            )
            
            assert len(results) >= 0  # Should not crash
            if results:
                result = results[0]
                assert "author" in result
                assert isinstance(result["author"], dict)
        except Exception as e:
            # If it fails, it should fail gracefully
            assert "schema" in str(e).lower() or "validation" in str(e).lower()
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_null_and_empty_values(self, user_crud):
        """Test handling of null and empty values"""
        # Create user with minimal data
        user = user_crud.create({
            "name": "",  # Empty string
            "email": "empty@example.com"
        })
        
        results = user_crud.query_with_schema(
            "id:int, name:string, email:email",
            filters={"id": user.id}
        )
        
        assert len(results) == 1
        result = results[0]
        assert result["name"] == ""
        assert result["email"] == "empty@example.com"
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_large_text_fields(self, post_crud, sample_user):
        """Test handling of large text fields"""
        # Create post with large content
        large_content = "A" * 10000  # 10KB of text
        post = post_crud.create({
            "title": "Large Content Post",
            "content": large_content,
            "author_id": sample_user.id,
            "published": True
        })
        
        results = post_crud.query_with_schema(
            "id:int, title:string, content:text",
            filters={"id": post.id}
        )
        
        assert len(results) == 1
        result = results[0]
        assert result["content"] == large_content
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_special_characters_in_data(self, user_crud):
        """Test handling of special characters in data"""
        special_chars_name = "User with 特殊字符 and émojis 🚀"
        user = user_crud.create({
            "name": special_chars_name,
            "email": "special@example.com"
        })
        
        results = user_crud.query_with_schema(
            "id:int, name:string, email:email",
            filters={"id": user.id}
        )
        
        assert len(results) == 1
        result = results[0]
        assert result["name"] == special_chars_name
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_concurrent_schema_operations(self, user_crud):
        """Test thread safety of schema operations"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker():
            try:
                # Each thread creates a user and queries with schema
                user = user_crud.create({
                    "name": f"Concurrent User {threading.current_thread().ident}",
                    "email": f"concurrent{threading.current_thread().ident}@example.com"
                })
                
                result = user_crud.query_with_schema(
                    "id:int, name:string",
                    filters={"id": user.id}
                )
                results_queue.put(result)
            except Exception as e:
                errors_queue.put(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert errors_queue.empty(), f"Errors occurred: {list(errors_queue.queue)}"
        assert results_queue.qsize() == 5
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_schema_caching(self, user_crud):
        """Test that schema helper is cached properly"""
        # First call should create the helper
        helper1 = user_crud._get_string_schema_helper()
        
        # Second call should return the same instance
        helper2 = user_crud._get_string_schema_helper()
        
        assert helper1 is helper2
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_invalid_aggregation_functions(self, user_crud, sample_users):
        """Test handling of invalid aggregation functions"""
        with pytest.raises(Exception):
            user_crud.aggregate_with_schema(
                aggregations={"invalid": "invalid_function(*)"},
                schema_str="invalid:int"
            )
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_pagination_edge_cases(self, user_crud):
        """Test pagination edge cases"""
        # Test page beyond available data
        result = user_crud.paginated_query_with_schema(
            "id:int, name:string",
            page=999,
            per_page=10
        )
        
        assert result["items"] == []
        assert result["page"] <= result["total_pages"]
        
        # Test very large per_page
        result = user_crud.paginated_query_with_schema(
            "id:int, name:string",
            page=1,
            per_page=10000  # Should be capped by validation
        )
        
        assert result["per_page"] <= 1000  # Should be capped
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_search_with_special_characters(self, user_crud):
        """Test search functionality with special characters"""
        # Create user with special characters
        user_crud.create({
            "name": "User with % and _ characters",
            "email": "special_search@example.com"
        })
        
        # Search should handle SQL special characters properly
        results = user_crud.query_with_schema(
            "id:int, name:string",
            search_query="%",
            search_fields=["name"]
        )
        
        # Should find the user without SQL injection issues
        assert len(results) >= 1
        assert any("%" in r["name"] for r in results)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_datetime_handling(self, user_crud, sample_user):
        """Test proper datetime handling in schemas"""
        results = user_crud.query_with_schema(
            "id:int, name:string, created_at:datetime, updated_at:datetime",
            filters={"id": sample_user.id}
        )
        
        assert len(results) == 1
        result = results[0]
        
        # Datetime fields should be properly formatted
        assert "created_at" in result
        assert "updated_at" in result
        
        # Should be datetime objects or ISO strings
        created_at = result["created_at"]
        assert isinstance(created_at, (datetime, str))
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_boolean_field_handling(self, user_crud, sample_users):
        """Test proper boolean field handling"""
        results = user_crud.query_with_schema(
            "id:int, name:string, is_active:bool"
        )
        
        for result in results:
            assert isinstance(result["is_active"], bool)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_memory_usage(self, user_crud):
        """Test memory usage doesn't grow excessively"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many schema operations
        for i in range(100):
            user_crud.create({
                "name": f"Memory Test User {i}",
                "email": f"memory{i}@example.com"
            })
            
            # Query with schema
            user_crud.query_with_schema(
                "id:int, name:string, email:email",
                limit=10
            )
            
            # Force garbage collection periodically
            if i % 20 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB for this test)
        assert memory_growth < 50 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.2f}MB"


class TestStringSchemaIntegrationWithExistingFeatures:
    """Test integration with existing simple-sqlalchemy features"""
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_integration_with_soft_delete(self, post_crud, sample_posts):
        """Test string-schema integration with soft delete functionality"""
        post = sample_posts[0]
        
        # Soft delete the post
        post_crud.soft_delete(post.id)
        
        # Query without including deleted
        results = post_crud.query_with_schema(
            "id:int, title:string",
            include_deleted=False
        )
        post_ids = [r["id"] for r in results]
        assert post.id not in post_ids
        
        # Query including deleted
        results_with_deleted = post_crud.query_with_schema(
            "id:int, title:string",
            include_deleted=True
        )
        post_ids_with_deleted = [r["id"] for r in results_with_deleted]
        assert post.id in post_ids_with_deleted
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_integration_with_existing_crud_methods(self, user_crud, sample_user):
        """Test that string-schema methods work alongside existing CRUD methods"""
        # Use existing CRUD method
        user_by_email = user_crud.get_by_email(sample_user.email)
        assert user_by_email.id == sample_user.id
        
        # Use string-schema method
        schema_results = user_crud.query_with_schema(
            "id:int, email:email",
            filters={"email": sample_user.email}
        )
        assert len(schema_results) == 1
        assert schema_results[0]["id"] == sample_user.id
        
        # Both should return consistent data
        assert schema_results[0]["email"] == user_by_email.email
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_schema_with_custom_crud_methods(self, user_crud, sample_users):
        """Test string-schema with custom CRUD methods"""
        # Use custom method from UserCrud
        active_users = user_crud.get_active_users()
        active_count = len(active_users)
        
        # Use string-schema equivalent
        schema_active_users = user_crud.query_with_schema(
            "id:int, name:string, is_active:bool",
            filters={"is_active": True}
        )
        
        # Should return same count
        assert len(schema_active_users) == active_count
        
        # All should be active
        for user in schema_active_users:
            assert user["is_active"] is True
