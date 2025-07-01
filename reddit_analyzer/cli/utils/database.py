"""CLI-specific database utilities with quiet mode support."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from reddit_analyzer.config import get_config

config = get_config()


def get_cli_engine(echo=False):
    """Get database engine with echo control for CLI."""
    return create_engine(
        config.DATABASE_URL,
        poolclass=StaticPool,
        connect_args=(
            {"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
        ),
        echo=echo,  # Control SQLAlchemy echo
    )


@contextmanager
def get_cli_session(echo=False):
    """Get database session for CLI with echo control."""
    engine = get_cli_engine(echo=echo)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
