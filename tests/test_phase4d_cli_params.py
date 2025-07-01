"""Parameter validation tests for Phase 4D CLI commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from reddit_analyzer.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_auth():
    """Mock authentication for CLI commands."""
    with patch(
        "reddit_analyzer.cli.utils.auth_manager.get_stored_tokens"
    ) as mock_tokens:
        mock_tokens.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "username": "testuser",
        }
        yield mock_tokens


@pytest.fixture
def mock_db_with_subreddit():
    """Mock database with a valid subreddit."""
    with patch("reddit_analyzer.database.get_session") as mock_session:
        mock_ctx = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_ctx)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        # Mock subreddit
        test_subreddit = Mock()
        test_subreddit.id = 1
        test_subreddit.name = "test_politics"

        mock_ctx.query().filter_by().first.return_value = test_subreddit
        mock_ctx.query().filter().order_by().limit().all.return_value = []
        mock_ctx.query().filter().order_by().all.return_value = []

        yield mock_ctx


class TestParameterValidation:
    """Test parameter validation for CLI commands."""

    def test_days_parameter_validation(self, mock_auth, mock_db_with_subreddit):
        """Test validation of days parameter."""
        with patch("reddit_analyzer.services.topic_analyzer.TopicAnalyzer"):
            # Test valid days parameter
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--days", "30"]
            )
            assert result.exit_code == 0

            # Test with different values
            for days in ["7", "14", "90", "365"]:
                result = runner.invoke(
                    app, ["analyze", "topics", "test_politics", "--days", days]
                )
                assert result.exit_code == 0

            # Test invalid days (should be converted or error)
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--days", "abc"]
            )
            assert result.exit_code != 0

    def test_limit_parameter_validation(self, mock_auth, mock_db_with_subreddit):
        """Test validation of limit parameter."""
        with patch("reddit_analyzer.services.topic_analyzer.TopicAnalyzer"):
            # Test valid limit parameter
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--limit", "100"]
            )
            assert result.exit_code == 0

            # Test edge cases
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--limit", "1"]
            )
            assert result.exit_code == 0

            # Test large limit
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--limit", "10000"]
            )
            assert result.exit_code == 0

            # Test invalid limit
            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--limit", "invalid"]
            )
            assert result.exit_code != 0

    def test_topic_parameter_filtering(self, mock_auth, mock_db_with_subreddit):
        """Test topic parameter in sentiment analysis."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance

            # Test valid topics
            valid_topics = [
                "healthcare",
                "economy",
                "climate",
                "immigration",
                "education",
            ]
            for topic in valid_topics:
                result = runner.invoke(
                    app, ["analyze", "sentiment", "test_politics", "--topic", topic]
                )
                assert result.exit_code == 0

            # Test case insensitive
            result = runner.invoke(
                app, ["analyze", "sentiment", "test_politics", "--topic", "HEALTHCARE"]
            )
            assert result.exit_code == 0

    def test_min_comments_threshold(self, mock_auth, mock_db_with_subreddit):
        """Test minimum comments parameter for quality analysis."""
        with patch("reddit_analyzer.services.topic_analyzer.TopicAnalyzer"):
            # Test default behavior
            result = runner.invoke(app, ["analyze", "quality", "test_politics"])
            assert result.exit_code == 0

            # Test with specific thresholds
            for threshold in ["5", "10", "20", "50"]:
                result = runner.invoke(
                    app,
                    [
                        "analyze",
                        "quality",
                        "test_politics",
                        "--min-comments",
                        threshold,
                    ],
                )
                assert result.exit_code == 0

            # Test zero threshold
            result = runner.invoke(
                app, ["analyze", "quality", "test_politics", "--min-comments", "0"]
            )
            assert result.exit_code == 0

    def test_multiple_subreddit_validation(self, mock_auth):
        """Test commands that require multiple subreddits."""
        with patch("reddit_analyzer.database.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__ = Mock(return_value=mock_ctx)
            mock_session.return_value.__exit__ = Mock(return_value=None)

            # Mock two subreddits
            sub1 = Mock()
            sub1.id = 1
            sub1.name = "politics"

            sub2 = Mock()
            sub2.id = 2
            sub2.name = "news"

            # Setup alternating returns
            mock_ctx.query().filter_by().first.side_effect = [sub1, sub2]

            result = runner.invoke(app, ["analyze", "overlap", "politics", "news"])
            assert result.exit_code == 0

            # Test with missing second subreddit
            mock_ctx.query().filter_by().first.side_effect = [sub1, None]
            result = runner.invoke(
                app, ["analyze", "overlap", "politics", "nonexistent"]
            )
            assert result.exit_code == 1

    def test_save_report_functionality(self, mock_auth, mock_db_with_subreddit):
        """Test saving reports to file."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.detect_political_topics.return_value = {
                "healthcare": 0.8,
                "economy": 0.6,
            }

            with tempfile.TemporaryDirectory() as tmpdir:
                report_path = os.path.join(tmpdir, "test_report.json")

                result = runner.invoke(
                    app, ["analyze", "topics", "test_politics", "--save", report_path]
                )
                assert result.exit_code == 0

                # Check file was created
                assert os.path.exists(report_path)

                # Verify JSON content
                with open(report_path, "r") as f:
                    data = json.load(f)
                    assert "topics" in data or "results" in data

    def test_detailed_flag_behavior(self, mock_auth, mock_db_with_subreddit):
        """Test detailed flag for dimensions analysis."""
        with patch(
            "reddit_analyzer.services.political_dimensions_analyzer.PoliticalDimensionsAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.analyze_dimensions.return_value = {
                "economic": {"left_right": 0.2, "confidence": 0.8},
                "social": {"progressive_conservative": -0.3, "confidence": 0.7},
            }

            # Test without detailed flag
            result = runner.invoke(app, ["analyze", "dimensions", "test_politics"])
            assert result.exit_code == 0

            # Test with detailed flag
            result = runner.invoke(
                app, ["analyze", "dimensions", "test_politics", "--detailed"]
            )
            assert result.exit_code == 0
            # Detailed output should have more information
            assert len(result.stdout) > 100  # Rough check for more output


class TestParameterCombinations:
    """Test various parameter combinations."""

    def test_combined_parameters(self, mock_auth, mock_db_with_subreddit):
        """Test using multiple parameters together."""
        with patch("reddit_analyzer.services.topic_analyzer.TopicAnalyzer"):
            # Test topics with days and limit
            result = runner.invoke(
                app,
                [
                    "analyze",
                    "topics",
                    "test_politics",
                    "--days",
                    "14",
                    "--limit",
                    "50",
                    "--save",
                    "report.json",
                ],
            )
            assert result.exit_code == 0

            # Test sentiment with days and topic
            result = runner.invoke(
                app,
                [
                    "analyze",
                    "sentiment",
                    "test_politics",
                    "--days",
                    "30",
                    "--topic",
                    "healthcare",
                ],
            )
            assert result.exit_code == 0

    def test_parameter_precedence(self, mock_auth, mock_db_with_subreddit):
        """Test parameter precedence and defaults."""
        with patch("reddit_analyzer.services.topic_analyzer.TopicAnalyzer"):
            # Test that explicit parameters override defaults
            result = runner.invoke(app, ["analyze", "topics", "test_politics"])
            assert result.exit_code == 0
            # Should use default 30 days

            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--days", "7"]
            )
            assert result.exit_code == 0
            # Should use specified 7 days
