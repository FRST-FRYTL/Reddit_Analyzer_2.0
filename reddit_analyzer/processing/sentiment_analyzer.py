"""
Multi-model sentiment analysis system for Reddit content.

This module provides comprehensive sentiment analysis using multiple models
including VADER, TextBlob, and transformer-based models for robust results.
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Optional transformer imports (will handle gracefully if not available)
try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    # Don't warn at import time - only warn if transformers are actually requested

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Multi-model sentiment analysis system for comprehensive sentiment detection.

    Combines VADER (lexicon-based), TextBlob (rule-based), and optionally
    transformer models for robust sentiment analysis with ensemble scoring.
    """

    def __init__(
        self,
        use_transformers: bool = True,
        transformer_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
        ensemble_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the sentiment analyzer with multiple models.

        Args:
            use_transformers: Whether to use transformer-based models
            transformer_model: Hugging Face model name for transformer analysis
            ensemble_weights: Weights for ensemble scoring (vader, textblob, transformer)
        """
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE

        # Warn only if transformers were requested but not available
        if use_transformers and not TRANSFORMERS_AVAILABLE:
            logger.warning(
                "Transformers library not available. Transformer-based sentiment analysis disabled. "
                "Install with: uv sync --extra nlp-enhanced"
            )
        self.transformer_model_name = transformer_model

        # Default ensemble weights
        if ensemble_weights is None:
            if self.use_transformers:
                self.ensemble_weights = {
                    "vader": 0.3,
                    "textblob": 0.3,
                    "transformer": 0.4,
                }
            else:
                self.ensemble_weights = {
                    "vader": 0.5,
                    "textblob": 0.5,
                    "transformer": 0.0,
                }
        else:
            self.ensemble_weights = ensemble_weights

        # Initialize models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize all sentiment analysis models."""
        # Initialize VADER
        try:
            self.vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VADER: {e}")
            self.vader = None

        # Initialize transformer model
        self.transformer_pipeline = None
        if self.use_transformers:
            try:
                self.transformer_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.transformer_model_name,
                    tokenizer=self.transformer_model_name,
                    max_length=512,
                    truncation=True,
                )
                logger.info(
                    f"Transformer model {self.transformer_model_name} initialized"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize transformer model: {e}")
                self.transformer_pipeline = None
                self.use_transformers = False

    def analyze_with_vader(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using VADER (Valence Aware Dictionary and sEntiment Reasoner).

        Args:
            text: Text to analyze

        Returns:
            Dictionary with VADER sentiment scores
        """
        if not self.vader or not text:
            return {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0}

        try:
            scores = self.vader.polarity_scores(text)
            return {
                "compound": scores["compound"],
                "positive": scores["pos"],
                "negative": scores["neg"],
                "neutral": scores["neu"],
            }
        except Exception as e:
            logger.warning(f"VADER analysis failed: {e}")
            return {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0}

    def analyze_with_textblob(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using TextBlob.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with TextBlob sentiment scores
        """
        if not text:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            }

        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Convert polarity to positive/negative/neutral scores
            if polarity > 0:
                positive = polarity
                negative = 0.0
                neutral = 1.0 - polarity
            elif polarity < 0:
                positive = 0.0
                negative = abs(polarity)
                neutral = 1.0 - abs(polarity)
            else:
                positive = 0.0
                negative = 0.0
                neutral = 1.0

            return {
                "polarity": polarity,
                "subjectivity": subjectivity,
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
            }
        except Exception as e:
            logger.warning(f"TextBlob analysis failed: {e}")
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            }

    def analyze_with_transformer(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using transformer-based model.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with transformer sentiment scores
        """
        if not self.transformer_pipeline or not text:
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            }

        try:
            # Truncate text if too long
            if len(text) > 500:
                text = text[:500]

            result = self.transformer_pipeline(text)[0]
            label = result["label"].upper()
            confidence = result["score"]

            # Map labels to scores
            if "POSITIVE" in label or "POS" in label:
                positive = confidence
                negative = 0.0
                neutral = 1.0 - confidence
            elif "NEGATIVE" in label or "NEG" in label:
                positive = 0.0
                negative = confidence
                neutral = 1.0 - confidence
            else:  # NEUTRAL
                positive = 0.0
                negative = 0.0
                neutral = confidence

            return {
                "label": label,
                "score": confidence,
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
            }
        except Exception as e:
            logger.warning(f"Transformer analysis failed: {e}")
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            }

    def calculate_ensemble_score(
        self,
        vader_scores: Dict[str, float],
        textblob_scores: Dict[str, float],
        transformer_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Calculate ensemble sentiment scores from multiple models.

        Args:
            vader_scores: VADER sentiment scores
            textblob_scores: TextBlob sentiment scores
            transformer_scores: Transformer sentiment scores

        Returns:
            Dictionary with ensemble sentiment scores
        """
        # Extract individual model scores
        vader_compound = vader_scores.get("compound", 0.0)
        textblob_polarity = textblob_scores.get("polarity", 0.0)
        transformer_pos = transformer_scores.get("positive", 0.0)
        transformer_neg = transformer_scores.get("negative", 0.0)

        # Calculate weighted positive/negative/neutral scores
        positive_score = (
            self.ensemble_weights["vader"] * max(0, vader_compound)
            + self.ensemble_weights["textblob"] * max(0, textblob_polarity)
            + self.ensemble_weights["transformer"] * transformer_pos
        )

        negative_score = (
            self.ensemble_weights["vader"] * max(0, -vader_compound)
            + self.ensemble_weights["textblob"] * max(0, -textblob_polarity)
            + self.ensemble_weights["transformer"] * transformer_neg
        )

        neutral_score = 1.0 - positive_score - negative_score
        neutral_score = max(0.0, neutral_score)  # Ensure non-negative

        # Calculate overall compound score
        compound_score = positive_score - negative_score

        # Determine sentiment label
        if compound_score >= 0.05:
            sentiment_label = "POSITIVE"
        elif compound_score <= -0.05:
            sentiment_label = "NEGATIVE"
        else:
            sentiment_label = "NEUTRAL"

        # Calculate confidence as the maximum of the three scores
        confidence = max(positive_score, negative_score, neutral_score)

        return {
            "compound_score": compound_score,
            "positive_score": positive_score,
            "negative_score": negative_score,
            "neutral_score": neutral_score,
            "sentiment_label": sentiment_label,
            "confidence": confidence,
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis using all available models.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with comprehensive sentiment analysis results
        """
        if not text or not isinstance(text, str):
            return self._empty_result()

        # Clean text for analysis
        cleaned_text = text.strip()
        if not cleaned_text:
            return self._empty_result()

        # Analyze with individual models
        vader_scores = self.analyze_with_vader(cleaned_text)
        textblob_scores = self.analyze_with_textblob(cleaned_text)
        transformer_scores = self.analyze_with_transformer(cleaned_text)

        # Calculate ensemble scores
        ensemble_scores = self.calculate_ensemble_score(
            vader_scores, textblob_scores, transformer_scores
        )

        # Combine all results
        result = {
            "text": text,
            "text_length": len(text),
            "cleaned_text_length": len(cleaned_text),
            # Ensemble scores (primary results)
            **ensemble_scores,
            # Individual model scores
            "vader": vader_scores,
            "textblob": textblob_scores,
            "transformer": transformer_scores,
            # Metadata
            "models_used": {
                "vader": self.vader is not None,
                "textblob": True,  # TextBlob is always available
                "transformer": self.transformer_pipeline is not None,
            },
            "ensemble_weights": self.ensemble_weights.copy(),
        }

        return result

    def analyze_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of texts.

        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process at once

        Returns:
            List of sentiment analysis results
        """
        if not texts:
            return []

        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = []

            for text in batch:
                try:
                    result = self.analyze(text)
                    batch_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to analyze text in batch: {e}")
                    batch_results.append(self._empty_result())

            results.extend(batch_results)

            # Log progress for large batches
            if len(texts) > 1000 and (i + batch_size) % 1000 == 0:
                logger.info(f"Processed {i + batch_size}/{len(texts)} texts")

        return results

    def analyze_emotions(self, text: str) -> Dict[str, float]:
        """
        Analyze emotional content of text (basic implementation).

        Args:
            text: Text to analyze

        Returns:
            Dictionary with emotion scores
        """
        # This is a simplified emotion detection
        # In a full implementation, you might use specialized emotion models

        if not text:
            return {
                "joy": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "sadness": 0.0,
                "surprise": 0.0,
                "disgust": 0.0,
            }

        # Basic emotion keywords (this could be much more sophisticated)
        emotion_keywords = {
            "joy": ["happy", "joy", "excited", "love", "amazing", "wonderful", "great"],
            "anger": ["angry", "mad", "furious", "hate", "terrible", "awful"],
            "fear": ["scared", "afraid", "worried", "anxious", "nervous"],
            "sadness": ["sad", "depressed", "crying", "upset", "disappointed"],
            "surprise": ["surprised", "shocked", "wow", "amazing", "incredible"],
            "disgust": ["disgusting", "gross", "sick", "revolting", "nasty"],
        }

        text_lower = text.lower()
        emotion_scores = {}

        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = min(score / 10.0, 1.0)  # Normalize to 0-1

        return emotion_scores

    def calculate_sentiment_trend(
        self, sentiment_results: List[Dict[str, Any]], window_size: int = 10
    ) -> List[Dict[str, float]]:
        """
        Calculate sentiment trend over a sequence of texts.

        Args:
            sentiment_results: List of sentiment analysis results
            window_size: Size of moving average window

        Returns:
            List of trend data points
        """
        if not sentiment_results or len(sentiment_results) < window_size:
            return []

        trend_data = []

        for i in range(window_size - 1, len(sentiment_results)):
            window = sentiment_results[i - window_size + 1 : i + 1]

            # Calculate moving averages
            avg_compound = np.mean([r.get("compound_score", 0) for r in window])
            avg_positive = np.mean([r.get("positive_score", 0) for r in window])
            avg_negative = np.mean([r.get("negative_score", 0) for r in window])
            avg_confidence = np.mean([r.get("confidence", 0) for r in window])

            trend_point = {
                "index": i,
                "avg_compound": avg_compound,
                "avg_positive": avg_positive,
                "avg_negative": avg_negative,
                "avg_confidence": avg_confidence,
                "window_size": window_size,
            }

            trend_data.append(trend_point)

        return trend_data

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty/default sentiment analysis result."""
        return {
            "text": "",
            "text_length": 0,
            "cleaned_text_length": 0,
            "compound_score": 0.0,
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 1.0,
            "sentiment_label": "NEUTRAL",
            "confidence": 0.0,
            "vader": {
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            },
            "textblob": {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            },
            "transformer": {
                "label": "NEUTRAL",
                "score": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
            },
            "models_used": {
                "vader": self.vader is not None,
                "textblob": True,
                "transformer": self.transformer_pipeline is not None,
            },
            "ensemble_weights": self.ensemble_weights.copy(),
        }
