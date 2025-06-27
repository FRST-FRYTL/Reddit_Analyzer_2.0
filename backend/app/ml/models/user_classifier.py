"""
User classification and behavior analysis model for Reddit users.

This module provides machine learning models to classify Reddit users
based on their behavior patterns, content preferences, and engagement metrics.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler, LabelEncoder

logger = logging.getLogger(__name__)


class UserClassifier:
    """
    User classification and behavior analysis system.

    Classifies users into behavioral categories like lurker, casual_user,
    active_user, power_user, content_creator, etc. based on activity patterns.
    """

    def __init__(
        self,
        classification_type: str = "activity_level",
        model_type: str = "random_forest",
        user_categories: Optional[List[str]] = None,
    ):
        """
        Initialize the user classifier.

        Args:
            classification_type: Type of classification ('activity_level', 'behavior_type', 'cluster')
            model_type: ML model to use ('random_forest', 'logistic', 'kmeans')
            user_categories: List of user categories for supervised learning
        """
        self.classification_type = classification_type
        self.model_type = model_type

        # Default categories based on classification type
        if user_categories is None:
            if classification_type == "activity_level":
                self.user_categories = ["lurker", "casual", "active", "power_user"]
            elif classification_type == "behavior_type":
                self.user_categories = [
                    "consumer",
                    "commenter",
                    "poster",
                    "creator",
                    "moderator",
                ]
            else:
                self.user_categories = []
        else:
            self.user_categories = user_categories

        # Initialize components
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.is_fitted = False

        # For clustering
        self.cluster_labels = {}
        self.cluster_centers = None

        # Performance metrics
        self.training_metrics = {}
        self.validation_metrics = {}

        # Initialize the model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the machine learning model."""
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
        elif self.model_type == "gradient_boost":
            self.model = GradientBoostingClassifier(
                n_estimators=100, max_depth=6, random_state=42
            )
        elif self.model_type == "kmeans":
            n_clusters = len(self.user_categories) if self.user_categories else 4
            self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif self.model_type == "dbscan":
            self.model = DBSCAN(eps=0.5, min_samples=5)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        logger.info(
            f"Initialized {self.model_type} user classifier for {self.classification_type}"
        )

    def prepare_user_features(
        self, user_data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare user features from Reddit activity data.

        Args:
            user_data: List of user dictionaries with activity data

        Returns:
            Tuple of (feature_matrix, label_array)
        """
        if not user_data:
            return np.array([]), np.array([])

        features = []
        labels = []

        for user in user_data:
            # Extract comprehensive user features
            activity_features = self._extract_activity_features(user)
            content_features = self._extract_content_features(user)
            engagement_features = self._extract_engagement_features(user)
            temporal_features = self._extract_temporal_features(user)
            community_features = self._extract_community_features(user)

            # Combine all features
            user_features = (
                activity_features
                + content_features
                + engagement_features
                + temporal_features
                + community_features
            )

            # Extract label
            label = self._extract_user_label(user)

            features.append(user_features)
            if label is not None:
                labels.append(label)
            else:
                labels.append("unknown")  # For unsupervised learning

        # Convert to numpy arrays
        X = np.array(features)
        y = (
            np.array(labels)
            if any(label != "unknown" for label in labels)
            else np.array([])
        )

        # Store feature names
        if not self.feature_names:
            self.feature_names = self._get_feature_names()

        return X, y

    def _extract_activity_features(self, user: Dict[str, Any]) -> List[float]:
        """Extract activity-based features."""
        posts = user.get("posts", [])
        comments = user.get("comments", [])

        # Basic activity metrics
        total_posts = len(posts)
        total_comments = len(comments)
        total_activity = total_posts + total_comments

        # Calculate activity over time periods
        now = datetime.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        recent_posts = len(
            [
                p
                for p in posts
                if self._parse_timestamp(p.get("created_utc")) > last_week
            ]
        )
        recent_comments = len(
            [
                c
                for c in comments
                if self._parse_timestamp(c.get("created_utc")) > last_week
            ]
        )

        monthly_posts = len(
            [
                p
                for p in posts
                if self._parse_timestamp(p.get("created_utc")) > last_month
            ]
        )
        monthly_comments = len(
            [
                c
                for c in comments
                if self._parse_timestamp(c.get("created_utc")) > last_month
            ]
        )

        # Account age and activity ratios
        account_created = self._parse_timestamp(user.get("created_utc"))
        account_age_days = (now - account_created).days if account_created else 1

        features = [
            total_posts,
            total_comments,
            total_activity,
            recent_posts,
            recent_comments,
            recent_posts + recent_comments,
            monthly_posts,
            monthly_comments,
            monthly_posts + monthly_comments,
            total_posts / max(account_age_days, 1),  # Posts per day
            total_comments / max(account_age_days, 1),  # Comments per day
            total_activity / max(account_age_days, 1),  # Total activity per day
            total_comments / max(total_posts, 1),  # Comment to post ratio
            account_age_days,
        ]

        return features

    def _extract_content_features(self, user: Dict[str, Any]) -> List[float]:
        """Extract content creation features."""
        posts = user.get("posts", [])
        comments = user.get("comments", [])

        # Content length statistics
        post_lengths = [len(p.get("selftext", "") or "") for p in posts]
        comment_lengths = [len(c.get("body", "") or "") for c in comments]

        avg_post_length = np.mean(post_lengths) if post_lengths else 0
        avg_comment_length = np.mean(comment_lengths) if comment_lengths else 0

        # Content types
        text_posts = len([p for p in posts if p.get("is_self", True)])
        link_posts = len([p for p in posts if not p.get("is_self", True)])

        # Media content
        image_posts = len(
            [
                p
                for p in posts
                if any(
                    domain in (p.get("url", "") or "")
                    for domain in ["imgur", "i.redd.it", "reddit.com/gallery"]
                )
            ]
        )
        video_posts = len(
            [
                p
                for p in posts
                if any(
                    domain in (p.get("url", "") or "")
                    for domain in ["youtube", "streamable", "v.redd.it"]
                )
            ]
        )

        # Content quality indicators
        total_post_score = sum(p.get("score", 0) for p in posts)
        total_comment_score = sum(c.get("score", 0) for c in comments)

        avg_post_score = total_post_score / max(len(posts), 1)
        avg_comment_score = total_comment_score / max(len(comments), 1)

        # Awards and recognition
        total_awards = sum(p.get("total_awards_received", 0) for p in posts)
        gilded_posts = len([p for p in posts if p.get("gilded", 0) > 0])

        features = [
            avg_post_length,
            avg_comment_length,
            text_posts,
            link_posts,
            image_posts,
            video_posts,
            text_posts / max(len(posts), 1),  # Ratio of text posts
            link_posts / max(len(posts), 1),  # Ratio of link posts
            avg_post_score,
            avg_comment_score,
            total_awards,
            gilded_posts,
            gilded_posts / max(len(posts), 1),  # Ratio of gilded posts
        ]

        return features

    def _extract_engagement_features(self, user: Dict[str, Any]) -> List[float]:
        """Extract engagement and interaction features."""
        posts = user.get("posts", [])
        comments = user.get("comments", [])

        # Karma metrics
        comment_karma = user.get("comment_karma", 0)
        link_karma = user.get("link_karma", 0)
        total_karma = comment_karma + link_karma

        # Engagement rates
        total_upvotes = sum(p.get("ups", 0) for p in posts) + sum(
            c.get("ups", 0) for c in comments
        )
        total_downvotes = sum(p.get("downs", 0) for p in posts) + sum(
            c.get("downs", 0) for c in comments
        )

        # Response generation (posts that generate comments)
        posts_with_comments = len([p for p in posts if p.get("num_comments", 0) > 0])
        avg_comments_per_post = (
            np.mean([p.get("num_comments", 0) for p in posts]) if posts else 0
        )

        # Controversial content
        controversial_posts = len(
            [p for p in posts if p.get("upvote_ratio", 0.5) < 0.6]
        )
        controversial_comments = len(
            [c for c in comments if c.get("controversiality", 0) > 0]
        )

        # User status indicators
        is_verified = 1 if user.get("has_verified_email", False) else 0
        is_premium = 1 if user.get("is_gold", False) else 0
        is_moderator = 1 if user.get("is_mod", False) else 0

        features = [
            comment_karma,
            link_karma,
            total_karma,
            total_upvotes,
            total_downvotes,
            total_upvotes / max(total_downvotes, 1),  # Upvote ratio
            posts_with_comments,
            posts_with_comments / max(len(posts), 1),  # Engagement rate
            avg_comments_per_post,
            controversial_posts,
            controversial_comments,
            controversial_posts / max(len(posts), 1),  # Controversial post ratio
            is_verified,
            is_premium,
            is_moderator,
        ]

        return features

    def _extract_temporal_features(self, user: Dict[str, Any]) -> List[float]:
        """Extract temporal behavior features."""
        posts = user.get("posts", [])
        comments = user.get("comments", [])

        # Activity timing patterns
        post_hours = []
        comment_hours = []

        for post in posts:
            timestamp = self._parse_timestamp(post.get("created_utc"))
            if timestamp:
                post_hours.append(timestamp.hour)

        for comment in comments:
            timestamp = self._parse_timestamp(comment.get("created_utc"))
            if timestamp:
                comment_hours.append(timestamp.hour)

        # Calculate activity patterns
        peak_post_hour = (
            max(set(post_hours), key=post_hours.count) if post_hours else 12
        )
        peak_comment_hour = (
            max(set(comment_hours), key=comment_hours.count) if comment_hours else 12
        )

        # Activity distribution across hours
        business_hours_posts = len([h for h in post_hours if 9 <= h <= 17])
        evening_posts = len([h for h in post_hours if 18 <= h <= 22])
        late_night_posts = len([h for h in post_hours if h >= 23 or h <= 5])

        # Consistency metrics
        all_timestamps = []
        for post in posts:
            ts = self._parse_timestamp(post.get("created_utc"))
            if ts:
                all_timestamps.append(ts)
        for comment in comments:
            ts = self._parse_timestamp(comment.get("created_utc"))
            if ts:
                all_timestamps.append(ts)

        # Calculate activity consistency (standard deviation of intervals)
        if len(all_timestamps) > 1:
            all_timestamps.sort()
            intervals = [
                (all_timestamps[i] - all_timestamps[i - 1]).total_seconds()
                for i in range(1, len(all_timestamps))
            ]
            activity_consistency = 1.0 / (
                1.0 + np.std(intervals) / (24 * 3600)
            )  # Normalize by day
        else:
            activity_consistency = 0.0

        features = [
            peak_post_hour,
            peak_comment_hour,
            business_hours_posts / max(len(posts), 1),
            evening_posts / max(len(posts), 1),
            late_night_posts / max(len(posts), 1),
            activity_consistency,
            len(set([ts.date() for ts in all_timestamps if ts])),  # Active days
        ]

        return features

    def _extract_community_features(self, user: Dict[str, Any]) -> List[float]:
        """Extract community interaction features."""
        posts = user.get("posts", [])
        comments = user.get("comments", [])

        # Subreddit diversity
        post_subreddits = set(
            p.get("subreddit", "") for p in posts if p.get("subreddit")
        )
        comment_subreddits = set(
            c.get("subreddit", "") for c in comments if c.get("subreddit")
        )
        all_subreddits = post_subreddits.union(comment_subreddits)

        # Community focus metrics
        if all_subreddits:
            # Calculate subreddit distribution entropy
            subreddit_counts = {}
            for post in posts:
                sub = post.get("subreddit", "")
                if sub:
                    subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
            for comment in comments:
                sub = comment.get("subreddit", "")
                if sub:
                    subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1

            total_activity = sum(subreddit_counts.values())
            if total_activity > 0:
                probabilities = [
                    count / total_activity for count in subreddit_counts.values()
                ]
                entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
            else:
                entropy = 0
        else:
            entropy = 0

        # Cross-posting behavior
        cross_posts = len(
            [p for p in posts if "crosspost" in p.get("title", "").lower()]
        )

        # Moderator interactions
        mod_interactions = len(
            [c for c in comments if "moderator" in c.get("distinguished", "")]
        )

        features = [
            len(all_subreddits),  # Number of unique subreddits
            len(post_subreddits),  # Unique subreddits for posts
            len(comment_subreddits),  # Unique subreddits for comments
            entropy,  # Community diversity (entropy)
            cross_posts,
            cross_posts / max(len(posts), 1),  # Cross-posting rate
            mod_interactions,
        ]

        return features

    def _extract_user_label(self, user: Dict[str, Any]) -> Optional[str]:
        """Extract or infer user classification label."""
        # Check if label is explicitly provided
        if "user_type" in user:
            return user["user_type"]

        if "category" in user:
            return user["category"]

        # Auto-labeling based on activity patterns
        return self._auto_classify_user(user)

    def _auto_classify_user(self, user: Dict[str, Any]) -> str:
        """Automatically classify user based on activity patterns."""
        posts = user.get("posts", [])
        comments = user.get("comments", [])

        total_posts = len(posts)
        total_comments = len(comments)
        total_activity = total_posts + total_comments

        account_created = self._parse_timestamp(user.get("created_utc"))
        account_age_days = (
            (datetime.now() - account_created).days if account_created else 1
        )

        activity_per_day = total_activity / max(account_age_days, 1)
        comment_ratio = total_comments / max(total_activity, 1)

        if self.classification_type == "activity_level":
            if activity_per_day < 0.1:
                return "lurker"
            elif activity_per_day < 1.0:
                return "casual"
            elif activity_per_day < 5.0:
                return "active"
            else:
                return "power_user"

        elif self.classification_type == "behavior_type":
            if total_activity < 10:
                return "consumer"
            elif comment_ratio > 0.8:
                return "commenter"
            elif total_posts > 50:
                return "poster"
            elif any(p.get("total_awards_received", 0) > 0 for p in posts):
                return "creator"
            else:
                return "commenter"

        else:
            return "unknown"

    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        else:
            return None

    def _get_feature_names(self) -> List[str]:
        """Get names of all features."""
        return [
            # Activity features
            "total_posts",
            "total_comments",
            "total_activity",
            "recent_posts",
            "recent_comments",
            "recent_activity",
            "monthly_posts",
            "monthly_comments",
            "monthly_activity",
            "posts_per_day",
            "comments_per_day",
            "activity_per_day",
            "comment_post_ratio",
            "account_age_days",
            # Content features
            "avg_post_length",
            "avg_comment_length",
            "text_posts",
            "link_posts",
            "image_posts",
            "video_posts",
            "text_post_ratio",
            "link_post_ratio",
            "avg_post_score",
            "avg_comment_score",
            "total_awards",
            "gilded_posts",
            "gilded_post_ratio",
            # Engagement features
            "comment_karma",
            "link_karma",
            "total_karma",
            "total_upvotes",
            "total_downvotes",
            "upvote_ratio",
            "posts_with_comments",
            "engagement_rate",
            "avg_comments_per_post",
            "controversial_posts",
            "controversial_comments",
            "controversial_ratio",
            "is_verified",
            "is_premium",
            "is_moderator",
            # Temporal features
            "peak_post_hour",
            "peak_comment_hour",
            "business_hours_ratio",
            "evening_ratio",
            "late_night_ratio",
            "activity_consistency",
            "active_days",
            # Community features
            "unique_subreddits",
            "post_subreddits",
            "comment_subreddits",
            "community_entropy",
            "cross_posts",
            "cross_post_ratio",
            "mod_interactions",
        ]

    def fit(self, user_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train the user classification model.

        Args:
            user_data: List of user dictionaries with activity data

        Returns:
            Training results and metrics
        """
        logger.info(f"Training {self.model_type} user classifier")

        # Prepare features
        X, y = self.prepare_user_features(user_data)

        if len(X) == 0:
            logger.error("No valid user data available")
            return {"error": "No valid user data"}

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        try:
            if self.model_type in ["kmeans", "dbscan"]:
                # Unsupervised learning
                cluster_labels = self.model.fit_predict(X_scaled)

                # Map clusters to meaningful labels
                self._map_clusters_to_labels(X_scaled, cluster_labels, user_data)

                # Calculate clustering metrics
                if len(set(cluster_labels)) > 1:
                    silhouette = silhouette_score(X_scaled, cluster_labels)
                else:
                    silhouette = 0.0

                self.training_metrics = {
                    "n_clusters": len(set(cluster_labels)),
                    "silhouette_score": silhouette,
                    "cluster_sizes": {
                        f"cluster_{i}": np.sum(cluster_labels == i)
                        for i in set(cluster_labels)
                    },
                }

            else:
                # Supervised learning
                if len(y) == 0 or len(set(y)) < 2:
                    logger.error("Insufficient labeled data for supervised learning")
                    return {"error": "Insufficient labeled data"}

                y_encoded = self.label_encoder.fit_transform(y)
                self.model.fit(X_scaled, y_encoded)

                # Calculate training metrics
                y_pred = self.model.predict(X_scaled)
                self.training_metrics = self._calculate_classification_metrics(
                    y_encoded, y_pred
                )

            self.is_fitted = True
            logger.info("User classifier training completed")

            # Feature importance
            feature_importance = self._get_feature_importance()

            results = {
                "model_type": self.model_type,
                "classification_type": self.classification_type,
                "n_users": len(X),
                "n_features": X.shape[1],
                "training_metrics": self.training_metrics,
                "feature_importance": feature_importance,
                "training_timestamp": datetime.now().isoformat(),
            }

            return results

        except Exception as e:
            logger.error(f"User classifier training failed: {e}")
            return {"error": f"Training failed: {e}"}

    def predict(self, user_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify users based on their activity patterns.

        Args:
            user_data: List of user dictionaries to classify

        Returns:
            List of classification results
        """
        if not self.is_fitted:
            logger.warning("Model not fitted. Call fit() first.")
            return []

        # Prepare features
        X, _ = self.prepare_user_features(user_data)

        if len(X) == 0:
            return []

        # Scale features
        X_scaled = self.scaler.transform(X)

        results = []

        try:
            if self.model_type in ["kmeans", "dbscan"]:
                # Clustering prediction
                predictions = self.model.predict(X_scaled)

                for i, (user, pred) in enumerate(zip(user_data, predictions)):
                    result = {
                        "user_id": user.get("id", f"user_{i}"),
                        "predicted_cluster": int(pred),
                        "predicted_category": self.cluster_labels.get(
                            pred, f"cluster_{pred}"
                        ),
                        "prediction_timestamp": datetime.now().isoformat(),
                    }
                    results.append(result)

            else:
                # Classification prediction
                predictions = self.model.predict(X_scaled)
                probabilities = self.model.predict_proba(X_scaled)

                for i, (user, pred, prob) in enumerate(
                    zip(user_data, predictions, probabilities)
                ):
                    predicted_category = self.label_encoder.inverse_transform([pred])[0]
                    confidence = float(max(prob))

                    # Create probability distribution
                    prob_dist = {}
                    for j, category in enumerate(self.label_encoder.classes_):
                        cat_name = self.label_encoder.inverse_transform([category])[0]
                        prob_dist[cat_name] = float(prob[j])

                    result = {
                        "user_id": user.get("id", f"user_{i}"),
                        "predicted_category": predicted_category,
                        "confidence": confidence,
                        "probability_distribution": prob_dist,
                        "prediction_timestamp": datetime.now().isoformat(),
                    }

                    # Add actual category if available
                    actual = user.get("user_type") or user.get("category")
                    if actual:
                        result["actual_category"] = actual
                        result["correct"] = actual == predicted_category

                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"User classification prediction failed: {e}")
            return []

    def _map_clusters_to_labels(
        self, X: np.ndarray, cluster_labels: np.ndarray, user_data: List[Dict[str, Any]]
    ):
        """Map cluster numbers to meaningful labels based on cluster characteristics."""
        unique_clusters = set(cluster_labels)

        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_users = [
                user_data[i] for i, mask in enumerate(cluster_mask) if mask
            ]

            # Analyze cluster characteristics
            avg_activity = np.mean(
                [
                    len(u.get("posts", [])) + len(u.get("comments", []))
                    for u in cluster_users
                ]
            )

            # Assign meaningful labels based on characteristics
            if avg_activity < 10:
                label = "lurker"
            elif avg_activity < 50:
                label = "casual"
            elif avg_activity < 200:
                label = "active"
            else:
                label = "power_user"

            self.cluster_labels[cluster_id] = label

    def _calculate_classification_metrics(
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
        }

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if hasattr(self.model, "feature_importances_"):
            importance_scores = {}
            for name, importance in zip(
                self.feature_names, self.model.feature_importances_
            ):
                importance_scores[name] = float(importance)
            return dict(
                sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
            )
        return {}

    def save_model(self, filepath: str):
        """Save the trained model."""
        if not self.is_fitted:
            logger.warning("No fitted model to save")
            return

        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "label_encoder": self.label_encoder,
                "model_type": self.model_type,
                "classification_type": self.classification_type,
                "user_categories": self.user_categories,
                "cluster_labels": self.cluster_labels,
                "feature_names": self.feature_names,
                "training_metrics": self.training_metrics,
            }

            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def load_model(self, filepath: str):
        """Load a trained model."""
        try:
            model_data = joblib.load(filepath)

            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.label_encoder = model_data["label_encoder"]
            self.model_type = model_data["model_type"]
            self.classification_type = model_data["classification_type"]
            self.user_categories = model_data["user_categories"]
            self.cluster_labels = model_data["cluster_labels"]
            self.feature_names = model_data["feature_names"]
            self.training_metrics = model_data["training_metrics"]

            self.is_fitted = True
            logger.info(f"Model loaded from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
