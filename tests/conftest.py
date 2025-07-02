"""Pytest configuration and fixtures."""

import os
import glob
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models first to ensure they're registered with Base
from reddit_analyzer.models import Base

# Import fixtures from fixtures directory


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    # Clean up all tables before each test
    with test_engine.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override database dependency for testing."""

    def _override_get_db():
        try:
            yield test_db
        finally:
            pass

    return _override_get_db


# Alias for compatibility with existing tests
@pytest.fixture(scope="function")
def db_session(test_db):
    """Database session fixture (alias for test_db)."""
    return test_db


def pytest_sessionfinish(session, exitstatus):
    """Clean up coverage files after test session completes."""
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Find all .coverage.* files (but not .coverage itself)
    coverage_files = glob.glob(os.path.join(root_dir, ".coverage.*"))

    # Remove each coverage file
    for coverage_file in coverage_files:
        try:
            os.remove(coverage_file)
        except OSError:
            # Ignore errors if file doesn't exist or can't be removed
            pass
