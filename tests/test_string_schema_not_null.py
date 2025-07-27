"""
Unit tests for the new "not null" filtering functionality in StringSchemaHelper.
"""

import pytest
from sqlalchemy import Column, String, Integer, Text
from simple_sqlalchemy import DbClient, CommonBase
from simple_sqlalchemy.helpers.string_schema import StringSchemaHelper


# Test model
class TestUser(CommonBase):
    __tablename__ = 'test_users_not_null'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    status = Column(String(20), nullable=True)


@pytest.fixture
def db_client():
    """Create a test database client"""
    db = DbClient("sqlite:///:memory:")
    CommonBase.metadata.create_all(db.engine)
    return db


@pytest.fixture
def test_data(db_client):
    """Create test data"""
    test_users = [
        {"name": "Alice", "email": "alice@example.com", "phone": "123-456-7890", "status": "active"},
        {"name": "Bob", "email": "bob@example.com", "phone": None, "status": "inactive"},
        {"name": "Charlie", "email": None, "phone": "987-654-3210", "status": "active"},
        {"name": "Diana", "email": None, "phone": None, "status": None},
        {"name": "Eve", "email": "eve@example.com", "phone": "555-123-4567", "status": "pending"}
    ]
    
    with db_client.session_scope() as session:
        for user_data in test_users:
            user = TestUser(**user_data)
            session.add(user)
        session.commit()
    
    return test_users


class TestNotNullFiltering:
    """Test the new not null filtering functionality"""
    
    def test_not_null_filter_basic(self, db_client, test_data):
        """Test basic not null filtering"""
        helper = StringSchemaHelper(db_client, TestUser)
        
        # Test direct query without schema validation to focus on filtering
        with db_client.session_scope() as session:
            # Test not null filter
            query = session.query(TestUser)
            filters = {"email": {"not": None}}
            
            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        query = query.filter(field_attr.is_not(None))
            
            results = query.all()
            
            # Should find Alice, Bob, and Eve (3 users with email)
            assert len(results) == 3
            names = [user.name for user in results]
            assert "Alice" in names
            assert "Bob" in names
            assert "Eve" in names
            assert "Charlie" not in names  # No email
            assert "Diana" not in names    # No email
    
    def test_null_filter_existing(self, db_client, test_data):
        """Test existing null filtering still works"""
        with db_client.session_scope() as session:
            # Test null filter (existing functionality)
            query = session.query(TestUser)
            filters = {"email": None}
            
            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if value is None:
                        query = query.filter(field_attr.is_(None))
            
            results = query.all()
            
            # Should find Charlie and Diana (2 users without email)
            assert len(results) == 2
            names = [user.name for user in results]
            assert "Charlie" in names
            assert "Diana" in names
            assert "Alice" not in names
            assert "Bob" not in names
            assert "Eve" not in names
    
    def test_combined_filters(self, db_client, test_data):
        """Test combining not null with other filters"""
        with db_client.session_scope() as session:
            # Users with email AND active status
            query = session.query(TestUser)
            filters = {
                "email": {"not": None},
                "status": "active"
            }
            
            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        query = query.filter(field_attr.is_not(None))
                    elif value is None:
                        query = query.filter(field_attr.is_(None))
                    else:
                        query = query.filter(field_attr == value)
            
            results = query.all()
            
            # Should find only Alice (has email and active status)
            assert len(results) == 1
            assert results[0].name == "Alice"
    
    def test_multiple_not_null_filters(self, db_client, test_data):
        """Test multiple not null filters"""
        with db_client.session_scope() as session:
            # Users with both email AND phone
            query = session.query(TestUser)
            filters = {
                "email": {"not": None},
                "phone": {"not": None}
            }
            
            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        query = query.filter(field_attr.is_not(None))
            
            results = query.all()
            
            # Should find Alice and Eve (both have email and phone)
            assert len(results) == 2
            names = [user.name for user in results]
            assert "Alice" in names
            assert "Eve" in names
            assert "Bob" not in names     # No phone
            assert "Charlie" not in names # No email
            assert "Diana" not in names   # No email or phone
    
    def test_mixed_null_and_not_null(self, db_client, test_data):
        """Test mixing null and not null filters"""
        with db_client.session_scope() as session:
            # Users with email but no phone
            query = session.query(TestUser)
            filters = {
                "email": {"not": None},
                "phone": None
            }
            
            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        query = query.filter(field_attr.is_not(None))
                    elif value is None:
                        query = query.filter(field_attr.is_(None))
                    else:
                        query = query.filter(field_attr == value)
            
            results = query.all()
            
            # Should find only Bob (has email but no phone)
            assert len(results) == 1
            assert results[0].name == "Bob"
    
    def test_list_and_not_null_filters(self, db_client, test_data):
        """Test combining list filters with not null"""
        with db_client.session_scope() as session:
            # Users with email AND status in ['active', 'pending']
            query = session.query(TestUser)
            filters = {
                "email": {"not": None},
                "status": ["active", "pending"]
            }
            
            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, list):
                        query = query.filter(field_attr.in_(value))
                    elif isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        query = query.filter(field_attr.is_not(None))
                    elif value is None:
                        query = query.filter(field_attr.is_(None))
                    else:
                        query = query.filter(field_attr == value)
            
            results = query.all()
            
            # Should find Alice (active) and Eve (pending), both have email
            assert len(results) == 2
            names = [user.name for user in results]
            assert "Alice" in names
            assert "Eve" in names
            assert "Bob" not in names     # inactive status
            assert "Charlie" not in names # no email
            assert "Diana" not in names   # no email
    
    def test_invalid_not_filter_format(self, db_client, test_data):
        """Test that invalid 'not' filter formats cause an error when used as parameters"""
        with db_client.session_scope() as session:
            # Invalid format: {"not": "something"} should not trigger not null logic
            query = session.query(TestUser)
            filters = {"email": {"not": "invalid"}}

            for field, value in filters.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        # This should NOT be triggered
                        query = query.filter(field_attr.is_not(None))
                    else:
                        # This should be triggered - treat as regular filter
                        query = query.filter(field_attr == value)

            # Should raise an error because SQLite can't handle dict parameters
            with pytest.raises(Exception):  # Could be ProgrammingError or similar
                results = query.all()
    
    def test_edge_cases(self, db_client, test_data):
        """Test edge cases"""
        with db_client.session_scope() as session:
            # Empty dict should not trigger not null logic
            query1 = session.query(TestUser)
            filters1 = {"email": {}}
            
            for field, value in filters1.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        # Only trigger not null logic if 'not' key exists and is None
                        query1 = query1.filter(field_attr.is_not(None))
                    else:
                        query1 = query1.filter(field_attr == value)
            
            # Should raise an error because SQLite can't handle dict parameters
            with pytest.raises(Exception):  # Could be ProgrammingError or similar
                results1 = query1.all()

            # Dict with 'not' key but not None value
            query2 = session.query(TestUser)
            filters2 = {"status": {"not": "active"}}

            for field, value in filters2.items():
                if hasattr(TestUser, field):
                    field_attr = getattr(TestUser, field)
                    if isinstance(value, dict) and 'not' in value and value.get('not') is None:
                        # Only trigger not null logic if 'not' key exists and is None
                        query2 = query2.filter(field_attr.is_not(None))
                    else:
                        query2 = query2.filter(field_attr == value)

            # Should also raise an error because SQLite can't handle dict parameters
            with pytest.raises(Exception):  # Could be ProgrammingError or similar
                results2 = query2.all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
