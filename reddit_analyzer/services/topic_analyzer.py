"""Topic analysis service for political content."""

import re
from typing import Dict, List, Any
from collections import defaultdict
import numpy as np

from reddit_analyzer.services.nlp_service import get_nlp_service
from reddit_analyzer.data.political_topics import (
    POLITICAL_TOPIC_TAXONOMY,
    get_topic_keywords,
)
import structlog

logger = structlog.get_logger(__name__)


class TopicAnalyzer:
    """
    Service for analyzing political topics in Reddit content.
    Uses existing NLP capabilities for topic detection.
    """

    def __init__(self):
        """Initialize the topic analyzer."""
        self.nlp_service = get_nlp_service()
        self.political_topics = POLITICAL_TOPIC_TAXONOMY
        self._keyword_patterns = self._compile_keyword_patterns()

    def _compile_keyword_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficient keyword matching."""
        patterns = {}
        for topic, data in self.political_topics.items():
            topic_patterns = []
            for keyword in data["keywords"]:
                # Create word boundary pattern for each keyword
                pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
                topic_patterns.append(pattern)
            patterns[topic] = topic_patterns
        return patterns

    def detect_political_topics(self, text: str) -> Dict[str, float]:
        """
        Detect political topics in text with confidence scores.

        Args:
            text: Text to analyze

        Returns:
            Dict mapping topic names to confidence scores (0.0 to 1.0)
            Example: {"healthcare": 0.8, "economy": 0.6, "climate": 0.3}
        """
        if not text or len(text.strip()) < 10:
            return {}

        # Lowercase text for matching
        text_lower = text.lower()

        # Count keyword matches for each topic
        topic_scores = defaultdict(float)
        topic_matches = defaultdict(list)

        for topic, patterns in self._keyword_patterns.items():
            match_count = 0
            matched_keywords = []

            for pattern in patterns:
                matches = pattern.findall(text_lower)
                if matches:
                    match_count += len(matches)
                    matched_keywords.extend(matches)

            if match_count > 0:
                # Calculate base score from match density
                word_count = len(text.split())
                density_score = min(match_count / max(word_count * 0.05, 1), 1.0)

                # Boost score for multiple unique keywords
                unique_keywords = len(set(matched_keywords))
                diversity_bonus = min(unique_keywords * 0.1, 0.3)

                # Calculate final score
                topic_scores[topic] = min(density_score + diversity_bonus, 1.0)
                topic_matches[topic] = matched_keywords[:5]  # Keep first 5 for evidence

        # Normalize scores if multiple topics detected
        if topic_scores:
            max_score = max(topic_scores.values())
            if max_score > 0:
                # Keep only topics with significant presence
                threshold = max_score * 0.2
                topic_scores = {
                    topic: score
                    for topic, score in topic_scores.items()
                    if score >= threshold
                }

        return dict(topic_scores)

    def analyze_topic_sentiment(self, text: str, topic: str) -> Dict[str, Any]:
        """
        Analyze sentiment specifically around a political topic.

        Args:
            text: Text to analyze
            topic: Political topic to focus on

        Returns:
            Dict containing sentiment score, subjectivity, and confidence
        """
        if topic not in self.political_topics:
            raise ValueError(f"Unknown political topic: {topic}")

        # Extract sentences containing topic keywords
        topic_keywords = get_topic_keywords(topic)
        sentences = self._extract_topic_sentences(text, topic_keywords)

        if not sentences:
            return {
                "sentiment": 0.0,
                "subjectivity": 0.0,
                "confidence": 0.0,
                "analyzed_sentences": 0,
            }

        # Analyze sentiment of topic-relevant sentences
        sentiments = []
        subjectivities = []

        for sentence in sentences:
            result = self.nlp_service.sentiment_analyzer.analyze(sentence)
            if result:
                sentiments.append(result.get("compound_score", 0.0))
                # Estimate subjectivity from sentiment components
                subjectivity = self._estimate_subjectivity(result)
                subjectivities.append(subjectivity)

        if sentiments:
            avg_sentiment = np.mean(sentiments)
            avg_subjectivity = np.mean(subjectivities)
            # Confidence based on number of sentences and consistency
            confidence = (
                min(len(sentences) / 10.0, 0.5) + (0.5 * (1 - np.std(sentiments)))
                if len(sentiments) > 1
                else 0.5
            )

            return {
                "sentiment": float(avg_sentiment),
                "subjectivity": float(avg_subjectivity),
                "confidence": float(min(confidence, 1.0)),
                "analyzed_sentences": len(sentences),
            }

        return {
            "sentiment": 0.0,
            "subjectivity": 0.0,
            "confidence": 0.0,
            "analyzed_sentences": 0,
        }

    def calculate_discussion_quality(self, comments: List[str]) -> Dict[str, float]:
        """
        Assess quality metrics: civility, constructiveness, diversity.

        Args:
            comments: List of comment texts

        Returns:
            Dict with quality metrics (all 0.0 to 1.0)
        """
        if not comments:
            return {
                "overall_quality": 0.0,
                "civility_score": 0.0,
                "constructiveness_score": 0.0,
                "viewpoint_diversity": 0.0,
                "engagement_quality": 0.0,
                "confidence": 0.0,
            }

        # Calculate individual metrics
        civility = self._calculate_civility(comments)
        constructiveness = self._calculate_constructiveness(comments)
        diversity = self._calculate_viewpoint_diversity(comments)
        engagement = self._calculate_engagement_quality(comments)

        # Weight the scores for overall quality
        weights = [0.3, 0.3, 0.2, 0.2]  # civility, constructive, diversity, engagement
        scores = [civility, constructiveness, diversity, engagement]
        overall = sum(w * s for w, s in zip(weights, scores))

        # Confidence based on sample size
        confidence = min(len(comments) / 50.0, 1.0)

        return {
            "overall_quality": float(overall),
            "civility_score": float(civility),
            "constructiveness_score": float(constructiveness),
            "viewpoint_diversity": float(diversity),
            "engagement_quality": float(engagement),
            "confidence": float(confidence),
        }

    def _extract_topic_sentences(self, text: str, keywords: List[str]) -> List[str]:
        """Extract sentences containing topic keywords."""
        sentences = text.split(". ")
        topic_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in keywords:
                if keyword.lower() in sentence_lower:
                    topic_sentences.append(sentence.strip())
                    break

        return topic_sentences

    def _estimate_subjectivity(self, sentiment_result: Dict[str, Any]) -> float:
        """Estimate subjectivity from sentiment components."""
        # Use TextBlob subjectivity if available
        if (
            "textblob" in sentiment_result
            and "subjectivity" in sentiment_result["textblob"]
        ):
            return sentiment_result["textblob"]["subjectivity"]

        # Otherwise estimate from sentiment scores
        # pos = sentiment_result.get("positive_score", 0.0)
        # neg = sentiment_result.get("negative_score", 0.0)
        neu = sentiment_result.get("neutral_score", 0.0)

        # More neutral = less subjective
        subjectivity = 1.0 - neu
        return max(0.0, min(1.0, subjectivity))

    def _calculate_civility(self, comments: List[str]) -> float:
        """Calculate civility score based on absence of toxic language."""
        if not comments:
            return 1.0

        toxic_indicators = [
            "stupid",
            "idiot",
            "moron",
            "dumb",
            "hate",
            "disgusting",
            "pathetic",
            "loser",
            "trash",
            "garbage",
            "shut up",
        ]

        toxic_count = 0
        total_words = 0

        for comment in comments:
            words = comment.lower().split()
            total_words += len(words)
            for word in words:
                if word in toxic_indicators:
                    toxic_count += 1

        if total_words == 0:
            return 1.0

        # Calculate civility as inverse of toxicity rate
        toxicity_rate = toxic_count / total_words
        civility = 1.0 - min(toxicity_rate * 20, 1.0)  # Scale factor of 20

        return civility

    def _calculate_constructiveness(self, comments: List[str]) -> float:
        """Calculate constructiveness based on length, references, questions."""
        if not comments:
            return 0.0

        scores = []

        for comment in comments:
            score = 0.0

            # Length factor (longer = more constructive, up to a point)
            word_count = len(comment.split())
            if word_count > 20:
                score += 0.3
            elif word_count > 10:
                score += 0.2

            # Question marks indicate engagement
            if "?" in comment:
                score += 0.2

            # References to sources or evidence
            if any(
                indicator in comment.lower()
                for indicator in [
                    "according to",
                    "research",
                    "study",
                    "source",
                    "evidence",
                ]
            ):
                score += 0.3

            # Acknowledgment of other viewpoints
            if any(
                phrase in comment.lower()
                for phrase in [
                    "i understand",
                    "good point",
                    "you're right",
                    "i agree",
                    "however",
                ]
            ):
                score += 0.2

            scores.append(min(score, 1.0))

        return np.mean(scores) if scores else 0.0

    def _calculate_viewpoint_diversity(self, comments: List[str]) -> float:
        """Calculate diversity of viewpoints expressed."""
        if len(comments) < 2:
            return 0.0

        # Analyze sentiment variance as proxy for viewpoint diversity
        sentiments = []
        for comment in comments[:50]:  # Limit for performance
            result = self.nlp_service.sentiment_analyzer.analyze(comment)
            if result:
                sentiments.append(result.get("compound_score", 0.0))

        if len(sentiments) < 2:
            return 0.0

        # Higher variance = more diverse viewpoints
        variance = np.var(sentiments)
        # Normalize to 0-1 range (variance of 0.25 = maximum diversity)
        diversity = min(variance * 4, 1.0)

        return diversity

    def _calculate_engagement_quality(self, comments: List[str]) -> float:
        """Calculate quality of engagement between users."""
        if not comments:
            return 0.0

        # Look for indicators of quality engagement
        engagement_indicators = [
            "thank you",
            "thanks",
            "great point",
            "interesting",
            "i hadn't considered",
            "you make a good",
            "appreciate",
            "helpful",
            "insightful",
            "well said",
        ]

        indicator_count = 0
        for comment in comments:
            comment_lower = comment.lower()
            for indicator in engagement_indicators:
                if indicator in comment_lower:
                    indicator_count += 1
                    break

        # Calculate engagement rate
        engagement_rate = indicator_count / len(comments)
        return min(engagement_rate * 3, 1.0)  # Scale factor of 3
