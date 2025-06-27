"""
Feature extraction utilities for machine learning models.

This module provides feature extraction capabilities for converting
processed text and metadata into numerical features for ML models.
"""

import logging
from typing import Dict, List, Any
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract numerical features from Reddit posts and comments for ML models.

    Converts text, metadata, and engagement metrics into feature vectors
    suitable for machine learning algorithms.
    """

    def __init__(self, max_features: int = 5000, min_df: int = 2, max_df: float = 0.8):
        """
        Initialize the feature extractor.

        Args:
            max_features: Maximum number of features for text vectorization
            min_df: Minimum document frequency for text features
            max_df: Maximum document frequency for text features
        """
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df

        # Initialize vectorizers
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df,
            stop_words="english",
            ngram_range=(1, 2),
        )

        self.count_vectorizer = CountVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df,
            stop_words="english",
        )

        # Initialize scalers and encoders
        self.scaler = StandardScaler()
        self.label_encoders = {}

        # Track if fitted
        self.is_fitted = False

    def extract_text_features(
        self, texts: List[str], method: str = "tfidf"
    ) -> np.ndarray:
        """
        Extract text features using vectorization.

        Args:
            texts: List of text strings to vectorize
            method: Vectorization method ('tfidf' or 'count')

        Returns:
            Feature matrix as numpy array
        """
        if not texts:
            return np.array([])

        # Clean None values
        cleaned_texts = [text if text else "" for text in texts]

        try:
            if method == "tfidf":
                if not self.is_fitted:
                    features = self.tfidf_vectorizer.fit_transform(cleaned_texts)
                else:
                    features = self.tfidf_vectorizer.transform(cleaned_texts)
            else:
                if not self.is_fitted:
                    features = self.count_vectorizer.fit_transform(cleaned_texts)
                else:
                    features = self.count_vectorizer.transform(cleaned_texts)

            return features.toarray()

        except Exception as e:
            logger.warning(f"Text feature extraction failed: {e}")
            return np.zeros((len(texts), self.max_features))

    def extract_temporal_features(self, timestamps: List[datetime]) -> np.ndarray:
        """
        Extract temporal features from timestamps.

        Args:
            timestamps: List of datetime objects

        Returns:
            Feature matrix with temporal features
        """
        if not timestamps:
            return np.array([])

        features = []

        for timestamp in timestamps:
            if timestamp is None:
                # Default features for None timestamps
                temp_features = [0, 0, 0, 0, 0, 0, 0]
            else:
                temp_features = [
                    timestamp.hour,  # Hour of day (0-23)
                    timestamp.weekday(),  # Day of week (0-6)
                    timestamp.day,  # Day of month (1-31)
                    timestamp.month,  # Month (1-12)
                    timestamp.year,  # Year
                    int(timestamp.timestamp()),  # Unix timestamp
                    1 if timestamp.weekday() < 5 else 0,  # Is weekday
                ]

            features.append(temp_features)

        return np.array(features)

    def extract_engagement_features(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract engagement and metadata features.

        Args:
            data: List of dictionaries with engagement data

        Returns:
            Feature matrix with engagement features
        """
        if not data:
            return np.array([])

        features = []

        for item in data:
            item_features = [
                item.get("score", 0),  # Post/comment score
                item.get("num_comments", 0),  # Number of comments
                item.get("upvote_ratio", 0.5),  # Upvote ratio
                len(item.get("title", "")),  # Title length
                len(item.get("selftext", "")),  # Content length
                len(item.get("body", "")),  # Comment body length
                1 if item.get("stickied", False) else 0,  # Is stickied
                1 if item.get("locked", False) else 0,  # Is locked
                1 if item.get("over_18", False) else 0,  # Is NSFW
                item.get("author_comment_karma", 0),  # Author karma
                item.get("author_link_karma", 0),  # Author link karma
                item.get("gilded", 0),  # Number of awards
            ]

            features.append(item_features)

        return np.array(features)

    def extract_content_features(
        self, processed_data: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Extract content-based features from processed text.

        Args:
            processed_data: List of processed text data dictionaries

        Returns:
            Feature matrix with content features
        """
        if not processed_data:
            return np.array([])

        features = []

        for item in processed_data:
            stats = item.get("stats", {})
            readability = item.get("readability", {})
            keywords = item.get("keywords", [])
            entities = item.get("entities", [])

            content_features = [
                stats.get("token_count", 0),  # Number of tokens
                stats.get("entity_count", 0),  # Number of entities
                stats.get("keyword_count", 0),  # Number of keywords
                readability.get("avg_sentence_length", 0),  # Avg sentence length
                readability.get("avg_word_length", 0),  # Avg word length
                readability.get("readability_score", 0),  # Readability score
                len(
                    [k for k in keywords if k.get("score", 0) > 0.1]
                ),  # High-value keywords
                len(
                    [e for e in entities if e.get("label") == "PERSON"]
                ),  # Person mentions
                len(
                    [e for e in entities if e.get("label") == "ORG"]
                ),  # Organization mentions
                1 if item.get("language", "en") == "en" else 0,  # Is English
            ]

            features.append(content_features)

        return np.array(features)

    def extract_sentiment_features(
        self, sentiment_data: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Extract features from sentiment analysis results.

        Args:
            sentiment_data: List of sentiment analysis results

        Returns:
            Feature matrix with sentiment features
        """
        if not sentiment_data:
            return np.array([])

        features = []

        for item in sentiment_data:
            sentiment_features = [
                item.get("compound_score", 0),  # VADER compound score
                item.get("positive_score", 0),  # Positive sentiment
                item.get("negative_score", 0),  # Negative sentiment
                item.get("neutral_score", 0),  # Neutral sentiment
                item.get("polarity", 0),  # TextBlob polarity
                item.get("subjectivity", 0),  # TextBlob subjectivity
                item.get("confidence", 0),  # Model confidence
            ]

            features.append(sentiment_features)

        return np.array(features)

    def extract_subreddit_features(self, subreddit_names: List[str]) -> np.ndarray:
        """
        Extract features from subreddit information.

        Args:
            subreddit_names: List of subreddit names

        Returns:
            Feature matrix with subreddit features (one-hot encoded)
        """
        if not subreddit_names:
            return np.array([])

        # Use label encoder for subreddit names
        if "subreddit" not in self.label_encoders:
            self.label_encoders["subreddit"] = LabelEncoder()

        encoder = self.label_encoders["subreddit"]

        try:
            if not self.is_fitted:
                encoded = encoder.fit_transform(subreddit_names)
            else:
                # Handle unseen subreddits
                encoded = []
                for name in subreddit_names:
                    if name in encoder.classes_:
                        encoded.append(encoder.transform([name])[0])
                    else:
                        encoded.append(-1)  # Unknown subreddit
                encoded = np.array(encoded)

            # Convert to one-hot if reasonable number of classes
            if len(encoder.classes_) <= 100:
                one_hot = np.zeros(
                    (len(encoded), len(encoder.classes_) + 1)
                )  # +1 for unknown
                for i, val in enumerate(encoded):
                    if val >= 0:
                        one_hot[i, val] = 1
                    else:
                        one_hot[i, -1] = 1  # Unknown class
                return one_hot
            else:
                # Too many classes, return label encoded
                return encoded.reshape(-1, 1)

        except Exception as e:
            logger.warning(f"Subreddit feature extraction failed: {e}")
            return np.zeros((len(subreddit_names), 1))

    def combine_features(self, *feature_arrays: np.ndarray) -> np.ndarray:
        """
        Combine multiple feature arrays into a single feature matrix.

        Args:
            *feature_arrays: Variable number of feature arrays to combine

        Returns:
            Combined feature matrix
        """
        valid_arrays = [arr for arr in feature_arrays if arr.size > 0]

        if not valid_arrays:
            return np.array([])

        # Ensure all arrays have the same number of samples
        n_samples = valid_arrays[0].shape[0]
        processed_arrays = []

        for arr in valid_arrays:
            if arr.shape[0] != n_samples:
                logger.warning(
                    f"Feature array shape mismatch: {arr.shape[0]} vs {n_samples}"
                )
                continue

            # Ensure 2D array
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)

            processed_arrays.append(arr)

        if not processed_arrays:
            return np.array([])

        try:
            combined = np.hstack(processed_arrays)

            # Scale features if fitted
            if self.is_fitted:
                combined = self.scaler.transform(combined)
            else:
                combined = self.scaler.fit_transform(combined)

            return combined

        except Exception as e:
            logger.error(f"Feature combination failed: {e}")
            return np.array([])

    def fit(self, data: Dict[str, List[Any]]) -> "FeatureExtractor":
        """
        Fit the feature extractor on training data.

        Args:
            data: Dictionary with different types of data for fitting

        Returns:
            Self for method chaining
        """
        logger.info("Fitting feature extractor on training data")

        # Fit text vectorizers
        if "texts" in data and data["texts"]:
            self.extract_text_features(data["texts"])

        # Fit subreddit encoder
        if "subreddits" in data and data["subreddits"]:
            self.extract_subreddit_features(data["subreddits"])

        # Extract and fit other features for scaling
        feature_arrays = []

        if "timestamps" in data and data["timestamps"]:
            feature_arrays.append(self.extract_temporal_features(data["timestamps"]))

        if "engagement" in data and data["engagement"]:
            feature_arrays.append(self.extract_engagement_features(data["engagement"]))

        if "content" in data and data["content"]:
            feature_arrays.append(self.extract_content_features(data["content"]))

        if "sentiment" in data and data["sentiment"]:
            feature_arrays.append(self.extract_sentiment_features(data["sentiment"]))

        # Fit scaler on combined features
        if feature_arrays:
            combined = self.combine_features(*feature_arrays)
            if combined.size > 0:
                self.scaler.fit(combined)

        self.is_fitted = True
        logger.info("Feature extractor fitted successfully")

        return self

    def transform(self, data: Dict[str, List[Any]]) -> np.ndarray:
        """
        Transform data into feature matrix.

        Args:
            data: Dictionary with different types of data to transform

        Returns:
            Feature matrix
        """
        if not self.is_fitted:
            logger.warning("Feature extractor not fitted. Call fit() first.")
            return np.array([])

        feature_arrays = []

        # Extract text features
        if "texts" in data and data["texts"]:
            text_features = self.extract_text_features(data["texts"])
            if text_features.size > 0:
                feature_arrays.append(text_features)

        # Extract other features
        if "timestamps" in data and data["timestamps"]:
            temporal_features = self.extract_temporal_features(data["timestamps"])
            if temporal_features.size > 0:
                feature_arrays.append(temporal_features)

        if "engagement" in data and data["engagement"]:
            engagement_features = self.extract_engagement_features(data["engagement"])
            if engagement_features.size > 0:
                feature_arrays.append(engagement_features)

        if "content" in data and data["content"]:
            content_features = self.extract_content_features(data["content"])
            if content_features.size > 0:
                feature_arrays.append(content_features)

        if "sentiment" in data and data["sentiment"]:
            sentiment_features = self.extract_sentiment_features(data["sentiment"])
            if sentiment_features.size > 0:
                feature_arrays.append(sentiment_features)

        if "subreddits" in data and data["subreddits"]:
            subreddit_features = self.extract_subreddit_features(data["subreddits"])
            if subreddit_features.size > 0:
                feature_arrays.append(subreddit_features)

        # Combine all features
        if feature_arrays:
            return self.combine_features(*feature_arrays)
        else:
            logger.warning("No valid features extracted")
            return np.array([])

    def get_feature_names(self) -> List[str]:
        """
        Get names of all features.

        Returns:
            List of feature names
        """
        feature_names = []

        # Text features
        if hasattr(self.tfidf_vectorizer, "feature_names_out_"):
            feature_names.extend(
                [
                    f"tfidf_{name}"
                    for name in self.tfidf_vectorizer.get_feature_names_out()
                ]
            )

        # Temporal features
        feature_names.extend(
            ["hour", "weekday", "day", "month", "year", "timestamp", "is_weekday"]
        )

        # Engagement features
        feature_names.extend(
            [
                "score",
                "num_comments",
                "upvote_ratio",
                "title_length",
                "selftext_length",
                "body_length",
                "is_stickied",
                "is_locked",
                "is_nsfw",
                "author_comment_karma",
                "author_link_karma",
                "gilded",
            ]
        )

        # Content features
        feature_names.extend(
            [
                "token_count",
                "entity_count",
                "keyword_count",
                "avg_sentence_length",
                "avg_word_length",
                "readability_score",
                "high_value_keywords",
                "person_mentions",
                "org_mentions",
                "is_english",
            ]
        )

        # Sentiment features
        feature_names.extend(
            [
                "compound_score",
                "positive_score",
                "negative_score",
                "neutral_score",
                "polarity",
                "subjectivity",
                "sentiment_confidence",
            ]
        )

        # Subreddit features (would need to be dynamically determined)
        if "subreddit" in self.label_encoders:
            encoder = self.label_encoders["subreddit"]
            if hasattr(encoder, "classes_"):
                feature_names.extend([f"subreddit_{cls}" for cls in encoder.classes_])
                feature_names.append("subreddit_unknown")

        return feature_names
