"""
Processing tasks for Reddit data analysis.

This module defines Celery tasks for text processing, sentiment analysis,
topic modeling, and other data processing operations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import current_app

from reddit_analyzer.database import get_db
from reddit_analyzer.models import Post, Comment, TextAnalysis, Topic, UserMetric, User
from reddit_analyzer.processing.text_processor import TextProcessor
from reddit_analyzer.processing.sentiment_analyzer import SentimentAnalyzer
from reddit_analyzer.processing.topic_modeler import TopicModeler
from reddit_analyzer.processing.feature_extractor import FeatureExtractor
from reddit_analyzer.ml.models.popularity_predictor import PopularityPredictor
from reddit_analyzer.ml.models.content_classifier import ContentClassifier
from reddit_analyzer.analytics.metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)

# Initialize processors (will be imported when worker starts)
text_processor = None
sentiment_analyzer = None
topic_modeler = None
feature_extractor = None
metrics_calculator = None


def get_processors():
    """Initialize processors lazily to avoid import issues."""
    global \
        text_processor, \
        sentiment_analyzer, \
        topic_modeler, \
        feature_extractor, \
        metrics_calculator

    if text_processor is None:
        text_processor = TextProcessor()
        sentiment_analyzer = SentimentAnalyzer()
        topic_modeler = TopicModeler()
        feature_extractor = FeatureExtractor()
        metrics_calculator = MetricsCalculator()

    return (
        text_processor,
        sentiment_analyzer,
        topic_modeler,
        feature_extractor,
        metrics_calculator,
    )


@current_app.task(bind=True, name="process_text_batch")
def process_text_batch(
    self, content_ids: List[str], content_type: str = "post"
) -> Dict[str, Any]:
    """
    Process a batch of text content for NLP analysis.

    Args:
        content_ids: List of post or comment IDs to process
        content_type: Type of content ('post' or 'comment')

    Returns:
        Processing results summary
    """
    try:
        logger.info(
            f"Starting text processing batch for {len(content_ids)} {content_type}s"
        )

        processors = get_processors()
        text_proc, sentiment_analyzer, _, _, _ = processors

        db = next(get_db())
        processed_count = 0
        error_count = 0

        # Get content from database
        if content_type == "post":
            content_items = db.query(Post).filter(Post.id.in_(content_ids)).all()
        else:
            content_items = db.query(Comment).filter(Comment.id.in_(content_ids)).all()

        for item in content_items:
            try:
                # Extract text content
                if content_type == "post":
                    text = f"{item.title or ''} {item.selftext or ''}".strip()
                else:
                    text = item.body or ""

                if not text:
                    continue

                # Process text
                text_features = text_proc.process_text(text)
                sentiment_results = sentiment_analyzer.analyze(text)

                # Store results in database
                existing_analysis = (
                    db.query(TextAnalysis)
                    .filter(getattr(TextAnalysis, f"{content_type}_id") == item.id)
                    .first()
                )

                if existing_analysis:
                    # Update existing analysis
                    existing_analysis.sentiment_score = sentiment_results.get(
                        "compound_score"
                    )
                    existing_analysis.sentiment_label = sentiment_results.get(
                        "sentiment_label"
                    )
                    existing_analysis.emotion_scores = sentiment_results.get(
                        "emotions", {}
                    )
                    existing_analysis.language = text_features.get("language")
                    existing_analysis.confidence_score = sentiment_results.get(
                        "confidence"
                    )
                    existing_analysis.keywords = text_features.get("keywords")
                    existing_analysis.entities = text_features.get("entities")
                    existing_analysis.quality_score = self._calculate_quality_score(
                        text_features, sentiment_results
                    )
                    existing_analysis.readability_score = text_features.get(
                        "readability", {}
                    ).get("readability_score")
                    existing_analysis.processed_at = datetime.utcnow()
                else:
                    # Create new analysis
                    analysis = TextAnalysis(
                        **{f"{content_type}_id": item.id},
                        sentiment_score=sentiment_results.get("compound_score"),
                        sentiment_label=sentiment_results.get("sentiment_label"),
                        emotion_scores=sentiment_results.get("emotions", {}),
                        language=text_features.get("language"),
                        confidence_score=sentiment_results.get("confidence"),
                        keywords=text_features.get("keywords"),
                        entities=text_features.get("entities"),
                        quality_score=self._calculate_quality_score(
                            text_features, sentiment_results
                        ),
                        readability_score=text_features.get("readability", {}).get(
                            "readability_score"
                        ),
                        processed_at=datetime.utcnow(),
                    )
                    db.add(analysis)

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing {content_type} {item.id}: {e}")
                error_count += 1

        db.commit()
        db.close()

        result = {
            "task_id": self.request.id,
            "content_type": content_type,
            "total_items": len(content_ids),
            "processed_count": processed_count,
            "error_count": error_count,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Text processing batch completed: {processed_count} processed, {error_count} errors"
        )
        return result

    except Exception as e:
        logger.error(f"Text processing batch failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@current_app.task(bind=True, name="calculate_sentiment_trends")
def calculate_sentiment_trends(
    self, subreddit_name: str, days_back: int = 7
) -> Dict[str, Any]:
    """
    Calculate sentiment trends for a subreddit over time.

    Args:
        subreddit_name: Name of subreddit to analyze
        days_back: Number of days to look back

    Returns:
        Sentiment trend analysis results
    """
    try:
        logger.info(
            f"Calculating sentiment trends for r/{subreddit_name} ({days_back} days)"
        )

        _, sentiment_analyzer, _, _, _ = get_processors()
        db = next(get_db())

        # Get recent posts and comments with text analysis
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        posts_query = (
            db.query(Post, TextAnalysis)
            .join(TextAnalysis, Post.id == TextAnalysis.post_id)
            .filter(
                Post.created_utc >= cutoff_date,
                Post.subreddit.has(display_name=subreddit_name),
            )
        )

        comments_query = (
            db.query(Comment, TextAnalysis)
            .join(TextAnalysis, Comment.id == TextAnalysis.comment_id)
            .filter(Comment.created_utc >= cutoff_date)
        )

        # Aggregate sentiment data by day
        daily_sentiment = {}

        for post, analysis in posts_query:
            date_key = post.created_utc.date()
            if date_key not in daily_sentiment:
                daily_sentiment[date_key] = []
            daily_sentiment[date_key].append(analysis.sentiment_score or 0)

        for comment, analysis in comments_query:
            date_key = comment.created_utc.date()
            if date_key not in daily_sentiment:
                daily_sentiment[date_key] = []
            daily_sentiment[date_key].append(analysis.sentiment_score or 0)

        # Calculate trends
        trend_data = []
        for date_key in sorted(daily_sentiment.keys()):
            scores = daily_sentiment[date_key]
            if scores:
                trend_data.append(
                    {
                        "date": date_key.isoformat(),
                        "avg_sentiment": sum(scores) / len(scores),
                        "sentiment_count": len(scores),
                        "positive_ratio": len([s for s in scores if s > 0.1])
                        / len(scores),
                        "negative_ratio": len([s for s in scores if s < -0.1])
                        / len(scores),
                    }
                )

        # Calculate overall trend
        if len(trend_data) >= 2:
            first_avg = trend_data[0]["avg_sentiment"]
            last_avg = trend_data[-1]["avg_sentiment"]
            trend_direction = (
                "improving"
                if last_avg > first_avg
                else "declining"
                if last_avg < first_avg
                else "stable"
            )
        else:
            trend_direction = "insufficient_data"

        db.close()

        result = {
            "task_id": self.request.id,
            "subreddit": subreddit_name,
            "period_days": days_back,
            "trend_direction": trend_direction,
            "daily_trends": trend_data,
            "total_items_analyzed": sum(
                len(daily_sentiment[d]) for d in daily_sentiment
            ),
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Sentiment trends calculated for r/{subreddit_name}: {trend_direction}"
        )
        return result

    except Exception as e:
        logger.error(f"Sentiment trends calculation failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@current_app.task(bind=True, name="update_topic_models")
def update_topic_models(
    self, subreddit_name: Optional[str] = None, min_documents: int = 50
) -> Dict[str, Any]:
    """
    Update topic models with new data.

    Args:
        subreddit_name: Specific subreddit to model (None for all)
        min_documents: Minimum documents required for modeling

    Returns:
        Topic modeling results
    """
    try:
        logger.info(f"Updating topic models for {subreddit_name or 'all subreddits'}")

        _, _, topic_modeler, _, _ = get_processors()
        db = next(get_db())

        # Get recent posts for topic modeling
        cutoff_date = datetime.utcnow() - timedelta(days=30)  # Last 30 days

        query = db.query(Post).filter(Post.created_utc >= cutoff_date)
        if subreddit_name:
            query = query.filter(Post.subreddit.has(display_name=subreddit_name))

        posts = query.limit(1000).all()  # Limit for performance

        if len(posts) < min_documents:
            logger.warning(
                f"Insufficient documents for topic modeling: {len(posts)} < {min_documents}"
            )
            return {
                "task_id": self.request.id,
                "error": "insufficient_documents",
                "document_count": len(posts),
                "min_required": min_documents,
            }

        # Prepare texts for modeling
        texts = []
        post_ids = []

        for post in posts:
            text = f"{post.title or ''} {post.selftext or ''}".strip()
            if len(text) > 50:  # Minimum text length
                texts.append(text)
                post_ids.append(post.id)

        # Fit topic model
        modeling_results = topic_modeler.fit(texts)

        if "error" in modeling_results:
            logger.error(f"Topic modeling failed: {modeling_results['error']}")
            return modeling_results

        # Store topic results in database
        topics_stored = 0

        if "lda" in modeling_results:
            lda_topics = modeling_results["lda"].get("topics", [])

            for topic_data in lda_topics:
                topic = Topic(
                    topic_id=f"lda_{subreddit_name or 'global'}_{topic_data['topic_id']}",
                    topic_name=f"Topic {topic_data['topic_id']}",
                    subreddit_name=subreddit_name,
                    model_type="lda",
                    topic_words=topic_data.get("words", []),
                    topic_probability=topic_data.get("total_weight", 0),
                    document_count=len(post_ids),
                    time_period=datetime.utcnow().date(),
                    coherence_score=modeling_results["lda"].get("coherence_score"),
                    created_at=datetime.utcnow(),
                    model_version="1.0",
                )
                db.add(topic)
                topics_stored += 1

        db.commit()
        db.close()

        result = {
            "task_id": self.request.id,
            "subreddit": subreddit_name,
            "documents_processed": len(texts),
            "topics_identified": len(modeling_results.get("lda", {}).get("topics", [])),
            "topics_stored": topics_stored,
            "modeling_results": modeling_results,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Topic modeling completed: {topics_stored} topics stored")
        return result

    except Exception as e:
        logger.error(f"Topic modeling failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)


@current_app.task(bind=True, name="train_ml_models")
def train_ml_models(
    self, model_type: str, training_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Train or retrain machine learning models.

    Args:
        model_type: Type of model to train ('popularity', 'classification', 'user_behavior')
        training_config: Model training configuration

    Returns:
        Training results
    """
    try:
        logger.info(f"Training {model_type} model with config: {training_config}")

        db = next(get_db())

        if model_type == "popularity":
            model = PopularityPredictor(
                model_type=training_config.get("algorithm", "random_forest"),
                target_metric=training_config.get("target", "score"),
            )

            # Get training data
            training_posts = (
                db.query(Post)
                .filter(
                    Post.created_utc >= datetime.utcnow() - timedelta(days=30),
                    Post.score > 0,  # Only posts with engagement
                )
                .limit(5000)
                .all()
            )

            # Convert to training format
            training_data = []
            for post in training_posts:
                post_dict = {
                    "id": post.id,
                    "title": post.title,
                    "selftext": post.selftext,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "upvote_ratio": post.upvote_ratio,
                    "created_utc": post.created_utc,
                    "is_self": post.is_self,
                    # Add additional features as needed
                }
                training_data.append(post_dict)

            # Train model
            training_results = model.fit(training_data)

            # Save model (in a real implementation, you'd save to file storage)
            model_path = f"/tmp/{model_type}_model_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pkl"
            model.save_model(model_path)

        elif model_type == "classification":
            model = ContentClassifier(
                model_type=training_config.get("algorithm", "random_forest"),
                categories=training_config.get("categories"),
            )

            # Similar training process for classification
            training_results = {
                "message": "Classification training not yet implemented"
            }

        else:
            training_results = {"error": f"Unknown model type: {model_type}"}

        db.close()

        result = {
            "task_id": self.request.id,
            "model_type": model_type,
            "training_config": training_config,
            "training_results": training_results,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Model training completed for {model_type}")
        return result

    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


@current_app.task(bind=True, name="calculate_user_metrics")
def calculate_user_metrics(
    self, user_ids: List[int], time_period_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate comprehensive user metrics.

    Args:
        user_ids: List of user IDs to calculate metrics for
        time_period_days: Time period for metric calculation

    Returns:
        User metrics calculation results
    """
    try:
        logger.info(f"Calculating metrics for {len(user_ids)} users")

        _, _, _, _, metrics_calc = get_processors()
        db = next(get_db())

        metrics_calculated = 0
        error_count = 0

        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

        for user_id in user_ids:
            try:
                # Get user data
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue

                # Get user's posts and comments
                posts = (
                    db.query(Post)
                    .filter(Post.author_id == user_id, Post.created_utc >= cutoff_date)
                    .all()
                )

                comments = (
                    db.query(Comment)
                    .filter(
                        Comment.author_id == user_id, Comment.created_utc >= cutoff_date
                    )
                    .all()
                )

                # Prepare data for metrics calculation
                user_data = {
                    "user_info": {
                        "id": user.id,
                        "username": user.username,
                        "created_utc": user.created_utc,
                        "comment_karma": user.comment_karma,
                        "link_karma": user.link_karma,
                        "is_verified": user.is_verified,
                    },
                    "posts": [
                        {
                            "id": p.id,
                            "title": p.title,
                            "selftext": p.selftext,
                            "score": p.score,
                            "num_comments": p.num_comments,
                            "upvote_ratio": p.upvote_ratio,
                            "created_utc": p.created_utc,
                            "is_self": p.is_self,
                        }
                        for p in posts
                    ],
                    "comments": [
                        {
                            "id": c.id,
                            "body": c.body,
                            "score": c.score,
                            "created_utc": c.created_utc,
                        }
                        for c in comments
                    ],
                }

                # Calculate metrics
                metrics = metrics_calc.calculate_user_metrics(user_data)

                # Store metrics in database
                existing_metric = (
                    db.query(UserMetric)
                    .filter(
                        UserMetric.user_id == user_id,
                        UserMetric.period_start >= cutoff_date,
                    )
                    .first()
                )

                if existing_metric:
                    # Update existing metrics
                    for key, value in metrics.items():
                        if hasattr(existing_metric, key) and isinstance(
                            value, (int, float)
                        ):
                            setattr(existing_metric, key, value)
                    existing_metric.calculated_at = datetime.utcnow()
                else:
                    # Create new metrics record
                    user_metric = UserMetric(
                        user_id=user_id,
                        activity_score=metrics.get("activity_score", 0.0),
                        influence_score=metrics.get("influence_score", 0.0),
                        reputation_score=metrics.get("reputation_score", 0.0),
                        engagement_rate=metrics.get("engagement_metrics", {}).get(
                            "response_rate", 0.0
                        ),
                        content_quality_score=metrics.get(
                            "content_quality_metrics", {}
                        ).get("content_diversity_score", 0.0),
                        sentiment_trend=0.0,  # Would need sentiment analysis
                        consistency_score=metrics.get("consistency_metrics", {}).get(
                            "posting_regularity", 0.0
                        ),
                        community_diversity=metrics.get("community_metrics", {}).get(
                            "subreddit_diversity", 0.0
                        ),
                        detailed_metrics=metrics,
                        period_start=cutoff_date,
                        period_end=datetime.utcnow(),
                        calculated_at=datetime.utcnow(),
                    )
                    db.add(user_metric)

                metrics_calculated += 1

            except Exception as e:
                logger.error(f"Error calculating metrics for user {user_id}: {e}")
                error_count += 1

        db.commit()
        db.close()

        result = {
            "task_id": self.request.id,
            "total_users": len(user_ids),
            "metrics_calculated": metrics_calculated,
            "error_count": error_count,
            "time_period_days": time_period_days,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"User metrics calculation completed: {metrics_calculated} users processed"
        )
        return result

    except Exception as e:
        logger.error(f"User metrics calculation failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


def _calculate_quality_score(
    text_features: Dict[str, Any], sentiment_results: Dict[str, Any]
) -> float:
    """Calculate a simple quality score from text features and sentiment."""
    try:
        # Basic quality factors
        readability = text_features.get("readability", {})
        stats = text_features.get("stats", {})

        # Length factor (medium length is better)
        length = stats.get("cleaned_length", 0)
        length_score = (
            min(1.0, length / 500) if length < 500 else max(0.5, 1000 / length)
        )

        # Readability factor
        readability_score = 1.0 - min(1.0, readability.get("readability_score", 0.5))

        # Sentiment factor (neutral to positive is better)
        sentiment_score = max(
            0.3, 0.7 + sentiment_results.get("compound_score", 0) * 0.3
        )

        # Combine factors
        quality = length_score * 0.4 + readability_score * 0.3 + sentiment_score * 0.3

        return min(1.0, max(0.0, quality))

    except Exception as e:
        logger.warning(f"Quality score calculation failed: {e}")
        return 0.5  # Default middle score
