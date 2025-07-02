"""Basic CLI tests for Phase 4D political analysis commands using real data."""

import pytest
from typer.testing import CliRunner
import json

from reddit_analyzer.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def use_real_test_db(real_reddit_db, monkeypatch):
    """Use real Reddit test data for all tests in this module."""

    # Monkey patch get_session to use our test database
    def mock_get_session():
        return real_reddit_db

    monkeypatch.setattr("reddit_analyzer.database.get_session", mock_get_session)

    # Also patch it in all CLI modules
    cli_modules = [
        "reddit_analyzer.cli.analyze",
        "reddit_analyzer.cli.data",
        "reddit_analyzer.cli.visualization",
    ]

    for module_name in cli_modules:
        try:
            import importlib

            importlib.import_module(module_name)
            monkeypatch.setattr(f"{module_name}.get_session", mock_get_session)
        except ImportError:
            pass


@pytest.fixture(autouse=True)
def enable_auth_test_mode():
    """Enable test mode for authentication."""
    from reddit_analyzer.cli.utils import auth_manager

    original_skip_auth = auth_manager.cli_auth.skip_auth
    auth_manager.cli_auth.skip_auth = True

    yield

    auth_manager.cli_auth.skip_auth = original_skip_auth


class TestAnalyzeCommandsWithRealData:
    """Test analyze commands with real Reddit data."""

    def test_analyze_topics_command(
        self, real_reddit_db, expected_topics, political_subreddits
    ):
        """Test topics analysis with real data."""
        # Use the first political subreddit from our test data
        subreddit = political_subreddits[0]

        # Use 365 days to ensure we capture all test data
        result = runner.invoke(app, ["analyze", "topics", subreddit, "--days", "365"])

        # Basic assertions
        assert result.exit_code == 0
        assert "Political Topic Analysis" in result.stdout
        assert f"r/{subreddit}" in result.stdout
        assert "Posts analyzed:" in result.stdout

        # Check that some expected topics appear
        output_lower = result.stdout.lower()
        topics_found = [topic for topic in expected_topics if topic in output_lower]
        assert len(topics_found) > 0, (
            f"Expected at least one topic from {expected_topics}"
        )

        # Check for reasonable metrics
        assert "%" in result.stdout  # Prevalence percentages
        assert "0." in result.stdout  # Confidence scores

    def test_analyze_sentiment_command(self, real_reddit_db, political_subreddits):
        """Test sentiment analysis with real data."""
        subreddit = political_subreddits[0]

        result = runner.invoke(
            app,
            [
                "analyze",
                "sentiment",
                subreddit,
                "--topic",
                "healthcare",
                "--days",
                "365",
            ],
        )

        assert result.exit_code == 0
        # Either shows sentiment analysis or indicates no data for topic
        assert ("Sentiment" in result.stdout) or (
            "No significant discussions" in result.stdout
        )

    def test_analyze_quality_command(self, real_reddit_db, political_subreddits):
        """Test discussion quality analysis with real data."""
        subreddit = political_subreddits[0]

        result = runner.invoke(app, ["analyze", "quality", subreddit, "--days", "365"])

        assert result.exit_code == 0
        assert "Discussion Quality" in result.stdout

        # Should show some posts in the quality table
        if "Posts analyzed:" in result.stdout:
            # Extract post count
            import re

            match = re.search(r"Posts analyzed:\s*(\d+)", result.stdout)
            if match and int(match.group(1)) > 0:
                # Should have quality metrics
                assert any(
                    metric in result.stdout.lower()
                    for metric in [
                        "constructiveness",
                        "civility",
                        "quality",
                        "engagement",
                    ]
                )

    def test_analyze_dimensions_command(self, real_reddit_db, political_subreddits):
        """Test political dimensions analysis with real data."""
        subreddit = political_subreddits[0]

        # Use a large date range to ensure we capture our test data
        result = runner.invoke(
            app, ["analyze", "dimensions", subreddit, "--days", "365"]
        )

        assert result.exit_code == 0
        assert "Political Dimensions" in result.stdout

        # If we have posts analyzed, check for dimension names
        if "Posts analyzed: 0" not in result.stdout:
            dimensions = ["economic", "social", "governance"]
            for dim in dimensions:
                assert dim in result.stdout.lower()
        else:
            # Just check that the output is formatted correctly even with no data
            assert "Average Political Positions" in result.stdout
            assert "Diversity Metrics" in result.stdout

    def test_analyze_political_diversity_command(
        self, real_reddit_db, political_subreddits
    ):
        """Test political diversity analysis with real data."""
        subreddit = political_subreddits[0]

        result = runner.invoke(
            app, ["analyze", "political-diversity", subreddit, "--days", "365"]
        )

        assert result.exit_code == 0
        assert "Political Diversity" in result.stdout
        assert "diversity" in result.stdout.lower()

    def test_save_report_functionality(
        self, real_reddit_db, political_subreddits, tmp_path
    ):
        """Test saving analysis reports."""
        subreddit = political_subreddits[0]
        output_file = tmp_path / "test_report.json"

        result = runner.invoke(
            app,
            [
                "analyze",
                "topics",
                subreddit,
                "--days",
                "365",
                "--save",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Validate JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "subreddit" in data
            assert data["subreddit"] == subreddit
            assert "topic_distribution" in data or "topics" in data

    def test_multiple_subreddit_analysis(self, real_reddit_db, political_subreddits):
        """Test analyzing multiple subreddits."""
        if len(political_subreddits) < 2:
            pytest.skip("Need at least 2 subreddits for overlap test")

        sub1, sub2 = political_subreddits[:2]

        # Note: overlap command doesn't have --days option, so it uses default 30 days
        # Our test data might be older, but that's ok - we'll just check the format
        result = runner.invoke(app, ["analyze", "overlap", sub1, sub2])

        assert result.exit_code == 0
        assert "Community Overlap Analysis" in result.stdout
        assert sub1 in result.stdout
        assert sub2 in result.stdout


class TestErrorHandlingWithRealData:
    """Test error handling with real data."""

    def test_nonexistent_subreddit(self, real_reddit_db):
        """Test error when subreddit doesn't exist."""
        result = runner.invoke(app, ["analyze", "topics", "nonexistent_subreddit_xyz"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_empty_time_range(self, real_reddit_db, political_subreddits):
        """Test with time range that has no data."""
        subreddit = political_subreddits[0]

        # Use future date to ensure no data
        result = runner.invoke(app, ["analyze", "topics", subreddit, "--days", "0"])

        # Should handle gracefully
        assert result.exit_code == 0
        assert "Posts analyzed: 0" in result.stdout or "No posts found" in result.stdout


class TestParameterValidationWithRealData:
    """Test parameter validation with real data."""

    def test_limit_parameter(self, real_reddit_db, political_subreddits):
        """Test limit parameter actually limits results."""
        subreddit = political_subreddits[0]

        # Run with small limit
        result = runner.invoke(app, ["analyze", "topics", subreddit, "--limit", "5"])

        assert result.exit_code == 0

        # Extract post count if shown
        import re

        match = re.search(r"Posts analyzed:\s*(\d+)", result.stdout)
        if match:
            post_count = int(match.group(1))
            assert post_count <= 5

    def test_days_parameter(self, real_reddit_db, political_subreddits):
        """Test days parameter filters by date."""
        subreddit = political_subreddits[0]

        # Compare different day ranges
        result_7days = runner.invoke(
            app, ["analyze", "topics", subreddit, "--days", "7"]
        )
        result_30days = runner.invoke(
            app, ["analyze", "topics", subreddit, "--days", "30"]
        )

        assert result_7days.exit_code == 0
        assert result_30days.exit_code == 0

        # 30 days should analyze more or equal posts
        import re

        def extract_post_count(output):
            match = re.search(r"Posts analyzed:\s*(\d+)", output)
            return int(match.group(1)) if match else 0

        count_7days = extract_post_count(result_7days.stdout)
        count_30days = extract_post_count(result_30days.stdout)

        assert count_30days >= count_7days
