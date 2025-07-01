#!/usr/bin/env python3
"""Verify test users can authenticate properly."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session  # noqa: E402
from reddit_analyzer.database import SessionLocal  # noqa: E402
from reddit_analyzer.models.user import User  # noqa: E402

# Test user credentials
TEST_CREDENTIALS = [
    ("testuser", "testpass123"),
    ("testmod", "modpass123"),
    ("testadmin", "adminpass123"),
]


def verify_test_users(db: Session):
    """Verify test users can authenticate."""
    print("Verifying test user authentication...\n")

    for username, password in TEST_CREDENTIALS:
        user = db.query(User).filter_by(username=username).first()

        if not user:
            print(f"❌ User '{username}' not found in database")
            continue

        # Verify password
        if user.verify_password(password):
            print(f"✅ User '{username}' authenticated successfully")
            print(f"   Role: {user.role.value}")
            print(f"   Email: {user.email}")
            print(f"   Active: {user.is_active}")
            print(f"   Karma: {user.comment_karma} comment / {user.link_karma} link")
        else:
            print(f"❌ User '{username}' failed authentication")

        print()


def main():
    """Main function."""
    # Create database session
    db = SessionLocal()

    try:
        verify_test_users(db)
    except Exception as e:
        print(f"Error verifying test users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
