"""
Test Phase 3 data processing models and basic functionality.

This module tests the new database models and core processing components
without requiring heavy ML dependencies.
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session

from reddit_analyzer.models import (
    TextAnalysis,
    Topic,
    UserMetric,
    SubredditAnalytics,
    MLPrediction,
    Post,
    User,
    Subreddit,
)


class TestPhase3Models:
    """Test Phase 3 database models."""

    def test_text_analysis_model_creation(self, test_db: Session):
        """Test TextAnalysis model creation and relationships."""
        # Create test user and subreddit
        user = User(username="testuser", comment_karma=100, link_karma=50)
        subreddit = Subreddit(
            display_name="testsubreddit", description="Test subreddit"
        )
        test_db.add_all([user, subreddit])
        test_db.flush()

        # Create test post
        post = Post(
            id="test_post_1",
            title="Test Post",
            selftext="This is a test post for sentiment analysis.",
            author_id=user.id,
            subreddit_id=subreddit.id,
            score=10,
            upvote_ratio=0.8,
            num_comments=5,
            created_utc=datetime.utcnow(),
        )
        test_db.add(post)
        test_db.flush()

        # Create text analysis
        text_analysis = TextAnalysis(
            post_id=post.id,
            sentiment_score=0.5,
            sentiment_label="POSITIVE",
            emotion_scores={"joy": 0.8, "anger": 0.1},
            language="en",
            confidence_score=0.9,
            keywords=[{"keyword": "test", "score": 0.8}],
            entities=[{"text": "test", "label": "ORG"}],
            quality_score=0.7,
            readability_score=0.6,
        )

        test_db.add(text_analysis)
        test_db.commit()

        # Verify creation
        saved_analysis = test_db.query(TextAnalysis).filter_by(post_id=post.id).first()
        assert saved_analysis is not None
        assert saved_analysis.sentiment_score == 0.5
        assert saved_analysis.sentiment_label == "POSITIVE"
        assert saved_analysis.language == "en"
        assert saved_analysis.post.title == "Test Post"

    def test_topic_model_creation(self, db_session: Session):
        """Test Topic model creation."""
        topic = Topic(
            topic_id="lda_test_0",
            topic_name="Test Topic",
            subreddit_name="testsubreddit",
            model_type="lda",
            topic_words=["word1", "word2", "word3"],
            topic_probability=0.8,
            document_count=100,
            time_period=date.today(),
            coherence_score=0.7,
            model_version="1.0",
        )

        db_session.add(topic)
        db_session.commit()

        # Verify creation
        saved_topic = db_session.query(Topic).filter_by(topic_id="lda_test_0").first()
        assert saved_topic is not None
        assert saved_topic.topic_name == "Test Topic"
        assert saved_topic.model_type == "lda"
        assert len(saved_topic.topic_words) == 3
        assert saved_topic.document_count == 100

    def test_user_metric_model_creation(self, db_session: Session):
        """Test UserMetric model creation and relationships."""
        # Create test user
        user = User(username="metricuser", comment_karma=500, link_karma=200)
        db_session.add(user)
        db_session.flush()

        # Create user metric
        user_metric = UserMetric(
            user_id=user.id,
            activity_score=0.8,
            influence_score=0.6,
            reputation_score=0.7,
            engagement_rate=0.5,
            content_quality_score=0.6,
            sentiment_trend=0.2,
            consistency_score=0.9,
            community_diversity=0.4,
            detailed_metrics={
                "engagement_metrics": {"avg_post_score": 15.5},
                "behavioral_metrics": {"posting_regularity": 0.8},
            },
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
        )

        db_session.add(user_metric)
        db_session.commit()

        # Verify creation and relationship
        saved_metric = db_session.query(UserMetric).filter_by(user_id=user.id).first()
        assert saved_metric is not None
        assert saved_metric.activity_score == 0.8
        assert saved_metric.user.username == "metricuser"
        assert (
            saved_metric.detailed_metrics["engagement_metrics"]["avg_post_score"]
            == 15.5
        )

    def test_subreddit_analytics_model_creation(self, db_session: Session):
        """Test SubredditAnalytics model creation."""
        analytics = SubredditAnalytics(
            subreddit_name="analyticssub",
            period_start=date.today(),
            period_end=date.today(),
            total_posts=100,
            total_comments=500,
            unique_authors=50,
            avg_score=25.5,
            avg_comments_per_post=5.0,
            avg_upvote_ratio=0.85,
            avg_sentiment=0.3,
            health_score=0.8,
            activity_level=0.7,
            engagement_quality=0.75,
            growth_rate=0.1,
            content_diversity=0.6,
            top_topics=[
                {"topic_id": "topic_1", "keywords": ["word1", "word2"]},
                {"topic_id": "topic_2", "keywords": ["word3", "word4"]},
            ],
            engagement_metrics={"avg_engagement_score": 0.7},
            growth_metrics={"activity_growth_rate": 0.15},
        )

        db_session.add(analytics)
        db_session.commit()

        # Verify creation
        saved_analytics = (
            db_session.query(SubredditAnalytics)
            .filter_by(subreddit_name="analyticssub")
            .first()
        )
        assert saved_analytics is not None
        assert saved_analytics.total_posts == 100
        assert saved_analytics.health_score == 0.8
        assert len(saved_analytics.top_topics) == 2

    def test_ml_prediction_model_creation(self, db_session: Session):
        """Test MLPrediction model creation."""
        prediction = MLPrediction(
            model_name="popularity_predictor",
            model_version="1.0",
            model_type="regression",
            input_data_id="test_post_123",
            input_type="post",
            prediction={"predicted_score": 45.2, "confidence": 0.8},
            confidence_score=0.8,
            probability_distribution={"high": 0.7, "medium": 0.2, "low": 0.1},
            feature_importance={"title_length": 0.3, "content_quality": 0.5},
            processing_time_ms=150,
        )

        db_session.add(prediction)
        db_session.commit()

        # Verify creation
        saved_prediction = (
            db_session.query(MLPrediction)
            .filter_by(input_data_id="test_post_123")
            .first()
        )
        assert saved_prediction is not None
        assert saved_prediction.model_name == "popularity_predictor"
        assert saved_prediction.prediction["predicted_score"] == 45.2
        assert saved_prediction.confidence_score == 0.8


class TestPhase3BasicProcessing:
    """Test basic processing functionality without heavy ML dependencies."""

    def test_text_processor_import(self):
        """Test that text processor can be imported."""
        try:
            from reddit_analyzer.processing.text_processor import TextProcessor

            processor = TextProcessor()
            assert processor is not None
        except ImportError as e:
            pytest.skip(f"Text processor dependencies not available: {e}")

    def test_sentiment_analyzer_import(self):
        """Test that sentiment analyzer can be imported."""
        try:
            from reddit_analyzer.processing.sentiment_analyzer import SentimentAnalyzer

            analyzer = SentimentAnalyzer(
                use_transformers=False
            )  # Disable transformers for testing
            assert analyzer is not None
        except ImportError as e:
            pytest.skip(f"Sentiment analyzer dependencies not available: {e}")

    def test_feature_extractor_import(self):
        """Test that feature extractor can be imported."""
        try:
            from reddit_analyzer.processing.feature_extractor import FeatureExtractor

            extractor = FeatureExtractor()
            assert extractor is not None
        except ImportError as e:
            pytest.skip(f"Feature extractor dependencies not available: {e}")

    def test_metrics_calculator_import(self):
        """Test that metrics calculator can be imported."""
        from reddit_analyzer.analytics.metrics_calculator import MetricsCalculator

        calculator = MetricsCalculator()
        assert calculator is not None

    def test_statistical_analyzer_import(self):
        """Test that statistical analyzer can be imported."""
        try:
            from reddit_analyzer.analytics.statistical_analyzer import (
                StatisticalAnalyzer,
            )

            analyzer = StatisticalAnalyzer()
            assert analyzer is not None
        except ImportError as e:
            pytest.skip(f"Statistical analyzer dependencies not available: {e}")

    def test_ml_models_import(self):
        """Test that ML models can be imported."""
        try:
            from reddit_analyzer.ml.models.popularity_predictor import (
                PopularityPredictor,
            )
            from reddit_analyzer.ml.models.content_classifier import ContentClassifier
            from reddit_analyzer.ml.models.user_classifier import UserClassifier

            predictor = PopularityPredictor()
            classifier = ContentClassifier()
            user_classifier = UserClassifier()

            assert predictor is not None
            assert classifier is not None
            assert user_classifier is not None
        except ImportError as e:
            pytest.skip(f"ML model dependencies not available: {e}")


class TestPhase3Integration:
    """Test integration between Phase 3 components."""

    def test_model_relationships(self, db_session: Session):
        """Test relationships between old and new models."""
        # Create user, subreddit, and post
        user = User(username="integrationuser", comment_karma=100)
        subreddit = Subreddit(display_name="integrationtest", description="Test")
        db_session.add_all([user, subreddit])
        db_session.flush()

        post = Post(
            id="integration_post",
            title="Integration Test Post",
            selftext="Testing integration between models",
            author_id=user.id,
            subreddit_id=subreddit.id,
            score=20,
            created_utc=datetime.utcnow(),
        )
        db_session.add(post)
        db_session.flush()

        # Create text analysis for the post
        text_analysis = TextAnalysis(
            post_id=post.id,
            sentiment_score=0.3,
            sentiment_label="POSITIVE",
            language="en",
            quality_score=0.8,
        )
        db_session.add(text_analysis)

        # Create user metric
        user_metric = UserMetric(
            user_id=user.id,
            activity_score=0.6,
            influence_score=0.4,
            reputation_score=0.5,
        )
        db_session.add(user_metric)

        db_session.commit()

        # Test relationships
        # Post -> TextAnalysis
        saved_post = db_session.query(Post).filter_by(id="integration_post").first()
        assert saved_post.text_analysis is not None
        assert saved_post.text_analysis.sentiment_score == 0.3

        # User -> UserMetric
        saved_user = (
            db_session.query(User).filter_by(username="integrationuser").first()
        )
        assert len(saved_user.metrics) == 1
        assert saved_user.metrics[0].activity_score == 0.6

    def test_metrics_calculation_basic(self):
        """Test basic metrics calculation without dependencies."""
        from reddit_analyzer.analytics.metrics_calculator import MetricsCalculator

        calculator = MetricsCalculator()

        # Test with sample post data
        sample_posts = [
            {
                "id": "post1",
                "title": "Test Post 1",
                "selftext": "This is a test post with some content.",
                "score": 10,
                "num_comments": 5,
                "upvote_ratio": 0.8,
                "created_utc": datetime.utcnow(),
                "is_self": True,
            },
            {
                "id": "post2",
                "title": "Another Test Post",
                "selftext": "Another test post with different metrics.",
                "score": 25,
                "num_comments": 12,
                "upvote_ratio": 0.9,
                "created_utc": datetime.utcnow(),
                "is_self": True,
            },
        ]

        # Calculate post metrics
        enhanced_posts = calculator.calculate_post_metrics(sample_posts)

        assert len(enhanced_posts) == 2
        assert "calculated_metrics" in enhanced_posts[0]
        assert "engagement_score" in enhanced_posts[0]["calculated_metrics"]
        assert "quality_score" in enhanced_posts[0]["calculated_metrics"]

        # Check that metrics are reasonable
        metrics = enhanced_posts[0]["calculated_metrics"]
        assert 0 <= metrics["engagement_score"] <= 1
        assert 0 <= metrics["quality_score"] <= 1


@pytest.fixture
def sample_processing_data():
    """Provide sample data for processing tests."""
    return {
        "posts": [
            {
                "id": "sample1",
                "title": "Interesting Discussion About Technology",
                "selftext": "I think artificial intelligence is going to change everything. What are your thoughts on the future of AI and its impact on society?",
                "score": 45,
                "num_comments": 23,
                "upvote_ratio": 0.85,
                "created_utc": datetime.utcnow(),
                "is_self": True,
                "subreddit": {"display_name": "technology"},
            },
            {
                "id": "sample2",
                "title": "Quick Question About Programming",
                "selftext": "Can someone help me understand how to implement a binary search algorithm in Python?",
                "score": 12,
                "num_comments": 8,
                "upvote_ratio": 0.92,
                "created_utc": datetime.utcnow(),
                "is_self": True,
                "subreddit": {"display_name": "programming"},
            },
        ],
        "users": [
            {
                "id": 1,
                "username": "tech_enthusiast",
                "comment_karma": 1500,
                "link_karma": 800,
                "created_utc": datetime.utcnow(),
                "posts": [],
                "comments": [],
            }
        ],
    }
