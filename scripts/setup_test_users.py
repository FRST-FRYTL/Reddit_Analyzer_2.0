#!/usr/bin/env python3
"""Setup test users for CLI testing."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reddit_analyzer.database import get_db, engine
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.models import Base


def create_test_users():
    """Create test users with different roles."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    test_users = [
        {
            "username": "admin_test",
            "password": "admin123",
            "email": "admin@test.com",
            "role": UserRole.ADMIN,
        },
        {
            "username": "mod_test",
            "password": "mod123",
            "email": "mod@test.com",
            "role": UserRole.MODERATOR,
        },
        {
            "username": "user_test",
            "password": "user123",
            "email": "user@test.com",
            "role": UserRole.USER,
        },
    ]

    created_count = 0
    for user_data in test_users:
        # Check if user exists
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=True,
                is_verified=True,
            )
            user.set_password(user_data["password"])
            db.add(user)
            print(
                f"✅ Created {user_data['username']} with role {user_data['role'].value}"
            )
            created_count += 1
        else:
            print(f"ℹ️  User {user_data['username']} already exists")

    db.commit()
    db.close()

    if created_count > 0:
        print(f"\n✅ Created {created_count} test users successfully")
    else:
        print("\nℹ️  All test users already exist")


if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        sys.exit(1)
