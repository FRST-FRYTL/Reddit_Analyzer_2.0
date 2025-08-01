"""Basic CLI tests for Phase 4D political analysis commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from contextlib import contextmanager


# Mock get_session before importing
@contextmanager
def mock_get_session():
    """Mock session context manager."""
    session = MagicMock()
    yield session


# Patch get_session at module level
with patch("reddit_analyzer.database.get_session", mock_get_session):
    from reddit_analyzer.cli.main import app
    from reddit_analyzer.models import Subreddit, Post, Comment

runner = CliRunner()


@pytest.fixture(autouse=True)
def enable_auth_test_mode():
    """Enable test mode for all tests in this module."""
    # Import and modify the global cli_auth instance
    from reddit_analyzer.cli.utils import auth_manager

    # Save original state
    original_skip_auth = getattr(auth_manager.cli_auth, "skip_auth", False)

    # Enable skip_auth on the existing instance
    auth_manager.cli_auth.skip_auth = True

    # Patch all CLI modules that might have already imported cli_auth
    import sys

    cli_modules = [
        "reddit_analyzer.cli.analyze",
        "reddit_analyzer.cli.admin",
        "reddit_analyzer.cli.data",
        "reddit_analyzer.cli.nlp",
        "reddit_analyzer.cli.reports",
        "reddit_analyzer.cli.visualization",
        "reddit_analyzer.cli.auth",
    ]

    for module_name in cli_modules:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, "cli_auth"):
                module.cli_auth.skip_auth = True

    yield

    # Restore original state
    auth_manager.cli_auth.skip_auth = original_skip_auth
    for module_name in cli_modules:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, "cli_auth"):
                module.cli_auth.skip_auth = original_skip_auth


@pytest.fixture
def mock_auth():
    """Mock authentication for CLI commands - now simplified since test mode is enabled."""
    # No longer need complex mocking - test mode handles it
    yield


@pytest.fixture
def mock_db_session():
    """Mock database session with test data."""
    with patch("reddit_analyzer.database.get_session") as mock_get_session:
        # Create mock session context manager
        mock_ctx = MagicMock()
        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_ctx)
        mock_session.__exit__ = Mock(return_value=None)
        mock_get_session.return_value = mock_session

        # Create test subreddit
        test_subreddit = Mock(spec=Subreddit)
        test_subreddit.id = 1
        test_subreddit.name = "test_politics"

        # Create test posts
        test_posts = []
        for i in range(5):
            post = Mock(spec=Post)
            post.id = i
            post.title = f"Political discussion {i}"
            post.selftext = f"This is about healthcare policy and economic reform {i}"
            post.created_utc = datetime.utcnow() - timedelta(days=i)
            post.score = 100 - i * 10
            post.subreddit_id = 1
            test_posts.append(post)

        # Setup query mocks to handle different query patterns
        def query_side_effect(model):
            query_mock = Mock()

            if model == Subreddit:
                # For Subreddit queries
                query_mock.filter_by.return_value.first.return_value = test_subreddit
            elif model == Post:
                # For Post queries
                filter_mock = Mock()
                filter_mock.order_by.return_value.limit.return_value.all.return_value = test_posts
                filter_mock.order_by.return_value.all.return_value = test_posts
                query_mock.filter.return_value = filter_mock
            elif model == Comment:
                # For Comment queries
                query_mock.filter.return_value.all.return_value = []

            return query_mock

        mock_ctx.query.side_effect = query_side_effect

        yield mock_ctx, test_subreddit, test_posts


class TestAnalyzeCommands:
    """Test analyze command group."""

    def test_analyze_topics_command(self, mock_auth, mock_db_session):
        """Test the analyze topics command."""
        mock_ctx, test_subreddit, test_posts = mock_db_session

        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            # Setup mock analyzer
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance

            # Mock detect_topics to process the posts
            def mock_detect_topics(posts):
                # Return topics based on the actual mock posts
                return {
                    "healthcare": 0.8,
                    "economy": 0.6,
                    "environment": 0.3,
                }

            mock_instance.detect_political_topics.side_effect = mock_detect_topics

            result = runner.invoke(
                app, ["analyze", "topics", "test_politics", "--days", "7"]
            )

            # Check command executed successfully
            if result.exit_code != 0:
                print(f"Error output: {result.stdout}")
            assert result.exit_code == 0

            # Use flexible matching for output validation
            assert "Political Topic Analysis" in result.stdout
            assert any(
                x in result.stdout.lower()
                for x in ["healthcare", "health care", "health"]
            )
            assert any(x in result.stdout.lower() for x in ["economy", "economic"])
            assert "Posts analyzed:" in result.stdout

    def test_analyze_sentiment_command(self, mock_auth, mock_db_session):
        """Test the analyze sentiment command."""
        mock_ctx, test_subreddit, test_posts = mock_db_session

        with patch(
            "reddit_analyzer.services.topic_analyzer.TopicAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance

            # Mock to return sentiment data
            mock_instance.analyze_topic_sentiment.return_value = {
                "positive": 0.4,
                "negative": 0.3,
                "neutral": 0.3,
                "compound": 0.1,
                "posts_analyzed": len(test_posts),
            }

            result = runner.invoke(
                app, ["analyze", "sentiment", "test_politics", "--topic", "healthcare"]
            )

            assert result.exit_code == 0
            # Flexible output matching
            assert any(
                x in result.stdout
                for x in ["Sentiment Analysis", "sentiment analysis", "Sentiment"]
            )
            assert any(
                x in result.stdout.lower() for x in ["positive", "negative", "neutral"]
            )

    def test_analyze_quality_command(self, mock_auth, mock_db_session):
        """Test the analyze quality command."""
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

    def test_analyze_overlap_command(self, mock_auth, mock_db_session):
        """Test the analyze overlap command."""
        # Mock second subreddit
        mock_ctx, _, _ = mock_db_session
        test_subreddit2 = Mock(spec=Subreddit)
        test_subreddit2.id = 2
        test_subreddit2.name = "test_news"

        # Update mock to handle multiple subreddit queries
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                return Mock(
                    first=Mock(return_value=mock_ctx.query().filter_by().first())
                )
            else:
                return Mock(first=Mock(return_value=test_subreddit2))

        mock_ctx.query().filter_by.side_effect = side_effect

        result = runner.invoke(
            app, ["analyze", "overlap", "test_politics", "test_news"]
        )

        assert result.exit_code == 0
        assert "Community Overlap Analysis" in result.stdout

    def test_analyze_dimensions_command(self, mock_auth, mock_db_session):
        """Test the analyze dimensions command."""
        with patch(
            "reddit_analyzer.services.political_dimensions_analyzer.PoliticalDimensionsAnalyzer"
        ) as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            # Mock the analyze_political_dimensions method
            from reddit_analyzer.services.political_dimensions_analyzer import (
                PoliticalAnalysisResult,
            )

            mock_result = Mock(spec=PoliticalAnalysisResult)
            mock_result.dimensions = {
                "economic": {
                    "score": 0.2,
                    "confidence": 0.8,
                    "evidence": [],
                    "label": "Mixed Economy",
                },
                "social": {
                    "score": -0.3,
                    "confidence": 0.7,
                    "evidence": [],
                    "label": "Moderately Progressive",
                },
                "governance": {
                    "score": 0.1,
                    "confidence": 0.6,
                    "evidence": [],
                    "label": "Balanced Governance",
                },
            }
            mock_result.dominant_topics = {"healthcare": 0.5, "economy": 0.3}
            mock_result.analysis_quality = 0.7
            mock_instance.analyze_political_dimensions.return_value = mock_result

            result = runner.invoke(app, ["analyze", "dimensions", "test_politics"])

            assert result.exit_code == 0
            assert "Political Dimensions" in result.stdout

    def test_analyze_political_compass_command(self, mock_auth, mock_db_session):
        """Test the analyze political-compass command."""
        mock_ctx, test_subreddit, test_posts = mock_db_session

        # Mock the SubredditPoliticalDimensions query
        from reddit_analyzer.models import SubredditPoliticalDimensions

        mock_analysis = Mock(spec=SubredditPoliticalDimensions)
        mock_analysis.avg_economic_score = 0.3
        mock_analysis.avg_social_score = -0.4
        mock_analysis.avg_governance_score = 0.1
        mock_analysis.political_diversity_index = 0.65
        mock_analysis.avg_confidence_level = 0.75
        mock_analysis.analysis_start_date = datetime.utcnow() - timedelta(days=7)
        mock_analysis.analysis_end_date = datetime.utcnow()

        # Update the query mock to return our analysis
        def query_side_effect(model):
            query_mock = Mock()

            if model == Subreddit:
                query_mock.filter_by.return_value.first.return_value = test_subreddit
            elif model == SubredditPoliticalDimensions:
                filter_mock = Mock()
                order_mock = Mock()
                order_mock.first.return_value = mock_analysis
                filter_mock.order_by.return_value = order_mock
                query_mock.filter.return_value = filter_mock
            else:
                # Default behavior for other models
                query_mock.filter_by.return_value.first.return_value = None

            return query_mock

        mock_ctx.query.side_effect = query_side_effect

        result = runner.invoke(app, ["analyze", "political-compass", "test_politics"])

        assert result.exit_code == 0
        assert "Political Compass" in result.stdout

    def test_analyze_political_diversity_command(self, mock_auth, mock_db_session):
        """Test the analyze political-diversity command."""
        with patch(
            "reddit_analyzer.services.political_dimensions_analyzer.calculate_political_diversity"
        ) as mock_diversity:
            mock_diversity.return_value = {
                "diversity_index": 0.73,
                "dominant_views": ["center-left", "progressive"],
                "echo_chamber_score": 0.25,
            }

            result = runner.invoke(
                app, ["analyze", "political-diversity", "test_politics"]
            )

            assert result.exit_code == 0
            assert "Political Diversity" in result.stdout

    def test_help_text_for_each_command(self):
        """Test help text is available for all commands."""
        commands = [
            ["analyze", "topics", "--help"],
            ["analyze", "sentiment", "--help"],
            ["analyze", "quality", "--help"],
            ["analyze", "overlap", "--help"],
            ["analyze", "dimensions", "--help"],
            ["analyze", "political-compass", "--help"],
            ["analyze", "political-diversity", "--help"],
        ]

        for cmd in commands:
            result = runner.invoke(app, cmd)
            assert result.exit_code == 0
            assert "Usage:" in result.stdout
            assert "Options" in result.stdout  # Rich uses ╭─ Options ─╮


class TestErrorHandling:
    """Test error handling in CLI commands."""

    def test_nonexistent_subreddit_error(self, mock_auth):
        """Test error when subreddit doesn't exist."""
        with patch("reddit_analyzer.database.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__ = Mock(return_value=mock_ctx)
            mock_session.return_value.__exit__ = Mock(return_value=None)

            # Mock query to return None (subreddit not found)
            mock_query = Mock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_ctx.query.return_value = mock_query

            result = runner.invoke(app, ["analyze", "topics", "nonexistent_sub"])

            assert result.exit_code == 1
            assert "not found" in result.stdout.lower()
            assert any(
                x in result.stdout
                for x in ["reddit-analyzer data collect", "data collect"]
            )

    def test_authentication_required_error(self):
        """Test error when not authenticated."""
        # Temporarily disable test mode to test authentication
        from reddit_analyzer.cli.utils import auth_manager

        original_skip_auth = auth_manager.cli_auth.skip_auth
        auth_manager.cli_auth.skip_auth = False

        try:
            with patch(
                "reddit_analyzer.cli.utils.auth_manager.get_stored_tokens"
            ) as mock_tokens:
                mock_tokens.return_value = None

                result = runner.invoke(app, ["analyze", "topics", "test_politics"])

                assert result.exit_code == 1
                assert (
                    "Not authenticated" in result.stdout
                    or "authentication" in result.stdout.lower()
                )
        finally:
            # Restore test mode
            auth_manager.cli_auth.skip_auth = original_skip_auth
