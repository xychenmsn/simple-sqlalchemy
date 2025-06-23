"""
Integration tests for simple-sqlalchemy components working together
"""

import pytest
from datetime import datetime, timezone

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud, SoftDeleteMixin
from tests.conftest import User, Post, UserCrud, PostCrud


class TestIntegration:
    """Test integration between different components"""
    
    def test_full_crud_workflow(self, db_client):
        """Test complete CRUD workflow"""
        user_crud = UserCrud(db_client)
        post_crud = PostCrud(db_client)
        
        # Create user
        user_data = {
            "name": "Integration User",
            "email": "integration@example.com",
            "is_active": True
        }
        user = user_crud.create(user_data)
        assert user.id is not None
        
        # Create posts for user
        post_data = {
            "title": "Integration Post",
            "content": "This is an integration test post",
            "author_id": user.id,
            "published": True
        }
        post = post_crud.create(post_data)
        assert post.id is not None
        assert post.author_id == user.id
        
        # Update user
        updated_user = user_crud.update(user.id, {"name": "Updated Integration User"})
        assert updated_user.name == "Updated Integration User"
        
        # Get posts by author
        user_posts = post_crud.get_by_author(user.id)
        assert len(user_posts) == 1
        assert user_posts[0].id == post.id
        
        # Soft delete post
        soft_deleted_post = post_crud.soft_delete(post.id)
        assert soft_deleted_post.deleted_at is not None
        
        # Verify post is not in normal queries
        user_posts_after_delete = post_crud.get_by_author(user.id)
        assert len(user_posts_after_delete) == 0
        
        # But can be found when including deleted
        user_posts_with_deleted = post_crud.get_multi(
            filters={"author_id": user.id},
            include_deleted=True
        )
        assert len(user_posts_with_deleted) == 1
        
        # Restore post
        restored_post = post_crud.undelete(post.id)
        assert restored_post.deleted_at is None
        
        # Hard delete post
        delete_result = post_crud.delete(post.id)
        assert delete_result is True
        
        # Hard delete user
        delete_result = user_crud.delete(user.id)
        assert delete_result is True
    
    def test_session_management_with_crud(self, db_client):
        """Test session management integration with CRUD operations"""
        user_crud = UserCrud(db_client)
        
        # Test that CRUD operations handle sessions properly
        users = []
        for i in range(3):
            user = user_crud.create({
                "name": f"Session User {i}",
                "email": f"session{i}@example.com"
            })
            users.append(user)
        
        # All users should be created and have IDs
        assert all(user.id is not None for user in users)
        
        # Test bulk operations using bulk_update_fields
        bulk_update_count = user_crud.bulk_update_fields({"is_active": False})
        assert bulk_update_count >= 3  # Should update at least our test users

        # Verify updates for our test users
        for user in users:
            updated_user = user_crud.get_by_id(user.id)
            assert updated_user.is_active is False
    
    def test_search_and_pagination_integration(self, db_client, sample_users):
        """Test search helper with pagination"""
        search_helper = db_client.create_search_helper(User)
        
        def active_users_query(session):
            return session.query(User).filter(User.is_active == True)
        
        # Test paginated search
        result = search_helper.paginated_search_with_count(
            base_query_builder=active_users_query,
            page=1,
            per_page=2
        )
        
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) <= 2
        
        # Test custom query execution
        active_users = search_helper.execute_custom_query(active_users_query)
        assert all(user.is_active for user in active_users)
        
        # Test count
        count = search_helper.count_with_custom_query(active_users_query)
        assert count == len(active_users)
    
    def test_m2m_integration(self, db_client):
        """Test M2M helper integration"""
        from tests.test_helpers import Role, user_role_table
        
        # Create tables
        user_role_table.create(db_client.engine, checkfirst=True)
        Role.__table__.create(db_client.engine, checkfirst=True)
        
        user_crud = UserCrud(db_client)
        
        # Create test data
        user = user_crud.create({
            "name": "M2M User",
            "email": "m2m@example.com"
        })
        
        # Create role using raw SQL since we don't have RoleCrud
        with db_client.session_scope() as session:
            role = Role(name="M2M Role", description="Test role")
            session.add(role)
            session.flush()
            role_id = role.id
        
        # Test M2M operations
        m2m_helper = db_client.create_m2m_helper(User, Role, "roles", "users")
        
        # Add relationship
        result = m2m_helper.add_relationship(user.id, role_id)
        assert result is not None
        
        # Verify relationship
        user_roles = m2m_helper.get_related_for_source(user.id)
        assert len(user_roles) == 1
        assert user_roles[0].id == role_id
        
        # Count relationships
        count = m2m_helper.count_related_for_source(user.id)
        assert count == 1
    
    def test_error_handling_integration(self, db_client):
        """Test error handling across components"""
        user_crud = UserCrud(db_client)
        
        # Test creating user with invalid data
        try:
            with db_client.session_scope() as session:
                # Try to create user with duplicate email
                user1 = User(name="User 1", email="duplicate@example.com")
                user2 = User(name="User 2", email="duplicate@example.com")
                session.add(user1)
                session.add(user2)
                session.flush()
        except Exception:
            # Should rollback automatically
            pass
        
        # Verify no users were created due to rollback
        users = user_crud.get_multi(filters={"email": "duplicate@example.com"})
        assert len(users) == 0
    
    def test_timestamp_behavior_integration(self, db_client):
        """Test timestamp behavior across operations"""
        user_crud = UserCrud(db_client)
        
        # Create user
        user = user_crud.create({
            "name": "Timestamp User",
            "email": "timestamp@example.com"
        })
        
        original_created_at = user.created_at
        original_updated_at = user.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Update user
        updated_user = user_crud.update(user.id, {"name": "Updated Timestamp User"})
        
        # Verify timestamp behavior
        assert updated_user.created_at == original_created_at  # Should not change
        assert updated_user.updated_at > original_updated_at   # Should be updated
    
    def test_soft_delete_integration(self, db_client):
        """Test soft delete integration across components"""
        post_crud = PostCrud(db_client)
        user_crud = UserCrud(db_client)
        
        # Create user and post
        user = user_crud.create({
            "name": "Soft Delete User",
            "email": "softdelete@example.com"
        })
        
        post = post_crud.create({
            "title": "Soft Delete Post",
            "content": "This post will be soft deleted",
            "author_id": user.id
        })
        
        # Soft delete post
        soft_deleted_post = post_crud.soft_delete(post.id)
        assert soft_deleted_post.deleted_at is not None
        
        # Test that soft deleted posts are excluded from normal queries
        all_posts = post_crud.get_multi()
        post_ids = [p.id for p in all_posts]
        assert post.id not in post_ids
        
        # But included when explicitly requested
        all_posts_with_deleted = post_crud.get_multi(include_deleted=True)
        post_ids_with_deleted = [p.id for p in all_posts_with_deleted]
        assert post.id in post_ids_with_deleted
        
        # Test search helper with soft deleted records
        search_helper = db_client.create_search_helper(Post)

        def all_posts_query(session):
            return session.query(Post)

        def active_posts_query(session):
            return session.query(Post).filter(Post.deleted_at.is_(None))

        # SearchHelper returns all records (including soft deleted)
        all_posts = search_helper.execute_custom_query(all_posts_query)
        all_post_ids = [p.id for p in all_posts]
        assert post.id in all_post_ids  # Soft deleted post is included

        # But we can filter them out explicitly
        active_posts = search_helper.execute_custom_query(active_posts_query)
        active_post_ids = [p.id for p in active_posts]
        assert post.id not in active_post_ids  # Soft deleted post is excluded
    
    def test_detached_objects_integration(self, db_client):
        """Test that objects returned from CRUD are properly detached"""
        user_crud = UserCrud(db_client)
        
        # Create user
        user = user_crud.create({
            "name": "Detached User",
            "email": "detached@example.com"
        })
        
        # User should be detached (not in any session)
        assert user._sa_instance_state.session is None
        
        # Should be able to access properties
        assert user.name == "Detached User"
        assert user.email == "detached@example.com"
        assert user.id is not None
        
        # Get user by ID
        retrieved_user = user_crud.get_by_id(user.id)
        
        # Should also be detached
        assert retrieved_user._sa_instance_state.session is None
        assert retrieved_user.name == "Detached User"
    
    def test_multiple_database_clients(self):
        """Test using multiple independent database clients"""
        client1 = DbClient("sqlite:///:memory:")
        client2 = DbClient("sqlite:///:memory:")
        
        try:
            # Create tables in both
            CommonBase.metadata.create_all(client1.engine)
            CommonBase.metadata.create_all(client2.engine)
            
            user_crud1 = UserCrud(client1)
            user_crud2 = UserCrud(client2)
            
            # Create user in client1
            user1 = user_crud1.create({
                "name": "Client 1 User",
                "email": "client1@example.com"
            })
            
            # Create user in client2
            user2 = user_crud2.create({
                "name": "Client 2 User",
                "email": "client2@example.com"
            })
            
            # Verify isolation
            client1_users = user_crud1.get_multi()
            client2_users = user_crud2.get_multi()
            
            assert len(client1_users) == 1
            assert len(client2_users) == 1
            assert client1_users[0].name == "Client 1 User"
            assert client2_users[0].name == "Client 2 User"
            
        finally:
            client1.close()
            client2.close()
