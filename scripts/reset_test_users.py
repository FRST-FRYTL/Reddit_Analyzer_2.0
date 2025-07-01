#!/usr/bin/env python3
"""Reset passwords for test users."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session  # noqa: E402
from reddit_analyzer.database import SessionLocal  # noqa: E402
from reddit_analyzer.models.user import User, UserRole  # noqa: E402

# Test user credentials
TEST_USERS = {
    "testuser": {"password": "testpass123", "role": UserRole.USER},
    "testmod": {"password": "modpass123", "role": UserRole.MODERATOR},
    "testadmin": {"password": "adminpass123", "role": UserRole.ADMIN},
}


def reset_test_users(db: Session):
    """Reset passwords and roles for test users."""
    print("Resetting test user passwords and roles...\n")

    for username, info in TEST_USERS.items():
        user = db.query(User).filter_by(username=username).first()

        if not user:
            print(f"❌ User '{username}' not found in database")
            continue

        # Update password and role
        user.set_password(info["password"])
        user.role = info["role"]
        user.is_active = True
        user.is_verified = True

        print(f"✅ Reset user '{username}':")
        print(f"   New password: {info['password']}")
        print(f"   Role: {info['role'].value}")

    # Commit changes
    db.commit()
    print("\nAll changes committed successfully!")


def main():
    """Main function."""
    # Create database session
    db = SessionLocal()

    try:
        reset_test_users(db)
    except Exception as e:
        print(f"Error resetting test users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
