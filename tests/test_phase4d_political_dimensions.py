"""Tests for Political Dimensions Analyzer - Phase 4D."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from reddit_analyzer.services.political_dimensions_analyzer import (
    PoliticalDimensionsAnalyzer,
    calculate_political_diversity,
    identify_political_clusters,
)
from reddit_analyzer.models import Post


class TestPoliticalDimensionsAnalyzer:
    """Test the PoliticalDimensionsAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        with patch(
            "reddit_analyzer.services.political_dimensions_analyzer.TopicAnalyzer"
        ):
            return PoliticalDimensionsAnalyzer()

    @pytest.fixture
    def sample_posts(self):
        """Create sample posts for testing."""
        posts = []

        # Economic left post
        post1 = Mock(spec=Post)
        post1.title = "We need universal healthcare now"
        post1.selftext = "Healthcare is a human right. The free market has failed to provide affordable care."
        post1.created_utc = datetime.utcnow()
        posts.append(post1)

        # Economic right post
        post2 = Mock(spec=Post)
        post2.title = "Free markets drive innovation"
        post2.selftext = (
            "Government intervention stifles economic growth. Let the market decide."
        )
        post2.created_utc = datetime.utcnow()
        posts.append(post2)

        # Social progressive post
        post3 = Mock(spec=Post)
        post3.title = "Marriage equality is fundamental"
        post3.selftext = (
            "Everyone deserves equal rights regardless of sexual orientation."
        )
        post3.created_utc = datetime.utcnow()
        posts.append(post3)

        # Social conservative post
        post4 = Mock(spec=Post)
        post4.title = "Traditional values matter"
        post4.selftext = "We need to preserve our cultural heritage and family values."
        post4.created_utc = datetime.utcnow()
        posts.append(post4)

        return posts

    def test_analyze_economic_dimension(self, analyzer, sample_posts):
        """Test economic dimension analysis."""
        # Test left-leaning economic text
        result = analyzer.analyze_political_dimensions(sample_posts[0].selftext)

        assert "economic" in result.dimensions
        economic = result.dimensions["economic"]
        assert "score" in economic
        assert "confidence" in economic
        assert "evidence" in economic
        assert -1 <= economic["score"] <= 1
        assert 0 <= economic["confidence"] <= 1
        assert economic["score"] < 0  # Should lean left

        # Test right-leaning economic text
        result = analyzer.analyze_political_dimensions(sample_posts[1].selftext)
        assert result.dimensions["economic"]["score"] > 0  # Should lean right

    def test_analyze_social_dimension(self, analyzer, sample_posts):
        """Test social dimension analysis."""
        # Test progressive social text
        result = analyzer.analyze_political_dimensions(sample_posts[2].selftext)

        assert "social" in result.dimensions
        social = result.dimensions["social"]
        assert "score" in social
        assert "confidence" in social
        assert "evidence" in social
        assert social["score"] < 0  # Progressive is negative

        # Test conservative social text
        result = analyzer.analyze_political_dimensions(sample_posts[3].selftext)
        assert result.dimensions["social"]["score"] > 0  # Conservative is positive

    def test_analyze_governance_dimension(self, analyzer):
        """Test governance dimension analysis."""
        authoritarian_text = (
            "We need strong leadership and strict law enforcement to maintain order"
        )
        result = analyzer.analyze_political_dimensions(authoritarian_text)

        assert "governance" in result.dimensions
        assert result.dimensions["governance"]["score"] > 0  # Authoritarian is positive

        libertarian_text = (
            "Government should have minimal involvement in personal freedoms"
        )
        result = analyzer.analyze_political_dimensions(libertarian_text)
        assert result.dimensions["governance"]["score"] < 0  # Libertarian is negative

    def test_analyze_dimensions_integration(self, analyzer, sample_posts):
        """Test full dimensions analysis."""
        # Combine all sample posts into one text
        combined_text = " ".join([p.selftext for p in sample_posts])
        result = analyzer.analyze_political_dimensions(combined_text)

        assert "economic" in result.dimensions
        assert "social" in result.dimensions
        assert "governance" in result.dimensions
        assert hasattr(result, "analysis_quality")
        assert hasattr(result, "dominant_topics")

        # Check structure of each dimension
        for dimension in ["economic", "social", "governance"]:
            assert "score" in result.dimensions[dimension]
            assert "confidence" in result.dimensions[dimension]
            assert "evidence" in result.dimensions[dimension]
            assert "label" in result.dimensions[dimension]

    def test_calculate_political_compass(self, analyzer, sample_posts):
        """Test political compass calculation."""
        # First analyze dimensions
        combined_text = " ".join([p.selftext for p in sample_posts])
        result = analyzer.analyze_political_dimensions(combined_text)

        # Political compass would use economic (x-axis) and governance (y-axis)
        economic_score = result.dimensions.get("economic", {}).get("score", 0)
        governance_score = result.dimensions.get("governance", {}).get("score", 0)

        assert -1 <= economic_score <= 1
        assert -1 <= governance_score <= 1

        # Determine quadrant based on scores
        if economic_score < -0.2 and governance_score < -0.2:
            quadrant = "Libertarian Left"
        elif economic_score > 0.2 and governance_score < -0.2:
            quadrant = "Libertarian Right"
        elif economic_score < -0.2 and governance_score > 0.2:
            quadrant = "Authoritarian Left"
        elif economic_score > 0.2 and governance_score > 0.2:
            quadrant = "Authoritarian Right"
        else:
            quadrant = "Centrist"

        assert quadrant in [
            "Authoritarian Left",
            "Authoritarian Right",
            "Libertarian Left",
            "Libertarian Right",
            "Centrist",
        ]

    def test_edge_cases(self, analyzer):
        """Test edge cases and error handling."""
        # Empty text
        result = analyzer.analyze_political_dimensions("")
        assert result.analysis_quality == 0
        assert result.dimensions == {}

        # Non-political text
        result = analyzer.analyze_political_dimensions("The weather is nice today")
        # Should have low quality or no dimensions
        assert result.analysis_quality < 0.5 or not result.dimensions

        # Mixed signals
        mixed_text = "I support free markets but also believe in universal healthcare"
        result = analyzer.analyze_political_dimensions(mixed_text)
        if "economic" in result.dimensions:
            # Should show mixed/moderate position
            # Should show low confidence due to mixed signals
            assert result.dimensions["economic"]["confidence"] < 0.7


class TestPoliticalDiversity:
    """Test political diversity calculations."""

    def test_calculate_political_diversity_high(self):
        """Test high diversity calculation."""
        # Create diverse political scores with proper structure
        analyses = []
        for i in range(10):
            # Alternate between left and right
            score_offset = -0.8 if i % 2 == 0 else 0.8
            analysis = {
                "economic": {"score": score_offset, "confidence": 0.8},
                "social": {"score": score_offset * 0.9, "confidence": 0.7},
                "governance": {"score": score_offset * 0.7, "confidence": 0.6},
                "analysis_quality": 0.75,
            }
            analyses.append(analysis)

        result = calculate_political_diversity(analyses)

        assert result > 0.7  # High diversity (returns float between 0-1)

    def test_calculate_political_diversity_low(self):
        """Test low diversity (echo chamber)."""
        # Create homogeneous political scores
        analyses = []
        for i in range(10):
            # All far left with slight variation
            base_score = -0.7 + (i * 0.02)
            analysis = {
                "economic": {"score": base_score, "confidence": 0.8},
                "social": {"score": base_score - 0.1, "confidence": 0.7},
                "governance": {"score": base_score + 0.05, "confidence": 0.6},
                "analysis_quality": 0.8,
            }
            analyses.append(analysis)

        result = calculate_political_diversity(analyses)

        assert result < 0.3  # Low diversity (returns float between 0-1)

    def test_calculate_political_diversity_centrist(self):
        """Test centrist community."""
        analyses = []
        for i in range(10):
            # All center with slight variation
            base_score = -0.1 + (i * 0.02)
            analysis = {
                "economic": {"score": base_score, "confidence": 0.8},
                "social": {"score": base_score + 0.05, "confidence": 0.7},
                "governance": {"score": base_score - 0.05, "confidence": 0.6},
                "analysis_quality": 0.85,
            }
            analyses.append(analysis)

        result = calculate_political_diversity(analyses)

        # Centrist communities can still have low diversity if everyone is center
        assert (
            result < 0.75
        )  # Centrist communities have lower diversity than mixed ones


class TestPoliticalClusters:
    """Test political cluster identification."""

    def test_identify_political_clusters(self):
        """Test cluster identification."""
        # Create analyses with clear clusters
        analyses = []

        # Cluster 1: Progressive economic positions
        for i in range(5):
            analysis = {
                "economic": {"score": -0.6, "confidence": 0.8},
                "social": {"score": -0.7, "confidence": 0.8},
                "governance": {"score": -0.5, "confidence": 0.7},
                "analysis_quality": 0.8,
                "political_topics": {"healthcare": 0.8, "economy": 0.7},
            }
            analyses.append(analysis)

        # Cluster 2: Conservative economic positions
        for i in range(5):
            analysis = {
                "economic": {"score": 0.7, "confidence": 0.8},
                "social": {"score": 0.6, "confidence": 0.8},
                "governance": {"score": 0.8, "confidence": 0.7},
                "analysis_quality": 0.8,
                "political_topics": {"economy": 0.9, "taxes": 0.8},
            }
            analyses.append(analysis)

        result = identify_political_clusters(analyses)

        assert result["num_clusters"] >= 2  # Should identify at least 2 clusters
        assert result["total_points"] == 10

        # Check cluster profiles
        clusters = result["clusters"]
        assert len(clusters) >= 2

        # Each cluster should have expected structure
        for cluster_name, cluster_data in clusters.items():
            assert "size" in cluster_data
            assert "percentage" in cluster_data
            assert "centroid" in cluster_data
            assert "label" in cluster_data

    def test_identify_political_clusters_single(self):
        """Test with single dominant cluster."""
        analyses = []
        for i in range(10):
            # All center-left with slight variation
            base_score = -0.3 + (i * 0.05)
            analysis = {
                "economic": {"score": base_score, "confidence": 0.8},
                "social": {"score": base_score - 0.1, "confidence": 0.8},
                "governance": {"score": base_score + 0.1, "confidence": 0.7},
                "analysis_quality": 0.75,
                "political_topics": {"healthcare": 0.5},
            }
            analyses.append(analysis)

        result = identify_political_clusters(analyses)

        # With homogeneous data, might get 1-2 clusters
        assert result["num_clusters"] <= 2
        assert result["total_points"] == 10
