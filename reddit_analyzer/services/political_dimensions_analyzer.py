"""Multi-dimensional political analysis service."""

import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

from reddit_analyzer.services.topic_analyzer import TopicAnalyzer
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PoliticalAnalysisResult:
    """Result of multi-dimensional political analysis."""

    dimensions: Dict[str, Dict[str, Any]]
    dominant_topics: Dict[str, float]
    analysis_quality: float


class PoliticalDimensionsAnalyzer:
    """
    Multi-dimensional political analysis system.
    Avoids oversimplified left-right classification.
    """

    def __init__(self):
        """Initialize the political dimensions analyzer."""
        self.topic_analyzer = TopicAnalyzer()
        self.dimensions = self._initialize_dimensions()

    def _initialize_dimensions(self) -> Dict[str, Any]:
        """Initialize the three-axis political model."""
        return {
            "economic": EconomicDimension(),
            "social": SocialDimension(),
            "governance": GovernanceDimension(),
        }

    def analyze_political_dimensions(self, text: str) -> PoliticalAnalysisResult:
        """
        Analyze text across multiple political dimensions.
        Returns scores with confidence intervals.
        """
        if not text or len(text.strip()) < 20:
            return PoliticalAnalysisResult(
                dimensions={}, dominant_topics={}, analysis_quality=0.0
            )

        # Extract political topics first
        topics = self.topic_analyzer.detect_political_topics(text)

        # Analyze each dimension based on topic content
        results = {}
        confidence_scores = []

        for dimension_name, dimension in self.dimensions.items():
            score, confidence, evidence = dimension.analyze(text, topics)
            results[dimension_name] = {
                "score": score,  # -1.0 to 1.0
                "confidence": confidence,  # 0.0 to 1.0
                "evidence": evidence,  # Key phrases/topics that influenced score
                "label": dimension.get_label(score),  # Human-readable position
            }
            # Only include dimensions with actual detections in quality calculation
            if confidence > 0:
                confidence_scores.append(confidence)

        # Calculate overall quality - average only dimensions with detections
        if confidence_scores:
            analysis_quality = np.mean(confidence_scores)
        else:
            # No dimensions detected anything - give minimal quality
            analysis_quality = 0.05

        return PoliticalAnalysisResult(
            dimensions=results,
            dominant_topics=topics,
            analysis_quality=float(analysis_quality),
        )


class BaseDimension:
    """Base class for political dimensions."""

    def _compile_patterns(self, keywords: List[str]) -> List[re.Pattern]:
        """Compile regex patterns for keywords."""
        patterns = []
        for keyword in keywords:
            pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
            patterns.append(pattern)
        return patterns

    def _score_indicators(
        self, text: str, topics: Dict[str, float], indicators: Dict[str, Any]
    ) -> float:
        """Score text based on indicators."""
        score = 0.0
        text_lower = text.lower()

        # Score based on keywords
        if "keywords" in indicators:
            for keyword in indicators["keywords"]:
                if keyword.lower() in text_lower:
                    score += 1.0

        # Score based on topics
        if "topics" in indicators:
            for topic in indicators["topics"]:
                if topic in topics:
                    score += topics[topic] * 2.0  # Weight topic presence

        return score

    def _extract_evidence(self, text: str, score1: float, score2: float) -> List[str]:
        """Extract evidence phrases that influenced the score."""
        evidence = []
        # This is a simplified version - in production, would extract actual phrases
        if score1 > score2:
            evidence.append("Text shows indicators of first position")
        elif score2 > score1:
            evidence.append("Text shows indicators of second position")
        return evidence


class EconomicDimension(BaseDimension):
    """Economic axis: Market-oriented <-> Planned economy."""

    MARKET_INDICATORS = {
        "keywords": [
            "free market",
            "competition",
            "privatization",
            "deregulation",
            "entrepreneurship",
            "capitalism",
            "private sector",
            "market forces",
            "economic freedom",
            "small government",
            "tax cuts",
            "business",
            "innovation",
            "startup",
            "venture capital",
            "profit",
        ],
        "topics": [
            "entrepreneurship",
            "market_solutions",
            "economic_freedom",
            "deregulation",
        ],
    }

    PLANNED_INDICATORS = {
        "keywords": [
            "regulation",
            "public ownership",
            "wealth redistribution",
            "socialism",
            "nationalization",
            "welfare",
            "social safety net",
            "public services",
            "economic equality",
            "progressive taxation",
            "workers rights",
            "unions",
            "minimum wage",
            "universal basic income",
            "public option",
            "universal healthcare",
            "healthcare is a human right",
            "human right",
            "market failure",
            "government intervention",
        ],
        "topics": [
            "market_regulation",
            "public_services",
            "economic_equality",
            "social_programs",
            "healthcare",
        ],
    }

    def analyze(
        self, text: str, topics: Dict[str, float]
    ) -> Tuple[float, float, List[str]]:
        """Analyze economic dimension with evidence tracking."""
        market_score = self._score_indicators(text, topics, self.MARKET_INDICATORS)
        planned_score = self._score_indicators(text, topics, self.PLANNED_INDICATORS)

        # Calculate position (-1 = left/planned, +1 = right/market)
        total = market_score + planned_score
        if total > 0:
            position = (market_score - planned_score) / total
            confidence = min(total / 3.0, 1.0)  # Confidence based on evidence strength
        else:
            position = 0.0
            confidence = 0.0

        evidence = self._extract_evidence(text, market_score, planned_score)
        return position, confidence, evidence

    def get_label(self, score: float) -> str:
        """Convert numeric score to human-readable label."""
        if score < -0.6:
            return "Strongly Planned Economy"
        elif score < -0.2:
            return "Moderately Planned Economy"
        elif score < 0.2:
            return "Mixed Economy"
        elif score < 0.6:
            return "Moderately Market Economy"
        else:
            return "Strongly Market Economy"


class SocialDimension(BaseDimension):
    """Social axis: Individual liberty <-> Social authority."""

    LIBERTY_INDICATORS = {
        "keywords": [
            "individual freedom",
            "personal choice",
            "civil liberties",
            "privacy",
            "freedom of speech",
            "libertarian",
            "individual rights",
            "personal autonomy",
            "limited government",
            "self determination",
            "voluntary",
            "consent",
            "decriminalization",
            "marriage equality",
            "reproductive rights",
            "equal rights",
            "equality",
            "regardless of sexual orientation",
            "everyone deserves",
        ],
        "topics": [
            "personal_autonomy",
            "privacy_rights",
            "freedom_expression",
            "individual_liberty",
            "equality",
        ],
    }

    AUTHORITY_INDICATORS = {
        "keywords": [
            "social order",
            "traditional values",
            "collective good",
            "authority",
            "law and order",
            "social cohesion",
            "moral standards",
            "community values",
            "social responsibility",
            "duty",
            "obligation",
            "discipline",
            "hierarchy",
            "family values",
            "religious values",
            "social norms",
            "preserve",
            "cultural heritage",
            "heritage",
        ],
        "topics": [
            "social_cohesion",
            "moral_standards",
            "community_values",
            "traditional_order",
            "tradition",
        ],
    }

    def analyze(
        self, text: str, topics: Dict[str, float]
    ) -> Tuple[float, float, List[str]]:
        """Analyze social dimension with evidence tracking."""
        liberty_score = self._score_indicators(text, topics, self.LIBERTY_INDICATORS)
        authority_score = self._score_indicators(
            text, topics, self.AUTHORITY_INDICATORS
        )

        # Calculate position (-1 = progressive/liberty, +1 = conservative/authority)
        total = liberty_score + authority_score
        if total > 0:
            position = (authority_score - liberty_score) / total
            confidence = min(total / 3.0, 1.0)
        else:
            position = 0.0
            confidence = 0.0

        evidence = self._extract_evidence(text, liberty_score, authority_score)
        return position, confidence, evidence

    def get_label(self, score: float) -> str:
        """Convert numeric score to human-readable label."""
        if score < -0.6:
            return "Strongly Progressive"
        elif score < -0.2:
            return "Moderately Progressive"
        elif score < 0.2:
            return "Balanced Social View"
        elif score < 0.6:
            return "Moderately Conservative"
        else:
            return "Strongly Conservative"


class GovernanceDimension(BaseDimension):
    """Governance axis: Decentralized <-> Centralized power."""

    DECENTRALIZED_INDICATORS = {
        "keywords": [
            "local control",
            "states rights",
            "grassroots",
            "bottom-up",
            "federalism",
            "devolution",
            "local governance",
            "community solutions",
            "decentralization",
            "regional autonomy",
            "self governance",
            "direct democracy",
            "town hall",
            "local decision",
            "community driven",
            "neighborhood",
            "minimal involvement",
            "personal freedoms",
            "government should have minimal",
            "limited government",
        ],
        "topics": [
            "federalism",
            "local_governance",
            "community_solutions",
            "decentralization",
            "personal_freedom",
        ],
    }

    CENTRALIZED_INDICATORS = {
        "keywords": [
            "federal",
            "national policy",
            "central planning",
            "top-down",
            "federal regulation",
            "unified policy",
            "national standards",
            "central authority",
            "federal mandate",
            "national program",
            "centralized",
            "federal oversight",
            "national security",
            "federal law",
            "supreme court",
            "executive order",
            "strong leadership",
            "strict law enforcement",
            "maintain order",
            "law enforcement",
        ],
        "topics": [
            "national_programs",
            "federal_regulation",
            "unified_policy",
            "central_authority",
        ],
    }

    def analyze(
        self, text: str, topics: Dict[str, float]
    ) -> Tuple[float, float, List[str]]:
        """Analyze governance dimension with evidence tracking."""
        decentralized_score = self._score_indicators(
            text, topics, self.DECENTRALIZED_INDICATORS
        )
        centralized_score = self._score_indicators(
            text, topics, self.CENTRALIZED_INDICATORS
        )

        # Calculate position (-1 = libertarian/decentralized, +1 = authoritarian/centralized)
        total = decentralized_score + centralized_score
        if total > 0:
            position = (centralized_score - decentralized_score) / total
            confidence = min(total / 3.0, 1.0)
        else:
            position = 0.0
            confidence = 0.0

        evidence = self._extract_evidence(text, decentralized_score, centralized_score)
        return position, confidence, evidence

    def get_label(self, score: float) -> str:
        """Convert numeric score to human-readable label."""
        if score < -0.6:
            return "Strongly Libertarian"
        elif score < -0.2:
            return "Moderately Libertarian"
        elif score < 0.2:
            return "Balanced Governance"
        elif score < 0.6:
            return "Moderately Authoritarian"
        else:
            return "Strongly Authoritarian"


def calculate_political_diversity(analyses: List[Dict[str, Any]]) -> float:
    """
    Calculate political diversity using multi-dimensional dispersion.
    """
    if len(analyses) < 10:
        return 0.0

    # Extract all dimension scores
    points = []
    for analysis in analyses:
        if all(dim in analysis for dim in ["economic", "social", "governance"]):
            points.append(
                [
                    analysis["economic"]["score"],
                    analysis["social"]["score"],
                    analysis["governance"]["score"],
                ]
            )

    if not points:
        return 0.0

    points = np.array(points)

    # Calculate dispersion metrics
    centroid = np.mean(points, axis=0)
    distances = np.linalg.norm(points - centroid, axis=1)

    # Normalize by theoretical maximum dispersion
    max_distance = np.sqrt(3)  # Maximum distance in 3D unit cube
    normalized_distances = distances / max_distance

    # Weight by confidence levels
    weights = np.array([a.get("analysis_quality", 0.5) for a in analyses])

    # Calculate weighted average of normalized distances
    if len(weights) > 0 and len(normalized_distances) > 0:
        weighted_diversity = np.average(normalized_distances, weights=weights)
    else:
        weighted_diversity = 0.0

    return min(weighted_diversity * 1.5, 1.0)  # Scale to 0-1 range


def identify_political_clusters(
    analyses: List[Dict[str, Any]], min_cluster_size: int = 5
) -> Dict[str, Any]:
    """
    Identify distinct political groups within a subreddit.
    Simplified version without sklearn dependency.
    """
    if len(analyses) < min_cluster_size * 2:
        return {"clusters": [], "message": "Insufficient data for clustering"}

    # Extract points
    points = []
    for analysis in analyses:
        if all(dim in analysis for dim in ["economic", "social", "governance"]):
            points.append(
                [
                    analysis["economic"]["score"],
                    analysis["social"]["score"],
                    analysis["governance"]["score"],
                ]
            )

    if not points:
        return {"clusters": [], "message": "No valid political dimension data"}

    points = np.array(points)

    # Simple clustering based on quadrants
    clusters = defaultdict(list)

    for i, point in enumerate(points):
        # Determine quadrant based on signs
        economic_side = "market" if point[0] > 0 else "planned"
        social_side = "liberty" if point[1] > 0 else "authority"
        governance_side = "decentralized" if point[2] > 0 else "centralized"

        cluster_key = f"{economic_side}_{social_side}_{governance_side}"
        clusters[cluster_key].append(i)

    # Format cluster results
    cluster_profiles = {}
    for cluster_name, indices in clusters.items():
        if len(indices) >= min_cluster_size:
            cluster_points = points[indices]
            cluster_profiles[cluster_name] = {
                "size": len(indices),
                "percentage": len(indices) / len(points) * 100,
                "centroid": {
                    "economic": float(np.mean(cluster_points[:, 0])),
                    "social": float(np.mean(cluster_points[:, 1])),
                    "governance": float(np.mean(cluster_points[:, 2])),
                },
                "label": _generate_cluster_label(cluster_name),
            }

    return {
        "clusters": cluster_profiles,
        "total_points": len(points),
        "num_clusters": len(cluster_profiles),
    }


def _generate_cluster_label(cluster_name: str) -> str:
    """Generate human-readable label for a political cluster."""
    # parts = cluster_name.split("_")

    labels = {
        "market_liberty_decentralized": "Libertarian",
        "market_liberty_centralized": "Neo-liberal",
        "market_authority_decentralized": "Conservative Federalist",
        "market_authority_centralized": "National Conservative",
        "planned_liberty_decentralized": "Libertarian Socialist",
        "planned_liberty_centralized": "Progressive",
        "planned_authority_decentralized": "Communitarian",
        "planned_authority_centralized": "Statist",
    }

    return labels.get(cluster_name, "Mixed Political Group")
