"""
NLP Service Layer for coordinating text analysis operations.

This service provides a unified interface for all NLP operations including
sentiment analysis, topic modeling, keyword extraction, and emotion detection.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from reddit_analyzer.processing.sentiment_analyzer import SentimentAnalyzer
from reddit_analyzer.processing.topic_modeler import TopicModeler
from reddit_analyzer.processing.feature_extractor import FeatureExtractor
from reddit_analyzer.processing.text_processor import TextProcessor
from reddit_analyzer.models import Post, TextAnalysis
from reddit_analyzer.database import SessionLocal
from pathlib import Path

logger = logging.getLogger(__name__)


class NLPService:
    """Service for coordinating NLP analysis operations."""

    # Class-level cache for model instances
    _instance = None
    _sentiment_analyzer = None
    _topic_modeler = None
    _feature_extractor = None
    _text_processor = None

    def __new__(cls):
        """Implement singleton pattern for model caching."""
        if cls._instance is None:
            cls._instance = super(NLPService, cls).__new__(cls)
            cls._instance.initialization_time = 0
        return cls._instance

    def __init__(self):
        """Initialize NLP service with lazy-loaded models."""
        if not hasattr(self, "_initialized"):
            start_time = time.time()
            self._initialized = True
            self.initialization_time = time.time() - start_time
            logger.info(f"NLP Service initialized in {self.initialization_time:.2f}s")

    @property
    def sentiment_analyzer(self) -> SentimentAnalyzer:
        """Lazy-load sentiment analyzer."""
        if NLPService._sentiment_analyzer is None:
            logger.info("Loading sentiment analyzer...")
            NLPService._sentiment_analyzer = SentimentAnalyzer()
        return NLPService._sentiment_analyzer

    @property
    def topic_modeler(self) -> TopicModeler:
        """Lazy-load topic modeler."""
        if NLPService._topic_modeler is None:
            logger.info("Loading topic modeler...")
            NLPService._topic_modeler = TopicModeler()
        return NLPService._topic_modeler

    @property
    def feature_extractor(self) -> FeatureExtractor:
        """Lazy-load feature extractor."""
        if NLPService._feature_extractor is None:
            logger.info("Loading feature extractor...")
            NLPService._feature_extractor = FeatureExtractor()
        return NLPService._feature_extractor

    @property
    def text_processor(self) -> TextProcessor:
        """Lazy-load text processor."""
        if NLPService._text_processor is None:
            logger.info("Loading text processor...")
            NLPService._text_processor = TextProcessor()
        return NLPService._text_processor

    def analyze_text(self, text: str, post_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single text with all NLP processors.

        Args:
            text: Text to analyze
            post_id: Optional post ID for database storage

        Returns:
            Dictionary containing all analysis results
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for analysis (post_id: {post_id})")
            return self._empty_analysis()

        start_time = time.time()

        try:
            # Clean and process text
            processed_text = self.text_processor.clean_text(text)

            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer.analyze(processed_text)

            # Extract keywords and entities
            keyword_data = self.text_processor.extract_keywords(
                processed_text, max_keywords=10
            )
            # Extract just the keyword text
            keywords = [kw["keyword"] for kw in keyword_data] if keyword_data else []
            entities = self.text_processor.extract_entities(processed_text)

            # Language detection
            language = self.text_processor.detect_language(processed_text)

            # Calculate readability
            readability = self.text_processor.calculate_readability(processed_text)

            # Topic assignment (requires fitted model)
            topics = []
            if (
                hasattr(self.topic_modeler, "model")
                and self.topic_modeler.model is not None
            ):
                try:
                    topic_dist = self.topic_modeler.predict_topics([processed_text])[0]
                    topics = [
                        {"topic_id": idx, "probability": prob}
                        for idx, prob in enumerate(topic_dist)
                        if prob > 0.1  # Only include significant topics
                    ]
                except Exception as e:
                    logger.warning(f"Topic prediction failed: {e}")

            # Emotion detection (from sentiment analyzer)
            emotions = sentiment_result.get("emotions", {})

            processing_time = time.time() - start_time

            result = {
                "text": text,
                "processed_text": processed_text,
                "sentiment": sentiment_result,
                "keywords": keywords,
                "entities": entities,
                "topics": topics,
                "emotions": emotions,
                "language": language,
                "readability": readability,
                "processing_time": processing_time,
                "model_versions": self._get_model_versions(),
            }

            # Store in database if post_id provided
            if post_id:
                self._store_analysis(post_id, result)

            return result

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return self._error_analysis(str(e))

    def analyze_batch(
        self, texts: List[str], post_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts in batch for efficiency.

        Args:
            texts: List of texts to analyze
            post_ids: Optional list of corresponding post IDs

        Returns:
            List of analysis results
        """
        if not texts:
            return []

        # Ensure post_ids matches texts length
        if post_ids and len(post_ids) != len(texts):
            logger.warning("post_ids length doesn't match texts length")
            post_ids = None

        results = []
        for i, text in enumerate(texts):
            post_id = post_ids[i] if post_ids else None
            result = self.analyze_text(text, post_id)
            results.append(result)

        return results

    def analyze_posts(self, posts: List[Post], reanalyze: bool = False) -> int:
        """
        Analyze Post objects and store results in database.

        Args:
            posts: List of Post objects to analyze
            reanalyze: Whether to re-analyze posts with existing analysis

        Returns:
            Number of posts analyzed
        """
        db = SessionLocal()
        analyzed_count = 0

        try:
            for post in posts:
                # Skip if already analyzed and not reanalyzing
                if not reanalyze:
                    existing = (
                        db.query(TextAnalysis)
                        .filter(TextAnalysis.post_id == post.id)
                        .first()
                    )
                    if existing:
                        continue

                # Combine title and body for analysis
                full_text = f"{post.title}\n\n{post.body}" if post.body else post.title

                # Analyze text
                result = self.analyze_text(full_text, post.id)

                if result.get("sentiment"):
                    analyzed_count += 1

            db.commit()

        except Exception as e:
            logger.error(f"Error analyzing posts: {e}")
            db.rollback()
        finally:
            db.close()

        return analyzed_count

    def fit_topic_model(self, texts: List[str], num_topics: int = 10) -> bool:
        """
        Fit topic model on a collection of texts.

        Args:
            texts: List of texts to fit model on
            num_topics: Number of topics to discover

        Returns:
            Success status
        """
        try:
            # Clean texts
            processed_texts = [self.text_processor.clean_text(text) for text in texts]

            # Fit topic model
            self.topic_modeler.fit(processed_texts, num_topics=num_topics)

            # Save model for future use
            model_path = Path("data/models/topic_model.pkl")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            self.topic_modeler.save_model(str(model_path))

            return True

        except Exception as e:
            logger.error(f"Error fitting topic model: {e}")
            return False

    def get_topics(self, num_words: int = 10) -> List[Dict[str, Any]]:
        """
        Get discovered topics with their keywords.

        Args:
            num_words: Number of words per topic

        Returns:
            List of topics with keywords and probabilities
        """
        if not hasattr(self.topic_modeler, "model") or self.topic_modeler.model is None:
            # Try to load saved model
            model_path = Path("data/models/topic_model.pkl")
            if model_path.exists():
                self.topic_modeler.load_model(str(model_path))
            else:
                return []

        return self.topic_modeler.get_topics(num_words=num_words)

    def extract_keywords(
        self, texts: Union[str, List[str]], num_keywords: int = 20
    ) -> List[str]:
        """
        Extract keywords from text(s).

        Args:
            texts: Single text or list of texts
            num_keywords: Number of keywords to extract

        Returns:
            List of keywords
        """
        if isinstance(texts, str):
            texts = [texts]

        # Combine all texts
        combined_text = " ".join(texts)

        # Extract keywords
        keyword_data = self.text_processor.extract_keywords(
            combined_text, max_keywords=num_keywords
        )

        # Extract just the keyword text
        keywords = [kw["keyword"] for kw in keyword_data] if keyword_data else []

        return keywords

    def _store_analysis(self, post_id: str, result: Dict[str, Any]) -> None:
        """Store analysis results in database."""
        db = SessionLocal()
        try:
            # Check if analysis already exists
            existing = (
                db.query(TextAnalysis).filter(TextAnalysis.post_id == post_id).first()
            )

            sentiment = result.get("sentiment", {})

            analysis_data = {
                "post_id": post_id,
                "sentiment_score": sentiment.get("compound", 0.0),
                "sentiment_label": sentiment.get("label", "neutral"),
                "confidence_score": sentiment.get("confidence", 0.0),
                "keywords": result.get("keywords", []),
                "entities": result.get("entities", []),
                "topics": result.get("topics", []),
                "emotion_scores": result.get("emotions", {}),
                "language": result.get("language", "en"),
                "readability_score": result.get("readability", {}).get(
                    "flesch_reading_ease", 0.0
                ),
                "processed_at": datetime.utcnow(),
                "quality_score": None,  # Can be calculated later
            }

            if existing:
                # Update existing record
                for key, value in analysis_data.items():
                    setattr(existing, key, value)
            else:
                # Create new record
                analysis = TextAnalysis(**analysis_data)
                db.add(analysis)

            db.commit()

        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
            db.rollback()
        finally:
            db.close()

    def _get_model_versions(self) -> Dict[str, str]:
        """Get versions of all loaded models."""
        versions = {
            "nlp_service": "1.0.0",
            "sentiment_analyzer": getattr(
                self.sentiment_analyzer, "__version__", "unknown"
            ),
            "text_processor": getattr(self.text_processor, "__version__", "unknown"),
        }

        # Add transformer model info if available
        if hasattr(self.sentiment_analyzer, "transformer_model"):
            versions["transformer_model"] = getattr(
                self.sentiment_analyzer.transformer_model, "model_name", "unknown"
            )

        return versions

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis result."""
        return {
            "text": "",
            "processed_text": "",
            "sentiment": {"compound": 0.0, "label": "neutral", "confidence": 0.0},
            "keywords": [],
            "entities": [],
            "topics": [],
            "emotions": {},
            "language": "unknown",
            "readability": {},
            "processing_time": 0.0,
            "model_versions": self._get_model_versions(),
        }

    def _error_analysis(self, error: str) -> Dict[str, Any]:
        """Return error analysis result."""
        result = self._empty_analysis()
        result["error"] = error
        return result


# Singleton instance getter
def get_nlp_service() -> NLPService:
    """Get or create the NLP service singleton instance."""
    return NLPService()
