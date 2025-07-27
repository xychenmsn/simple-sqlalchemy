"""
Demonstration of M2M efficiency improvements.

This script shows the performance difference between the original and efficient
implementations of relationship_exists and count_sources_for_target methods.
"""

import time
from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from simple_sqlalchemy.helpers.m2m import M2MHelper


# Define test models
user_role_table = Table(
    'demo_user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('demo_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('demo_roles.id'), primary_key=True)
)

class DemoUser(CommonBase):
    __tablename__ = 'demo_users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    roles = relationship("DemoRole", secondary=user_role_table, back_populates="users")

class DemoRole(CommonBase):
    __tablename__ = 'demo_roles'
    
    name = Column(String(50), nullable=False, unique=True)
    users = relationship("DemoUser", secondary=user_role_table, back_populates="roles")


class DemoUserCrud(BaseCrud[DemoUser]):
    def __init__(self, db_client):
        super().__init__(DemoUser, db_client)

class DemoRoleCrud(BaseCrud[DemoRole]):
    def __init__(self, db_client):
        super().__init__(DemoRole, db_client)


def setup_test_data(db, num_users=50, num_roles=10):
    """Create test data with many relationships"""
    print(f"Creating {num_users} users and {num_roles} roles...")
    
    user_crud = DemoUserCrud(db)
    role_crud = DemoRoleCrud(db)
    m2m_helper = M2MHelper(db, DemoUser, DemoRole, "roles", "users")
    
    # Create roles
    roles = []
    for i in range(num_roles):
        role = role_crud.create({"name": f"Role_{i}"})
        roles.append(role)
    
    # Create users and assign them to multiple roles
    users = []
    for i in range(num_users):
        user = user_crud.create({"name": f"User_{i}", "email": f"user{i}@example.com"})
        users.append(user)
        
        # Assign user to 3-5 random roles
        import random
        num_roles_for_user = random.randint(3, min(5, num_roles))
        selected_roles = random.sample(roles, num_roles_for_user)
        
        for role in selected_roles:
            m2m_helper.add_relationship(user.id, role.id)
    
    print(f"Created {len(users)} users and {len(roles)} roles with relationships")
    return users, roles, m2m_helper


def benchmark_methods(m2m_helper, users, roles, iterations=100):
    """Benchmark the new automatic strategy selection"""
    print(f"\nBenchmarking with {iterations} iterations...")
    print(f"Strategy being used: {m2m_helper.strategy_type}")

    # Select test data
    test_user = users[0]
    test_role = roles[0]

    # Test all methods with the automatically selected strategy
    print("\n1. Testing relationship_exists:")
    start_time = time.time()
    for _ in range(iterations):
        result = m2m_helper.relationship_exists(test_user.id, test_role.id)
    elapsed_time = time.time() - start_time
    print(f"   Time: {elapsed_time:.4f}s ({elapsed_time/iterations*1000:.2f}ms per call)")
    print(f"   Result: {result}")

    print("\n2. Testing count_sources_for_target:")
    start_time = time.time()
    for _ in range(iterations):
        count = m2m_helper.count_sources_for_target(test_role.id)
    elapsed_time = time.time() - start_time
    print(f"   Time: {elapsed_time:.4f}s ({elapsed_time/iterations*1000:.2f}ms per call)")
    print(f"   Count: {count}")

    print("\n3. Testing get_related_for_source:")
    start_time = time.time()
    for _ in range(iterations):
        related = m2m_helper.get_related_for_source(test_user.id)
    elapsed_time = time.time() - start_time
    print(f"   Time: {elapsed_time:.4f}s ({elapsed_time/iterations*1000:.2f}ms per call)")
    print(f"   Related count: {len(related)}")

    print("\n4. Testing count_related_for_source:")
    start_time = time.time()
    for _ in range(iterations):
        count = m2m_helper.count_related_for_source(test_user.id)
    elapsed_time = time.time() - start_time
    print(f"   Time: {elapsed_time:.4f}s ({elapsed_time/iterations*1000:.2f}ms per call)")
    print(f"   Count: {count}")


def demonstrate_strategy_selection(db):
    """Demonstrate automatic strategy selection for different relationship types"""
    print("\n5. Testing automatic strategy selection:")

    # Create a complex M2M table with extra metadata
    complex_table = Table(
        'demo_complex_user_tags',
        CommonBase.metadata,
        Column('user_id', Integer, ForeignKey('demo_users.id'), primary_key=True),
        Column('tag_id', Integer, ForeignKey('demo_complex_tags.id'), primary_key=True),
        Column('assigned_at', String(50)),  # Extra metadata
        Column('assigned_by', String(50))  # Extra metadata
    )

    class DemoComplexTag(CommonBase):
        __tablename__ = 'demo_complex_tags'
        name = Column(String(50), nullable=False, unique=True)
        users = relationship("DemoUser", secondary=complex_table, back_populates="complex_tags")

    # Add relationship to DemoUser
    DemoUser.complex_tags = relationship("DemoComplexTag", secondary=complex_table, back_populates="users")

    # Create tables
    complex_table.create(db.engine, checkfirst=True)
    DemoComplexTag.__table__.create(db.engine, checkfirst=True)

    # Create M2M helpers - they will automatically select the right strategy
    simple_m2m_helper = M2MHelper(db, DemoUser, DemoRole, "roles", "users")
    complex_m2m_helper = M2MHelper(db, DemoUser, DemoComplexTag, "complex_tags", "users")

    print(f"   Simple relationship strategy: {simple_m2m_helper.strategy_type}")
    print(f"   Complex relationship strategy: {complex_m2m_helper.strategy_type}")

    # Test that both work correctly
    user_crud = DemoUserCrud(db)
    tag_crud = BaseCrud(DemoComplexTag, db)

    user = user_crud.create({"name": "Strategy User", "email": "strategy@example.com"})
    tag = tag_crud.create({"name": "Strategy Tag"})

    # Test complex relationship
    result = complex_m2m_helper.relationship_exists(user.id, tag.id)
    print(f"   Complex relationship exists (before): {result}")

    complex_m2m_helper.add_relationship(user.id, tag.id)
    result = complex_m2m_helper.relationship_exists(user.id, tag.id)
    print(f"   Complex relationship exists (after): {result}")

    print(f"   Strategy selection is automatic and transparent to the user!")


def main():
    """Main demonstration function"""
    print("M2M Efficiency Demonstration")
    print("=" * 50)
    
    # Setup database
    db = DbClient("sqlite:///m2m_demo.db")

    # Create tables
    CommonBase.metadata.create_all(db.engine)
    
    try:
        # Setup test data
        users, roles, m2m_helper = setup_test_data(db, num_users=50, num_roles=10)
        
        # Run benchmarks
        benchmark_methods(m2m_helper, users, roles, iterations=100)

        # Demonstrate strategy selection
        demonstrate_strategy_selection(db)
        
        print("\n" + "=" * 50)
        print("Demonstration complete!")
        print("\nKey takeaways:")
        print("1. M2MHelper now automatically selects the best strategy at initialization")
        print("2. Simple relationships use EfficientM2MStrategy for maximum performance")
        print("3. Complex relationships use OriginalM2MStrategy for compatibility")
        print("4. All methods are optimized - no need for separate 'fast' methods")
        print("5. Strategy selection is cached and transparent to the user")
        print("6. Backward compatibility is maintained for existing code")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import os
        if os.path.exists("m2m_demo.db"):
            os.remove("m2m_demo.db")
            print("\nCleaned up demo database")


if __name__ == "__main__":
    main()
