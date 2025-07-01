#!/usr/bin/env python3
"""Create test users for Reddit Analyzer CLI testing."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from reddit_analyzer.database import SessionLocal, create_tables  # noqa: E402
from reddit_analyzer.models.user import User, UserRole  # noqa: E402
from reddit_analyzer.config import get_config  # noqa: E402

# Test user definitions
TEST_USERS = [
    {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123",
        "role": UserRole.USER,
        "comment_karma": 100,
        "link_karma": 50,
    },
    {
        "username": "testmod",
        "email": "testmod@example.com",
        "password": "modpass123",
        "role": UserRole.MODERATOR,
        "comment_karma": 500,
        "link_karma": 200,
    },
    {
        "username": "testadmin",
        "email": "testadmin@example.com",
        "password": "adminpass123",
        "role": UserRole.ADMIN,
        "comment_karma": 1000,
        "link_karma": 500,
    },
]


def create_test_users(db: Session):
    """Create test users in the database."""
    created_users = []

    for user_data in TEST_USERS:
        # Check if user already exists
        existing_user = db.query(User).filter_by(username=user_data["username"]).first()
        if existing_user:
            print(f"User '{user_data['username']}' already exists, skipping...")
            continue

        # Create new user
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            comment_karma=user_data["comment_karma"],
            link_karma=user_data["link_karma"],
            is_active=True,
            is_verified=True,
            created_utc=datetime.utcnow(),
        )

        # Set password using the model's method
        user.set_password(user_data["password"])

        # Add to session
        db.add(user)
        created_users.append(user)

        print(f"Created user: {user.username} (role: {user.role.value})")

    # Commit all changes
    db.commit()

    return created_users


def main():
    """Main function."""
    print("Creating test users for Reddit Analyzer CLI testing...")
    print(f"Using database: {get_config().DATABASE_URL}")

    # Create tables if they don't exist
    print("\nEnsuring database tables exist...")
    create_tables()

    # Create database session
    db = SessionLocal()

    try:
        # Create test users
        created_users = create_test_users(db)

        if created_users:
            print(f"\nSuccessfully created {len(created_users)} test users!")
            print("\nTest user credentials:")
            for user_data in TEST_USERS:
                print(
                    f"  - Username: {user_data['username']}, Password: {user_data['password']}, Role: {user_data['role'].value}"
                )
        else:
            print("\nNo new users created (all users already exist)")

        # Verify users were created
        print("\nVerifying users in database:")
        all_users = (
            db.query(User)
            .filter(User.username.in_([u["username"] for u in TEST_USERS]))
            .all()
        )

        for user in all_users:
            print(f"  - {user}")

    except Exception as e:
        print(f"\nError creating test users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
