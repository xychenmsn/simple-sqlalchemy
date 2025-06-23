"""
Base models and mixins for simple-sqlalchemy
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, DateTime, MetaData
from sqlalchemy.orm import declarative_base, declared_attr

# Create shared metadata object
metadata_obj = MetaData()

# Create declarative base with shared metadata
Base = declarative_base(metadata=metadata_obj)


class CommonBase(Base):
    """
    Base class for all database models with common fields.
    
    Provides:
    - id: Primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Adds deleted_at field and provides soft delete methods.
    """
    
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self):
        """Mark this record as deleted"""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """Restore this soft-deleted record"""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if this record is soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def is_active(self) -> bool:
        """Check if this record is active (not soft-deleted)"""
        return self.deleted_at is None


class TimestampMixin:
    """
    Mixin for timestamp fields only (without id).
    Useful when you want timestamps but not the full CommonBase.
    """
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True), 
            default=lambda: datetime.now(timezone.utc),
            nullable=False
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True), 
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False
        )


# Backward compatibility aliases
metadata = metadata_obj
