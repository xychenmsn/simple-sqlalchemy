"""
Basic usage example for simple-sqlalchemy
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud, SoftDeleteMixin


# Define your models
class User(CommonBase):
    __tablename__ = 'users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    posts = relationship("Post", back_populates="author")


class Post(CommonBase, SoftDeleteMixin):
    __tablename__ = 'posts'
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    author = relationship("User", back_populates="posts")


# Create CRUD operations
class UserOps(BaseCrud[User]):
    def __init__(self, db_client):
        super().__init__(User, db_client)
    
    def get_by_email(self, email: str):
        return self.get_by_field("email", email)
    
    def search_by_name(self, name: str):
        return self.search(name, ["name", "email"])


class PostOps(BaseCrud[Post]):
    def __init__(self, db_client):
        super().__init__(Post, db_client)
    
    def get_by_author(self, author_id: int):
        return self.get_multi(filters={"author_id": author_id})
    
    def get_published_posts(self):
        # Get posts that are not soft-deleted
        return self.get_multi(include_deleted=False)


def main():
    # Initialize database client
    db = DbClient("sqlite:///example.db")
    
    # Create tables (in real app, use Alembic)
    CommonBase.metadata.create_all(db.engine)
    
    # Initialize CRUD operations
    user_ops = UserOps(db)
    post_ops = PostOps(db)
    
    # Create a user
    user = user_ops.create({
        "name": "John Doe",
        "email": "john@example.com"
    })
    print(f"Created user: {user.name} ({user.id})")
    
    # Create a post
    post = post_ops.create({
        "title": "My First Post",
        "content": "This is the content of my first post.",
        "author_id": user.id
    })
    print(f"Created post: {post.title} ({post.id})")
    
    # Search users
    users = user_ops.search_by_name("John")
    print(f"Found {len(users)} users matching 'John'")
    
    # Get posts by author
    author_posts = post_ops.get_by_author(user.id)
    print(f"User has {len(author_posts)} posts")
    
    # Soft delete a post
    post_ops.soft_delete(post.id)
    print("Post soft deleted")
    
    # Get published posts (excludes soft-deleted)
    published_posts = post_ops.get_published_posts()
    print(f"Published posts: {len(published_posts)}")
    
    # Get all posts including deleted
    all_posts = post_ops.get_multi(include_deleted=True)
    print(f"All posts (including deleted): {len(all_posts)}")
    
    # Restore the post
    restored_post = post_ops.undelete(post.id)
    print(f"Restored post: {restored_post.title}")
    
    # Pagination example
    paginated_users = user_ops.get_multi(skip=0, limit=10)
    print(f"First 10 users: {len(paginated_users)}")
    
    # Count users
    user_count = user_ops.count()
    print(f"Total users: {user_count}")
    
    # Close database connection
    db.close()


if __name__ == "__main__":
    main()
