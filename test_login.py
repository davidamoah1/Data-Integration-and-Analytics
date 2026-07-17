#!/usr/bin/env python3
"""Test login functionality for super admin."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from authentication.repositories import UserRepository
from shared.database import Session as DbSession
from shared.database import get_engine
from shared.security import verify_password


def test_super_admin():
    """Test super admin login credentials."""
    print("Testing super admin credentials...")

    # Get database session
    engine = get_engine()
    db = DbSession(engine)

    try:
        # Get user repository
        user_repo = UserRepository(db)

        # Find super admin user
        admin = user_repo.get_by_email("admin@dataflow.io")

        if not admin:
            print("❌ Super admin user NOT found in database!")
            return False

        print(f"✅ Found super admin: {admin.full_name}")
        print(f"   Email: {admin.email}")
        print(f"   Active: {admin.is_active}")
        print(f"   Email verified: {admin.email_verified_at is not None}")

        # Test password
        if verify_password("Admin@12345", admin.password_hash):
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")
            return False

        # Check roles
        from authentication.repositories import UserRoleRepository

        user_role_repo = UserRoleRepository(db)
        roles = user_role_repo.get_roles_for_user(admin.id)
        print(f"✅ User roles: {roles}")

        if "super_admin" not in roles:
            print("⚠️  Warning: User does not have super_admin role!")
        else:
            print("✅ User has super_admin role!")

        print("\n🎉 Super admin is ready to use!")
        print("\nLogin credentials:")
        print("   Email: admin@dataflow.io")
        print("   Password: Admin@12345")

        return True

    except Exception as e:
        print(f"❌ Error testing super admin: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_super_admin()
    sys.exit(0 if success else 1)
