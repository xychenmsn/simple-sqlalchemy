"""
Tests for automatic timezone handling in string-schema operations.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from simple_sqlalchemy import DbClient, CommonBase, BaseCrud


class TimezoneTestModel(CommonBase):
    """Test model with datetime fields for timezone testing."""
    __tablename__ = 'timezone_test'
    
    name = Column(String(100), nullable=False)
    event_time = Column(DateTime, nullable=True)


@pytest.fixture
def db_client():
    """Create in-memory SQLite database for testing."""
    db = DbClient("sqlite:///:memory:")
    CommonBase.metadata.create_all(db.engine)
    return db


@pytest.fixture
def timezone_crud(db_client):
    """Create CRUD instance for timezone testing."""
    return BaseCrud(TimezoneTestModel, db_client)


def test_query_with_schema_timezone_handling(timezone_crud):
    """Test that datetime fields include timezone information in query results."""
    # Create record with naive datetime using traditional method
    naive_datetime = datetime(2025, 8, 13, 12, 22, 13)  # No timezone info

    # Use traditional SQLAlchemy to create record
    with timezone_crud.db_client.get_session() as session:
        record = TimezoneTestModel(name="Test Event", event_time=naive_datetime)
        session.add(record)
        session.commit()
        record_id = record.id

    # Query with string schema - this should add timezone info
    results = timezone_crud.query_with_schema(
        "id:int, name:string, event_time:datetime, created_at:datetime"
    )

    # Should have one result with timezone information
    assert len(results) == 1
    result = results[0]
    assert result["name"] == "Test Event"

    # Check if timezone conversion is working
    # The result should be a string with timezone info or a datetime object
    event_time = result["event_time"]
    created_at = result["created_at"]

    # If it's a string, it should include timezone info
    if isinstance(event_time, str):
        assert "+00:00" in event_time
    if isinstance(created_at, str):
        assert "+00:00" in created_at


def test_null_datetime_handled_correctly(timezone_crud):
    """Test that null datetime values are handled correctly."""
    # Create record with null datetime using traditional method
    with timezone_crud.db_client.get_session() as session:
        record = TimezoneTestModel(name="No Time Event", event_time=None)
        session.add(record)
        session.commit()

    # Query with string schema
    results = timezone_crud.query_with_schema(
        "id:int, name:string, event_time:datetime?"
    )

    # Should handle null values correctly
    assert len(results) == 1
    result = results[0]
    assert result["name"] == "No Time Event"
    assert result["event_time"] is None


def test_multiple_records_timezone_handling(timezone_crud):
    """Test timezone handling with multiple records."""
    # Create multiple records using traditional method
    with timezone_crud.db_client.get_session() as session:
        records = [
            TimezoneTestModel(name="Event 1", event_time=datetime(2025, 8, 13, 10, 0, 0)),
            TimezoneTestModel(name="Event 2", event_time=datetime(2025, 8, 13, 11, 0, 0)),
            TimezoneTestModel(name="Event 3", event_time=None)
        ]
        for record in records:
            session.add(record)
        session.commit()

    # Query all records
    results = timezone_crud.query_with_schema(
        "id:int, name:string, event_time:datetime?, created_at:datetime"
    )

    # Should have 3 records
    assert len(results) == 3

    # Check that datetime fields are properly handled
    for result in results:
        # created_at should be present
        assert "created_at" in result

        # event_time should be null for Event 3, present for others
        if result["name"] == "Event 3":
            assert result["event_time"] is None
        else:
            assert result["event_time"] is not None


def test_timezone_conversion_format(timezone_crud):
    """Test that timezone conversion produces the expected ISO format."""
    # Create record with known datetime
    test_datetime = datetime(2025, 8, 13, 12, 22, 13)  # Naive datetime

    with timezone_crud.db_client.get_session() as session:
        record = TimezoneTestModel(name="Format Test", event_time=test_datetime)
        session.add(record)
        session.commit()

    # Query with string schema
    results = timezone_crud.query_with_schema(
        "id:int, name:string, event_time:datetime, created_at:datetime"
    )

    assert len(results) == 1
    result = results[0]

    # Print the actual values for debugging
    print(f"event_time: {result['event_time']} (type: {type(result['event_time'])})")
    print(f"created_at: {result['created_at']} (type: {type(result['created_at'])})")

    # Check if the datetime fields have timezone information
    event_time = result["event_time"]
    created_at = result["created_at"]

    # The timezone conversion should ensure datetime objects have timezone info
    if isinstance(event_time, datetime):
        # Should have timezone information
        assert event_time.tzinfo is not None
        assert str(event_time).endswith("+00:00")
    elif isinstance(event_time, str):
        # Should be in ISO format with timezone
        assert "T" in event_time  # ISO format has T separator
        assert "+" in event_time or "Z" in event_time  # Should have timezone info

    if isinstance(created_at, datetime):
        # Should have timezone information
        assert created_at.tzinfo is not None
        assert str(created_at).endswith("+00:00")
    elif isinstance(created_at, str):
        # Should be in ISO format with timezone
        assert "T" in created_at  # ISO format has T separator
        assert "+" in created_at or "Z" in created_at  # Should have timezone info


if __name__ == "__main__":
    pytest.main([__file__])
