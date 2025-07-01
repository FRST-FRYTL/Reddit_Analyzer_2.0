"""Tests for the political dimensions analyzer."""

import pytest
from reddit_analyzer.services.political_dimensions_analyzer import (
    PoliticalDimensionsAnalyzer,
    calculate_political_diversity,
    identify_political_clusters,
)


class TestPoliticalDimensionsAnalyzer:
    """Test cases for PoliticalDimensionsAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a PoliticalDimensionsAnalyzer instance."""
        return PoliticalDimensionsAnalyzer()

    def test_analyze_economic_dimension_market(self, analyzer):
        """Test analysis of market-oriented economic text."""
        text = """
        We need free market solutions and less regulation.
        Privatization and competition drive innovation.
        Economic freedom leads to prosperity.
        """

        result = analyzer.analyze_political_dimensions(text)

        assert "economic" in result.dimensions
        economic = result.dimensions["economic"]
        assert economic["score"] > 0  # Should be market-oriented
        assert economic["confidence"] > 0
        assert economic["label"] is not None
        assert "evidence" in economic

    def test_analyze_economic_dimension_planned(self, analyzer):
        """Test analysis of planned economy text."""
        text = """
        We need more regulation and wealth redistribution.
        Public services and social safety nets are essential.
        Workers rights and unions must be protected.
        """

        result = analyzer.analyze_political_dimensions(text)

        economic = result.dimensions["economic"]
        assert economic["score"] < 0  # Should be planned-oriented

    def test_analyze_social_dimension_liberty(self, analyzer):
        """Test analysis of liberty-oriented social text."""
        text = """
        Individual freedom and personal choice are paramount.
        Civil liberties and privacy rights must be protected.
        Personal autonomy should be respected.
        """

        result = analyzer.analyze_political_dimensions(text)

        assert "social" in result.dimensions
        social = result.dimensions["social"]
        assert social["score"] > 0  # Should be liberty-oriented

    def test_analyze_social_dimension_authority(self, analyzer):
        """Test analysis of authority-oriented social text."""
        text = """
        Social order and traditional values are important.
        Community values and moral standards guide us.
        Law and order maintain social cohesion.
        """

        result = analyzer.analyze_political_dimensions(text)

        social = result.dimensions["social"]
        assert social["score"] < 0  # Should be authority-oriented

    def test_analyze_governance_dimension_decentralized(self, analyzer):
        """Test analysis of decentralized governance text."""
        text = """
        Local control and states rights are essential.
        Grassroots solutions work better than federal mandates.
        Community-driven governance is more effective.
        """

        result = analyzer.analyze_political_dimensions(text)

        assert "governance" in result.dimensions
        governance = result.dimensions["governance"]
        assert governance["score"] > 0  # Should be decentralized

    def test_analyze_governance_dimension_centralized(self, analyzer):
        """Test analysis of centralized governance text."""
        text = """
        Federal regulation and national policy are needed.
        Central planning ensures unified standards.
        National programs provide consistency.
        """

        result = analyzer.analyze_political_dimensions(text)

        governance = result.dimensions["governance"]
        assert governance["score"] < 0  # Should be centralized

    def test_empty_text_returns_empty_result(self, analyzer):
        """Test that empty text returns empty result."""
        result = analyzer.analyze_political_dimensions("")

        assert result.dimensions == {}
        assert result.analysis_quality == 0.0

    def test_short_text_returns_empty_result(self, analyzer):
        """Test that very short text returns empty result."""
        result = analyzer.analyze_political_dimensions("Hello world")

        assert result.dimensions == {}
        assert result.analysis_quality == 0.0

    def test_mixed_political_text(self, analyzer):
        """Test analysis of text with mixed political positions."""
        text = """
        I support free markets but also believe in social safety nets.
        Individual liberty is important, but so is community responsibility.
        Some federal oversight is needed, but local control matters too.
        """

        result = analyzer.analyze_political_dimensions(text)

        # Should have moderate scores
        for dimension in ["economic", "social", "governance"]:
            if dimension in result.dimensions:
                score = result.dimensions[dimension]["score"]
                assert -0.5 < score < 0.5  # Should be relatively centrist


class TestPoliticalDiversityCalculation:
    """Test cases for political diversity calculation."""

    def test_calculate_diversity_high(self):
        """Test diversity calculation with diverse viewpoints."""
        analyses = [
            {
                "economic": {"score": 0.8},
                "social": {"score": 0.5},
                "governance": {"score": 0.2},
                "analysis_quality": 0.8,
            },
            {
                "economic": {"score": -0.7},
                "social": {"score": -0.5},
                "governance": {"score": -0.3},
                "analysis_quality": 0.7,
            },
            {
                "economic": {"score": 0.2},
                "social": {"score": 0.8},
                "governance": {"score": -0.6},
                "analysis_quality": 0.9,
            },
            {
                "economic": {"score": -0.3},
                "social": {"score": -0.8},
                "governance": {"score": 0.7},
                "analysis_quality": 0.6,
            },
            {
                "economic": {"score": 0.5},
                "social": {"score": -0.2},
                "governance": {"score": 0.1},
                "analysis_quality": 0.8,
            },
            {
                "economic": {"score": -0.6},
                "social": {"score": 0.3},
                "governance": {"score": -0.4},
                "analysis_quality": 0.7,
            },
            {
                "economic": {"score": 0.1},
                "social": {"score": 0.6},
                "governance": {"score": 0.5},
                "analysis_quality": 0.9,
            },
            {
                "economic": {"score": -0.4},
                "social": {"score": -0.1},
                "governance": {"score": -0.8},
                "analysis_quality": 0.8,
            },
            {
                "economic": {"score": 0.7},
                "social": {"score": -0.6},
                "governance": {"score": 0.3},
                "analysis_quality": 0.7,
            },
            {
                "economic": {"score": -0.2},
                "social": {"score": 0.4},
                "governance": {"score": -0.2},
                "analysis_quality": 0.6,
            },
        ]

        diversity = calculate_political_diversity(analyses)
        assert diversity > 0.6  # Should show high diversity

    def test_calculate_diversity_low(self):
        """Test diversity calculation with similar viewpoints."""
        analyses = [
            {
                "economic": {"score": 0.6},
                "social": {"score": 0.5},
                "governance": {"score": 0.4},
                "analysis_quality": 0.8,
            },
            {
                "economic": {"score": 0.7},
                "social": {"score": 0.6},
                "governance": {"score": 0.5},
                "analysis_quality": 0.7,
            },
            {
                "economic": {"score": 0.5},
                "social": {"score": 0.4},
                "governance": {"score": 0.3},
                "analysis_quality": 0.9,
            },
            {
                "economic": {"score": 0.8},
                "social": {"score": 0.7},
                "governance": {"score": 0.6},
                "analysis_quality": 0.6,
            },
            {
                "economic": {"score": 0.6},
                "social": {"score": 0.5},
                "governance": {"score": 0.4},
                "analysis_quality": 0.8,
            },
            {
                "economic": {"score": 0.7},
                "social": {"score": 0.6},
                "governance": {"score": 0.5},
                "analysis_quality": 0.7,
            },
            {
                "economic": {"score": 0.5},
                "social": {"score": 0.4},
                "governance": {"score": 0.3},
                "analysis_quality": 0.9,
            },
            {
                "economic": {"score": 0.8},
                "social": {"score": 0.7},
                "governance": {"score": 0.6},
                "analysis_quality": 0.8,
            },
            {
                "economic": {"score": 0.6},
                "social": {"score": 0.5},
                "governance": {"score": 0.4},
                "analysis_quality": 0.7,
            },
            {
                "economic": {"score": 0.7},
                "social": {"score": 0.6},
                "governance": {"score": 0.5},
                "analysis_quality": 0.6,
            },
        ]

        diversity = calculate_political_diversity(analyses)
        assert diversity < 0.4  # Should show low diversity

    def test_calculate_diversity_insufficient_data(self):
        """Test diversity calculation with insufficient data."""
        analyses = [
            {
                "economic": {"score": 0.5},
                "social": {"score": 0.5},
                "governance": {"score": 0.5},
            }
        ]

        diversity = calculate_political_diversity(analyses)
        assert diversity == 0.0  # Should return 0 for insufficient data


class TestPoliticalClustering:
    """Test cases for political clustering."""

    def test_identify_clusters_distinct_groups(self):
        """Test cluster identification with distinct political groups."""
        analyses = []

        # Add libertarian cluster (market, liberty, decentralized)
        for _ in range(10):
            analyses.append(
                {
                    "economic": {"score": 0.8},
                    "social": {"score": 0.7},
                    "governance": {"score": 0.6},
                }
            )

        # Add progressive cluster (planned, liberty, centralized)
        for _ in range(8):
            analyses.append(
                {
                    "economic": {"score": -0.7},
                    "social": {"score": 0.6},
                    "governance": {"score": -0.5},
                }
            )

        clusters = identify_political_clusters(analyses)

        assert "clusters" in clusters
        assert len(clusters["clusters"]) >= 2
        assert clusters["total_points"] == 18

    def test_identify_clusters_insufficient_data(self):
        """Test cluster identification with insufficient data."""
        analyses = [
            {
                "economic": {"score": 0.5},
                "social": {"score": 0.5},
                "governance": {"score": 0.5},
            },
            {
                "economic": {"score": -0.5},
                "social": {"score": -0.5},
                "governance": {"score": -0.5},
            },
        ]

        clusters = identify_political_clusters(analyses)

        assert clusters["message"] == "Insufficient data for clustering"
        assert clusters["clusters"] == []
