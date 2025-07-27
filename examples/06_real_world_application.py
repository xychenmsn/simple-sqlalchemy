#!/usr/bin/env python3
"""
Real-World Application Example

This example demonstrates a complete blog application using simple-sqlalchemy:
- User authentication and authorization
- Content management with categories
- Comment system with moderation
- Search and filtering
- API endpoints simulation
- Performance considerations
- Error handling and validation

This shows how to structure a real application with simple-sqlalchemy!
"""

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, List, Optional


# Setup
print("=== Real-World Blog Application Demo ===")
import os
import time
# Use a unique database name to avoid conflicts
db_name = f"blog_app_{int(time.time())}.db"
db = DbClient(f"sqlite:///{db_name}")
print(f"✅ Connected to database: {db_name}")


# Models
class User(CommonBase):
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    posts = relationship("Post", back_populates="author", lazy="dynamic")
    comments = relationship("Comment", back_populates="author", lazy="dynamic")
    
    def set_password(self, password: str):
        """Hash and set password"""
        salt = secrets.token_hex(16)
        self.password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ':' + salt
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        try:
            hash_part, salt = self.password_hash.split(':')
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hash_part
        except:
            return False
    
    def get_post_count(self) -> int:
        """Get published post count"""
        return self.posts.filter_by(published=True).count()
    
    def can_moderate(self) -> bool:
        """Check if user can moderate content"""
        return self.is_admin or self.is_active


class Category(CommonBase):
    __tablename__ = 'categories'
    
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(7), default='#007bff')  # Hex color
    is_active = Column(Boolean, default=True)
    post_count = Column(Integer, default=0)  # Denormalized for performance
    
    # Relationships
    posts = relationship("Post", back_populates="category", lazy="dynamic")


class Post(CommonBase):
    __tablename__ = 'posts'
    
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    featured_image = Column(String(200))
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)  # Denormalized
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Relationships
    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    comments = relationship("Comment", back_populates="post", lazy="dynamic")
    
    def publish(self):
        """Publish the post"""
        if not self.published:
            self.published = True
            self.published_at = datetime.now()
    
    def get_reading_time(self) -> int:
        """Estimate reading time in minutes"""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))  # 200 words per minute


class Comment(CommonBase):
    __tablename__ = 'comments'
    
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Foreign keys
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'))
    parent_id = Column(Integer, ForeignKey('comments.id'))  # For replies
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", lazy="dynamic")

CommonBase.metadata.create_all(db.engine)

# CRUD instances
user_crud = BaseCrud(User, db)
category_crud = BaseCrud(Category, db)
post_crud = BaseCrud(Post, db)
comment_crud = BaseCrud(Comment, db)


# Application Services
class UserService:
    """User management service"""
    
    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: str = None) -> Dict:
        """Register a new user"""
        # Check if user exists
        existing = user_crud.query_with_schema(
            "id:int",
            filters={"email": email},
            limit=1
        )
        
        if existing:
            raise ValueError("Email already registered")
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name or username,
            "is_active": True
        }
        
        # Hash password (simplified - in real app, use proper hashing)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_data["password_hash"] = password_hash
        
        user_id = user_crud.create(user_data)
        
        return user_crud.query_with_schema(
            "id:int, username:string, email:email, full_name:string, created_at:datetime",
            filters={"id": user_id}
        )[0]
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict]:
        """Authenticate user login"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        users = user_crud.query_with_schema(
            "id:int, username:string, email:email, full_name:string, is_active:bool",
            filters={
                "email": email,
                "password_hash": password_hash,
                "is_active": True
            },
            limit=1
        )
        
        if users:
            # Update last login
            user_crud.update(users[0]['id'], {"last_login": datetime.now()})
            return users[0]
        
        return None
    
    @staticmethod
    def get_user_profile(user_id: int) -> Dict:
        """Get user profile with stats"""
        user = user_crud.query_with_schema(
            "id:int, username:string, email:email, full_name:string, bio:text?, avatar_url:string?, created_at:datetime",
            filters={"id": user_id}
        )[0]
        
        # Add stats
        user_instance = user_crud.get_by_id(user_id)
        user['post_count'] = user_instance.get_post_count()
        user['comment_count'] = user_instance.comments.count()
        
        return user


class BlogService:
    """Blog content management service"""
    
    @staticmethod
    def create_post(author_id: int, title: str, content: str, category_id: int = None, published: bool = False) -> Dict:
        """Create a new blog post"""
        # Generate slug from title
        slug = title.lower().replace(' ', '-').replace('[^a-z0-9-]', '')[:50]
        
        # Create excerpt
        excerpt = content[:200] + "..." if len(content) > 200 else content
        
        post_data = {
            "title": title,
            "slug": slug,
            "content": content,
            "excerpt": excerpt,
            "author_id": author_id,
            "category_id": category_id,
            "published": published
        }
        
        if published:
            post_data["published_at"] = datetime.now()
        
        post_id = post_crud.create(post_data)
        
        # Update category post count if categorized
        if category_id:
            category = category_crud.get_by_id(category_id)
            category_crud.update(category_id, {"post_count": category.post_count + 1})
        
        return post_crud.query_with_schema(
            "id:int, title:string, slug:string, excerpt:text?, published:bool, created_at:datetime",
            filters={"id": post_id}
        )[0]
    
    @staticmethod
    def get_published_posts(page: int = 1, per_page: int = 10, category_id: int = None) -> Dict:
        """Get published posts with pagination"""
        filters = {"published": True}
        if category_id:
            filters["category_id"] = category_id
        
        return post_crud.paginated_query_with_schema(
            "id:int, title:string, slug:string, excerpt:text?, published_at:datetime, view_count:int, like_count:int, comment_count:int, author_id:int, category_id:int?",
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by="published_at",
            sort_desc=True
        )
    
    @staticmethod
    def get_post_detail(slug: str) -> Dict:
        """Get post detail by slug"""
        posts = post_crud.query_with_schema(
            "id:int, title:string, slug:string, content:text, published_at:datetime, view_count:int, like_count:int, comment_count:int, author_id:int, category_id:int?",
            filters={"slug": slug, "published": True},
            limit=1
        )
        
        if not posts:
            raise ValueError("Post not found")
        
        post = posts[0]
        
        # Increment view count
        post_crud.update(post['id'], {"view_count": post['view_count'] + 1})
        post['view_count'] += 1
        
        # Add author info
        author = user_crud.query_with_schema(
            "id:int, username:string, full_name:string, bio:text?, avatar_url:string?",
            filters={"id": post['author_id']}
        )[0]
        post['author'] = author
        
        # Add category info if exists
        if post['category_id']:
            category = category_crud.query_with_schema(
                "id:int, name:string, slug:string, color:string",
                filters={"id": post['category_id']}
            )[0]
            post['category'] = category
        
        return post
    
    @staticmethod
    def search_posts(query: str, page: int = 1, per_page: int = 10) -> Dict:
        """Search posts by title and content"""
        return post_crud.paginated_query_with_schema(
            "id:int, title:string, slug:string, excerpt:text?, published_at:datetime, author_id:int",
            search_query=query,
            search_fields=["title", "content"],
            filters={"published": True},
            page=page,
            per_page=per_page,
            sort_by="published_at",
            sort_desc=True
        )


class CommentService:
    """Comment management service"""
    
    @staticmethod
    def add_comment(post_id: int, author_id: int, content: str, parent_id: int = None) -> Dict:
        """Add a comment to a post"""
        comment_data = {
            "post_id": post_id,
            "author_id": author_id,
            "content": content,
            "parent_id": parent_id,
            "is_approved": True  # Auto-approve for demo
        }
        
        comment_id = comment_crud.create(comment_data)
        
        # Update post comment count
        post = post_crud.get_by_id(post_id)
        post_crud.update(post_id, {"comment_count": post.comment_count + 1})
        
        return comment_crud.query_with_schema(
            "id:int, content:text, created_at:datetime, author_id:int",
            filters={"id": comment_id}
        )[0]
    
    @staticmethod
    def get_post_comments(post_id: int) -> List[Dict]:
        """Get approved comments for a post"""
        return comment_crud.query_with_schema(
            "id:int, content:text, created_at:datetime, author_id:int, parent_id:int?",
            filters={"post_id": post_id, "is_approved": True},
            sort_by="created_at"
        )


# Demo Application Usage
print("\n=== 1. User Registration and Authentication ===")

# Register users
alice = UserService.register_user("alice", "alice@example.com", "password123", "Alice Johnson")
bob = UserService.register_user("bob", "bob@example.com", "password456", "Bob Smith")

print(f"✅ Registered users: {alice['username']}, {bob['username']}")

# Authenticate user
auth_user = UserService.authenticate_user("alice@example.com", "password123")
if auth_user:
    print(f"✅ Authenticated user: {auth_user['username']}")


print("\n=== 2. Content Management ===")

# Create categories
tech_cat_id = category_crud.create({
    "name": "Technology",
    "slug": "technology",
    "description": "Tech news and tutorials",
    "color": "#007bff"
})

lifestyle_cat_id = category_crud.create({
    "name": "Lifestyle",
    "slug": "lifestyle", 
    "description": "Lifestyle and personal development",
    "color": "#28a745"
})

print(f"✅ Created categories: {tech_cat_id}, {lifestyle_cat_id}")

# Create blog posts
post1 = BlogService.create_post(
    author_id=alice['id'],
    title="Getting Started with Python",
    content="Python is an amazing programming language that's perfect for beginners. In this comprehensive guide, we'll explore the fundamentals of Python programming, from basic syntax to advanced concepts. Whether you're new to programming or coming from another language, this tutorial will help you master Python quickly and effectively.",
    category_id=tech_cat_id,
    published=True
)

post2 = BlogService.create_post(
    author_id=bob['id'],
    title="The Art of Productive Morning Routines",
    content="Starting your day right can transform your entire life. A well-structured morning routine sets the tone for productivity, creativity, and overall well-being. In this article, we'll explore evidence-based strategies for creating a morning routine that works for your lifestyle and goals.",
    category_id=lifestyle_cat_id,
    published=True
)

print(f"✅ Created posts: '{post1['title']}', '{post2['title']}'")


print("\n=== 3. Blog API Simulation ===")

# Get published posts (API endpoint simulation)
blog_posts = BlogService.get_published_posts(page=1, per_page=5)
print(f"Published posts (page 1): {blog_posts['total']} total, {len(blog_posts['items'])} on page")

for post in blog_posts['items']:
    print(f"  - '{post['title']}' ({post['view_count']} views)")

# Get post detail
post_detail = BlogService.get_post_detail(post1['slug'])
print(f"\nPost detail: '{post_detail['title']}'")
print(f"  Author: {post_detail['author']['full_name']}")
print(f"  Views: {post_detail['view_count']}")
print(f"  Content: {post_detail['content'][:100]}...")


print("\n=== 4. Search Functionality ===")

# Search posts
search_results = BlogService.search_posts("python", page=1, per_page=10)
print(f"Search results for 'python': {search_results['total']} found")

for post in search_results['items']:
    print(f"  - '{post['title']}'")


print("\n=== 5. Comment System ===")

# Add comments
comment1 = CommentService.add_comment(
    post_id=post_detail['id'],
    author_id=bob['id'],
    content="Great tutorial! This really helped me understand Python basics."
)

comment2 = CommentService.add_comment(
    post_id=post_detail['id'],
    author_id=alice['id'],
    content="Thanks for the feedback! I'm glad it was helpful."
)

print(f"✅ Added {2} comments")

# Get post comments
comments = CommentService.get_post_comments(post_detail['id'])
print(f"Comments for '{post_detail['title']}': {len(comments)}")

for comment in comments:
    author = user_crud.get_by_id(comment['author_id'])
    print(f"  - {author.username}: {comment['content'][:50]}...")


print("\n=== 6. Analytics and Statistics ===")

# Blog statistics
stats = post_crud.aggregate_with_schema(
    aggregations={
        "total_posts": "count(id)",
        "published_posts": "sum(case when published = 1 then 1 else 0 end)",
        "total_views": "sum(view_count)",
        "avg_views": "avg(view_count)"
    },
    schema_str="total_posts:int, published_posts:int, total_views:int, avg_views:float?"
)[0]

print("Blog Statistics:")
print(f"  - Total posts: {stats['total_posts']}")
print(f"  - Published posts: {stats['published_posts']}")
print(f"  - Total views: {stats['total_views']}")
print(f"  - Average views per post: {stats['avg_views']:.1f}")

# Category statistics
category_stats = post_crud.aggregate_with_schema(
    aggregations={
        "post_count": "count(id)",
        "total_views": "sum(view_count)"
    },
    schema_str="category_id:int?, post_count:int, total_views:int",
    group_by=["category_id"],
    filters={"published": True}
)

print("\nCategory Statistics:")
for stat in category_stats:
    if stat['category_id']:
        category = category_crud.get_by_id(stat['category_id'])
        print(f"  - {category.name}: {stat['post_count']} posts, {stat['total_views']} views")


print("\n🎉 Real-World Blog Application Demo Complete!")
print("\nFeatures demonstrated:")
print("✅ User registration and authentication")
print("✅ Content management with categories")
print("✅ Blog post creation and publishing")
print("✅ Search functionality")
print("✅ Comment system")
print("✅ API endpoint simulation")
print("✅ Analytics and statistics")
print("✅ Performance considerations (denormalized counts)")
print("✅ Error handling and validation")

print(f"\n🧹 Cleaning up database file: {db_name}")
try:
    os.remove(db_name)
    print("✅ Database file removed")
except:
    print("⚠️ Could not remove database file")
