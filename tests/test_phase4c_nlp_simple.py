#!/usr/bin/env python3
"""
Simplified Phase 4C NLP Integration Tests

Focus on testing the actual implemented functionality.
"""

import pytest
from datetime import datetime
from reddit_analyzer.services.nlp_service import get_nlp_service
from reddit_analyzer.models.text_analysis import TextAnalysis
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.subreddit import Subreddit
from reddit_analyzer.models.user import User as RedditUser
from reddit_analyzer.database import SessionLocal


class TestNLPService:
    """Test the NLP service functionality."""

    def test_nlp_service_singleton(self):
        """Test that NLP service uses singleton pattern."""
        service1 = get_nlp_service()
        service2 = get_nlp_service()
        assert service1 is service2

    def test_analyze_text_basic(self):
        """Test basic text analysis."""
        nlp = get_nlp_service()

        # Test with sample text
        result = nlp.analyze_text("Python is amazing! I love programming with it.")

        # Check basic structure
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "keywords" in result
        assert "entities" in result
        assert "language" in result

        # Check sentiment structure
        sentiment = result["sentiment"]
        assert "compound" in sentiment
        assert isinstance(sentiment["compound"], (int, float))
        assert -1 <= sentiment["compound"] <= 1

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        nlp = get_nlp_service()

        # Test empty string
        result = nlp.analyze_text("")
        assert result["sentiment"]["compound"] == 0.0

        # Test None
        result = nlp.analyze_text(None)
        assert result["sentiment"]["compound"] == 0.0

    def test_sentiment_analysis_vader(self):
        """Test VADER sentiment analysis specifically."""
        nlp = get_nlp_service()

        # Positive text
        positive_result = nlp.analyze_text(
            "This is absolutely fantastic! I'm so happy!"
        )
        assert positive_result["sentiment"]["compound"] > 0.5

        # Negative text
        negative_result = nlp.analyze_text("This is terrible. I hate it completely.")
        assert negative_result["sentiment"]["compound"] < -0.5

        # Neutral text
        neutral_result = nlp.analyze_text("The sky is blue. Water is wet.")
        assert -0.1 <= neutral_result["sentiment"]["compound"] <= 0.1


class TestDatabaseIntegration:
    """Test database integration for NLP data."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        session = SessionLocal()
        yield session
        # Cleanup
        session.rollback()
        session.close()

    def test_text_analysis_creation(self, db_session):
        """Test creating a TextAnalysis record."""
        # First ensure we have a post to analyze
        user = db_session.query(RedditUser).first()
        if not user:
            user = RedditUser(username="nlp_test_user", email="nlp@test.com")
            db_session.add(user)
            db_session.commit()

        subreddit = db_session.query(Subreddit).first()
        if not subreddit:
            subreddit = Subreddit(name="nlptest", display_name="NLP Test")
            db_session.add(subreddit)
            db_session.commit()

        # Create a test post
        post = Post(
            id=f"nlp_test_{datetime.utcnow().timestamp()}",
            title="Test Post for NLP",
            selftext="This is test content.",
            author_id=user.id,
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
            score=1,
            num_comments=0,
        )
        db_session.add(post)
        db_session.commit()

        # Create text analysis
        analysis = TextAnalysis(
            post_id=post.id,
            sentiment_score=0.75,
            sentiment_label="positive",
            confidence_score=0.95,
            keywords=["test", "nlp"],
            entities=[],
            language="en",
            analyzed_at=datetime.utcnow(),
        )
        db_session.add(analysis)
        db_session.commit()

        # Verify it was saved
        saved = db_session.query(TextAnalysis).filter_by(post_id=post.id).first()
        assert saved is not None
        assert saved.sentiment_score == 0.75
        assert saved.sentiment_label == "positive"
        assert saved.keywords == ["test", "nlp"]


class TestCLIIntegration:
    """Test CLI integration."""

    def test_cli_help(self):
        """Test that CLI commands are accessible."""
        from typer.testing import CliRunner
        from reddit_analyzer.cli.main import app

        runner = CliRunner()

        # Test main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "nlp" in result.output

        # Test NLP help
        result = runner.invoke(app, ["nlp", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "export" in result.output
        assert "keywords" in result.output


class TestNLPWorkflow:
    """Test the complete NLP workflow."""

    def test_analyze_and_store(self):
        """Test analyzing text and storing results."""
        # Get services
        nlp = get_nlp_service()
        db = SessionLocal()

        try:
            # Ensure we have test data
            user = db.query(RedditUser).first()
            subreddit = db.query(Subreddit).first()

            if user and subreddit:
                # Create a test post
                post = Post(
                    id=f"workflow_test_{datetime.utcnow().timestamp()}",
                    title="Python Data Science Tutorial",
                    selftext="Learn how to use pandas and numpy for data analysis.",
                    author_id=user.id,
                    subreddit_id=subreddit.id,
                    created_utc=datetime.utcnow(),
                    score=100,
                    num_comments=20,
                )
                db.add(post)
                db.commit()

                # Analyze the post
                text = f"{post.title} {post.selftext or ''}"
                analysis_result = nlp.analyze_text(text)

                # Store the analysis
                analysis = TextAnalysis(
                    post_id=post.id,
                    sentiment_score=analysis_result["sentiment"]["compound"],
                    sentiment_label=self._get_sentiment_label(
                        analysis_result["sentiment"]["compound"]
                    ),
                    confidence_score=1.0,
                    keywords=analysis_result.get("keywords", [])[:10],
                    entities=analysis_result.get("entities", []),
                    language=analysis_result.get("language", "en"),
                    analyzed_at=datetime.utcnow(),
                )
                db.add(analysis)
                db.commit()

                # Verify it worked
                saved = db.query(TextAnalysis).filter_by(post_id=post.id).first()
                assert saved is not None
                assert saved.sentiment_score == analysis_result["sentiment"]["compound"]

        finally:
            db.close()

    def _get_sentiment_label(self, score):
        """Convert sentiment score to label."""
        if score >= 0.05:
            return "positive"
        elif score <= -0.05:
            return "negative"
        else:
            return "neutral"


class TestPerformance:
    """Test performance characteristics."""

    def test_analysis_speed(self):
        """Test that analysis is reasonably fast."""
        import time

        nlp = get_nlp_service()

        # Test with 10 texts
        texts = [
            "Python is great for programming.",
            "Data science with pandas and numpy.",
            "Machine learning models are powerful.",
            "Natural language processing is interesting.",
            "Reddit has many interesting discussions.",
            "Software engineering best practices.",
            "Test driven development helps quality.",
            "Code reviews improve team collaboration.",
            "Documentation is important for maintenance.",
            "Performance optimization requires measurement.",
        ]

        start = time.time()
        for text in texts:
            nlp.analyze_text(text)
        elapsed = time.time() - start

        # Should analyze 10 texts in under 2 seconds
        assert elapsed < 2.0

        # Average should be under 200ms per text
        avg_time = elapsed / len(texts)
        assert avg_time < 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
