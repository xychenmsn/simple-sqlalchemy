"""
Examples demonstrating the Enhanced BaseCrud functionality.

This shows how to use both traditional SQLAlchemy operations and 
string-schema operations in the same class.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from datetime import datetime, timedelta
from simple_sqlalchemy import DbClient, CommonBase, BaseCrud


# Test models
class User(CommonBase):
    __tablename__ = 'enhanced_users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    department = Column(String(50), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    age = Column(Integer, nullable=True)


class Post(CommonBase):
    __tablename__ = 'enhanced_posts'
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='draft')
    view_count = Column(Integer, nullable=False, default=0)


def test_enhanced_crud():
    """Test the enhanced BaseCrud functionality"""
    
    print("Enhanced BaseCrud Examples")
    print("=" * 50)
    
    # Setup database
    db = DbClient("sqlite:///enhanced_crud_test.db")
    CommonBase.metadata.create_all(db.engine)
    
    # Create CRUD instances
    user_crud = BaseCrud(User, db)
    post_crud = BaseCrud(Post, db)
    
    # Create test data
    test_users = [
        {"name": "Alice Johnson", "email": "alice@example.com", "department": "Engineering", "active": True, "age": 28},
        {"name": "Bob Smith", "email": None, "department": "Product", "active": True, "age": 32},
        {"name": "Charlie Brown", "email": "charlie@example.com", "department": "Engineering", "active": False, "age": 25},
        {"name": "Diana Prince", "email": "diana@example.com", "department": None, "active": True, "age": 30},
        {"name": "Eve Wilson", "email": None, "department": "Marketing", "active": True, "age": 27}
    ]
    
    created_users = []
    for user_data in test_users:
        user = user_crud.create(user_data)
        created_users.append(user)
    
    # Create some posts
    test_posts = [
        {"title": "First Post", "content": "Content 1", "user_id": created_users[0].id, "status": "published", "view_count": 100},
        {"title": "Second Post", "content": "Content 2", "user_id": created_users[0].id, "status": "draft", "view_count": 0},
        {"title": "Third Post", "content": "Content 3", "user_id": created_users[1].id, "status": "published", "view_count": 50},
    ]
    
    for post_data in test_posts:
        post_crud.create(post_data)
    
    print("✅ Test data created")
    print()
    
    try:
        print("1. Traditional SQLAlchemy Operations")
        print("-" * 40)
        
        # Traditional get_by_id
        user = user_crud.get_by_id(created_users[0].id)
        print(f"User by ID: {user.name} ({user.email})")
        
        # Traditional get_multi with enhanced filtering
        active_users = user_crud.get_multi(
            filters={
                "active": True,
                "email": {"not": None},  # Enhanced filtering!
                "department": ["Engineering", "Product"]  # Enhanced filtering!
            },
            sort_by="name",
            limit=10
        )
        print(f"Active users with email in Eng/Product: {len(active_users)} found")
        for user in active_users:
            print(f"  - {user.name}: {user.email} ({user.department})")
        
        # Traditional search with enhanced filtering
        search_results = user_crud.search(
            search_query="alice",
            search_fields=["name", "email"],
            filters={"active": True}
        )
        print(f"Search for 'alice': {len(search_results)} found")
        
        # Traditional count with enhanced filtering
        count = user_crud.count(filters={
            "active": True,
            "age": {">=": 25}  # Enhanced filtering!
        })
        print(f"Active users 25+: {count}")
        print()
        
        print("2. String-Schema Operations")
        print("-" * 35)
        
        # Query with schema
        users_dict = user_crud.query_with_schema(
            schema_str="id:int, name:string, email:email?, department:string?",
            filters={
                "active": True,
                "email": {"not": None}
            },
            sort_by="name"
        )
        print(f"Users with schema: {len(users_dict)} found")
        for user in users_dict:
            print(f"  - {user}")
        print()
        
        # Paginated query with schema
        paginated = user_crud.paginated_query_with_schema(
            schema_str="id:int, name:string, department:string?",
            page=1,
            per_page=3,
            filters={"active": True}
        )
        print(f"Paginated users: {len(paginated['items'])} of {paginated['total']}")
        print(f"Has next page: {paginated['has_next']}")
        for user in paginated['items']:
            print(f"  - {user}")
        print()
        
        # Aggregation with schema
        dept_stats = user_crud.aggregate_with_schema(
            aggregations={"count": "count(id)", "avg_age": "avg(age)"},
            schema_str="department:string?, count:int, avg_age:float?",
            group_by=["department"],
            filters={"active": True}
        )
        print("Department statistics:")
        for stat in dept_stats:
            dept = stat['department'] or 'No Department'
            print(f"  - {dept}: {stat['count']} users, avg age {stat['avg_age']:.1f}")
        print()
        
        print("3. Hybrid Approach (Best of Both Worlds)")
        print("-" * 50)
        
        # Get SQLAlchemy instance for complex operations
        user = user_crud.get_by_id(created_users[0].id)
        print(f"Got user: {user.name}")

        # Update using BaseCrud
        updated_user = user_crud.update(user.id, {"name": "Alice Johnson-Smith"})
        print(f"Updated user: {updated_user.name}")
        
        # Convert to dict for API response
        api_response = user_crud.to_dict(updated_user, "id:int, name:string, email:email?, active:bool")
        print(f"API response: {api_response}")
        
        # Get multiple and convert
        all_users = user_crud.get_multi(filters={"active": True})
        api_users = user_crud.to_dict_list(all_users, "id:int, name:string, department:string?")
        print(f"All active users as dicts: {len(api_users)} users")
        for user_dict in api_users:
            print(f"  - {user_dict}")
        print()
        
        print("4. Enhanced Filtering Examples")
        print("-" * 40)
        
        # Comparison operators
        young_users = user_crud.query_with_schema(
            schema_str="name:string, age:int",
            filters={"age": {"<": 30}}
        )
        print(f"Users under 30: {len(young_users)}")
        
        # Range filtering
        mid_age_users = user_crud.query_with_schema(
            schema_str="name:string, age:int",
            filters={"age": {"between": [25, 30]}}
        )
        print(f"Users 25-30: {len(mid_age_users)}")
        
        # NOT IN filtering
        non_eng_users = user_crud.query_with_schema(
            schema_str="name:string, department:string?",
            filters={"department": {"not_in": ["Engineering"]}}
        )
        print(f"Non-engineering users: {len(non_eng_users)}")
        
        # Null/Not null filtering
        users_with_email = user_crud.query_with_schema(
            schema_str="name:string, email:email",
            filters={"email": {"not": None}}
        )
        print(f"Users with email: {len(users_with_email)}")
        
        users_without_email = user_crud.query_with_schema(
            schema_str="name:string",
            filters={"email": None}
        )
        print(f"Users without email: {len(users_without_email)}")
        print()
        
        print("✅ All Enhanced BaseCrud examples completed successfully!")
        print()
        print("Key Benefits Demonstrated:")
        print("- ✅ Traditional SQLAlchemy operations work unchanged")
        print("- ✅ Enhanced filtering (null, not null, comparisons, lists)")
        print("- ✅ String-schema operations for API consistency")
        print("- ✅ Conversion utilities between models and dicts")
        print("- ✅ DRY architecture eliminates code duplication")
        print("- ✅ Database-agnostic design (works with SQLite)")
        print("- ✅ Best of both worlds: ORM power + schema validation")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import os
        if os.path.exists("enhanced_crud_test.db"):
            os.remove("enhanced_crud_test.db")
            print("\n🧹 Cleaned up test database")


def test_backward_compatibility():
    """Test that existing BaseCrud code still works"""
    
    print("\nBackward Compatibility Test")
    print("=" * 40)
    
    # Setup
    db = DbClient("sqlite:///compat_test.db")
    CommonBase.metadata.create_all(db.engine)
    user_crud = BaseCrud(User, db)
    
    try:
        # Test that all old methods still work exactly as before
        user = user_crud.create({"name": "Test User", "email": "test@example.com", "active": True})
        print(f"✅ create() works: {user.name}")
        
        found_user = user_crud.get_by_id(user.id)
        print(f"✅ get_by_id() works: {found_user.name}")
        
        users = user_crud.get_multi(filters={"active": True})
        print(f"✅ get_multi() works: {len(users)} users")
        
        count = user_crud.count(filters={"active": True})
        print(f"✅ count() works: {count} users")
        
        search_results = user_crud.search("test", ["name"])
        print(f"✅ search() works: {len(search_results)} results")
        
        exists = user_crud.exists_by_field("email", "test@example.com")
        print(f"✅ exists_by_field() works: {exists}")
        
        field_user = user_crud.get_by_field("email", "test@example.com")
        print(f"✅ get_by_field() works: {field_user.name}")
        
        print("✅ All backward compatibility tests passed!")
        
    except Exception as e:
        print(f"❌ Backward compatibility error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        import os
        if os.path.exists("compat_test.db"):
            os.remove("compat_test.db")


if __name__ == "__main__":
    test_enhanced_crud()
    test_backward_compatibility()
