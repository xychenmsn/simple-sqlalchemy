#!/usr/bin/env python3
"""
Quick Start Example - 90% Use Case

This example shows the most common usage patterns that cover 90% of use cases:
- Database setup with DbClient
- Model definition with CommonBase
- String-schema operations for API-ready results
- Basic CRUD with validation
- Pagination for web APIs

Perfect for getting started quickly!
"""

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from datetime import datetime


# 1. Setup Database Connection
print("=== 1. Database Setup ===")
import os
import time
# Use a unique database name to avoid conflicts
db_name = f"quickstart_{int(time.time())}.db"
db = DbClient(f"sqlite:///{db_name}")
print(f"✅ Connected to database: {db_name}")


# 2. Define Your Models
print("\n=== 2. Model Definition ===")
class User(CommonBase):
    __tablename__ = 'users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    bio = Column(Text)
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)

class Post(CommonBase):
    __tablename__ = 'posts'
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, nullable=False)
    published = Column(Boolean, default=False)

# Create tables
CommonBase.metadata.create_all(db.engine)
print("✅ Models defined and tables created")


# 3. Create CRUD Operations
print("\n=== 3. CRUD Setup ===")
user_crud = BaseCrud(User, db)
post_crud = BaseCrud(Post, db)
print("✅ CRUD operations ready")


# 4. Create Sample Data
print("\n=== 4. Creating Sample Data ===")
# Create users - returns IDs by default
user1_id = user_crud.create({
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "bio": "Software engineer passionate about Python",
    "active": True,
    "last_login": datetime.now()
})

user2_id = user_crud.create({
    "name": "Bob Smith", 
    "email": "bob@example.com",
    "bio": "Data scientist and ML enthusiast",
    "active": True
})

user3_id = user_crud.create({
    "name": "Charlie Brown",
    "email": "charlie@example.com", 
    "active": False  # Inactive user
})

print(f"✅ Created users: {user1_id}, {user2_id}, {user3_id}")

# Create posts
post1_id = post_crud.create({
    "title": "Getting Started with Python",
    "content": "Python is an amazing language for beginners...",
    "author_id": user1_id.id if hasattr(user1_id, 'id') else user1_id,
    "published": True
})

post2_id = post_crud.create({
    "title": "Machine Learning Basics",
    "content": "Let's explore the fundamentals of ML...",
    "author_id": user2_id.id if hasattr(user2_id, 'id') else user2_id,
    "published": True
})

post3_id = post_crud.create({
    "title": "Draft Post",
    "content": "This is still a work in progress...",
    "author_id": user1_id.id if hasattr(user1_id, 'id') else user1_id,
    "published": False
})

print(f"✅ Created posts: {post1_id}, {post2_id}, {post3_id}")


# 5. Query with Schema Validation (API-Ready Results)
print("\n=== 5. String-Schema Queries (Recommended) ===")

# Get active users with specific fields
active_users = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email, active:bool",
    filters={"active": True},
    sort_by="name"
)

print("Active users:")
for user in active_users:
    print(f"  - {user['name']} ({user['email']}) - Active: {user['active']}")

# Get published posts with enhanced filtering
published_posts = post_crud.query_with_schema(
    schema_str="id:int, title:string, author_id:int, published:bool",
    filters={
        "published": True,
        "author_id": {"not": None}  # Has an author
    },
    sort_by="title"
)

print(f"\nPublished posts ({len(published_posts)}):")
for post in published_posts:
    print(f"  - '{post['title']}' by author {post['author_id']}")


# 6. Pagination for Web APIs
print("\n=== 6. Pagination (Perfect for Web APIs) ===")

# Paginated user results
paginated_users = user_crud.paginated_query_with_schema(
    schema_str="id:int, name:string, email:email, bio:string?",
    page=1,
    per_page=2,  # Small page size for demo
    filters={"active": True},
    sort_by="name"
)

print("Paginated users (page 1, 2 per page):")
print(f"  Total users: {paginated_users['total']}")
print(f"  Current page: {paginated_users['page']}")
print(f"  Has next page: {paginated_users['has_next']}")
print("  Users:")
for user in paginated_users['items']:
    bio = user['bio'][:50] + "..." if user['bio'] and len(user['bio']) > 50 else user['bio']
    print(f"    - {user['name']}: {bio}")


# 7. Search Functionality
print("\n=== 7. Search Across Fields ===")

# Search users by name or email
search_results = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email",
    search_query="alice",  # Search term
    search_fields=["name", "email"],  # Fields to search in
    filters={"active": True}
)

print("Search results for 'alice':")
for user in search_results:
    print(f"  - {user['name']} ({user['email']})")


# 8. Advanced Filtering
print("\n=== 8. Advanced Filtering ===")

# Complex filters with comparisons, lists, null checks
filtered_users = user_crud.query_with_schema(
    schema_str="id:int, name:string, email:email, last_login:datetime?",
    filters={
        "active": True,                           # Equality
        "email": {"not": None},                   # IS NOT NULL
        "id": {">=": 2},                         # Greater than or equal
        "name": {"like": "%o%"},                 # Contains 'o'
        # "last_login": {"not": None}            # Has logged in
    },
    sort_by="name"
)

print("Filtered users (active, has email, id >= 2, name contains 'o'):")
for user in filtered_users:
    login_time = user['last_login'] if user['last_login'] else 'Never'
    print(f"  - {user['name']} (ID: {user['id']}) - Last login: {login_time}")


# 9. Update Operations
print("\n=== 9. Update Operations ===")

# Update user (returns boolean by default)
user3_actual_id = user3_id.id if hasattr(user3_id, 'id') else user3_id
success = user_crud.update(user3_actual_id, {"active": True, "bio": "Now I'm active!"})
print(f"✅ Updated user {user3_actual_id}: {success}")

# Update and get data back
user1_actual_id = user1_id.id if hasattr(user1_id, 'id') else user1_id
user_crud.update(user1_actual_id, {"last_login": datetime.now()})

# Get the updated user with schema
updated_user = user_crud.query_with_schema(
    "id:int, name:string, last_login:datetime",
    filters={"id": user1_actual_id}
)[0]
print(f"✅ Updated user login: {updated_user['name']} at {updated_user['last_login']}")


# 10. Fetch One and Scalar Operations (90% Use Case)
print("\n=== 10. Fetch One and Scalar Operations ===")

# Get a single user by ID (very common operation)
user_id_to_fetch = user1_id.id if hasattr(user1_id, 'id') else user1_id
single_user = user_crud.get_one_with_schema(
    "id:int, name:string, email:email, active:bool",
    filters={"id": user_id_to_fetch}
)

if single_user:
    print(f"Single user: {single_user['name']} ({single_user['email']}) - Active: {single_user['active']}")

# Get the latest post
latest_post = post_crud.get_one_with_schema(
    "id:int, title:string, published:bool",
    sort_by="created_at",
    sort_desc=True
)

if latest_post:
    status = "Published" if latest_post['published'] else "Draft"
    print(f"Latest post: '{latest_post['title']}' ({status})")

# Get scalar values (counts, totals, etc.)
total_users = user_crud.get_scalar_with_schema("count(*)")
active_users = user_crud.get_scalar_with_schema("count(*)", filters={"active": True})
total_posts = post_crud.get_scalar_with_schema("count(*)")

print(f"Statistics: {total_users} total users, {active_users} active, {total_posts} posts")

# Get a specific field value
alice_email = user_crud.get_scalar_with_schema("email", filters={"name": "Alice Johnson"})
print(f"Alice's email: {alice_email}")


# 11. Aggregation Queries
print("\n=== 11. Aggregation Queries ===")

# Count posts by publication status
post_stats = post_crud.aggregate_with_schema(
    aggregations={
        "count": "count(id)",
        "avg_author_id": "avg(author_id)"
    },
    schema_str="published:bool, count:int, avg_author_id:float?",
    group_by=["published"]
)

print("Post statistics by publication status:")
for stat in post_stats:
    status = "Published" if stat['published'] else "Draft"
    print(f"  - {status}: {stat['count']} posts, avg author ID: {stat['avg_author_id']:.1f}")


print("\n🎉 Quick Start Complete!")
print("\nThis covers 90% of common use cases:")
print("✅ Database setup with DbClient")
print("✅ Model definition with CommonBase")
print("✅ String-schema queries (API-ready)")
print("✅ Enhanced filtering and search")
print("✅ Pagination for web APIs")
print("✅ CRUD operations with validation")
print("✅ Fetch one and scalar operations")
print("✅ Aggregation queries")
print("\nFor more advanced features, check out the other examples!")

# Cleanup
print(f"\n🧹 Cleaning up database file: {db_name}")
try:
    os.remove(db_name)
    print("✅ Database file removed")
except:
    print("⚠️ Could not remove database file")
