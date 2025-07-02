"""Real Reddit data fixtures for testing."""

import pytest
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


@pytest.fixture(scope="session")
def test_data_path():
    """Path to test data database."""
    return Path(__file__).parent / "test_data.db"


@pytest.fixture(scope="session")
def test_data_manifest():
    """Load test data manifest."""
    manifest_path = Path(__file__).parent / "test_data_manifest.json"

    if not manifest_path.exists():
        pytest.skip(
            "Test data manifest not found. Run scripts/collect_test_data.py first."
        )

    with open(manifest_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def real_data_engine(test_data_path):
    """Create engine for test database."""
    if not test_data_path.exists():
        pytest.skip("Test data not found. Run scripts/collect_test_data.py first.")

    engine = create_engine(f"sqlite:///{test_data_path}")
    return engine


@pytest.fixture(scope="session")
def real_data_session_factory(real_data_engine):
    """Create session factory for test database."""
    return sessionmaker(bind=real_data_engine)


@pytest.fixture(scope="function")
def real_reddit_db(real_data_session_factory):
    """Provide session to real Reddit test data."""
    session = real_data_session_factory()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@contextmanager
def real_data_session(engine=None):
    """Context manager for real data session."""
    if engine is None:
        test_data_path = Path(__file__).parent / "test_data.db"
        engine = create_engine(f"sqlite:///{test_data_path}")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def expected_topics(test_data_manifest):
    """Expected topics from test data."""
    return [topic for topic, _ in test_data_manifest["expected_results"]["top_topics"]]


@pytest.fixture(scope="function")
def expected_metrics(test_data_manifest):
    """Expected metrics from test data."""
    return {
        "post_count": test_data_manifest["statistics"]["posts"],
        "comment_count": test_data_manifest["statistics"]["comments"],
        "user_count": test_data_manifest["statistics"]["users"],
        "avg_comments": test_data_manifest["expected_results"]["avg_comments_per_post"],
    }


@pytest.fixture(scope="function")
def political_subreddits(test_data_manifest):
    """List of political subreddits in test data."""
    return list(test_data_manifest["config"]["subreddits"].keys())


# Golden output fixtures
@pytest.fixture(scope="session")
def golden_outputs_path():
    """Path to golden outputs directory."""
    path = Path(__file__).parent / "golden_outputs"
    path.mkdir(exist_ok=True)
    return path


def load_golden_output(command: str, output_type: str = "stdout"):
    """Load golden output for a command."""
    golden_path = (
        Path(__file__).parent / "golden_outputs" / f"{command}_{output_type}.txt"
    )

    if not golden_path.exists():
        return None

    with open(golden_path) as f:
        return f.read()


def save_golden_output(command: str, output: str, output_type: str = "stdout"):
    """Save golden output for a command."""
    golden_path = Path(__file__).parent / "golden_outputs"
    golden_path.mkdir(exist_ok=True)

    output_file = golden_path / f"{command}_{output_type}.txt"

    with open(output_file, "w") as f:
        f.write(output)
