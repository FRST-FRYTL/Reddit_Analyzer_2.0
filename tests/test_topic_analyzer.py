"""Tests for the topic analyzer service."""

import pytest
from reddit_analyzer.services.topic_analyzer import TopicAnalyzer


class TestTopicAnalyzer:
    """Test cases for TopicAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a TopicAnalyzer instance."""
        return TopicAnalyzer()

    def test_detect_political_topics_healthcare(self, analyzer):
        """Test detection of healthcare topics."""
        text = "We need universal healthcare and better insurance coverage for all Americans."
        topics = analyzer.detect_political_topics(text)

        assert "healthcare" in topics
        assert topics["healthcare"] > 0.5

    def test_detect_political_topics_economy(self, analyzer):
        """Test detection of economy topics."""
        text = "The economy is struggling with high inflation and unemployment rates."
        topics = analyzer.detect_political_topics(text)

        assert "economy" in topics
        assert topics["economy"] > 0.5

    def test_detect_political_topics_climate(self, analyzer):
        """Test detection of climate topics."""
        text = "Climate change requires immediate action on renewable energy and emissions reduction."
        topics = analyzer.detect_political_topics(text)

        assert "climate" in topics
        assert topics["climate"] > 0.5

    def test_detect_multiple_topics(self, analyzer):
        """Test detection of multiple topics in one text."""
        text = """
        The economy needs attention, but we can't ignore climate change.
        Healthcare costs are rising alongside inflation.
        """
        topics = analyzer.detect_political_topics(text)

        assert len(topics) >= 3
        assert "economy" in topics
        assert "climate" in topics
        assert "healthcare" in topics

    def test_empty_text_returns_empty(self, analyzer):
        """Test that empty text returns empty topics."""
        topics = analyzer.detect_political_topics("")
        assert topics == {}

        topics = analyzer.detect_political_topics("   ")
        assert topics == {}

    def test_non_political_text(self, analyzer):
        """Test that non-political text returns few or no topics."""
        text = "I went to the store to buy some groceries and milk."
        topics = analyzer.detect_political_topics(text)

        assert len(topics) == 0

    def test_analyze_topic_sentiment(self, analyzer):
        """Test sentiment analysis for specific topic."""
        text = (
            "I strongly support universal healthcare. It's essential for our society."
        )
        sentiment = analyzer.analyze_topic_sentiment(text, "healthcare")

        assert "sentiment" in sentiment
        assert "confidence" in sentiment
        assert sentiment["sentiment"] > 0  # Positive sentiment
        assert sentiment["confidence"] > 0

    def test_invalid_topic_sentiment(self, analyzer):
        """Test sentiment analysis with invalid topic."""
        with pytest.raises(ValueError):
            analyzer.analyze_topic_sentiment("Some text", "invalid_topic")

    def test_calculate_discussion_quality(self, analyzer):
        """Test discussion quality calculation."""
        comments = [
            "This is a thoughtful point about the economy.",
            "I agree, and according to research, this policy works.",
            "Thanks for sharing this perspective!",
            "Interesting viewpoint, though I see it differently.",
        ]

        quality = analyzer.calculate_discussion_quality(comments)

        assert "overall_quality" in quality
        assert "civility_score" in quality
        assert "constructiveness_score" in quality
        assert "viewpoint_diversity" in quality
        assert "engagement_quality" in quality
        assert "confidence" in quality

        # Should have good scores for civil discussion
        assert quality["civility_score"] > 0.8
        assert quality["overall_quality"] > 0.5

    def test_discussion_quality_with_toxic_comments(self, analyzer):
        """Test discussion quality with toxic comments."""
        comments = [
            "You're an idiot if you believe that.",
            "This is stupid and you're dumb.",
            "Shut up with your garbage opinions.",
        ]

        quality = analyzer.calculate_discussion_quality(comments)

        # Should have low civility score
        assert quality["civility_score"] < 0.5
        assert quality["overall_quality"] < 0.5

    def test_discussion_quality_empty_comments(self, analyzer):
        """Test discussion quality with empty comment list."""
        quality = analyzer.calculate_discussion_quality([])

        assert quality["overall_quality"] == 0.0
        assert quality["confidence"] == 0.0
