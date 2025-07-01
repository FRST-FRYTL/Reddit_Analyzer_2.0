"""CLI output validation tests for Phase 4D."""

import pytest
import json
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from reddit_analyzer.cli.main import app
from reddit_analyzer.models import Subreddit

runner = CliRunner()


@pytest.fixture
def mock_auth():
    """Mock authentication."""
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
def mock_db_and_analyzer():
    """Mock database and analyzers."""
    with patch("reddit_analyzer.database.get_session") as mock_session:
        # Setup database mock
        mock_ctx = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_ctx)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        # Mock subreddit
        test_subreddit = Mock(spec=Subreddit)
        test_subreddit.id = 1
        test_subreddit.name = "test_politics"

        mock_ctx.query().filter_by().first.return_value = test_subreddit
        mock_ctx.query().filter().order_by().limit().all.return_value = []
        mock_ctx.query().filter().order_by().all.return_value = []

        yield mock_ctx, test_subreddit


class TestCLIOutputFormats:
    """Test CLI output formatting."""

    def test_topics_json_output(self, mock_auth, mock_db_and_analyzer):
        """Test topics command JSON output."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.detect_political_topics.return_value = {
                "healthcare": 0.8,
                "economy": 0.6,
                "environment": 0.3,
            }

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                output_file = f.name

            try:
                result = runner.invoke(
                    app, ["analyze", "topics", "test_politics", "--save", output_file]
                )

                assert result.exit_code == 0
                assert os.path.exists(output_file)

                # Validate JSON structure
                with open(output_file, "r") as f:
                    data = json.load(f)
                    assert "subreddit" in data
                    assert "topics" in data
                    assert "healthcare" in data["topics"]
                    assert data["topics"]["healthcare"] == 0.8
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def test_sentiment_visualization(self, mock_auth, mock_db_and_analyzer):
        """Test sentiment command visualization output."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.analyze_topic_sentiment.return_value = {
                "positive": 0.4,
                "negative": 0.3,
                "neutral": 0.3,
                "compound": 0.1,
            }

            result = runner.invoke(
                app, ["analyze", "sentiment", "test_politics", "--topic", "healthcare"]
            )

            assert result.exit_code == 0
            # Check for visualization elements
            assert "Sentiment" in result.stdout
            assert "positive" in result.stdout.lower()
            assert "negative" in result.stdout.lower()
            assert "neutral" in result.stdout.lower()

    def test_quality_metrics_table(self, mock_auth, mock_db_and_analyzer):
        """Test quality command table output."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.calculate_discussion_quality.return_value = {
                "constructiveness": 0.75,
                "toxicity": 0.15,
                "engagement": 0.80,
                "overall_quality": 0.70,
            }

            result = runner.invoke(app, ["analyze", "quality", "test_politics"])

            assert result.exit_code == 0
            assert "Discussion Quality" in result.stdout
            assert (
                "constructiveness" in result.stdout.lower() or "0.75" in result.stdout
            )
            assert "toxicity" in result.stdout.lower() or "0.15" in result.stdout

    def test_dimensions_radar_chart(self, mock_auth, mock_db_and_analyzer):
        """Test dimensions command radar chart output."""
        with patch(
            "reddit_analyzer.services.political_dimensions_analyzer.PoliticalDimensionsAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.analyze_political_dimensions.return_value = Mock(
                dimensions={
                    "economic": {
                        "position": 0.2,
                        "confidence": 0.8,
                        "evidence": ["test"],
                    },
                    "social": {
                        "position": -0.3,
                        "confidence": 0.7,
                        "evidence": ["test"],
                    },
                    "governance": {
                        "position": 0.1,
                        "confidence": 0.6,
                        "evidence": ["test"],
                    },
                },
                dominant_topics={"healthcare": 0.5},
                analysis_quality=0.75,
            )

            result = runner.invoke(app, ["analyze", "dimensions", "test_politics"])

            assert result.exit_code == 0
            assert "economic" in result.stdout.lower()
            assert "social" in result.stdout.lower()

    def test_political_compass_plot(self, mock_auth, mock_db_and_analyzer):
        """Test political compass visualization."""
        with patch(
            "reddit_analyzer.services.political_dimensions_analyzer.PoliticalDimensionsAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance

            # Mock the analysis result
            mock_analysis_result = Mock()
            mock_analysis_result.dimensions = {
                "economic": {"position": 0.3, "confidence": 0.8},
                "social": {"position": -0.4, "confidence": 0.7},
            }
            mock_instance.analyze_political_dimensions.return_value = (
                mock_analysis_result
            )

            result = runner.invoke(
                app, ["analyze", "political-compass", "test_politics"]
            )

            assert result.exit_code == 0
            assert (
                "Political Compass" in result.stdout
                or "compass" in result.stdout.lower()
            )

    def test_save_report_formats(self, mock_auth, mock_db_and_analyzer):
        """Test saving reports in different formats."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.detect_political_topics.return_value = {
                "healthcare": 0.8,
                "economy": 0.6,
            }

            # Test JSON format
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json_file = f.name

            try:
                result = runner.invoke(
                    app, ["analyze", "topics", "test_politics", "--save", json_file]
                )

                assert result.exit_code == 0
                assert os.path.exists(json_file)

                # Validate it's valid JSON
                with open(json_file, "r") as f:
                    data = json.load(f)
                    assert isinstance(data, dict)
            finally:
                if os.path.exists(json_file):
                    os.unlink(json_file)


class TestOutputContent:
    """Test the content of CLI outputs."""

    def test_error_messages_formatting(self, mock_auth):
        """Test error message formatting."""
        with patch("reddit_analyzer.database.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__ = Mock(return_value=mock_ctx)
            mock_session.return_value.__exit__ = Mock(return_value=None)

            # Mock subreddit not found
            mock_ctx.query().filter_by().first.return_value = None

            result = runner.invoke(app, ["analyze", "topics", "nonexistent"])

            assert result.exit_code == 1
            assert "not found" in result.stdout.lower()
            assert "reddit-analyzer data collect" in result.stdout

    def test_progress_indicators(self, mock_auth, mock_db_and_analyzer):
        """Test that progress indicators are shown."""
        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            mock_instance.detect_political_topics.return_value = {"test": 0.5}

            result = runner.invoke(app, ["analyze", "topics", "test_politics"])

            assert result.exit_code == 0
            # Should show some kind of progress or processing indicator
            assert "Analyzing" in result.stdout or "Fetching" in result.stdout

    def test_help_text_formatting(self):
        """Test help text is properly formatted."""
        result = runner.invoke(app, ["analyze", "topics", "--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "--days" in result.stdout
        assert "--limit" in result.stdout
        assert "Analyze political topics" in result.stdout
