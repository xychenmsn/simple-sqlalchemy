"""
Test configuration and fixtures for simple-sqlalchemy tests
"""

import pytest
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud, SoftDeleteMixin


# Test Models
class User(CommonBase):
    """Test user model"""
    __tablename__ = 'test_users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    posts = relationship("Post", back_populates="author")


class Post(CommonBase, SoftDeleteMixin):
    """Test post model with soft delete"""
    __tablename__ = 'test_posts'
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('test_users.id'), nullable=False)
    published = Column(Boolean, default=False)
    
    author = relationship("User", back_populates="posts")


class Category(CommonBase):
    """Test category model"""
    __tablename__ = 'test_categories'
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)


# CRUD Classes
class UserCrud(BaseCrud[User]):
    """CRUD operations for User model"""
    
    def __init__(self, db_client):
        super().__init__(User, db_client)
    
    def get_by_email(self, email: str):
        """Get user by email"""
        return self.get_by_field("email", email)
    
    def get_active_users(self):
        """Get all active users"""
        return self.get_multi(filters={"is_active": True})


class PostCrud(BaseCrud[Post]):
    """CRUD operations for Post model"""
    
    def __init__(self, db_client):
        super().__init__(Post, db_client)
    
    def get_by_author(self, author_id: int):
        """Get posts by author"""
        return self.get_multi(filters={"author_id": author_id})
    
    def get_published_posts(self):
        """Get all published posts"""
        return self.get_multi(filters={"published": True})


class CategoryCrud(BaseCrud[Category]):
    """CRUD operations for Category model"""
    
    def __init__(self, db_client):
        super().__init__(Category, db_client)


# Fixtures
@pytest.fixture
def db_client():
    """Create test database client with SQLite in-memory database"""
    client = DbClient("sqlite:///:memory:")
    
    # Create all tables
    CommonBase.metadata.create_all(client.engine)
    
    yield client
    
    # Cleanup
    client.close()


@pytest.fixture
def user_crud(db_client):
    """User CRUD operations fixture"""
    return UserCrud(db_client)


@pytest.fixture
def post_crud(db_client):
    """Post CRUD operations fixture"""
    return PostCrud(db_client)


@pytest.fixture
def category_crud(db_client):
    """Category CRUD operations fixture"""
    return CategoryCrud(db_client)


@pytest.fixture
def sample_user(user_crud):
    """Create a sample user for testing"""
    return user_crud.create({
        "name": "John Doe",
        "email": "john@example.com",
        "is_active": True
    })


@pytest.fixture
def sample_users(user_crud):
    """Create multiple sample users for testing"""
    users = []
    for i in range(5):
        user = user_crud.create({
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "is_active": i % 2 == 0  # Alternate active/inactive
        })
        users.append(user)
    return users


@pytest.fixture
def sample_post(post_crud, sample_user):
    """Create a sample post for testing"""
    return post_crud.create({
        "title": "Test Post",
        "content": "This is a test post content",
        "author_id": sample_user.id,
        "published": True
    })


@pytest.fixture
def sample_posts(post_crud, sample_user):
    """Create multiple sample posts for testing"""
    posts = []
    for i in range(3):
        post = post_crud.create({
            "title": f"Test Post {i}",
            "content": f"This is test post content {i}",
            "author_id": sample_user.id,
            "published": i % 2 == 0  # Alternate published/unpublished
        })
        posts.append(post)
    return posts


@pytest.fixture
def sample_category(category_crud):
    """Create a sample category for testing"""
    return category_crud.create({
        "name": "Technology",
        "description": "Technology related content"
    })
