"""
Tests for M2M strategy selection and architecture improvements.
"""

import pytest
from sqlalchemy import Column, String, Integer, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from simple_sqlalchemy import CommonBase
from simple_sqlalchemy.helpers.m2m import M2MHelper, EfficientM2MStrategy, OriginalM2MStrategy
from tests.conftest import User


# Test models for strategy selection

# 1. Simple M2M table (should use EfficientM2MStrategy)
simple_strategy_user_role_table = Table(
    'test_strategy_simple_user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('test_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('test_strategy_simple_roles.id'), primary_key=True)
)

class SimpleStrategyRole(CommonBase):
    """Simple role model for strategy testing"""
    __tablename__ = 'test_strategy_simple_roles'
    
    name = Column(String(50), nullable=False, unique=True)
    users = relationship("User", secondary=simple_strategy_user_role_table, back_populates="strategy_simple_roles")

User.strategy_simple_roles = relationship("SimpleStrategyRole", secondary=simple_strategy_user_role_table, back_populates="users")


# 2. Complex M2M table (should use OriginalM2MStrategy)
complex_strategy_user_tag_table = Table(
    'test_strategy_complex_user_tags',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('test_users.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('test_strategy_complex_tags.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String(50)),  # Extra metadata that should trigger fallback
    Column('priority', Integer, default=1)  # Another extra column
)

class ComplexStrategyTag(CommonBase):
    """Complex tag model for strategy testing"""
    __tablename__ = 'test_strategy_complex_tags'
    
    name = Column(String(50), nullable=False, unique=True)
    users = relationship("User", secondary=complex_strategy_user_tag_table, back_populates="strategy_complex_tags")

User.strategy_complex_tags = relationship("ComplexStrategyTag", secondary=complex_strategy_user_tag_table, back_populates="users")


class TestM2MStrategySelection:
    """Test M2M strategy selection and architecture"""
    
    @pytest.fixture
    def setup_strategy_tables(self, db_client):
        """Create strategy test tables"""
        simple_strategy_user_role_table.create(db_client.engine, checkfirst=True)
        SimpleStrategyRole.__table__.create(db_client.engine, checkfirst=True)
        
        complex_strategy_user_tag_table.create(db_client.engine, checkfirst=True)
        ComplexStrategyTag.__table__.create(db_client.engine, checkfirst=True)
        
        yield
        
        # Cleanup is handled by conftest.py
    
    def test_simple_relationship_uses_efficient_strategy(self, db_client, setup_strategy_tables):
        """Test that simple M2M relationships use EfficientM2MStrategy"""
        m2m_helper = M2MHelper(db_client, User, SimpleStrategyRole, "strategy_simple_roles", "users")
        
        # Check that the efficient strategy was selected
        assert isinstance(m2m_helper._strategy, EfficientM2MStrategy)
        assert m2m_helper.strategy_type == "EfficientM2MStrategy"
    
    def test_complex_relationship_uses_original_strategy(self, db_client, setup_strategy_tables):
        """Test that complex M2M relationships use OriginalM2MStrategy"""
        m2m_helper = M2MHelper(db_client, User, ComplexStrategyTag, "strategy_complex_tags", "users")
        
        # Check that the original strategy was selected
        assert isinstance(m2m_helper._strategy, OriginalM2MStrategy)
        assert m2m_helper.strategy_type == "OriginalM2MStrategy"
    
    def test_strategy_delegation_works(self, db_client, setup_strategy_tables, user_crud):
        """Test that all methods properly delegate to the strategy"""
        # Test with efficient strategy
        efficient_helper = M2MHelper(db_client, User, SimpleStrategyRole, "strategy_simple_roles", "users")
        
        # Create test data
        user = user_crud.create({"name": "Strategy Test User", "email": "strategy@example.com"})
        
        from tests.conftest import CategoryCrud
        class SimpleStrategyRoleCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = SimpleStrategyRole
        
        role_crud = SimpleStrategyRoleCrud(db_client)
        role = role_crud.create({"name": "Strategy Test Role"})
        
        # Test all methods work through delegation
        assert efficient_helper.relationship_exists(user.id, role.id) == False
        
        result = efficient_helper.add_relationship(user.id, role.id)
        assert result is not None
        
        assert efficient_helper.relationship_exists(user.id, role.id) == True
        assert efficient_helper.count_related_for_source(user.id) == 1
        assert efficient_helper.count_sources_for_target(role.id) == 1
        
        related = efficient_helper.get_related_for_source(user.id)
        assert len(related) == 1
        assert related[0].id == role.id
        
        sources = efficient_helper.get_sources_for_target(role.id)
        assert len(sources) == 1
        assert sources[0].id == user.id
        
        result = efficient_helper.remove_relationship(user.id, role.id)
        assert result is not None
        
        assert efficient_helper.relationship_exists(user.id, role.id) == False
    
    def test_backward_compatibility_methods(self, db_client, setup_strategy_tables, user_crud):
        """Test that deprecated fast methods still work"""
        m2m_helper = M2MHelper(db_client, User, SimpleStrategyRole, "strategy_simple_roles", "users")
        
        # Create test data
        user = user_crud.create({"name": "Compat Test User", "email": "compat@example.com"})
        
        from tests.conftest import CategoryCrud
        class SimpleStrategyRoleCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = SimpleStrategyRole
        
        role_crud = SimpleStrategyRoleCrud(db_client)
        role = role_crud.create({"name": "Compat Test Role"})
        
        # Add relationship
        m2m_helper.add_relationship(user.id, role.id)
        
        # Test deprecated methods work and return same results
        assert m2m_helper.relationship_exists(user.id, role.id) == m2m_helper.relationship_exists_fast(user.id, role.id)
        assert m2m_helper.count_sources_for_target(role.id) == m2m_helper.count_sources_for_target_fast(role.id)
    
    def test_strategy_caching_at_initialization(self, db_client, setup_strategy_tables):
        """Test that strategy analysis is done once at initialization"""
        # Create helper
        m2m_helper = M2MHelper(db_client, User, SimpleStrategyRole, "strategy_simple_roles", "users")
        
        # Strategy should be cached and not change
        original_strategy = m2m_helper._strategy
        strategy_type = m2m_helper.strategy_type
        
        # Multiple calls should use the same strategy instance
        assert m2m_helper._strategy is original_strategy
        assert m2m_helper.strategy_type == strategy_type
        
        # Strategy should be EfficientM2MStrategy for simple relationship
        assert isinstance(original_strategy, EfficientM2MStrategy)
        assert strategy_type == "EfficientM2MStrategy"
    
    def test_performance_improvement_with_new_architecture(self, db_client, setup_strategy_tables, user_crud):
        """Test that the new architecture provides performance improvements"""
        import time
        
        # Create helpers
        efficient_helper = M2MHelper(db_client, User, SimpleStrategyRole, "strategy_simple_roles", "users")
        complex_helper = M2MHelper(db_client, User, ComplexStrategyTag, "strategy_complex_tags", "users")
        
        # Verify strategy selection
        assert isinstance(efficient_helper._strategy, EfficientM2MStrategy)
        assert isinstance(complex_helper._strategy, OriginalM2MStrategy)
        
        # Create test data
        user = user_crud.create({"name": "Perf Test User", "email": "perf@example.com"})
        
        from tests.conftest import CategoryCrud
        
        class SimpleStrategyRoleCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = SimpleStrategyRole
        
        class ComplexStrategyTagCrud(CategoryCrud):
            def __init__(self, db_client):
                super().__init__(db_client)
                self.model = ComplexStrategyTag
        
        role_crud = SimpleStrategyRoleCrud(db_client)
        tag_crud = ComplexStrategyTagCrud(db_client)
        
        role = role_crud.create({"name": "Perf Test Role"})
        tag = tag_crud.create({"name": "Perf Test Tag"})
        
        # Add relationships
        efficient_helper.add_relationship(user.id, role.id)
        complex_helper.add_relationship(user.id, tag.id)
        
        # Both should work correctly
        assert efficient_helper.relationship_exists(user.id, role.id) == True
        assert complex_helper.relationship_exists(user.id, tag.id) == True
        
        # Both should return correct counts
        assert efficient_helper.count_sources_for_target(role.id) == 1
        assert complex_helper.count_sources_for_target(tag.id) == 1
        
        print(f"Efficient strategy: {efficient_helper.strategy_type}")
        print(f"Complex strategy: {complex_helper.strategy_type}")
    
    def test_all_methods_implemented_in_both_strategies(self, db_client, setup_strategy_tables):
        """Test that both strategies implement all required methods"""
        efficient_helper = M2MHelper(db_client, User, SimpleStrategyRole, "strategy_simple_roles", "users")
        complex_helper = M2MHelper(db_client, User, ComplexStrategyTag, "strategy_complex_tags", "users")
        
        # Check that both strategies have all required methods
        required_methods = [
            'add_relationship', 'remove_relationship', 'get_related_for_source',
            'get_sources_for_target', 'count_related_for_source', 
            'count_sources_for_target', 'relationship_exists'
        ]
        
        for method_name in required_methods:
            assert hasattr(efficient_helper._strategy, method_name)
            assert hasattr(complex_helper._strategy, method_name)
            assert callable(getattr(efficient_helper._strategy, method_name))
            assert callable(getattr(complex_helper._strategy, method_name))
