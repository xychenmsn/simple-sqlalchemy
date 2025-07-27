"""
Tests for helper modules (M2M, Search, Pagination)
"""

import pytest
from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship

from simple_sqlalchemy import CommonBase, PaginationHelper
from simple_sqlalchemy.helpers.m2m import M2MHelper
from simple_sqlalchemy.helpers.search import SearchHelper
from tests.conftest import User, Post


# M2M Test Models
user_role_table = Table(
    'test_user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('test_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('test_roles.id'), primary_key=True)
)


class Role(CommonBase):
    """Test role model for M2M relationships"""
    __tablename__ = 'test_roles'
    
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200))
    
    users = relationship("User", secondary=user_role_table, back_populates="roles")


# Add roles relationship to User model
User.roles = relationship("Role", secondary=user_role_table, back_populates="users")


class TestM2MHelper:
    """Test M2MHelper functionality"""
    
    @pytest.fixture
    def role_crud(self, db_client):
        """Role CRUD operations fixture"""
        from tests.conftest import CategoryCrud  # Reuse pattern
        
        class RoleCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = Role
        
        return RoleCrud(db_client)
    
    @pytest.fixture
    def sample_role(self, role_crud):
        """Create a sample role for testing"""
        return role_crud.create({
            "name": "Admin",
            "description": "Administrator role"
        })
    
    @pytest.fixture
    def sample_roles(self, role_crud):
        """Create multiple sample roles for testing"""
        roles = []
        for i in range(3):
            role = role_crud.create({
                "name": f"Role {i}",
                "description": f"Test role {i}"
            })
            roles.append(role)
        return roles
    
    @pytest.fixture
    def m2m_helper(self, db_client):
        """M2M helper fixture"""
        # Create the M2M table
        user_role_table.create(db_client.engine, checkfirst=True)
        Role.__table__.create(db_client.engine, checkfirst=True)
        
        return M2MHelper(db_client, User, Role, "roles", "users")
    
    def test_m2m_helper_initialization(self, m2m_helper):
        """Test M2M helper initialization"""
        assert m2m_helper.source_model == User
        assert m2m_helper.target_model == Role
        assert m2m_helper.source_attr == "roles"
        assert m2m_helper.target_attr == "users"
    
    def test_add_relationship(self, m2m_helper, sample_user, sample_role):
        """Test adding M2M relationship"""
        result = m2m_helper.add_relationship(sample_user.id, sample_role.id)
        
        assert result is not None
        assert result.id == sample_user.id
        
        # Verify relationship exists
        exists = m2m_helper.relationship_exists(sample_user.id, sample_role.id)
        assert exists is True
    
    def test_add_duplicate_relationship(self, m2m_helper, sample_user, sample_role):
        """Test adding duplicate M2M relationship"""
        # Add relationship twice
        m2m_helper.add_relationship(sample_user.id, sample_role.id)
        result = m2m_helper.add_relationship(sample_user.id, sample_role.id)
        
        assert result is not None
        
        # Should still exist only once
        related_roles = m2m_helper.get_related_for_source(sample_user.id)
        assert len(related_roles) == 1
    
    def test_remove_relationship(self, m2m_helper, sample_user, sample_role):
        """Test removing M2M relationship"""
        # First add relationship
        m2m_helper.add_relationship(sample_user.id, sample_role.id)
        
        # Then remove it
        result = m2m_helper.remove_relationship(sample_user.id, sample_role.id)
        
        assert result is not None
        
        # Verify relationship no longer exists
        exists = m2m_helper.relationship_exists(sample_user.id, sample_role.id)
        assert exists is False
    
    def test_get_related_for_source(self, m2m_helper, sample_user, sample_roles):
        """Test getting related records for source"""
        # Add relationships
        for role in sample_roles:
            m2m_helper.add_relationship(sample_user.id, role.id)
        
        related_roles = m2m_helper.get_related_for_source(sample_user.id)
        
        assert len(related_roles) == len(sample_roles)
        role_ids = [role.id for role in related_roles]
        for role in sample_roles:
            assert role.id in role_ids
    
    def test_get_sources_for_target(self, m2m_helper, sample_users, sample_role):
        """Test getting source records for target"""
        # Add relationships
        for user in sample_users:
            m2m_helper.add_relationship(user.id, sample_role.id)
        
        related_users = m2m_helper.get_sources_for_target(sample_role.id)
        
        assert len(related_users) == len(sample_users)
        user_ids = [user.id for user in related_users]
        for user in sample_users:
            assert user.id in user_ids
    
    def test_count_related_for_source(self, m2m_helper, sample_user, sample_roles):
        """Test counting related records for source"""
        # Add relationships
        for role in sample_roles[:2]:  # Add only first 2
            m2m_helper.add_relationship(sample_user.id, role.id)
        
        count = m2m_helper.count_related_for_source(sample_user.id)
        assert count == 2
    
    def test_count_sources_for_target(self, m2m_helper, sample_users, sample_role):
        """Test counting source records for target"""
        # Add relationships
        for user in sample_users[:3]:  # Add only first 3
            m2m_helper.add_relationship(user.id, sample_role.id)
        
        count = m2m_helper.count_sources_for_target(sample_role.id)
        assert count == 3
    
    def test_relationship_exists(self, m2m_helper, sample_user, sample_role):
        """Test checking if relationship exists"""
        # Initially should not exist
        exists = m2m_helper.relationship_exists(sample_user.id, sample_role.id)
        assert exists is False
        
        # Add relationship
        m2m_helper.add_relationship(sample_user.id, sample_role.id)
        
        # Now should exist
        exists = m2m_helper.relationship_exists(sample_user.id, sample_role.id)
        assert exists is True
    
    def test_nonexistent_records(self, m2m_helper):
        """Test operations with non-existent records"""
        # Try to add relationship with non-existent IDs
        result = m2m_helper.add_relationship(99999, 99999)
        assert result is None
        
        # Try to remove relationship with non-existent IDs
        result = m2m_helper.remove_relationship(99999, 99999)
        assert result is None
        
        # Check relationship with non-existent IDs
        exists = m2m_helper.relationship_exists(99999, 99999)
        assert exists is False
        
        # Get related for non-existent source
        related = m2m_helper.get_related_for_source(99999)
        assert related == []
        
        # Count for non-existent records
        count = m2m_helper.count_related_for_source(99999)
        assert count == 0


class TestSearchHelper:
    """Test SearchHelper functionality"""
    
    @pytest.fixture
    def search_helper(self, db_client):
        """Search helper fixture"""
        return SearchHelper(db_client, User)
    
    def test_search_helper_initialization(self, search_helper):
        """Test SearchHelper initialization"""
        assert search_helper.model == User
        assert search_helper.db_client is not None
    
    def test_paginated_search_with_count(self, search_helper, sample_users):
        """Test paginated search with count"""
        def query_builder(session):
            return session.query(User).filter(User.is_active == True)
        
        result = search_helper.paginated_search_with_count(
            base_query_builder=query_builder,
            page=1,
            per_page=2
        )
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result
        assert "total_pages" in result
        
        assert result["page"] == 1
        assert result["per_page"] == 2
        assert len(result["items"]) <= 2
        assert result["total"] >= 0
    
    def test_execute_custom_query(self, search_helper, sample_users):
        """Test executing custom query"""
        def query_builder(session):
            return session.query(User).filter(User.is_active == True)
        
        users = search_helper.execute_custom_query(query_builder)
        
        assert isinstance(users, list)
        assert all(isinstance(user, User) for user in users)
        assert all(user.is_active for user in users)
    
    def test_count_with_custom_query(self, search_helper, sample_users):
        """Test counting with custom query"""
        def query_builder(session):
            return session.query(User).filter(User.is_active == True)
        
        count = search_helper.count_with_custom_query(query_builder)
        
        assert isinstance(count, int)
        assert count >= 0
    
    def test_batch_process(self, search_helper, sample_users):
        """Test batch processing"""
        processed_users = []
        
        def processor(users):
            processed_users.extend(users)
        
        def query_builder(session):
            return session.query(User)
        
        total_processed = search_helper.batch_process(
            query_builder=query_builder,
            batch_size=2,
            processor=processor
        )
        
        assert total_processed >= len(sample_users)
        assert len(processed_users) >= len(sample_users)
    
    def test_search_with_aggregation(self, search_helper, sample_users):
        """Test search with aggregation"""
        from sqlalchemy import func
        
        def query_builder(session):
            return session.query(User)
        
        def aggregation_func(query):
            return query.with_entities(func.count(User.id)).scalar()
        
        count = search_helper.search_with_aggregation(query_builder, aggregation_func)
        
        assert isinstance(count, int)
        assert count >= len(sample_users)


class TestPaginationHelper:
    """Test pagination functionality"""

    def test_calculate_pagination(self):
        """Test calculating pagination info"""
        from simple_sqlalchemy.helpers.pagination import calculate_pagination

        info = calculate_pagination(page=2, per_page=10, total=95)

        assert info["page"] == 2
        assert info["per_page"] == 10
        assert info["total"] == 95
        assert info["total_pages"] == 10
        assert info["has_prev"] is True
        assert info["has_next"] is True
        assert info["prev_page"] == 1
        assert info["next_page"] == 3
        assert info["offset"] == 10
        assert info["start_item"] == 11
        assert info["end_item"] == 20

    def test_calculate_pagination_first_page(self):
        """Test pagination info for first page"""
        from simple_sqlalchemy.helpers.pagination import calculate_pagination

        info = calculate_pagination(page=1, per_page=10, total=25)

        assert info["page"] == 1
        assert info["has_prev"] is False
        assert info["prev_page"] is None
        assert info["has_next"] is True
        assert info["next_page"] == 2
        assert info["offset"] == 0
        assert info["start_item"] == 1
        assert info["end_item"] == 10

    def test_calculate_pagination_last_page(self):
        """Test pagination info for last page"""
        from simple_sqlalchemy.helpers.pagination import calculate_pagination

        info = calculate_pagination(page=3, per_page=10, total=25)

        assert info["page"] == 3
        assert info["has_prev"] is True
        assert info["prev_page"] == 2
        assert info["has_next"] is False
        assert info["next_page"] is None
        assert info["offset"] == 20
        assert info["start_item"] == 21
        assert info["end_item"] == 25

    def test_calculate_pagination_single_page(self):
        """Test pagination info for single page"""
        from simple_sqlalchemy.helpers.pagination import calculate_pagination

        info = calculate_pagination(page=1, per_page=10, total=5)

        assert info["page"] == 1
        assert info["total_pages"] == 1
        assert info["has_prev"] is False
        assert info["has_next"] is False
        assert info["prev_page"] is None
        assert info["next_page"] is None
        assert info["offset"] == 0
        assert info["start_item"] == 1
        assert info["end_item"] == 5

    def test_calculate_pagination_empty(self):
        """Test pagination info for empty results"""
        from simple_sqlalchemy.helpers.pagination import calculate_pagination

        info = calculate_pagination(page=1, per_page=10, total=0)

        assert info["page"] == 1
        assert info["total"] == 0
        assert info["total_pages"] == 1
        assert info["has_prev"] is False
        assert info["has_next"] is False
        assert info["offset"] == 0
        assert info["start_item"] == 0
        assert info["end_item"] == 0

    def test_build_pagination_response(self):
        """Test building pagination response"""
        from simple_sqlalchemy.helpers.pagination import build_pagination_response

        items = ["item1", "item2", "item3"]
        response = build_pagination_response(
            items=items,
            page=2,
            per_page=10,
            total=95
        )

        assert response["items"] == items
        assert response["total"] == 95
        assert response["page"] == 2
        assert response["per_page"] == 10
        assert response["total_pages"] == 10
        assert "has_prev" in response
        assert "has_next" in response
        assert "prev_page" in response
        assert "next_page" in response

    def test_build_pagination_response_without_navigation(self):
        """Test building pagination response without navigation info"""
        from simple_sqlalchemy.helpers.pagination import build_pagination_response

        items = ["item1", "item2"]
        response = build_pagination_response(
            items=items,
            page=1,
            per_page=10,
            total=2,
            include_navigation=False
        )

        assert response["items"] == items
        assert "has_prev" not in response
        assert "has_next" not in response

    def test_validate_pagination_params_valid(self):
        """Test validating valid pagination parameters"""
        from simple_sqlalchemy.helpers.pagination import validate_pagination_params

        page, per_page = validate_pagination_params(page=2, per_page=15)

        assert page == 2
        assert per_page == 15

    def test_validate_pagination_params_invalid(self):
        """Test validating invalid pagination parameters"""
        from simple_sqlalchemy.helpers.pagination import validate_pagination_params
        import pytest

        # Test invalid page
        with pytest.raises(ValueError, match="Page must be >= 1"):
            validate_pagination_params(page=-1, per_page=10)

        # Test invalid per_page
        with pytest.raises(ValueError, match="Per page must be >= 1"):
            validate_pagination_params(page=1, per_page=0)

        # Test per_page too large
        with pytest.raises(ValueError, match="Per page must be <= 100"):
            validate_pagination_params(page=1, per_page=200, max_per_page=100)

    def test_pagination_summary(self):
        """Test pagination summary generation"""
        from simple_sqlalchemy.helpers.pagination import get_pagination_summary

        # Normal range
        summary = get_pagination_summary(page=2, per_page=10, total=95)
        assert summary == "Showing 11-20 of 95 items"

        # Single item
        summary = get_pagination_summary(page=1, per_page=10, total=1)
        assert summary == "Showing item 1 of 1"

        # Empty
        summary = get_pagination_summary(page=1, per_page=10, total=0)
        assert summary == "No items found"

    def test_validate_pagination_params_defaults(self):
        """Test validating with default values"""
        from simple_sqlalchemy.helpers.pagination import validate_pagination_params

        # None values should use defaults
        page, per_page = validate_pagination_params(page=None, per_page=None)
        assert page == 1
        assert per_page == 20

    def test_validate_pagination_params_custom_defaults(self):
        """Test validating with custom defaults"""
        from simple_sqlalchemy.helpers.pagination import validate_pagination_params

        page, per_page = validate_pagination_params(
            page=None,
            per_page=None,
            default_per_page=50
        )

        assert page == 1
        assert per_page == 50
