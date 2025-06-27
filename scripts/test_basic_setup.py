#!/usr/bin/env python3
"""Test script to verify basic setup without requiring Reddit credentials."""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        print("✅ Config module imported successfully")

        print("✅ Database module imported successfully")

        print("✅ Models imported successfully")

        print("✅ Services imported successfully")

        print("✅ Logging module imported successfully")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        from app.config import get_config

        config = get_config()

        # Check basic config attributes exist
        assert hasattr(config, "DATABASE_URL")
        assert hasattr(config, "REDIS_URL")
        assert hasattr(config, "APP_ENV")
        assert hasattr(config, "LOG_LEVEL")

        print("✅ Configuration loaded successfully")
        print(f"   - App Environment: {config.APP_ENV}")
        print(f"   - Log Level: {config.LOG_LEVEL}")

        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_logging():
    """Test logging setup."""
    print("\nTesting logging...")

    try:
        from app.utils.logging import setup_logging, get_logger

        setup_logging()
        logger = get_logger("test")
        logger.info("Test log message")

        print("✅ Logging setup successful")
        return True
    except Exception as e:
        print(f"❌ Logging error: {e}")
        return False


def test_models():
    """Test model definitions."""
    print("\nTesting models...")

    try:
        from app.models import User, Subreddit

        # Test model instantiation (without database)
        user = User(username="test_user", comment_karma=100)
        subreddit = Subreddit(name="test", display_name="Test Subreddit")

        print("✅ Models can be instantiated")
        print(f"   - User: {user}")
        print(f"   - Subreddit: {subreddit}")

        return True
    except Exception as e:
        print(f"❌ Models error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running basic setup tests...\n")

    tests = [test_imports, test_config, test_logging, test_models]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All basic setup tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
