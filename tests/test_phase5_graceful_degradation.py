"""Tests for graceful degradation when heavy models are unavailable."""

from unittest.mock import Mock, patch
import sys

from reddit_analyzer.services.nlp_service import NLPService


class TestModelAvailability:
    """Test system behavior with missing models."""

    def test_missing_spacy_import(self):
        """Test when spaCy is not installed."""
        # Temporarily remove spacy from modules
        spacy_backup = sys.modules.get("spacy")
        if "spacy" in sys.modules:
            del sys.modules["spacy"]

        try:
            # Mock the import to fail
            with patch.dict("sys.modules", {"spacy": None}):
                from reddit_analyzer.processing.entity_analyzer import EntityAnalyzer

                analyzer = EntityAnalyzer()
                assert analyzer.available is False
                assert analyzer.nlp is None
        finally:
            # Restore spacy if it was there
            if spacy_backup:
                sys.modules["spacy"] = spacy_backup

    def test_missing_transformers_import(self):
        """Test when transformers is not installed."""
        with patch.dict("sys.modules", {"transformers": None}):
            from reddit_analyzer.processing.emotion_analyzer import EmotionAnalyzer

            analyzer = EmotionAnalyzer()
            assert analyzer.available is False
            assert analyzer.model is None

    def test_missing_bertopic_import(self):
        """Test when BERTopic is not installed."""
        with patch.dict("sys.modules", {"bertopic": None}):
            from reddit_analyzer.processing.advanced_topic_modeler import (
                AdvancedTopicModeler,
            )

            modeler = AdvancedTopicModeler()
            assert modeler.bertopic_available is False

    @patch("torch.cuda.is_available")
    def test_cuda_not_available(self, mock_cuda):
        """Test when CUDA is not available."""
        mock_cuda.return_value = False

        from reddit_analyzer.processing.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        # Should fall back to CPU
        assert str(analyzer.device) == "cpu"


class TestNLPServiceFallbacks:
    """Test NLP service fallback mechanisms."""

    def test_service_with_no_heavy_models(self):
        """Test NLP service initialization without heavy models."""
        with patch.dict(
            "sys.modules", {"spacy": None, "transformers": None, "bertopic": None}
        ):
            service = NLPService()

            # Basic models should still work
            assert service.sentiment_analyzer is not None
            assert service.topic_analyzer is not None

            # Heavy models should be None
            assert service._entity_analyzer is None
            assert service._emotion_analyzer is None
            assert service._stance_detector is None

    def test_analyze_with_fallbacks(self):
        """Test analysis methods with fallbacks."""
        service = NLPService()

        # Mock heavy analyzers as unavailable
        service._entity_analyzer = None
        service._emotion_analyzer = None

        text = "This is a test text for analysis."

        # Should return appropriate fallback responses
        entities = service.extract_entities(text)
        assert entities["available"] is False
        assert "message" in entities

        emotions = service.analyze_emotions(text)
        assert emotions["available"] is False
        assert "fallback" in emotions

    def test_partial_model_availability(self):
        """Test when some models are available and others aren't."""
        service = NLPService()

        # Mock scenario: entity analyzer available, emotion analyzer not
        mock_entity = Mock()
        mock_entity.available = True
        mock_entity.extract_political_entities.return_value = {
            "politicians": ["Biden"],
            "available": True,
        }
        service._entity_analyzer = mock_entity
        service._emotion_analyzer = None

        # Entity extraction should work
        entities = service.extract_entities("Biden spoke today")
        assert entities["available"] is True

        # Emotion analysis should fall back
        emotions = service.analyze_emotions("I am happy")
        assert emotions["available"] is False


class TestCLIFallbacks:
    """Test CLI command fallbacks."""

    @patch("reddit_analyzer.cli.analyze.get_nlp_service")
    def test_emotion_command_without_model(self, mock_get_service):
        """Test emotion analysis command without model."""
        from reddit_analyzer.cli.analyze import app
        from typer.testing import CliRunner

        # Mock service with no emotion analyzer
        mock_service = Mock()
        mock_service.analyze_emotions.return_value = {
            "available": False,
            "message": "Emotion analysis not available",
            "fallback": {"sentiment": "positive", "score": 0.7},
        }
        mock_get_service.return_value = mock_service

        runner = CliRunner()
        result = runner.invoke(app, ["analyze-emotions", "test", "--limit", "1"])

        assert "Emotion analysis not available" in result.stdout
        assert "Fallback" in result.stdout

    @patch("reddit_analyzer.cli.analyze.get_nlp_service")
    def test_entity_command_without_model(self, mock_get_service):
        """Test entity extraction command without model."""
        from reddit_analyzer.cli.analyze import app
        from typer.testing import CliRunner

        # Mock service with no entity analyzer
        mock_service = Mock()
        mock_service.extract_entities.return_value = {
            "available": False,
            "message": "Entity extraction not available",
        }
        mock_get_service.return_value = mock_service

        runner = CliRunner()
        result = runner.invoke(app, ["analyze-entities", "test", "--limit", "1"])

        assert "Entity extraction not available" in result.stdout


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_model_loading_error_recovery(self):
        """Test recovery from model loading errors."""
        with patch("transformers.pipeline") as mock_pipeline:
            mock_pipeline.side_effect = Exception("Model download failed")

            from reddit_analyzer.processing.emotion_analyzer import EmotionAnalyzer

            analyzer = EmotionAnalyzer()

            assert analyzer.available is False
            result = analyzer.analyze_emotions("Test text")
            assert result["available"] is False

    def test_runtime_error_handling(self):
        """Test handling of runtime errors during analysis."""
        from reddit_analyzer.processing.stance_detector import StanceDetector

        detector = StanceDetector()

        # Mock model to raise error
        if detector.model:
            with patch.object(detector.model, "__call__") as mock_call:
                mock_call.side_effect = RuntimeError("Model error")

                result = detector.detect_stance("Test text", "topic")
                assert result["available"] is False
                assert "error" in result

    def test_memory_error_handling(self):
        """Test handling of memory errors."""
        service = NLPService()

        # Create very large text that might cause memory issues
        large_text = "word " * 1000000

        # Should handle without crashing
        result = service.analyze_sentiment(large_text)
        assert isinstance(result, dict)


class TestPerformanceWithFallbacks:
    """Test performance when using fallback methods."""

    def test_fallback_performance(self):
        """Test that fallback methods are reasonably fast."""
        import time

        service = NLPService()

        # Force fallbacks
        service._emotion_analyzer = None
        service._entity_analyzer = None

        text = "This is a test of fallback performance."

        # Measure fallback performance
        start = time.time()

        emotions = service.analyze_emotions(text)
        entities = service.extract_entities(text)

        elapsed = time.time() - start

        # Fallbacks should be fast (< 1 second)
        assert elapsed < 1.0
        assert emotions["available"] is False
        assert entities["available"] is False

    def test_mixed_availability_performance(self):
        """Test performance with mixed model availability."""
        service = NLPService()

        texts = ["Test text"] * 100
        results = []

        for text in texts:
            # Some methods might use heavy models, others fallback
            sentiment = service.analyze_sentiment(text)
            emotions = service.analyze_emotions(text)

            results.append({"sentiment": sentiment, "emotions": emotions})

        assert len(results) == 100
        # All results should have valid structure
        assert all("sentiment" in r for r in results)
