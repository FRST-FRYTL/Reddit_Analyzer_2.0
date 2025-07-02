"""Phase 4D CLI tests using real database data."""

import pytest
from typer.testing import CliRunner
from reddit_analyzer.cli.main import app
from reddit_analyzer.cli.utils.auth_manager import cli_auth
import json
import tempfile
import os

runner = CliRunner()


@pytest.fixture(scope="module")
def authenticated_session():
    """Ensure authentication for the test session."""
    # Login at the start
    cli_auth.login("user_test", "user123")
    yield
    # Logout at the end
    cli_auth.logout()


@pytest.fixture
def setup_test_data(authenticated_session, test_database_with_data):
    """Use the test database with political data."""
    # The test_database_with_data fixture already creates all needed data
    yield


class TestAnalyzeCommandsWithRealData:
    """Test analyze commands with real database data."""

    def test_analyze_topics_command(self, setup_test_data):
        """Test the analyze topics command with real data."""
        result = runner.invoke(
            app, ["analyze", "topics", "test_politics", "--days", "30"]
        )

        assert result.exit_code == 0
        assert "Political Topic Analysis" in result.stdout
        # Should find topics from our test data
        assert any(
            topic in result.stdout.lower()
            for topic in [
                "healthcare",
                "economy",
                "climate",
                "immigration",
                "education",
            ]
        )

    def test_analyze_sentiment_command(self, setup_test_data):
        """Test sentiment analysis with real data."""
        result = runner.invoke(
            app, ["analyze", "sentiment", "test_politics", "--topic", "healthcare"]
        )

        assert result.exit_code == 0
        assert "Sentiment Analysis" in result.stdout
        assert "positive" in result.stdout.lower()
        assert "negative" in result.stdout.lower()

    def test_analyze_quality_command(self, setup_test_data):
        """Test quality analysis with real data."""
        result = runner.invoke(app, ["analyze", "quality", "test_politics"])

        assert result.exit_code == 0
        assert "Discussion Quality" in result.stdout
        # Check for quality metrics
        assert any(
            metric in result.stdout.lower()
            for metric in ["overall", "civility", "constructive"]
        )

    def test_analyze_overlap_command(self, setup_test_data):
        """Test overlap analysis between subreddits."""
        result = runner.invoke(
            app, ["analyze", "overlap", "test_politics", "test_conservative"]
        )

        assert result.exit_code == 0
        assert "Community Overlap Analysis" in result.stdout

    def test_analyze_dimensions_command(self, setup_test_data):
        """Test political dimensions analysis."""
        result = runner.invoke(app, ["analyze", "dimensions", "test_politics"])

        assert result.exit_code == 0
        assert "Political Dimensions" in result.stdout
        assert "economic" in result.stdout.lower()
        assert "social" in result.stdout.lower()

    def test_analyze_political_compass_command(self, setup_test_data):
        """Test political compass visualization."""
        result = runner.invoke(app, ["analyze", "political-compass", "test_politics"])

        assert result.exit_code == 0
        assert "Political Compass" in result.stdout

    def test_analyze_political_diversity_command(self, setup_test_data):
        """Test political diversity analysis."""
        result = runner.invoke(app, ["analyze", "political-diversity", "test_politics"])

        assert result.exit_code == 0
        assert "Political Diversity" in result.stdout

    def test_save_report_functionality(self, setup_test_data):
        """Test saving analysis results to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--save", output_file]
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)
            assert f"Report saved to {output_file}" in result.stdout

            # Verify JSON content
            with open(output_file, "r") as f:
                data = json.load(f)
                assert "subreddit" in data
                assert data["subreddit"] == "test_politics"
                assert "posts_analyzed" in data
                assert data["posts_analyzed"] > 0
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_multiple_subreddit_analysis(self, setup_test_data):
        """Test analyzing multiple subreddits."""
        result = runner.invoke(
            app,
            ["analyze", "topics", "test_politics,test_conservative", "--days", "30"],
        )

        # Should handle comma-separated subreddits
        assert result.exit_code == 0
        assert "test_politics" in result.stdout
        assert "test_conservative" in result.stdout

    def test_parameter_combinations(self, setup_test_data):
        """Test various parameter combinations."""
        # Test with days and limit
        result = runner.invoke(
            app, ["analyze", "topics", "test_politics", "--days", "7", "--limit", "10"]
        )
        assert result.exit_code == 0

        # Test with topic filter
        result = runner.invoke(
            app,
            [
                "analyze",
                "sentiment",
                "test_politics",
                "--topic",
                "healthcare",
                "--days",
                "30",
            ],
        )
        assert result.exit_code == 0


class TestErrorHandlingWithRealData:
    """Test error cases with real data setup."""

    def test_nonexistent_subreddit(self, authenticated_session):
        """Test error for non-existent subreddit."""
        result = runner.invoke(
            app, ["analyze", "topics", "this_subreddit_does_not_exist"]
        )

        assert result.exit_code == 1
        assert "not found in database" in result.stdout
        assert "reddit-analyzer data collect" in result.stdout

    def test_invalid_topic_filter(self, setup_test_data):
        """Test error for invalid topic filter."""
        result = runner.invoke(
            app,
            ["analyze", "sentiment", "test_politics", "--topic", "nonexistent_topic"],
        )

        # Should either show no data or handle gracefully
        assert result.exit_code in [0, 1]
        if result.exit_code == 1:
            assert (
                "no data" in result.stdout.lower()
                or "not found" in result.stdout.lower()
            )

    def test_authentication_required(self):
        """Test that commands require authentication."""
        # Temporarily logout
        cli_auth.logout()

        result = runner.invoke(app, ["analyze", "topics", "test_politics"])

        assert result.exit_code == 1
        assert (
            "Not authenticated" in result.stdout
            or "authentication" in result.stdout.lower()
        )

        # Re-login for other tests
        cli_auth.login("user_test", "user123")
