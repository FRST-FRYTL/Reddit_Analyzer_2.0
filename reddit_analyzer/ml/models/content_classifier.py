"""
Content classification model for Reddit posts and comments.

This module provides machine learning models to classify Reddit content
into categories such as discussion, meme, news, question, etc.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Optional transformers for BERT-based classification
try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. BERT classification disabled.")

logger = logging.getLogger(__name__)


class ContentClassifier:
    """
    Multi-class content classifier for Reddit posts and comments.

    Classifies content into categories like discussion, meme, news, question,
    advice, story, etc. using both traditional ML and transformer models.
    """

    def __init__(
        self,
        model_type: str = "random_forest",
        categories: Optional[List[str]] = None,
        use_transformers: bool = False,
        normalize_features: bool = True,
    ):
        """
        Initialize the content classifier.

        Args:
            model_type: Type of model ('random_forest', 'logistic', 'svm', 'bert')
            categories: List of content categories to classify
            use_transformers: Whether to use transformer-based models
            normalize_features: Whether to normalize features
        """
        self.model_type = model_type
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE
        self.normalize_features = normalize_features

        # Default categories if none provided
        if categories is None:
            self.categories = [
                "discussion",
                "meme",
                "news",
                "question",
                "advice",
                "story",
                "image",
                "video",
                "link",
                "meta",
            ]
        else:
            self.categories = categories

        # Initialize components
        self.model = None
        self.scaler = StandardScaler() if normalize_features else None
        self.label_encoder = LabelEncoder()
        self.transformer_pipeline = None
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
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        elif self.model_type == "logistic":
            self.model = LogisticRegression(
                random_state=42, max_iter=1000, multi_class="ovr"
            )
        elif self.model_type == "svm":
            self.model = SVC(kernel="rbf", random_state=42, probability=True)
        elif self.model_type == "naive_bayes":
            self.model = MultinomialNB()
        elif self.model_type == "gradient_boost":
            self.model = GradientBoostingClassifier(
                n_estimators=100, max_depth=6, random_state=42
            )
        elif self.model_type == "bert" and self.use_transformers:
            self._initialize_bert_model()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        logger.info(
            f"Initialized {self.model_type} classifier with {len(self.categories)} categories"
        )

    def _initialize_bert_model(self):
        """Initialize BERT-based classifier."""
        try:
            # Use a pre-trained model for text classification
            model_name = "microsoft/DialoGPT-medium"  # Can be changed to other models
            self.transformer_pipeline = pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                max_length=512,
                truncation=True,
            )
            logger.info("BERT classifier initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize BERT model: {e}")
            # Fallback to traditional model
            self.model_type = "random_forest"
            self._initialize_model()

    def prepare_features(
        self, data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and labels from Reddit data.

        Args:
            data: List of Reddit post/comment dictionaries

        Returns:
            Tuple of (feature_matrix, label_array)
        """
        if not data:
            return np.array([]), np.array([])

        features = []
        labels = []

        for item in data:
            # Extract various feature types
            content_features = self._extract_content_features(item)
            metadata_features = self._extract_metadata_features(item)
            engagement_features = self._extract_engagement_features(item)

            # Combine features
            item_features = content_features + metadata_features + engagement_features

            # Extract label
            label = self._extract_label(item)

            if label is not None:
                features.append(item_features)
                labels.append(label)

        if not features:
            return np.array([]), np.array([])

        # Convert to numpy arrays
        X = np.array(features)
        y = np.array(labels)

        # Store feature names
        if not self.feature_names:
            self.feature_names = self._get_feature_names()

        return X, y

    def _extract_content_features(self, item: Dict[str, Any]) -> List[float]:
        """Extract content-based features."""
        title = item.get("title", "") or ""
        content = item.get("selftext", "") or item.get("body", "") or ""
        url = item.get("url", "") or ""

        features = [
            # Basic text features
            len(title),
            len(content),
            len(title.split()),
            len(content.split()),
            # Question indicators
            title.count("?"),
            content.count("?"),
            (
                1
                if any(
                    word in title.lower()
                    for word in ["how", "what", "why", "when", "where", "who"]
                )
                else 0
            ),
            1 if title.lower().startswith(("how to", "what is", "why does")) else 0,
            # News indicators
            (
                1
                if any(
                    word in title.lower()
                    for word in ["breaking", "news", "report", "update", "announcement"]
                )
                else 0
            ),
            (
                1
                if any(
                    word in content.lower()
                    for word in ["according to", "reported", "sources say"]
                )
                else 0
            ),
            # Discussion indicators
            (
                1
                if any(
                    word in title.lower()
                    for word in ["discussion", "thoughts", "opinion", "debate"]
                )
                else 0
            ),
            (
                1
                if any(
                    word in title.lower()
                    for word in ["what do you think", "your thoughts", "discussion"]
                )
                else 0
            ),
            # Meme/humor indicators
            (
                1
                if any(
                    word in title.lower()
                    for word in ["meme", "funny", "lol", "humor", "joke"]
                )
                else 0
            ),
            title.count("!"),
            (
                1
                if any(
                    caps_word in title
                    for caps_word in title.split()
                    if caps_word.isupper() and len(caps_word) > 2
                )
                else 0
            ),
            # Advice indicators
            (
                1
                if any(
                    word in title.lower()
                    for word in ["advice", "help", "need help", "suggestions"]
                )
                else 0
            ),
            (
                1
                if title.lower().startswith(
                    ("need advice", "help me", "looking for advice")
                )
                else 0
            ),
            # Story indicators
            (
                1
                if any(
                    word in title.lower()
                    for word in ["story", "happened", "experience", "today"]
                )
                else 0
            ),
            (
                1
                if any(
                    word in content.lower()
                    for word in ["so today", "this happened", "long story"]
                )
                else 0
            ),
            # Media indicators
            (
                1
                if any(
                    word in title.lower()
                    for word in ["image", "pic", "photo", "picture"]
                )
                else 0
            ),
            (
                1
                if any(word in title.lower() for word in ["video", "clip", "watch"])
                else 0
            ),
            (
                1
                if url
                and any(
                    domain in url
                    for domain in ["imgur", "youtube", "reddit.com/gallery"]
                )
                else 0
            ),
            (
                1 if url and not url.startswith("https://www.reddit.com") else 0
            ),  # External link
        ]

        # Sentiment features (if available)
        sentiment = item.get("sentiment", {})
        features.extend(
            [
                sentiment.get("compound_score", 0),
                sentiment.get("positive_score", 0),
                sentiment.get("negative_score", 0),
                1 if sentiment.get("sentiment_label", "NEUTRAL") == "POSITIVE" else 0,
                1 if sentiment.get("sentiment_label", "NEUTRAL") == "NEGATIVE" else 0,
            ]
        )

        # Text complexity features
        text_analysis = item.get("text_analysis", {})
        readability = text_analysis.get("readability", {})
        features.extend(
            [
                readability.get("avg_word_length", 0),
                readability.get("avg_sentence_length", 0),
                readability.get("readability_score", 0),
                len(text_analysis.get("entities", [])),
                len(text_analysis.get("keywords", [])),
            ]
        )

        return features

    def _extract_metadata_features(self, item: Dict[str, Any]) -> List[float]:
        """Extract metadata features."""
        features = [
            1 if item.get("stickied", False) else 0,
            1 if item.get("locked", False) else 0,
            1 if item.get("over_18", False) else 0,
            1 if item.get("spoiler", False) else 0,
            1 if item.get("is_original_content", False) else 0,
            len(item.get("link_flair_text", "") or ""),
            1 if item.get("is_self", True) else 0,
        ]

        # Subreddit characteristics
        subreddit = item.get("subreddit", {})
        if isinstance(subreddit, dict):
            subreddit_name = subreddit.get("display_name", "").lower()
            features.extend(
                [
                    (
                        1
                        if any(
                            word in subreddit_name for word in ["meme", "funny", "joke"]
                        )
                        else 0
                    ),
                    (
                        1
                        if any(word in subreddit_name for word in ["news", "worldnews"])
                        else 0
                    ),
                    (
                        1
                        if any(
                            word in subreddit_name for word in ["ask", "help", "advice"]
                        )
                        else 0
                    ),
                    (
                        1
                        if any(
                            word in subreddit_name for word in ["pic", "photo", "image"]
                        )
                        else 0
                    ),
                    (
                        1
                        if any(word in subreddit_name for word in ["video", "gif"])
                        else 0
                    ),
                ]
            )
        else:
            features.extend([0, 0, 0, 0, 0])

        return features

    def _extract_engagement_features(self, item: Dict[str, Any]) -> List[float]:
        """Extract engagement-based features."""
        features = [
            np.log1p(item.get("score", 0)),  # Log-transformed score
            item.get("upvote_ratio", 0.5),
            np.log1p(item.get("num_comments", 0)),  # Log-transformed comment count
            item.get("gilded", 0),
        ]

        # Author features
        author = item.get("author", {})
        if isinstance(author, dict):
            features.extend(
                [
                    np.log1p(author.get("comment_karma", 0)),
                    np.log1p(author.get("link_karma", 0)),
                    1 if author.get("is_gold", False) else 0,
                ]
            )
        else:
            features.extend([0, 0, 0])

        return features

    def _extract_label(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract ground truth label from item."""
        # Check if label is explicitly provided
        if "category" in item:
            return item["category"]

        if "content_type" in item:
            return item["content_type"]

        # Auto-labeling based on content analysis (for unlabeled data)
        return self._auto_label(item)

    def _auto_label(self, item: Dict[str, Any]) -> str:
        """Automatically assign a label based on content patterns."""
        title = (item.get("title", "") or "").lower()
        url = item.get("url", "") or ""

        # Rule-based auto-labeling
        if any(word in title for word in ["?", "how", "what", "why", "help me"]):
            return "question"
        elif any(word in title for word in ["meme", "funny", "lol", "humor"]):
            return "meme"
        elif any(word in title for word in ["breaking", "news", "report"]):
            return "news"
        elif any(word in title for word in ["advice", "suggestions", "help"]):
            return "advice"
        elif any(word in title for word in ["story", "happened", "experience"]):
            return "story"
        elif (
            any(domain in url for domain in ["imgur", "i.redd.it"]) or "image" in title
        ):
            return "image"
        elif (
            any(domain in url for domain in ["youtube", "streamable"])
            or "video" in title
        ):
            return "video"
        elif url and not url.startswith("https://www.reddit.com"):
            return "link"
        elif any(word in title for word in ["discussion", "thoughts", "opinion"]):
            return "discussion"
        else:
            return "discussion"  # Default category

    def _get_feature_names(self) -> List[str]:
        """Get names of all features."""
        return [
            # Content features
            "title_length",
            "content_length",
            "title_word_count",
            "content_word_count",
            "title_questions",
            "content_questions",
            "has_question_words",
            "starts_with_question",
            "has_news_words",
            "has_news_phrases",
            "has_discussion_words",
            "has_discussion_phrases",
            "has_meme_words",
            "exclamation_count",
            "has_caps_words",
            "has_advice_words",
            "starts_with_advice",
            "has_story_words",
            "has_story_phrases",
            "has_image_words",
            "has_video_words",
            "has_media_url",
            "has_external_url",
            # Sentiment features
            "sentiment_compound",
            "sentiment_positive",
            "sentiment_negative",
            "is_positive_sentiment",
            "is_negative_sentiment",
            # Text complexity
            "avg_word_length",
            "avg_sentence_length",
            "readability_score",
            "entity_count",
            "keyword_count",
            # Metadata features
            "is_stickied",
            "is_locked",
            "is_nsfw",
            "is_spoiler",
            "is_oc",
            "flair_length",
            "is_self_post",
            # Subreddit features
            "subreddit_is_meme",
            "subreddit_is_news",
            "subreddit_is_help",
            "subreddit_is_pics",
            "subreddit_is_video",
            # Engagement features
            "log_score",
            "upvote_ratio",
            "log_comments",
            "gilded",
            "log_author_comment_karma",
            "log_author_link_karma",
            "author_is_gold",
        ]

    def fit(
        self,
        training_data: List[Dict[str, Any]],
        validation_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Train the content classification model.

        Args:
            training_data: Training data as list of item dictionaries
            validation_data: Optional validation data for evaluation

        Returns:
            Dictionary with training results and metrics
        """
        logger.info(
            f"Training {self.model_type} classifier with {len(self.categories)} categories"
        )

        # Prepare training features and labels
        X_train, y_train = self.prepare_features(training_data)

        if len(X_train) == 0:
            logger.error("No valid training data available")
            return {"error": "No valid training data"}

        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(y_train)

        # Normalize features if requested
        if self.normalize_features and self.scaler:
            X_train = self.scaler.fit_transform(X_train)

        # Train the model
        try:
            if self.model_type == "bert" and self.transformer_pipeline:
                # BERT training is different (fine-tuning would be needed)
                # For now, we'll use the pre-trained model
                self.is_fitted = True
                logger.info("Using pre-trained BERT model")
            else:
                self.model.fit(X_train, y_train_encoded)
                self.is_fitted = True

                # Calculate training metrics
                y_train_pred = self.model.predict(X_train)
                self.training_metrics = self._calculate_metrics(
                    y_train_encoded, y_train_pred
                )

                logger.info(
                    f"Training completed. Accuracy: {self.training_metrics['accuracy']:.3f}"
                )

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"error": f"Training failed: {e}"}

        # Evaluate on validation data if provided
        if validation_data and self.model_type != "bert":
            X_val, y_val = self.prepare_features(validation_data)
            if len(X_val) > 0:
                y_val_encoded = self.label_encoder.transform(y_val)

                if self.normalize_features and self.scaler:
                    X_val = self.scaler.transform(X_val)

                y_val_pred = self.model.predict(X_val)
                self.validation_metrics = self._calculate_metrics(
                    y_val_encoded, y_val_pred
                )

                logger.info(
                    f"Validation accuracy: {self.validation_metrics['accuracy']:.3f}"
                )

        # Feature importance (for tree-based models)
        feature_importance = self._get_feature_importance()

        results = {
            "model_type": self.model_type,
            "categories": self.categories,
            "training_samples": len(X_train),
            "features_count": X_train.shape[1] if len(X_train) > 0 else 0,
            "training_metrics": self.training_metrics,
            "validation_metrics": self.validation_metrics,
            "feature_importance": feature_importance,
            "training_timestamp": datetime.now().isoformat(),
        }

        return results

    def predict(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predict content categories for new items.

        Args:
            data: List of item dictionaries to classify

        Returns:
            List of classification results
        """
        if not self.is_fitted:
            logger.warning("Model not fitted. Call fit() first.")
            return []

        results = []

        for i, item in enumerate(data):
            try:
                if self.model_type == "bert" and self.transformer_pipeline:
                    result = self._predict_with_bert(item, i)
                else:
                    result = self._predict_with_traditional(item, i)

                results.append(result)

            except Exception as e:
                logger.warning(f"Failed to classify item {i}: {e}")
                results.append(self._empty_prediction(item, i))

        return results

    def _predict_with_traditional(
        self, item: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Predict using traditional ML models."""
        # Prepare features
        X, _ = self.prepare_features([item])

        if len(X) == 0:
            return self._empty_prediction(item, index)

        # Normalize features if needed
        if self.normalize_features and self.scaler:
            X = self.scaler.transform(X)

        # Make prediction
        prediction = self.model.predict(X[0].reshape(1, -1))[0]
        probabilities = self.model.predict_proba(X[0].reshape(1, -1))[0]

        # Decode prediction
        predicted_category = self.label_encoder.inverse_transform([prediction])[0]

        # Create probability distribution
        prob_dist = {}
        for i, category in enumerate(self.label_encoder.classes_):
            prob_dist[self.label_encoder.inverse_transform([category])[0]] = float(
                probabilities[i]
            )

        result = {
            "item_id": item.get("id", f"item_{index}"),
            "predicted_category": predicted_category,
            "confidence": float(max(probabilities)),
            "probability_distribution": prob_dist,
            "prediction_timestamp": datetime.now().isoformat(),
        }

        # Add actual category if available
        actual = item.get("category") or item.get("content_type")
        if actual:
            result["actual_category"] = actual
            result["correct"] = actual == predicted_category

        return result

    def _predict_with_bert(self, item: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Predict using BERT model."""
        # Combine title and content for BERT
        title = item.get("title", "") or ""
        content = item.get("selftext", "") or item.get("body", "") or ""
        text = f"{title} {content}".strip()

        if not text:
            return self._empty_prediction(item, index)

        # Truncate if too long
        if len(text) > 500:
            text = text[:500]

        try:
            # Get BERT prediction
            bert_result = self.transformer_pipeline(text)[0]

            # Map BERT labels to our categories (this is simplified)
            label_mapping = {
                "POSITIVE": "discussion",
                "NEGATIVE": "discussion",
                "NEUTRAL": "discussion",
            }

            predicted_category = label_mapping.get(bert_result["label"], "discussion")
            confidence = bert_result["score"]

            result = {
                "item_id": item.get("id", f"item_{index}"),
                "predicted_category": predicted_category,
                "confidence": float(confidence),
                "bert_label": bert_result["label"],
                "bert_score": float(bert_result["score"]),
                "prediction_timestamp": datetime.now().isoformat(),
            }

            return result

        except Exception as e:
            logger.warning(f"BERT prediction failed: {e}")
            return self._empty_prediction(item, index)

    def _calculate_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Calculate classification metrics."""
        return {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision_macro": precision_score(
                y_true, y_pred, average="macro", zero_division=0
            ),
            "recall_macro": recall_score(
                y_true, y_pred, average="macro", zero_division=0
            ),
            "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
            "precision_weighted": precision_score(
                y_true, y_pred, average="weighted", zero_division=0
            ),
            "recall_weighted": recall_score(
                y_true, y_pred, average="weighted", zero_division=0
            ),
            "f1_weighted": f1_score(
                y_true, y_pred, average="weighted", zero_division=0
            ),
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

        return dict(sorted(importance_scores.items(), key=lambda x: x[1], reverse=True))

    def _empty_prediction(self, item: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Return empty prediction result."""
        return {
            "item_id": item.get("id", f"item_{index}"),
            "predicted_category": "discussion",
            "confidence": 0.0,
            "prediction_timestamp": datetime.now().isoformat(),
            "error": "Prediction failed",
        }

    def get_classification_report(self, data: List[Dict[str, Any]]) -> str:
        """Generate detailed classification report."""
        if not self.is_fitted:
            return "Model not fitted"

        X, y_true = self.prepare_features(data)

        if len(X) == 0:
            return "No valid data"

        y_true_encoded = self.label_encoder.transform(y_true)

        if self.normalize_features and self.scaler:
            X = self.scaler.transform(X)

        y_pred = self.model.predict(X)

        target_names = [
            self.label_encoder.inverse_transform([i])[0]
            for i in range(len(self.categories))
        ]

        return classification_report(y_true_encoded, y_pred, target_names=target_names)

    def save_model(self, filepath: str):
        """Save the trained model to file."""
        if not self.is_fitted:
            logger.warning("No fitted model to save")
            return

        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "label_encoder": self.label_encoder,
                "model_type": self.model_type,
                "categories": self.categories,
                "feature_names": self.feature_names,
                "training_metrics": self.training_metrics,
                "validation_metrics": self.validation_metrics,
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
            self.label_encoder = model_data["label_encoder"]
            self.model_type = model_data["model_type"]
            self.categories = model_data["categories"]
            self.feature_names = model_data["feature_names"]
            self.training_metrics = model_data["training_metrics"]
            self.validation_metrics = model_data["validation_metrics"]

            self.is_fitted = True
            logger.info(f"Model loaded from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
