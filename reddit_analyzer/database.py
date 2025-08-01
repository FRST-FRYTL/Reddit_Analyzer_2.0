"""Database configuration and connection management."""

from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis

from reddit_analyzer.config import get_config

config = get_config()

# SQLAlchemy setup
engine = create_engine(
    config.DATABASE_URL,
    poolclass=StaticPool,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
    ),
    echo=False,  # Disable SQLAlchemy echo - use logging config instead
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(config.REDIS_URL)

# Metadata for migrations
metadata = MetaData()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Get Redis client."""
    return redis_client


def create_tables():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables."""
    Base.metadata.drop_all(bind=engine)


@contextmanager
def get_session():
    """Get database session as a context manager for CLI usage."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
