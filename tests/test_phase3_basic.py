"""
Basic Phase 3 tests without heavy dependencies.

This module tests Phase 3 model imports and basic functionality
without requiring ML/NLP dependencies.
"""

import pytest
from datetime import datetime, date


class TestPhase3ModelImports:
    """Test that all Phase 3 models can be imported successfully."""

    def test_text_analysis_import(self):
        """Test TextAnalysis model import."""
        from reddit_analyzer.models.text_analysis import TextAnalysis

        assert TextAnalysis is not None

        # Test basic instantiation
        analysis = TextAnalysis(
            sentiment_score=0.5, sentiment_label="POSITIVE", language="en"
        )
        assert analysis.sentiment_score == 0.5
        assert analysis.sentiment_label == "POSITIVE"

    def test_topic_import(self):
        """Test Topic model import."""
        from reddit_analyzer.models.topic import Topic

        assert Topic is not None

        # Test basic instantiation
        topic = Topic(
            topic_id="test_topic",
            model_type="lda",
            topic_words=["word1", "word2", "word3"],
            document_count=10,
        )
        assert topic.topic_id == "test_topic"
        assert topic.model_type == "lda"
        assert len(topic.topic_words) == 3

    def test_user_metric_import(self):
        """Test UserMetric model import."""
        from reddit_analyzer.models.user_metric import UserMetric

        assert UserMetric is not None

        # Test basic instantiation
        metric = UserMetric(user_id=1, activity_score=0.8, influence_score=0.6)
        assert metric.user_id == 1
        assert metric.activity_score == 0.8
        assert metric.influence_score == 0.6

    def test_subreddit_analytics_import(self):
        """Test SubredditAnalytics model import."""
        from reddit_analyzer.models.subreddit_analytics import SubredditAnalytics

        assert SubredditAnalytics is not None

        # Test basic instantiation
        analytics = SubredditAnalytics(
            subreddit_name="test",
            period_start=date.today(),
            period_end=date.today(),
            total_posts=100,
            health_score=0.8,
        )
        assert analytics.subreddit_name == "test"
        assert analytics.total_posts == 100
        assert analytics.health_score == 0.8

    def test_ml_prediction_import(self):
        """Test MLPrediction model import."""
        from reddit_analyzer.models.ml_prediction import MLPrediction

        assert MLPrediction is not None

        # Test basic instantiation
        prediction = MLPrediction(
            model_name="test_model",
            model_type="classification",
            input_data_id="test_id",
            input_type="post",
            prediction={"class": "positive", "confidence": 0.9},
        )
        assert prediction.model_name == "test_model"
        assert prediction.model_type == "classification"
        assert prediction.prediction["class"] == "positive"


class TestPhase3ProcessingImports:
    """Test that processing modules can be imported."""

    def test_analytics_imports(self):
        """Test analytics module imports."""
        # This should always work as it has no external dependencies
        from reddit_analyzer.analytics.metrics_calculator import MetricsCalculator

        assert MetricsCalculator is not None

        calculator = MetricsCalculator()
        assert calculator.engagement_weights is not None
        assert calculator.quality_weights is not None

    def test_processing_module_structure(self):
        """Test that processing module structure exists."""
        # Test module imports without instantiation
        try:
            from reddit_analyzer.processing import (
                text_processor,
                sentiment_analyzer,
                topic_modeler,
                feature_extractor,
            )

            # Just test the modules exist
            assert hasattr(text_processor, "TextProcessor")
            assert hasattr(sentiment_analyzer, "SentimentAnalyzer")
            assert hasattr(topic_modeler, "TopicModeler")
            assert hasattr(feature_extractor, "FeatureExtractor")
        except ImportError:
            # This is expected if dependencies aren't installed
            pytest.skip("Processing dependencies not available")

    def test_ml_module_structure(self):
        """Test that ML module structure exists."""
        try:
            from reddit_analyzer.ml.models import (
                popularity_predictor,
                content_classifier,
                user_classifier,
            )

            # Just test the modules exist
            assert hasattr(popularity_predictor, "PopularityPredictor")
            assert hasattr(content_classifier, "ContentClassifier")
            assert hasattr(user_classifier, "UserClassifier")
        except ImportError:
            # This is expected if ML dependencies aren't installed
            pytest.skip("ML dependencies not available")

    def test_tasks_imports(self):
        """Test that task modules can be imported."""
        from reddit_analyzer.tasks import processing_tasks, analysis_tasks

        # Test that task functions are defined
        assert hasattr(processing_tasks, "process_text_batch")
        assert hasattr(processing_tasks, "calculate_sentiment_trends")
        assert hasattr(processing_tasks, "update_topic_models")
        assert hasattr(processing_tasks, "calculate_user_metrics")

        assert hasattr(analysis_tasks, "calculate_subreddit_analytics")
        assert hasattr(analysis_tasks, "run_statistical_analysis")
        assert hasattr(analysis_tasks, "detect_trending_topics")


class TestPhase3ModelIntegration:
    """Test Phase 3 model integration with existing models."""

    def test_all_models_import_together(self):
        """Test that all models can be imported together without conflicts."""
        from reddit_analyzer.models import (
            Base,
            User,
            Subreddit,
            Post,
            Comment,
            TextAnalysis,
            Topic,
            UserMetric,
            SubredditAnalytics,
            MLPrediction,
        )

        # Test that all models are available
        assert Base is not None
        assert User is not None
        assert Subreddit is not None
        assert Post is not None
        assert Comment is not None
        assert TextAnalysis is not None
        assert Topic is not None
        assert UserMetric is not None
        assert SubredditAnalytics is not None
        assert MLPrediction is not None

    def test_model_table_names(self):
        """Test that all models have correct table names."""
        from reddit_analyzer.models import (
            TextAnalysis,
            Topic,
            UserMetric,
            SubredditAnalytics,
            MLPrediction,
        )

        assert TextAnalysis.__tablename__ == "text_analysis"
        assert Topic.__tablename__ == "topics"
        assert UserMetric.__tablename__ == "user_metrics"
        assert SubredditAnalytics.__tablename__ == "subreddit_analytics"
        assert MLPrediction.__tablename__ == "ml_predictions"

    def test_basic_metrics_calculation(self):
        """Test basic metrics calculation without external dependencies."""
        from reddit_analyzer.analytics.metrics_calculator import MetricsCalculator

        calculator = MetricsCalculator()

        # Test with minimal sample data
        sample_posts = [
            {
                "id": "post1",
                "title": "Test Post",
                "selftext": "Test content",
                "score": 10,
                "num_comments": 5,
                "upvote_ratio": 0.8,
                "created_utc": datetime.utcnow(),
                "is_self": True,
            }
        ]

        # This should work without external dependencies
        try:
            enhanced_posts = calculator.calculate_post_metrics(sample_posts)
            assert len(enhanced_posts) == 1
            assert "calculated_metrics" in enhanced_posts[0]

            metrics = enhanced_posts[0]["calculated_metrics"]
            assert "engagement_score" in metrics
            assert "quality_score" in metrics
            assert "virality_score" in metrics

            # Check that scores are reasonable
            assert 0 <= metrics["engagement_score"] <= 1
            assert 0 <= metrics["quality_score"] <= 1
            assert 0 <= metrics["virality_score"] <= 1

        except Exception as e:
            # If this fails due to missing dependencies, skip
            if "numpy" in str(e) or "pandas" in str(e):
                pytest.skip(
                    f"Metrics calculation requires additional dependencies: {e}"
                )
            else:
                raise


class TestPhase3Configuration:
    """Test Phase 3 configuration and structure."""

    def test_directory_structure(self):
        """Test that Phase 3 directories exist."""
        import os

        base_path = "/home/walde/projects/reddit_analyzer/backend/app"

        # Check processing directory
        assert os.path.exists(os.path.join(base_path, "processing"))
        assert os.path.exists(os.path.join(base_path, "processing", "__init__.py"))

        # Check analytics directory
        assert os.path.exists(os.path.join(base_path, "analytics"))
        assert os.path.exists(os.path.join(base_path, "analytics", "__init__.py"))

        # Check ML directory
        assert os.path.exists(os.path.join(base_path, "ml"))
        assert os.path.exists(os.path.join(base_path, "ml", "__init__.py"))
        assert os.path.exists(os.path.join(base_path, "ml", "models"))

        # Check tasks directory
        assert os.path.exists(os.path.join(base_path, "tasks"))
        assert os.path.exists(os.path.join(base_path, "tasks", "__init__.py"))

    def test_phase3_file_structure(self):
        """Test that Phase 3 files exist."""
        import os

        base_path = "/home/walde/projects/reddit_analyzer/backend/app"

        # Processing files
        processing_files = [
            "text_processor.py",
            "sentiment_analyzer.py",
            "topic_modeler.py",
            "feature_extractor.py",
        ]

        for file in processing_files:
            assert os.path.exists(os.path.join(base_path, "processing", file))

        # Analytics files
        analytics_files = ["statistical_analyzer.py", "metrics_calculator.py"]

        for file in analytics_files:
            assert os.path.exists(os.path.join(base_path, "analytics", file))

        # ML model files
        ml_files = [
            "popularity_predictor.py",
            "content_classifier.py",
            "user_classifier.py",
        ]

        for file in ml_files:
            assert os.path.exists(os.path.join(base_path, "ml", "models", file))

        # Task files
        task_files = ["processing_tasks.py", "analysis_tasks.py"]

        for file in task_files:
            assert os.path.exists(os.path.join(base_path, "tasks", file))

        # New model files
        model_files = [
            "text_analysis.py",
            "topic.py",
            "user_metric.py",
            "subreddit_analytics.py",
            "ml_prediction.py",
        ]

        for file in model_files:
            assert os.path.exists(os.path.join(base_path, "models", file))
