"""
Advanced usage example for simple-sqlalchemy

This example demonstrates:
- Complex model relationships
- Advanced CRUD operations
- Search and pagination
- Bulk operations
- Many-to-many relationships
- PostgreSQL vector support
- Custom query builders
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship

from simple_sqlalchemy import (
    DbClient, CommonBase, BaseCrud, SoftDeleteMixin,
    SearchHelper, PaginationHelper
)

# PostgreSQL-specific imports (optional)
try:
    from simple_sqlalchemy.postgres import EmbeddingVector, PostgreSQLUtils
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# Define association tables for many-to-many relationships
user_roles_table = Table(
    'user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow)
)

article_tags_table = Table(
    'article_tags',
    CommonBase.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


# Define models
class User(CommonBase):
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    articles = relationship("Article", back_populates="author")
    roles = relationship("Role", secondary=user_roles_table, back_populates="users")


class Role(CommonBase):
    __tablename__ = 'roles'
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles_table, back_populates="roles")


class Category(CommonBase):
    __tablename__ = 'categories'
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    articles = relationship("Article", back_populates="category")


class Tag(CommonBase):
    __tablename__ = 'tags'
    
    name = Column(String(50), unique=True, nullable=False)
    
    # Relationships
    articles = relationship("Article", secondary=article_tags_table, back_populates="tags")


class Article(CommonBase, SoftDeleteMixin):
    __tablename__ = 'articles'
    
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    
    # PostgreSQL vector field (if available)
    if POSTGRES_AVAILABLE:
        embedding = Column(EmbeddingVector(384), nullable=True)
    
    # Relationships
    author = relationship("User", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags_table, back_populates="articles")


# CRUD Operations
class UserOps(BaseCrud[User]):
    def __init__(self, db_client):
        super().__init__(User, db_client)
    
    def get_by_username(self, username: str):
        """Get user by username"""
        return self.get_by_field("username", username)
    
    def get_by_email(self, email: str):
        """Get user by email"""
        return self.get_by_field("email", email)
    
    def search_users(self, query: str, include_inactive: bool = False):
        """Search users by username, email, or full name"""
        filters = {} if include_inactive else {"is_active": True}
        return self.search(
            search_query=query,
            search_fields=["username", "email", "full_name"],
            filters=filters
        )
    
    def get_active_users(self, limit: int = 100):
        """Get active users"""
        return self.get_multi(
            filters={"is_active": True},
            sort_by="last_login",
            sort_desc=True,
            limit=limit
        )
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        return self.update(user_id, {"last_login": datetime.utcnow()})


class ArticleOps(BaseCrud[Article]):
    def __init__(self, db_client):
        super().__init__(Article, db_client)
    
    def get_published_articles(self, page: int = 1, per_page: int = 20):
        """Get published articles with pagination"""
        return self.get_multi(
            skip=(page - 1) * per_page,
            limit=per_page,
            filters={"is_published": True},
            sort_by="created_at",
            sort_desc=True,
            include_deleted=False
        )
    
    def search_articles(self, query: str, category_id: int = None):
        """Search articles by title and content"""
        filters = {"is_published": True}
        if category_id:
            filters["category_id"] = category_id
        
        return self.search(
            search_query=query,
            search_fields=["title", "content", "summary"],
            filters=filters,
            include_deleted=False
        )
    
    def get_popular_articles(self, days: int = 7, limit: int = 10):
        """Get popular articles from the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        def popular_query(session):
            return session.query(Article).filter(
                Article.created_at >= cutoff_date,
                Article.is_published == True,
                Article.deleted_at.is_(None)
            ).order_by(Article.view_count.desc())
        
        search_helper = self.db_client.create_search_helper(Article)
        return search_helper.execute_custom_query(popular_query)[:limit]
    
    def increment_view_count(self, article_id: int):
        """Increment article view count"""
        with self.db_client.session_scope() as session:
            article = session.query(Article).filter(Article.id == article_id).first()
            if article:
                article.view_count += 1
                session.flush()
                return self.db_client.detach_object(article, session)
        return None
    
    def bulk_publish_articles(self, article_ids: list):
        """Bulk publish articles"""
        return self.bulk_update_fields(
            update_data={"is_published": True},
            filters={"id": article_ids}  # Note: This is simplified, real implementation would use IN clause
        )


class ApplicationDbClient(DbClient):
    """Application-specific database client with integrated operations"""
    
    def __init__(self, db_url: str, engine_options=None):
        super().__init__(db_url, engine_options)
        
        # Initialize CRUD operations
        self.users = UserOps(self)
        self.articles = ArticleOps(self)
        self.roles = BaseCrud(Role, self)
        self.categories = BaseCrud(Category, self)
        self.tags = BaseCrud(Tag, self)
        
        # Initialize helpers
        self.user_roles = self.create_m2m_helper(User, Role, "roles", "users")
        self.article_tags = self.create_m2m_helper(Article, Tag, "tags", "articles")
        
        # PostgreSQL utilities (if available)
        if POSTGRES_AVAILABLE:
            self.pg_utils = PostgreSQLUtils(self)
    
    def setup_database(self):
        """Initialize database schema"""
        CommonBase.metadata.create_all(self.engine)
        
        # Create default roles
        admin_role = self.roles.create({"name": "admin", "description": "Administrator"})
        user_role = self.roles.create({"name": "user", "description": "Regular user"})
        
        # Create default categories
        tech_category = self.categories.create({"name": "Technology", "description": "Tech articles"})
        news_category = self.categories.create({"name": "News", "description": "News articles"})
        
        return {
            "roles": [admin_role, user_role],
            "categories": [tech_category, news_category]
        }
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        return {
            "total_users": self.users.count(),
            "active_users": self.users.count(filters={"is_active": True}),
            "total_articles": self.articles.count(include_deleted=False),
            "published_articles": self.articles.count(filters={"is_published": True}, include_deleted=False),
            "recent_articles": len(self.articles.get_by_date_range("created_at", days_back=7))
        }
    
    def search_content(self, query: str, page: int = 1, per_page: int = 20):
        """Search across articles with pagination"""
        def search_query_builder(session):
            return session.query(Article).filter(
                Article.title.ilike(f"%{query}%") | 
                Article.content.ilike(f"%{query}%"),
                Article.is_published == True,
                Article.deleted_at.is_(None)
            )
        
        search_helper = self.create_search_helper(Article)
        return search_helper.paginated_search_with_count(
            base_query_builder=search_query_builder,
            page=page,
            per_page=per_page,
            sort_by="created_at",
            sort_desc=True
        )


def main():
    """Demonstrate advanced usage"""
    # Initialize database
    app_db = ApplicationDbClient("sqlite:///advanced_example.db")
    
    # Setup database schema and default data
    print("Setting up database...")
    defaults = app_db.setup_database()
    
    # Create users
    print("Creating users...")
    admin_user = app_db.users.create({
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Administrator",
        "is_active": True
    })
    
    regular_user = app_db.users.create({
        "username": "john_doe",
        "email": "john@example.com", 
        "full_name": "John Doe",
        "is_active": True
    })
    
    # Assign roles
    print("Assigning roles...")
    admin_role = defaults["roles"][0]
    user_role = defaults["roles"][1]
    
    app_db.user_roles.add_relationship(admin_user.id, admin_role.id)
    app_db.user_roles.add_relationship(regular_user.id, user_role.id)
    
    # Create articles
    print("Creating articles...")
    tech_category = defaults["categories"][0]
    
    article1 = app_db.articles.create({
        "title": "Introduction to SQLAlchemy",
        "content": "SQLAlchemy is a powerful Python ORM...",
        "summary": "Learn the basics of SQLAlchemy",
        "author_id": admin_user.id,
        "category_id": tech_category.id,
        "is_published": True
    })
    
    article2 = app_db.articles.create({
        "title": "Advanced Database Patterns",
        "content": "This article covers advanced patterns...",
        "summary": "Advanced database design patterns",
        "author_id": regular_user.id,
        "category_id": tech_category.id,
        "is_published": True
    })
    
    # Create and assign tags
    print("Creating tags...")
    python_tag = app_db.tags.create({"name": "python"})
    database_tag = app_db.tags.create({"name": "database"})
    
    app_db.article_tags.add_relationship(article1.id, python_tag.id)
    app_db.article_tags.add_relationship(article1.id, database_tag.id)
    app_db.article_tags.add_relationship(article2.id, database_tag.id)
    
    # Demonstrate search functionality
    print("\nSearching articles...")
    search_results = app_db.search_content("SQLAlchemy", page=1, per_page=10)
    print(f"Found {search_results['total']} articles matching 'SQLAlchemy'")
    
    # Demonstrate user search
    print("\nSearching users...")
    user_results = app_db.users.search_users("john")
    print(f"Found {len(user_results)} users matching 'john'")
    
    # Get dashboard statistics
    print("\nDashboard statistics:")
    stats = app_db.get_dashboard_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Demonstrate pagination
    print("\nPaginated articles:")
    paginated_articles = app_db.articles.get_published_articles(page=1, per_page=5)
    print(f"Retrieved {len(paginated_articles)} articles")
    
    # Demonstrate bulk operations
    print("\nIncrementing view counts...")
    app_db.articles.increment_view_count(article1.id)
    app_db.articles.increment_view_count(article2.id)
    
    # Get popular articles
    popular = app_db.articles.get_popular_articles(days=30, limit=5)
    print(f"Found {len(popular)} popular articles")
    
    # Demonstrate relationship queries
    print("\nUser roles:")
    admin_roles = app_db.user_roles.get_related_for_source(admin_user.id)
    print(f"Admin has {len(admin_roles)} roles: {[role.name for role in admin_roles]}")
    
    # Clean up
    app_db.close()
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main()
