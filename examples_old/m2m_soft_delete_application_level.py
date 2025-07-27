"""
Example showing how to handle soft delete at the application level with M2M relationships.

This demonstrates the clean separation of concerns where:
- M2MHelper handles pure M2M relationship operations
- Application code handles soft delete filtering when needed
"""

from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud, SoftDeleteMixin
from simple_sqlalchemy.helpers.m2m import M2MHelper


# Define models
user_role_table = Table(
    'app_user_roles',
    CommonBase.metadata,
    Column('user_id', Integer, ForeignKey('app_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('app_roles.id'), primary_key=True)
)

class AppUser(CommonBase, SoftDeleteMixin):
    __tablename__ = 'app_users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    roles = relationship("AppRole", secondary=user_role_table, back_populates="users")

class AppRole(CommonBase):
    __tablename__ = 'app_roles'
    
    name = Column(String(50), nullable=False, unique=True)
    users = relationship("AppUser", secondary=user_role_table, back_populates="roles")


class AppUserCrud(BaseCrud[AppUser]):
    def __init__(self, db_client):
        super().__init__(AppUser, db_client)

class AppRoleCrud(BaseCrud[AppRole]):
    def __init__(self, db_client):
        super().__init__(AppRole, db_client)


class UserRoleService:
    """
    Application service that handles user-role relationships with soft delete logic.
    
    This demonstrates how to handle soft delete at the application level
    rather than burying it in the M2M helper.
    """
    
    def __init__(self, db_client):
        self.db_client = db_client
        self.user_crud = AppUserCrud(db_client)
        self.role_crud = AppRoleCrud(db_client)
        self.m2m_helper = M2MHelper(db_client, AppUser, AppRole, "roles", "users")
    
    def add_user_role(self, user_id: int, role_id: int) -> bool:
        """Add role to user (only if user is not soft-deleted)"""
        user = self.user_crud.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            print(f"Cannot add role: User {user_id} not found or is deleted")
            return False
        
        role = self.role_crud.get_by_id(role_id)
        if not role:
            print(f"Cannot add role: Role {role_id} not found")
            return False
        
        result = self.m2m_helper.add_relationship(user_id, role_id)
        return result is not None
    
    def remove_user_role(self, user_id: int, role_id: int) -> bool:
        """Remove role from user"""
        result = self.m2m_helper.remove_relationship(user_id, role_id)
        return result is not None
    
    def get_active_users_for_role(self, role_id: int, skip: int = 0, limit: int = 100):
        """Get only active (non-soft-deleted) users for a role"""
        # Get all users for the role
        all_users = self.m2m_helper.get_sources_for_target(role_id, skip=0, limit=0)  # Get all first
        
        # Filter out soft-deleted users at application level
        active_users = [user for user in all_users if user.deleted_at is None]
        
        # Apply pagination to filtered results
        if skip > 0:
            active_users = active_users[skip:]
        if limit > 0:
            active_users = active_users[:limit]
        
        return active_users
    
    def count_active_users_for_role(self, role_id: int) -> int:
        """Count only active (non-soft-deleted) users for a role"""
        # Get all users for the role
        all_users = self.m2m_helper.get_sources_for_target(role_id)
        
        # Count only active users at application level
        return len([user for user in all_users if user.deleted_at is None])
    
    def get_roles_for_user(self, user_id: int, skip: int = 0, limit: int = 100):
        """Get roles for user (only if user is active)"""
        user = self.user_crud.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            return []
        
        return self.m2m_helper.get_related_for_source(user_id, skip, limit)
    
    def user_has_role(self, user_id: int, role_id: int) -> bool:
        """Check if active user has role"""
        user = self.user_crud.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            return False
        
        return self.m2m_helper.relationship_exists(user_id, role_id)
    
    def get_all_users_for_role_including_deleted(self, role_id: int):
        """Get ALL users for role, including soft-deleted (for admin purposes)"""
        return self.m2m_helper.get_sources_for_target(role_id)
    
    def cleanup_deleted_user_relationships(self, user_id: int):
        """Remove all role relationships for a soft-deleted user"""
        user = self.user_crud.get_by_id(user_id)
        if not user:
            print(f"User {user_id} not found")
            return
        if user.deleted_at is None:
            print(f"User {user_id} is not soft-deleted")
            return

        # Get all roles for the user
        roles = self.m2m_helper.get_related_for_source(user_id)

        # Remove all relationships
        for role in roles:
            self.m2m_helper.remove_relationship(user_id, role.id)
            print(f"Removed role {role.name} from deleted user {user.name}")


def main():
    """Demonstrate application-level soft delete handling"""
    print("M2M Soft Delete - Application Level Handling")
    print("=" * 50)
    
    # Setup database
    db = DbClient("sqlite:///m2m_soft_delete_demo.db")
    CommonBase.metadata.create_all(db.engine)
    
    try:
        # Create service
        service = UserRoleService(db)
        
        print(f"M2M Strategy: {service.m2m_helper.strategy_type}")
        
        # Create test data
        print("\n1. Creating test data...")
        user1 = service.user_crud.create({"name": "Alice", "email": "alice@example.com"})
        user2 = service.user_crud.create({"name": "Bob", "email": "bob@example.com"})
        admin_role = service.role_crud.create({"name": "Admin"})
        user_role = service.role_crud.create({"name": "User"})
        
        # Add relationships
        service.add_user_role(user1.id, admin_role.id)
        service.add_user_role(user1.id, user_role.id)
        service.add_user_role(user2.id, user_role.id)
        
        print(f"Created users: {user1.name}, {user2.name}")
        print(f"Created roles: {admin_role.name}, {user_role.name}")
        
        # Test active user queries
        print("\n2. Testing active user queries...")
        active_admins = service.get_active_users_for_role(admin_role.id)
        active_users = service.get_active_users_for_role(user_role.id)
        
        print(f"Active admins: {[u.name for u in active_admins]}")
        print(f"Active users: {[u.name for u in active_users]}")
        print(f"Active admin count: {service.count_active_users_for_role(admin_role.id)}")
        print(f"Active user count: {service.count_active_users_for_role(user_role.id)}")
        
        # Soft delete a user
        print("\n3. Soft deleting Alice...")
        user1.soft_delete()
        service.user_crud.update(user1.id, {"deleted_at": user1.deleted_at})
        
        # Test queries after soft delete
        print("\n4. Testing queries after soft delete...")
        active_admins = service.get_active_users_for_role(admin_role.id)
        active_users = service.get_active_users_for_role(user_role.id)
        all_admins = service.get_all_users_for_role_including_deleted(admin_role.id)
        
        print(f"Active admins: {[u.name for u in active_admins]}")
        print(f"Active users: {[u.name for u in active_users]}")
        print(f"All admins (including deleted): {[u.name for u in all_admins]}")
        print(f"Active admin count: {service.count_active_users_for_role(admin_role.id)}")
        print(f"Active user count: {service.count_active_users_for_role(user_role.id)}")
        
        # Test user operations
        print("\n5. Testing user operations...")
        print(f"Alice has admin role: {service.user_has_role(user1.id, admin_role.id)}")  # False - user deleted
        print(f"Bob has user role: {service.user_has_role(user2.id, user_role.id)}")      # True
        
        # Try to add role to deleted user
        print(f"Adding role to deleted user: {service.add_user_role(user1.id, user_role.id)}")  # False
        
        # Cleanup deleted user relationships
        print("\n6. Cleaning up deleted user relationships...")
        service.cleanup_deleted_user_relationships(user1.id)
        
        # Verify cleanup
        all_admins_after_cleanup = service.get_all_users_for_role_including_deleted(admin_role.id)
        print(f"All admins after cleanup: {[u.name for u in all_admins_after_cleanup]}")
        
        print("\n" + "=" * 50)
        print("Key Benefits of Application-Level Soft Delete Handling:")
        print("1. M2MHelper stays simple and focused on M2M operations")
        print("2. Soft delete logic is explicit and controllable")
        print("3. Different services can have different soft delete policies")
        print("4. Easy to audit and debug soft delete behavior")
        print("5. Clear separation of concerns")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import os
        if os.path.exists("m2m_soft_delete_demo.db"):
            os.remove("m2m_soft_delete_demo.db")
            print("\nCleaned up demo database")


if __name__ == "__main__":
    main()
