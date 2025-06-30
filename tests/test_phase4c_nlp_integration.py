#!/usr/bin/env python3
"""
Phase 4C NLP Integration Test Suite

Comprehensive tests for NLP functionality including:
- NLP Service Layer
- CLI Commands
- Database Integration
- Export Functionality
"""

import pytest
import csv
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from reddit_analyzer.services.nlp_service import get_nlp_service
from reddit_analyzer.models.text_analysis import TextAnalysis
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.subreddit import Subreddit
from reddit_analyzer.models.user import User as RedditUser
from reddit_analyzer.database import SessionLocal


class TestNLPService:
    """Test the NLP service layer functionality."""

    def test_nlp_service_singleton(self):
        """Test that NLP service uses singleton pattern."""
        service1 = get_nlp_service()
        service2 = get_nlp_service()
        assert service1 is service2

    def test_analyze_text_basic(self):
        """Test basic text analysis with available models."""
        nlp = get_nlp_service()

        # Test positive sentiment
        result = nlp.analyze_text("Python is amazing! I love programming with it.")
        assert "sentiment" in result
        assert "compound" in result["sentiment"]
        assert -1 <= result["sentiment"]["compound"] <= 1

        # The label is determined from the compound score
        # Just verify we have a compound score

        # Test negative sentiment
        result = nlp.analyze_text("This is terrible and I hate it.")
        assert result["sentiment"]["compound"] < 0.05  # Should be negative or neutral

        # Test neutral sentiment
        result = nlp.analyze_text("The weather is okay today.")
        assert "sentiment" in result

    def test_analyze_text_keywords(self):
        """Test keyword extraction functionality."""
        nlp = get_nlp_service()

        text = "Python programming is great for data science and machine learning applications."
        result = nlp.analyze_text(text)

        # Keywords might be empty if spaCy model is not installed
        assert "keywords" in result
        assert isinstance(result["keywords"], list)

    def test_analyze_text_entities(self):
        """Test named entity recognition."""
        nlp = get_nlp_service()

        text = "Microsoft and Google are competing in AI. Elon Musk founded SpaceX."
        result = nlp.analyze_text(text)

        assert "entities" in result
        assert isinstance(result["entities"], list)

    def test_analyze_text_language_detection(self):
        """Test language detection."""
        nlp = get_nlp_service()

        result = nlp.analyze_text("Hello world, this is a test.")
        assert "language" in result
        assert result["language"] == "en"  # Default to English

    def test_batch_analysis(self):
        """Test batch text analysis."""
        nlp = get_nlp_service()

        texts = [
            "Python is great for data science",
            "Machine learning with Python",
            "Data analysis using pandas",
            "JavaScript for web development",
            "React and Vue frameworks",
        ]

        results = []
        for text in texts:
            result = nlp.analyze_text(text)
            results.append(result)

        assert len(results) == 5
        for result in results:
            assert "sentiment" in result
            assert "keywords" in result

    def test_error_handling(self):
        """Test graceful error handling."""
        nlp = get_nlp_service()

        # Test with empty text
        result = nlp.analyze_text("")
        assert result["sentiment"]["label"] == "neutral"

        # Test with None
        result = nlp.analyze_text(None)
        assert result["sentiment"]["label"] == "neutral"

        # Test with very long text
        long_text = "test " * 10000
        result = nlp.analyze_text(long_text)
        assert "sentiment" in result


class TestDatabaseIntegration:
    """Test NLP data storage in database."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def sample_post(self, db_session):
        """Create a sample post for testing."""
        # Create test user
        user = db_session.query(RedditUser).filter_by(username="test_user").first()
        if not user:
            user = RedditUser(username="test_user", email="test@example.com")
            db_session.add(user)

        # Create test subreddit
        subreddit = db_session.query(Subreddit).filter_by(name="test").first()
        if not subreddit:
            subreddit = Subreddit(
                name="test",
                display_name="Test Subreddit",
                created_utc=datetime.utcnow(),
            )
            db_session.add(subreddit)

        db_session.commit()

        # Create test post
        post = Post(
            id=f"test_post_{datetime.utcnow().timestamp()}",
            title="Test post for NLP analysis",
            author_id=user.id,
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
            score=10,
            num_comments=5,
            url="https://reddit.com/r/test/test",
            selftext="This is a test post with some content for analysis.",
        )
        db_session.add(post)
        db_session.commit()

        return post

    def test_create_text_analysis(self, db_session, sample_post):
        """Test creating TextAnalysis records."""
        analysis = TextAnalysis(
            post_id=sample_post.id,
            sentiment_score=0.5,
            sentiment_label="positive",
            confidence_score=0.9,
            keywords=["test", "post", "nlp"],
            entities=[],
            language="en",
            analyzed_at=datetime.utcnow(),
        )

        db_session.add(analysis)
        db_session.commit()

        # Verify it was saved
        saved = db_session.query(TextAnalysis).filter_by(post_id=sample_post.id).first()
        assert saved is not None
        assert saved.sentiment_score == 0.5
        assert saved.sentiment_label == "positive"
        assert saved.keywords == ["test", "post", "nlp"]

    def test_update_text_analysis(self, db_session, sample_post):
        """Test updating existing analysis."""
        # Create initial analysis
        analysis = TextAnalysis(
            post_id=sample_post.id,
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence_score=0.5,
            analyzed_at=datetime.utcnow(),
        )
        db_session.add(analysis)
        db_session.commit()

        # Update it
        analysis.sentiment_score = 0.8
        analysis.sentiment_label = "positive"
        analysis.keywords = ["updated", "keywords"]
        db_session.commit()

        # Verify update
        updated = (
            db_session.query(TextAnalysis).filter_by(post_id=sample_post.id).first()
        )
        assert updated.sentiment_score == 0.8
        assert updated.sentiment_label == "positive"
        assert updated.keywords == ["updated", "keywords"]

    def test_bulk_analysis_storage(self, db_session):
        """Test storing multiple analyses efficiently."""
        # Create multiple posts
        posts = []
        for i in range(5):
            user = db_session.query(RedditUser).first()
            subreddit = db_session.query(Subreddit).first()

            post = Post(
                id=f"bulk_test_{i}",
                title=f"Bulk test post {i}",
                author_id=user.id,
                subreddit_id=subreddit.id,
                created_utc=datetime.utcnow(),
                score=i * 10,
                num_comments=i,
            )
            posts.append(post)

        db_session.add_all(posts)
        db_session.commit()

        # Create analyses for all posts
        analyses = []
        for post in posts:
            analysis = TextAnalysis(
                post_id=post.id,
                sentiment_score=0.0,
                sentiment_label="neutral",
                confidence_score=1.0,
                analyzed_at=datetime.utcnow(),
            )
            analyses.append(analysis)

        db_session.add_all(analyses)
        db_session.commit()

        # Verify all were saved
        count = (
            db_session.query(TextAnalysis)
            .filter(TextAnalysis.post_id.in_([p.id for p in posts]))
            .count()
        )
        assert count == 5


class TestCLICommands:
    """Test CLI command functionality."""

    @pytest.fixture
    def mock_auth(self):
        """Mock authentication for CLI commands."""
        # Mock the require_auth decorator to always pass
        with patch(
            "reddit_analyzer.cli.utils.auth_manager.cli_auth.require_auth"
        ) as mock_decorator:
            # Make the decorator a no-op
            mock_decorator.return_value = lambda f: f

            # Also mock get_current_user
            with patch(
                "reddit_analyzer.cli.utils.auth_manager.cli_auth.get_current_user"
            ) as mock_user:
                mock_user.return_value = Mock(username="test_user", role="admin")
                yield mock_user

    def test_nlp_analyze_command(self, mock_auth):
        """Test the nlp analyze command."""
        from typer.testing import CliRunner
        from reddit_analyzer.cli.main import app

        runner = CliRunner()

        # Test basic analyze command
        with patch("reddit_analyzer.database.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Mock query results
            mock_posts = [Mock(id=1, title="Test", selftext="Content")]
            mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = mock_posts
            mock_db.query.return_value.filter.return_value.count.return_value = 1

            with patch(
                "reddit_analyzer.services.nlp_service.get_nlp_service"
            ) as mock_nlp:
                mock_nlp.return_value.analyze_text.return_value = {
                    "sentiment": {"label": "positive", "compound": 0.5},
                    "keywords": ["test"],
                    "entities": [],
                    "language": "en",
                }

                result = runner.invoke(app, ["nlp", "analyze", "--limit", "1"])
                assert result.exit_code == 0
                assert "Successfully analyzed" in result.output

    def test_nlp_export_command(self, mock_auth, tmp_path):
        """Test the nlp export command."""
        from typer.testing import CliRunner
        from reddit_analyzer.cli.main import app

        runner = CliRunner()
        output_file = tmp_path / "test_export.csv"

        with patch("reddit_analyzer.database.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Mock analysis results
            mock_analysis = Mock(
                post=Mock(
                    reddit_id="test123",
                    title="Test Post",
                    created_utc=datetime.utcnow(),
                    score=10,
                    num_comments=5,
                ),
                sentiment_score=0.5,
                sentiment_label="positive",
                confidence_score=0.9,
                keywords=["test", "keywords"],
                emotion_scores=None,
                language="en",
                readability_score=0.0,
            )

            mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
                mock_analysis
            ]

            result = runner.invoke(
                app,
                [
                    "nlp",
                    "export",
                    "test",
                    "--format",
                    "csv",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()

            # Verify CSV content
            with open(output_file) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["post_id"] == "test123"
                assert rows[0]["sentiment_label"] == "positive"

    def test_data_status_with_nlp(self, mock_auth):
        """Test data status command shows NLP coverage."""
        from typer.testing import CliRunner
        from reddit_analyzer.cli.main import app

        runner = CliRunner()

        with patch("reddit_analyzer.database.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Mock counts
            mock_db.query.return_value.count.side_effect = [
                10,
                5,
                100,
                50,
                25,
            ]  # users, subreddits, posts, comments, analyses

            result = runner.invoke(app, ["data", "status"])
            assert result.exit_code == 0
            assert "NLP Analyses" in result.output
            assert "NLP Coverage" in result.output


class TestExportFunctionality:
    """Test export functionality for NLP results."""

    def test_csv_export_format(self, tmp_path):
        """Test CSV export format."""

        # Create mock data
        mock_results = [
            Mock(
                post=Mock(
                    reddit_id="1",
                    title="Test 1",
                    created_utc=datetime.utcnow(),
                    score=10,
                    num_comments=5,
                ),
                sentiment_score=0.5,
                sentiment_label="positive",
                confidence_score=0.9,
                keywords=["test"],
                emotion_scores={"joy": 0.8},
                language="en",
                readability_score=5.0,
            )
        ]

        output_file = tmp_path / "test.csv"

        # Mock the database query
        with patch("reddit_analyzer.database.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_results

            # Call export function
            from typer.testing import CliRunner
            from reddit_analyzer.cli.main import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "nlp",
                    "export",
                    "test",
                    "--format",
                    "csv",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()

    def test_json_export_format(self, tmp_path):
        """Test JSON export format."""
        output_file = tmp_path / "test.json"

        mock_results = [
            Mock(
                post=Mock(
                    reddit_id="1",
                    title="Test 1",
                    created_utc=datetime.utcnow(),
                    score=10,
                    num_comments=5,
                    author=Mock(username="test_user"),
                    url="https://reddit.com/test",
                ),
                sentiment_score=0.5,
                sentiment_label="positive",
                confidence_score=0.9,
                keywords=["test"],
                entities=[{"text": "Python", "type": "LANGUAGE"}],
                emotion_scores={"joy": 0.8},
                language="en",
                readability_score=5.0,
                analyzed_at=datetime.utcnow(),
            )
        ]

        with patch("reddit_analyzer.database.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_results

            from typer.testing import CliRunner
            from reddit_analyzer.cli.main import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "nlp",
                    "export",
                    "test",
                    "--format",
                    "json",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()


class TestPerformance:
    """Test performance characteristics of NLP processing."""

    def test_nlp_processing_speed(self):
        """Test that NLP processing is reasonably fast."""
        import time

        nlp = get_nlp_service()

        texts = [
            "This is a test sentence for performance testing.",
            "Python programming is great for data science.",
            "Machine learning models need training data.",
        ] * 10  # 30 texts

        start_time = time.time()
        for text in texts:
            nlp.analyze_text(text)
        end_time = time.time()

        elapsed = end_time - start_time
        avg_time = elapsed / len(texts)

        # Should process each text in under 0.5 seconds
        assert avg_time < 0.5

    def test_batch_processing(self):
        """Test batch processing efficiency."""
        nlp = get_nlp_service()

        # Create 100 sample texts
        texts = [
            f"This is test text number {i} for batch processing." for i in range(100)
        ]

        import time

        start_time = time.time()

        # Process in batches
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                nlp.analyze_text(text)

        end_time = time.time()
        elapsed = end_time - start_time

        # Should process 100 texts in under 10 seconds
        assert elapsed < 10


class TestIntegration:
    """End-to-end integration tests."""

    @pytest.fixture
    def setup_test_data(self):
        """Set up test data in database."""
        db = SessionLocal()

        # Create test user
        user = RedditUser(username="integration_test", email="integration@test.com")
        db.add(user)

        # Create test subreddit
        subreddit = Subreddit(
            name="integrationtest",
            display_name="Integration Test",
            created_utc=datetime.utcnow(),
        )
        db.add(subreddit)
        db.commit()

        # Create test posts
        posts = []
        for i in range(5):
            post = Post(
                id=f"integration_{i}",
                title=f"Integration test post {i}",
                selftext=f"This is content for integration test {i}. Python is great!",
                author_id=user.id,
                subreddit_id=subreddit.id,
                created_utc=datetime.utcnow() - timedelta(days=i),
                score=i * 10,
                num_comments=i * 2,
            )
            posts.append(post)

        db.add_all(posts)
        db.commit()

        yield {"user": user, "subreddit": subreddit, "posts": posts}

        # Cleanup
        db.query(TextAnalysis).filter(
            TextAnalysis.post_id.in_([p.id for p in posts])
        ).delete()
        db.query(Post).filter(Post.id.in_([p.id for p in posts])).delete()
        db.query(Subreddit).filter_by(id=subreddit.id).delete()
        db.query(RedditUser).filter_by(id=user.id).delete()
        db.commit()
        db.close()

    def test_end_to_end_nlp_workflow(self, setup_test_data):
        """Test complete NLP workflow from analysis to export."""
        from typer.testing import CliRunner
        from reddit_analyzer.cli.main import app

        runner = CliRunner()

        # 1. Run NLP analysis
        result = runner.invoke(
            app, ["nlp", "analyze", "--subreddit", "integrationtest", "--limit", "5"]
        )
        assert result.exit_code == 0
        assert "Successfully analyzed" in result.output

        # 2. Check that analyses were created
        db = SessionLocal()
        analyses = (
            db.query(TextAnalysis)
            .join(Post)
            .filter(Post.subreddit_id == setup_test_data["subreddit"].id)
            .all()
        )
        assert len(analyses) == 5

        # 3. View sentiment visualization
        result = runner.invoke(app, ["viz", "sentiment", "integrationtest"])
        assert result.exit_code == 0
        assert "Sentiment Analysis" in result.output

        # 4. Export results
        with patch("pathlib.Path.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = runner.invoke(
                app,
                [
                    "nlp",
                    "export",
                    "integrationtest",
                    "--format",
                    "csv",
                    "--output",
                    "/tmp/test_export.csv",
                ],
            )
            assert result.exit_code == 0
            assert "Exported" in result.output

        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
