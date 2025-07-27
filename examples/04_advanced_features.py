#!/usr/bin/env python3
"""
Advanced Features Example

This example demonstrates advanced features of simple-sqlalchemy:
- SearchHelper for complex custom queries
- M2MHelper for many-to-many relationships
- Batch processing and performance optimization
- Custom aggregations and statistical queries
- Advanced session management
- Error handling and edge cases

Use these features for complex applications and performance-critical scenarios!
"""

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from simple_sqlalchemy.helpers.search import SearchHelper
from simple_sqlalchemy.helpers.m2m import M2MHelper
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import time


# Setup
print("=== Advanced Features Demo ===")
import os
import time
# Use a unique database name to avoid conflicts
db_name = f"advanced_demo_{int(time.time())}.db"
db = DbClient(f"sqlite:///{db_name}")
print(f"✅ Connected to database: {db_name}")


# Define Models with Many-to-Many Relationships
# Association table for many-to-many relationship
user_role_association = Table(
    'user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.now)
)

class User(CommonBase):
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Many-to-many relationship
    roles = relationship("Role", secondary=user_role_association, back_populates="users")
    
    def update_login(self):
        """Update login statistics"""
        self.last_login = datetime.now()
        self.login_count = (self.login_count or 0) + 1


class Role(CommonBase):
    __tablename__ = 'roles'
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)
    
    # Many-to-many relationship
    users = relationship("User", secondary=user_role_association, back_populates="roles")


class ActivityLog(CommonBase):
    __tablename__ = 'activity_logs'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    ip_address = Column(String(45))
    
    user = relationship("User")

CommonBase.metadata.create_all(db.engine)

# Create CRUD instances
user_crud = BaseCrud(User, db)
role_crud = BaseCrud(Role, db)
log_crud = BaseCrud(ActivityLog, db)


# 1. SearchHelper for Complex Queries
print("\n=== 1. SearchHelper for Complex Queries ===")

# Create search helper
search_helper = db.create_search_helper(User)

# Create sample data
print("Creating sample data...")
roles_data = [
    {"name": "admin", "description": "System administrator"},
    {"name": "editor", "description": "Content editor"},
    {"name": "viewer", "description": "Read-only access"},
    {"name": "moderator", "description": "Community moderator"}
]

role_ids = []
for role_data in roles_data:
    role_id = role_crud.create(role_data)
    role_ids.append(role_id)

users_data = [
    {"username": "alice", "email": "alice@example.com", "full_name": "Alice Johnson", "login_count": 15},
    {"username": "bob", "email": "bob@example.com", "full_name": "Bob Smith", "login_count": 8},
    {"username": "charlie", "email": "charlie@example.com", "full_name": "Charlie Brown", "login_count": 23},
    {"username": "diana", "email": "diana@example.com", "full_name": "Diana Prince", "login_count": 5, "active": False}
]

user_ids = []
for user_data in users_data:
    user_id = user_crud.create(user_data)
    user_ids.append(user_id)

print(f"✅ Created {len(role_ids)} roles and {len(user_ids)} users")

# Complex query with JOINs and aggregations
def complex_user_stats_query(session):
    """Complex query that can't be easily done with basic CRUD"""
    return session.query(
        User.id,
        User.username,
        User.full_name,
        User.login_count,
        func.count(ActivityLog.id).label('activity_count')
    ).outerjoin(ActivityLog).group_by(User.id).having(
        func.coalesce(User.login_count, 0) > 10
    ).order_by(User.login_count.desc())

# Execute complex query with pagination
results = search_helper.paginated_search_with_count(
    query_func=complex_user_stats_query,
    page=1,
    per_page=10
)

print("Complex query results (users with >10 logins):")
print(f"  Total results: {results['total']}")
for row in results['items']:
    print(f"  - {row.username} ({row.full_name}): {row.login_count} logins, {row.activity_count} activities")


# 2. M2MHelper for Many-to-Many Relationships
print("\n=== 2. M2MHelper for Many-to-Many Relationships ===")

# Create M2M helper
user_roles_m2m = M2MHelper(
    db_client=db,
    source_model=User,
    target_model=Role,
    association_table='user_roles'
)

# Assign roles to users
print("Assigning roles to users...")
user_roles_m2m.add_relationship(user_ids[0], role_ids[0])  # alice -> admin
user_roles_m2m.add_relationship(user_ids[0], role_ids[1])  # alice -> editor
user_roles_m2m.add_relationship(user_ids[1], role_ids[2])  # bob -> viewer
user_roles_m2m.add_relationships(user_ids[2], [role_ids[1], role_ids[3]])  # charlie -> editor, moderator

print("✅ Role assignments complete")

# Query relationships
alice_roles = user_roles_m2m.get_target_ids(user_ids[0])
admin_users = user_roles_m2m.get_source_ids(role_ids[0])

print(f"Alice's roles: {alice_roles}")
print(f"Admin users: {admin_users}")

# Check relationship existence
has_admin = user_roles_m2m.relationship_exists(user_ids[0], role_ids[0])
print(f"Alice has admin role: {has_admin}")

# Get relationship counts
role_counts = {}
for role_id in role_ids:
    count = user_roles_m2m.count_sources_for_target(role_id)
    role = role_crud.get_by_id(role_id)
    role_counts[role.name] = count

print("Users per role:")
for role_name, count in role_counts.items():
    print(f"  - {role_name}: {count} users")


# 3. Batch Processing
print("\n=== 3. Batch Processing ===")

# Create activity logs for demonstration
print("Creating activity logs...")
import random

activities = ["login", "logout", "view_page", "edit_content", "delete_item", "upload_file"]
for i in range(50):
    log_crud.create({
        "user_id": random.choice(user_ids),
        "action": random.choice(activities),
        "details": f"Sample activity {i+1}",
        "timestamp": datetime.now() - timedelta(days=random.randint(0, 30)),
        "ip_address": f"192.168.1.{random.randint(1, 254)}"
    })

print("✅ Created 50 activity logs")

# Batch process logs
def process_logs_batch(logs_batch):
    """Process a batch of logs"""
    print(f"  Processing batch of {len(logs_batch)} logs...")
    
    # Simulate processing (e.g., analytics, notifications)
    login_count = sum(1 for log in logs_batch if log.action == 'login')
    if login_count > 0:
        print(f"    Found {login_count} login events in this batch")

# Process all logs in batches
print("Batch processing activity logs:")
search_helper_logs = db.create_search_helper(ActivityLog)

search_helper_logs.batch_process(
    query_func=lambda s: s.query(ActivityLog).order_by(ActivityLog.timestamp),
    process_func=process_logs_batch,
    batch_size=10
)

print("✅ Batch processing complete")


# 4. Advanced Aggregations
print("\n=== 4. Advanced Aggregations ===")

# Complex aggregation with multiple groupings
activity_stats = log_crud.aggregate_with_schema(
    aggregations={
        "count": "count(id)",
        "unique_users": "count(distinct user_id)",
        "latest_activity": "max(timestamp)"
    },
    schema_str="action:string, count:int, unique_users:int, latest_activity:datetime",
    group_by=["action"],
    filters={"timestamp": {">=": (datetime.now() - timedelta(days=7)).isoformat()}}
)

print("Activity statistics (last 7 days):")
for stat in activity_stats:
    print(f"  - {stat['action']}: {stat['count']} events, {stat['unique_users']} unique users")
    print(f"    Latest: {stat['latest_activity']}")


# 5. Performance Optimization
print("\n=== 5. Performance Optimization ===")

# Measure query performance
start_time = time.time()

# Efficient query with schema (only fetch needed fields)
efficient_users = user_crud.query_with_schema(
    schema_str="id:int, username:string, login_count:int",
    filters={"active": True},
    limit=100
)

schema_time = time.time() - start_time

start_time = time.time()

# Traditional query (fetches all fields)
traditional_users = user_crud.get_multi(
    filters={"active": True},
    limit=100
)

traditional_time = time.time() - start_time

print(f"Query performance comparison:")
print(f"  Schema query (3 fields): {schema_time:.4f}s")
print(f"  Traditional query (all fields): {traditional_time:.4f}s")
print(f"  Results count: {len(efficient_users)} vs {len(traditional_users)}")

# Memory usage comparison
import sys
schema_size = sys.getsizeof(efficient_users)
traditional_size = sys.getsizeof(traditional_users)

print(f"Memory usage:")
print(f"  Schema results: {schema_size} bytes")
print(f"  Traditional results: {traditional_size} bytes")


# 6. Advanced Session Management
print("\n=== 6. Advanced Session Management ===")

# Manual session management for complex operations
print("Manual session management example:")
with db.session_scope() as session:
    # Complex transaction
    try:
        # Get user
        user = session.query(User).filter_by(username='alice').first()
        
        # Update user
        user.update_login()
        
        # Create activity log
        activity = ActivityLog(
            user_id=user.id,
            action="manual_login",
            details="Login via advanced session management",
            timestamp=datetime.now()
        )
        session.add(activity)
        
        # Commit happens automatically when exiting context
        print(f"  ✅ Updated {user.username} login stats")
        
    except Exception as e:
        # Rollback happens automatically on exception
        print(f"  ❌ Transaction failed: {e}")


# 7. Error Handling and Edge Cases
print("\n=== 7. Error Handling and Edge Cases ===")

# Test error handling
try:
    # Invalid filter format
    invalid_results = user_crud.get_multi(
        filters={"login_count": {"invalid_operator": 10}}
    )
except ValueError as e:
    print(f"✅ Caught expected error: {e}")

try:
    # Non-existent field in schema
    invalid_schema = user_crud.query_with_schema(
        schema_str="id:int, nonexistent_field:string"
    )
except Exception as e:
    print(f"✅ Caught schema error: {type(e).__name__}")

# Edge case: Empty results
empty_results = user_crud.query_with_schema(
    schema_str="id:int, username:string",
    filters={"username": "nonexistent_user"}
)
print(f"Empty results handled gracefully: {len(empty_results)} results")

# Edge case: Large pagination
large_page = user_crud.paginated_query_with_schema(
    schema_str="id:int, username:string",
    page=999,  # Page that doesn't exist
    per_page=10
)
print(f"Large page handled: page {large_page['page']}, {len(large_page['items'])} items")


print("\n🎉 Advanced Features Complete!")
print("\nKey advanced features demonstrated:")
print("✅ SearchHelper for complex custom queries")
print("✅ M2MHelper for many-to-many relationships")
print("✅ Batch processing for large datasets")
print("✅ Advanced aggregations and statistics")
print("✅ Performance optimization techniques")
print("✅ Manual session management")
print("✅ Error handling and edge cases")
print("\nThese features enable building robust, high-performance applications!")

# Cleanup
print(f"\n🧹 Cleaning up database file: {db_name}")
try:
    os.remove(db_name)
    print("✅ Database file removed")
except:
    print("⚠️ Could not remove database file")
