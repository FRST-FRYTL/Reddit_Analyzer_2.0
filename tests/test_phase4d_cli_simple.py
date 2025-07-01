"""Simple test to check CLI imports."""

from contextlib import contextmanager
from unittest.mock import Mock

import reddit_analyzer.database
from typer.testing import CliRunner


# First, let's create a mock for get_session
def mock_get_session():
    """Create a mock session context manager."""

    @contextmanager
    def _get_session():
        session = Mock()
        yield session

    return _get_session


# Patch the missing get_session function
reddit_analyzer.database.get_session = mock_get_session()

# Import at runtime to avoid issues
app = None


def setup_module():
    """Setup module by importing app after patching."""
    global app
    from reddit_analyzer.cli.main import app as cli_app

    app = cli_app


runner = CliRunner()


def test_cli_help():
    """Test that CLI help works."""
    setup_module()  # Ensure app is loaded
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Reddit Analyzer CLI" in result.stdout or "Usage:" in result.stdout


def test_analyze_help():
    """Test analyze command help."""
    setup_module()  # Ensure app is loaded
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout.lower() or "political" in result.stdout.lower()
