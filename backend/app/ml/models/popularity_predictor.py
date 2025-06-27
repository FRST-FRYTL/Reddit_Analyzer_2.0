"""
Popularity prediction model for Reddit posts.

This module provides machine learning models to predict the popularity
of Reddit posts based on content, timing, and metadata features.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime
import joblib

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class PopularityPredictor:
    """
    Machine learning model for predicting Reddit post popularity.

    Predicts post scores based on content features, timing, metadata,
    and historical patterns using ensemble methods.
    """

    def __init__(
        self,
        model_type: str = "random_forest",
        target_metric: str = "score",
        normalize_features: bool = True,
    ):
        """
        Initialize the popularity predictor.

        Args:
            model_type: Type of model to use ('random_forest', 'gradient_boost', 'linear', 'ensemble')
            target_metric: Target metric to predict ('score', 'upvote_ratio', 'num_comments')
            normalize_features: Whether to normalize features
        """
        self.model_type = model_type
        self.target_metric = target_metric
        self.normalize_features = normalize_features

        # Initialize models
        self.model = None
        self.scaler = StandardScaler() if normalize_features else None
        self.feature_names = []
        self.is_fitted = False

        # Performance metrics
        self.training_metrics = {}
        self.validation_metrics = {}

        # Initialize the selected model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the machine learning model based on type."""
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        elif self.model_type == "gradient_boost":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )
        elif self.model_type == "linear":
            self.model = Ridge(alpha=1.0)
        elif self.model_type == "svm":
            self.model = SVR(kernel="rbf", C=1.0, gamma="scale")
        elif self.model_type == "ensemble":
            # Will be implemented as a voting regressor
            self.model = self._create_ensemble_model()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        logger.info(
            f"Initialized {self.model_type} model for {self.target_metric} prediction"
        )

    def _create_ensemble_model(self):
        """Create an ensemble model combining multiple algorithms."""
        from sklearn.ensemble import VotingRegressor

        models = [
            ("rf", RandomForestRegressor(n_estimators=50, random_state=42)),
            ("gb", GradientBoostingRegressor(n_estimators=50, random_state=42)),
            ("ridge", Ridge(alpha=1.0)),
        ]

        return VotingRegressor(estimators=models)

    def prepare_features(
        self, data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and targets from Reddit post data.

        Args:
            data: List of Reddit post dictionaries

        Returns:
            Tuple of (feature_matrix, target_array)
        """
        if not data:
            return np.array([]), np.array([])

        features = []
        targets = []

        for post in data:
            # Extract content features
            content_features = self._extract_content_features(post)

            # Extract temporal features
            temporal_features = self._extract_temporal_features(post)

            # Extract metadata features
            metadata_features = self._extract_metadata_features(post)

            # Extract author features
            author_features = self._extract_author_features(post)

            # Combine all features
            post_features = (
                content_features
                + temporal_features
                + metadata_features
                + author_features
            )

            # Extract target
            target = self._extract_target(post)

            if target is not None:
                features.append(post_features)
                targets.append(target)

        if not features:
            return np.array([]), np.array([])

        # Convert to numpy arrays
        X = np.array(features)
        y = np.array(targets)

        # Store feature names for the first fit
        if not self.feature_names:
            self.feature_names = self._get_feature_names()

        return X, y

    def _extract_content_features(self, post: Dict[str, Any]) -> List[float]:
        """Extract content-based features from post."""
        title = post.get("title", "")
        selftext = post.get("selftext", "")

        features = [
            len(title),  # Title length
            len(selftext),  # Content length
            len(title.split()),  # Title word count
            len(selftext.split()),  # Content word count
            title.count("?"),  # Question marks in title
            title.count("!"),  # Exclamation marks in title
            len([w for w in title.split() if w.isupper()]),  # Uppercase words
            (
                1
                if any(
                    word in title.lower() for word in ["breaking", "urgent", "update"]
                )
                else 0
            ),  # News keywords
            (
                1
                if any(word in title.lower() for word in ["ama", "ask", "question"])
                else 0
            ),  # Interactive keywords
            (
                1
                if any(
                    word in title.lower() for word in ["video", "image", "gif", "pic"]
                )
                else 0
            ),  # Media keywords
        ]

        # Sentiment features (if available)
        sentiment = post.get("sentiment", {})
        features.extend(
            [
                sentiment.get("compound_score", 0),
                sentiment.get("positive_score", 0),
                sentiment.get("negative_score", 0),
                sentiment.get("confidence", 0),
            ]
        )

        # Text analysis features (if available)
        text_analysis = post.get("text_analysis", {})
        stats = text_analysis.get("stats", {})
        readability = text_analysis.get("readability", {})

        features.extend(
            [
                stats.get("token_count", 0),
                stats.get("entity_count", 0),
                stats.get("keyword_count", 0),
                readability.get("readability_score", 0),
                len(text_analysis.get("entities", [])),
                1 if text_analysis.get("language", "en") == "en" else 0,
            ]
        )

        return features

    def _extract_temporal_features(self, post: Dict[str, Any]) -> List[float]:
        """Extract temporal features from post."""
        created_utc = post.get("created_utc")

        if created_utc:
            if isinstance(created_utc, (int, float)):
                dt = datetime.fromtimestamp(created_utc)
            elif isinstance(created_utc, datetime):
                dt = created_utc
            else:
                dt = datetime.now()
        else:
            dt = datetime.now()

        features = [
            dt.hour,  # Hour of day (0-23)
            dt.weekday(),  # Day of week (0-6)
            dt.day,  # Day of month
            dt.month,  # Month
            1 if dt.weekday() < 5 else 0,  # Is weekday
            1 if 9 <= dt.hour <= 17 else 0,  # Is business hours
            1 if 18 <= dt.hour <= 22 else 0,  # Is prime time
            1 if dt.weekday() in [5, 6] else 0,  # Is weekend
        ]

        return features

    def _extract_metadata_features(self, post: Dict[str, Any]) -> List[float]:
        """Extract metadata features from post."""
        features = [
            1 if post.get("stickied", False) else 0,
            1 if post.get("locked", False) else 0,
            1 if post.get("over_18", False) else 0,
            1 if post.get("spoiler", False) else 0,
            1 if post.get("is_original_content", False) else 0,
            post.get("gilded", 0),
            len(post.get("link_flair_text", "") or ""),
            1 if post.get("is_self", True) else 0,  # Is text post
            1 if post.get("url", "").startswith("http") else 0,  # Has external URL
        ]

        # Subreddit features
        subreddit = post.get("subreddit", {})
        if isinstance(subreddit, dict):
            features.extend(
                [
                    subreddit.get("subscribers", 0)
                    / 1000000,  # Subreddit size (millions)
                    1 if subreddit.get("over18", False) else 0,
                    len(subreddit.get("description", "") or ""),
                ]
            )
        else:
            features.extend([0, 0, 0])

        return features

    def _extract_author_features(self, post: Dict[str, Any]) -> List[float]:
        """Extract author-related features from post."""
        author = post.get("author", {})

        if isinstance(author, dict):
            features = [
                author.get("comment_karma", 0) / 1000,  # Comment karma (thousands)
                author.get("link_karma", 0) / 1000,  # Link karma (thousands)
                1 if author.get("has_verified_email", False) else 0,
                1 if author.get("is_gold", False) else 0,
                author.get("total_karma", 0) / 1000,  # Total karma (thousands)
            ]
        else:
            features = [0, 0, 0, 0, 0]

        # Author activity features (if available)
        author_metrics = post.get("author_metrics", {})
        features.extend(
            [
                author_metrics.get("activity_score", 0),
                author_metrics.get("influence_score", 0),
                author_metrics.get("avg_score", 0),
            ]
        )

        return features

    def _extract_target(self, post: Dict[str, Any]) -> Optional[float]:
        """Extract target variable from post."""
        target_value = post.get(self.target_metric)

        if target_value is None:
            return None

        # Apply transformations based on target type
        if self.target_metric == "score":
            # Log transform for scores to handle wide range
            return np.log1p(max(0, target_value))
        elif self.target_metric == "upvote_ratio":
            # Keep as-is (already 0-1 range)
            return float(target_value)
        elif self.target_metric == "num_comments":
            # Square root transform for comment counts
            return np.sqrt(max(0, target_value))
        else:
            return float(target_value)

    def _get_feature_names(self) -> List[str]:
        """Get names of all features."""
        names = [
            # Content features
            "title_length",
            "content_length",
            "title_word_count",
            "content_word_count",
            "question_marks",
            "exclamation_marks",
            "uppercase_words",
            "news_keywords",
            "interactive_keywords",
            "media_keywords",
            # Sentiment features
            "sentiment_compound",
            "sentiment_positive",
            "sentiment_negative",
            "sentiment_confidence",
            # Text analysis features
            "token_count",
            "entity_count",
            "keyword_count",
            "readability_score",
            "num_entities",
            "is_english",
            # Temporal features
            "hour",
            "weekday",
            "day",
            "month",
            "is_weekday",
            "is_business_hours",
            "is_prime_time",
            "is_weekend",
            # Metadata features
            "is_stickied",
            "is_locked",
            "is_nsfw",
            "is_spoiler",
            "is_oc",
            "gilded",
            "flair_length",
            "is_self_post",
            "has_external_url",
            "subreddit_size",
            "subreddit_nsfw",
            "subreddit_desc_length",
            # Author features
            "author_comment_karma",
            "author_link_karma",
            "author_verified_email",
            "author_is_gold",
            "author_total_karma",
            "author_activity_score",
            "author_influence_score",
            "author_avg_score",
        ]

        return names

    def fit(
        self,
        training_data: List[Dict[str, Any]],
        validation_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Train the popularity prediction model.

        Args:
            training_data: Training data as list of post dictionaries
            validation_data: Optional validation data for evaluation

        Returns:
            Dictionary with training results and metrics
        """
        logger.info(
            f"Training {self.model_type} model for {self.target_metric} prediction"
        )

        # Prepare training features and targets
        X_train, y_train = self.prepare_features(training_data)

        if len(X_train) == 0:
            logger.error("No valid training data available")
            return {"error": "No valid training data"}

        # Normalize features if requested
        if self.normalize_features and self.scaler:
            X_train = self.scaler.fit_transform(X_train)

        # Train the model
        try:
            self.model.fit(X_train, y_train)
            self.is_fitted = True

            # Calculate training metrics
            y_train_pred = self.model.predict(X_train)
            self.training_metrics = self._calculate_metrics(y_train, y_train_pred)

            logger.info(
                f"Training completed. R² score: {self.training_metrics['r2']:.3f}"
            )

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"error": f"Training failed: {e}"}

        # Evaluate on validation data if provided
        if validation_data:
            X_val, y_val = self.prepare_features(validation_data)
            if len(X_val) > 0:
                if self.normalize_features and self.scaler:
                    X_val = self.scaler.transform(X_val)

                y_val_pred = self.model.predict(X_val)
                self.validation_metrics = self._calculate_metrics(y_val, y_val_pred)

                logger.info(f"Validation R² score: {self.validation_metrics['r2']:.3f}")

        # Feature importance (for tree-based models)
        feature_importance = self._get_feature_importance()

        results = {
            "model_type": self.model_type,
            "target_metric": self.target_metric,
            "training_samples": len(X_train),
            "features_count": X_train.shape[1],
            "training_metrics": self.training_metrics,
            "validation_metrics": self.validation_metrics,
            "feature_importance": feature_importance,
            "training_timestamp": datetime.now().isoformat(),
        }

        return results

    def predict(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predict popularity for new posts.

        Args:
            data: List of post dictionaries to predict for

        Returns:
            List of prediction results
        """
        if not self.is_fitted:
            logger.warning("Model not fitted. Call fit() first.")
            return []

        # Prepare features
        X, _ = self.prepare_features(data)

        if len(X) == 0:
            return []

        # Normalize features if needed
        if self.normalize_features and self.scaler:
            X = self.scaler.transform(X)

        # Make predictions
        try:
            predictions = self.model.predict(X)

            # Transform predictions back to original scale
            if self.target_metric == "score":
                predictions = np.expm1(predictions)  # Inverse of log1p
            elif self.target_metric == "num_comments":
                predictions = np.square(predictions)  # Inverse of sqrt

            # Ensure non-negative predictions
            predictions = np.maximum(predictions, 0)

            # Create results
            results = []
            for i, (post, pred) in enumerate(zip(data, predictions)):
                result = {
                    "post_id": post.get("id", f"post_{i}"),
                    "predicted_value": float(pred),
                    "target_metric": self.target_metric,
                    "confidence": self._calculate_prediction_confidence(X[i]),
                    "prediction_timestamp": datetime.now().isoformat(),
                }

                # Add actual value if available for comparison
                actual = post.get(self.target_metric)
                if actual is not None:
                    result["actual_value"] = actual
                    result["error"] = abs(pred - actual)
                    result["relative_error"] = abs(pred - actual) / max(actual, 1)

                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return []

    def _calculate_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Calculate regression metrics."""
        return {
            "r2": r2_score(y_true, y_pred),
            "mse": mean_squared_error(y_true, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            "mae": mean_absolute_error(y_true, y_pred),
            "mape": np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100,
        }

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not hasattr(self.model, "feature_importances_"):
            return {}

        importance_scores = {}
        for name, importance in zip(
            self.feature_names, self.model.feature_importances_
        ):
            importance_scores[name] = float(importance)

        # Sort by importance
        return dict(sorted(importance_scores.items(), key=lambda x: x[1], reverse=True))

    def _calculate_prediction_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence score for a prediction."""
        # For tree-based models, use prediction variance
        if hasattr(self.model, "estimators_"):
            try:
                # Get predictions from all trees
                tree_predictions = np.array(
                    [
                        tree.predict(features.reshape(1, -1))[0]
                        for tree in self.model.estimators_
                    ]
                )

                # Calculate confidence as inverse of variance
                variance = np.var(tree_predictions)
                confidence = 1.0 / (1.0 + variance)
                return float(confidence)
            except Exception:
                pass

        # Default confidence
        return 0.5

    def cross_validate(
        self, data: List[Dict[str, Any]], cv_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Perform cross-validation on the model.

        Args:
            data: Data for cross-validation
            cv_folds: Number of cross-validation folds

        Returns:
            Cross-validation results
        """
        X, y = self.prepare_features(data)

        if len(X) == 0:
            return {"error": "No valid data for cross-validation"}

        if self.normalize_features and self.scaler:
            X = self.scaler.fit_transform(X)

        try:
            # Perform cross-validation
            cv_scores = cross_val_score(
                self.model, X, y, cv=cv_folds, scoring="r2", n_jobs=-1
            )

            cv_mse = -cross_val_score(
                self.model,
                X,
                y,
                cv=cv_folds,
                scoring="neg_mean_squared_error",
                n_jobs=-1,
            )

            results = {
                "cv_folds": cv_folds,
                "r2_scores": cv_scores.tolist(),
                "r2_mean": float(cv_scores.mean()),
                "r2_std": float(cv_scores.std()),
                "mse_scores": cv_mse.tolist(),
                "mse_mean": float(cv_mse.mean()),
                "mse_std": float(cv_mse.std()),
            }

            logger.info(
                f"Cross-validation R² score: {results['r2_mean']:.3f} ± {results['r2_std']:.3f}"
            )

            return results

        except Exception as e:
            logger.error(f"Cross-validation failed: {e}")
            return {"error": f"Cross-validation failed: {e}"}

    def save_model(self, filepath: str):
        """Save the trained model to file."""
        if not self.is_fitted:
            logger.warning("No fitted model to save")
            return

        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "model_type": self.model_type,
                "target_metric": self.target_metric,
                "feature_names": self.feature_names,
                "training_metrics": self.training_metrics,
                "validation_metrics": self.validation_metrics,
                "normalize_features": self.normalize_features,
            }

            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def load_model(self, filepath: str):
        """Load a trained model from file."""
        try:
            model_data = joblib.load(filepath)

            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.model_type = model_data["model_type"]
            self.target_metric = model_data["target_metric"]
            self.feature_names = model_data["feature_names"]
            self.training_metrics = model_data["training_metrics"]
            self.validation_metrics = model_data["validation_metrics"]
            self.normalize_features = model_data["normalize_features"]

            self.is_fitted = True
            logger.info(f"Model loaded from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
