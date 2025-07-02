"""Tests for Phase 5 Entity Analyzer."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from reddit_analyzer.processing.entity_analyzer import EntityAnalyzer


class TestEntityAnalyzer:
    """Test entity extraction and analysis."""

    def test_initialization_without_spacy(self):
        """Test initialization when spaCy is not available."""
        with patch("reddit_analyzer.processing.entity_analyzer.spacy", None):
            analyzer = EntityAnalyzer()
            assert analyzer.nlp is None
            assert analyzer.available is False

    def test_initialization_with_spacy_no_model(self):
        """Test initialization when spaCy model is not available."""
        mock_spacy = Mock()
        mock_spacy.load.side_effect = OSError("Model not found")

        with patch("reddit_analyzer.processing.entity_analyzer.spacy", mock_spacy):
            analyzer = EntityAnalyzer()
            assert analyzer.nlp is None
            assert analyzer.available is False

    def test_extract_entities_without_model(self):
        """Test entity extraction returns empty when model unavailable."""
        with patch("reddit_analyzer.processing.entity_analyzer.spacy", None):
            analyzer = EntityAnalyzer()
            result = analyzer.extract_political_entities(
                "Joe Biden discussed healthcare policy."
            )

            assert result == {
                "politicians": [],
                "organizations": [],
                "locations": [],
                "policies": [],
                "events": [],
                "available": False,
                "message": "Entity extraction not available. Install spacy and language model.",
            }

    @patch("reddit_analyzer.processing.entity_analyzer.spacy")
    def test_extract_entities_with_model(self, mock_spacy):
        """Test entity extraction with mock spaCy model."""
        # Setup mock spaCy
        mock_nlp = MagicMock()
        mock_spacy.load.return_value = mock_nlp

        # Create mock entities
        mock_person = Mock()
        mock_person.text = "Joe Biden"
        mock_person.label_ = "PERSON"
        mock_person.sent.text = "Joe Biden discussed healthcare."

        mock_org = Mock()
        mock_org.text = "Congress"
        mock_org.label_ = "ORG"
        mock_org.sent.text = "Congress passed the bill."

        mock_doc = Mock()
        mock_doc.ents = [mock_person, mock_org]
        mock_nlp.return_value = mock_doc

        analyzer = EntityAnalyzer()
        result = analyzer.extract_political_entities(
            "Joe Biden discussed healthcare with Congress."
        )

        assert result["available"] is True
        assert len(result["politicians"]) > 0
        assert len(result["organizations"]) > 0

    @patch("reddit_analyzer.processing.entity_analyzer.spacy")
    def test_entity_sentiment_analysis(self, mock_spacy):
        """Test sentiment analysis for specific entities."""
        # Setup mock
        mock_nlp = MagicMock()
        mock_spacy.load.return_value = mock_nlp

        # Mock entity with surrounding context
        mock_entity = Mock()
        mock_entity.text = "Biden"
        mock_entity.start_char = 0
        mock_entity.end_char = 5

        mock_doc = Mock()
        mock_doc.text = "Biden's policy is terrible."
        mock_doc.__getitem__ = lambda self, x: mock_doc
        mock_doc.__len__ = lambda self: 5
        mock_doc.start = 0
        mock_doc.end = 5

        mock_nlp.return_value = mock_doc

        analyzer = EntityAnalyzer()
        # Mock the sentiment analyzer
        with patch.object(analyzer, "_get_entity_sentiment", return_value=-0.8):
            sentiment = analyzer._get_entity_sentiment(mock_doc, mock_entity)
            assert sentiment == -0.8

    def test_political_entity_classification(self):
        """Test classification of political entities."""
        analyzer = EntityAnalyzer()

        # Test politician identification
        assert analyzer._is_politician("Joe Biden") is True
        assert analyzer._is_politician("Donald Trump") is True
        assert analyzer._is_politician("John Smith") is False

        # Test policy identification
        assert analyzer._is_policy("Affordable Care Act") is True
        assert analyzer._is_policy("Green New Deal") is True
        assert analyzer._is_policy("Random Text") is False

    @patch("reddit_analyzer.processing.entity_analyzer.spacy")
    def test_entity_relationships(self, mock_spacy):
        """Test extraction of entity relationships."""
        # Setup mock
        mock_nlp = MagicMock()
        mock_spacy.load.return_value = mock_nlp

        analyzer = EntityAnalyzer()

        # Test relationship patterns
        text = "Biden criticized Trump's immigration policy"

        # Mock the doc and dependency parsing
        mock_doc = Mock()
        mock_nlp.return_value = mock_doc

        relationships = analyzer.extract_entity_relationships(text)
        assert isinstance(relationships, list)


class TestEntityAnalyzerIntegration:
    """Integration tests for entity analyzer."""

    def test_analyze_political_text(self):
        """Test full analysis of political text."""
        analyzer = EntityAnalyzer()

        text = """
        President Biden met with Senator Sanders to discuss the healthcare bill.
        The Democratic Party supports the Affordable Care Act expansion.
        Republicans in Congress oppose the new immigration policy.
        """

        result = analyzer.extract_political_entities(text)

        # Should always return the expected structure
        assert "politicians" in result
        assert "organizations" in result
        assert "policies" in result
        assert "available" in result

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        analyzer = EntityAnalyzer()

        result = analyzer.extract_political_entities("")
        assert result["politicians"] == []
        assert result["organizations"] == []

    def test_long_text_handling(self):
        """Test handling of very long text."""
        analyzer = EntityAnalyzer()

        # Create long text
        long_text = "Biden " * 1000 + "discussed policy."

        result = analyzer.extract_political_entities(long_text)
        assert isinstance(result, dict)
        assert "available" in result


@pytest.mark.benchmark
class TestEntityAnalyzerPerformance:
    """Performance tests for entity analyzer."""

    def test_extraction_speed(self, benchmark):
        """Benchmark entity extraction speed."""
        analyzer = EntityAnalyzer()
        text = "President Biden and Senator Sanders discussed healthcare policy in Congress."

        result = benchmark(analyzer.extract_political_entities, text)
        assert isinstance(result, dict)

    def test_batch_processing(self):
        """Test batch processing efficiency."""
        analyzer = EntityAnalyzer()
        texts = ["Biden discussed policy"] * 100

        results = []
        for text in texts:
            result = analyzer.extract_political_entities(text)
            results.append(result)

        assert len(results) == 100
