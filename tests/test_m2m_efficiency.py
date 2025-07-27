"""
Tests to prove functional equivalence between original and efficient M2M methods.
"""

import pytest
from sqlalchemy import Column, String, Integer, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from simple_sqlalchemy import CommonBase, SoftDeleteMixin
from simple_sqlalchemy.helpers.m2m import M2MHelper
from tests.conftest import User


# Test models for different M2M scenarios

# 1. Simple M2M table (only foreign keys)
simple_user_role_table = Table(
    'test_simple_user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('test_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('test_simple_roles.id'), primary_key=True)
)

class SimpleRole(CommonBase):
    """Simple role model for basic M2M testing"""
    __tablename__ = 'test_simple_roles'
    
    name = Column(String(50), nullable=False, unique=True)
    users = relationship("User", secondary=simple_user_role_table, back_populates="simple_roles")

# Add relationship to User
User.simple_roles = relationship("SimpleRole", secondary=simple_user_role_table, back_populates="users")


# 2. M2M table with metadata (should fall back to original method)
complex_user_tag_table = Table(
    'test_complex_user_tags',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('test_users.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('test_complex_tags.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String(50))  # Extra metadata that should trigger fallback
)

class ComplexTag(CommonBase):
    """Tag model with complex M2M table"""
    __tablename__ = 'test_complex_tags'
    
    name = Column(String(50), nullable=False, unique=True)
    users = relationship("User", secondary=complex_user_tag_table, back_populates="complex_tags")

User.complex_tags = relationship("ComplexTag", secondary=complex_user_tag_table, back_populates="users")


# 3. M2M with soft-delete on source model
soft_delete_user_category_table = Table(
    'test_soft_delete_user_categories',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('test_soft_delete_users.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('test_efficiency_categories.id'), primary_key=True)
)

class SoftDeleteUser(CommonBase, SoftDeleteMixin):
    """User model with soft delete for testing soft-delete filtering"""
    __tablename__ = 'test_soft_delete_users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    categories = relationship("TestCategory", secondary=soft_delete_user_category_table, back_populates="soft_delete_users")

class TestCategory(CommonBase):
    """Category model for soft-delete testing"""
    __tablename__ = 'test_efficiency_categories'

    name = Column(String(50), nullable=False, unique=True)
    soft_delete_users = relationship("SoftDeleteUser", secondary=soft_delete_user_category_table, back_populates="categories")


class TestM2MEfficiency:
    """Test functional equivalence between original and efficient M2M methods"""
    
    @pytest.fixture
    def simple_role_crud(self, db_client):
        """Simple role CRUD operations fixture"""
        from tests.conftest import CategoryCrud
        
        class SimpleRoleCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = SimpleRole
        
        return SimpleRoleCrud(db_client)
    
    @pytest.fixture
    def complex_tag_crud(self, db_client):
        """Complex tag CRUD operations fixture"""
        from tests.conftest import CategoryCrud
        
        class ComplexTagCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = ComplexTag
        
        return ComplexTagCrud(db_client)
    
    @pytest.fixture
    def soft_delete_user_crud(self, db_client):
        """Soft delete user CRUD operations fixture"""
        from tests.conftest import CategoryCrud
        
        class SoftDeleteUserCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = SoftDeleteUser
        
        return SoftDeleteUserCrud(db_client)
    
    @pytest.fixture
    def category_crud(self, db_client):
        """Category CRUD operations fixture"""
        from tests.conftest import CategoryCrud
        
        class CategoryCrudImpl(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = TestCategory
        
        return CategoryCrudImpl(db_client)
    
    @pytest.fixture
    def setup_tables(self, db_client):
        """Create all test tables"""
        # Create tables
        simple_user_role_table.create(db_client.engine, checkfirst=True)
        SimpleRole.__table__.create(db_client.engine, checkfirst=True)
        
        complex_user_tag_table.create(db_client.engine, checkfirst=True)
        ComplexTag.__table__.create(db_client.engine, checkfirst=True)
        
        soft_delete_user_category_table.create(db_client.engine, checkfirst=True)
        SoftDeleteUser.__table__.create(db_client.engine, checkfirst=True)
        TestCategory.__table__.create(db_client.engine, checkfirst=True)
        
        yield
        
        # Cleanup is handled by conftest.py
    
    @pytest.fixture
    def simple_m2m_helper(self, db_client, setup_tables):
        """M2M helper for simple relationship"""
        return M2MHelper(db_client, User, SimpleRole, "simple_roles", "users")
    
    @pytest.fixture
    def complex_m2m_helper(self, db_client, setup_tables):
        """M2M helper for complex relationship"""
        return M2MHelper(db_client, User, ComplexTag, "complex_tags", "users")
    
    @pytest.fixture
    def soft_delete_m2m_helper(self, db_client, setup_tables):
        """M2M helper for soft-delete relationship"""
        return M2MHelper(db_client, SoftDeleteUser, TestCategory, "categories", "soft_delete_users")

    def test_relationship_exists_equivalence_simple(self, simple_m2m_helper, user_crud, simple_role_crud):
        """Test that relationship_exists and relationship_exists_fast return identical results for simple M2M"""
        # Create test data
        user = user_crud.create({"name": "Test User", "email": "test@example.com"})
        role1 = simple_role_crud.create({"name": "Admin"})
        role2 = simple_role_crud.create({"name": "User"})

        # Test non-existent relationship
        original_result = simple_m2m_helper.relationship_exists(user.id, role1.id)
        fast_result = simple_m2m_helper.relationship_exists_fast(user.id, role1.id)
        assert original_result == fast_result == False

        # Add relationship
        simple_m2m_helper.add_relationship(user.id, role1.id)

        # Test existing relationship
        original_result = simple_m2m_helper.relationship_exists(user.id, role1.id)
        fast_result = simple_m2m_helper.relationship_exists_fast(user.id, role1.id)
        assert original_result == fast_result == True

        # Test non-existent relationship with same user
        original_result = simple_m2m_helper.relationship_exists(user.id, role2.id)
        fast_result = simple_m2m_helper.relationship_exists_fast(user.id, role2.id)
        assert original_result == fast_result == False

        # Test with non-existent user
        original_result = simple_m2m_helper.relationship_exists(99999, role1.id)
        fast_result = simple_m2m_helper.relationship_exists_fast(99999, role1.id)
        assert original_result == fast_result == False

        # Test with non-existent role
        original_result = simple_m2m_helper.relationship_exists(user.id, 99999)
        fast_result = simple_m2m_helper.relationship_exists_fast(user.id, 99999)
        assert original_result == fast_result == False

    def test_relationship_exists_equivalence_complex(self, complex_m2m_helper, user_crud, complex_tag_crud):
        """Test that complex M2M relationships fall back to original method"""
        # Create test data
        user = user_crud.create({"name": "Test User", "email": "test2@example.com"})
        tag = complex_tag_crud.create({"name": "Python"})

        # For complex relationships, fast method should fall back to original
        # Both should return the same results
        original_result = complex_m2m_helper.relationship_exists(user.id, tag.id)
        fast_result = complex_m2m_helper.relationship_exists_fast(user.id, tag.id)
        assert original_result == fast_result == False

        # Add relationship using original method
        complex_m2m_helper.add_relationship(user.id, tag.id)

        # Both methods should detect the relationship
        original_result = complex_m2m_helper.relationship_exists(user.id, tag.id)
        fast_result = complex_m2m_helper.relationship_exists_fast(user.id, tag.id)
        assert original_result == fast_result == True

    def test_count_sources_for_target_equivalence_simple(self, simple_m2m_helper, user_crud, simple_role_crud):
        """Test that count_sources_for_target and count_sources_for_target_fast return identical results"""
        # Create test data
        role = simple_role_crud.create({"name": "Manager"})
        users = []
        for i in range(3):
            user = user_crud.create({"name": f"User {i}", "email": f"user{i}@example.com"})
            users.append(user)

        # Test with no relationships
        original_count = simple_m2m_helper.count_sources_for_target(role.id)
        fast_count = simple_m2m_helper.count_sources_for_target_fast(role.id)
        assert original_count == fast_count == 0

        # Add relationships one by one and test counts
        for i, user in enumerate(users):
            simple_m2m_helper.add_relationship(user.id, role.id)

            original_count = simple_m2m_helper.count_sources_for_target(role.id)
            fast_count = simple_m2m_helper.count_sources_for_target_fast(role.id)
            assert original_count == fast_count == i + 1

        # Test with non-existent target
        original_count = simple_m2m_helper.count_sources_for_target(99999)
        fast_count = simple_m2m_helper.count_sources_for_target_fast(99999)
        assert original_count == fast_count == 0



    def test_count_sources_for_target_equivalence_complex(self, complex_m2m_helper, user_crud, complex_tag_crud):
        """Test that complex M2M relationships fall back to original method for counting"""
        # Create test data
        tag = complex_tag_crud.create({"name": "Django"})
        users = []
        for i in range(2):
            user = user_crud.create({"name": f"Complex User {i}", "email": f"complex{i}@example.com"})
            users.append(user)
            complex_m2m_helper.add_relationship(user.id, tag.id)

        # Both methods should return the same count (fast should fall back to original)
        original_count = complex_m2m_helper.count_sources_for_target(tag.id)
        fast_count = complex_m2m_helper.count_sources_for_target_fast(tag.id)
        assert original_count == fast_count == 2

    def test_performance_difference(self, simple_m2m_helper, user_crud, simple_role_crud):
        """Test that demonstrates the performance difference (for manual verification)"""
        import time

        # Create test data with more relationships
        role = simple_role_crud.create({"name": "Performance Test Role"})
        users = []
        for i in range(10):  # Create 10 users
            user = user_crud.create({"name": f"Perf User {i}", "email": f"perf{i}@example.com"})
            users.append(user)
            simple_m2m_helper.add_relationship(user.id, role.id)

        # Time the original method
        start_time = time.time()
        for _ in range(10):  # Run multiple times to get measurable difference
            simple_m2m_helper.relationship_exists(users[0].id, role.id)
            simple_m2m_helper.count_sources_for_target(role.id)
        original_time = time.time() - start_time

        # Time the fast method
        start_time = time.time()
        for _ in range(10):
            simple_m2m_helper.relationship_exists_fast(users[0].id, role.id)
            simple_m2m_helper.count_sources_for_target_fast(role.id)
        fast_time = time.time() - start_time

        # Fast method should be faster (though with small dataset, difference might be minimal)
        print(f"Original method time: {original_time:.4f}s")
        print(f"Fast method time: {fast_time:.4f}s")
        print(f"Speedup: {original_time/fast_time:.2f}x")

        # The important thing is that results are identical
        assert simple_m2m_helper.relationship_exists(users[0].id, role.id) == \
               simple_m2m_helper.relationship_exists_fast(users[0].id, role.id)
        assert simple_m2m_helper.count_sources_for_target(role.id) == \
               simple_m2m_helper.count_sources_for_target_fast(role.id)
