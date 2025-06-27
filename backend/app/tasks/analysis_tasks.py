"""
Analysis and metrics calculation tasks.

This module defines Celery tasks for statistical analysis, metrics calculation,
and aggregated analytics for subreddits and users.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import current_app
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    Post,
    Comment,
    Subreddit,
    TextAnalysis,
    UserMetric,
    SubredditAnalytics,
    Topic,
)
from app.analytics.statistical_analyzer import StatisticalAnalyzer
from app.analytics.metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)

# Initialize analyzers
statistical_analyzer = None
metrics_calculator = None


def get_analyzers():
    """Initialize analyzers lazily."""
    global statistical_analyzer, metrics_calculator

    if statistical_analyzer is None:
        statistical_analyzer = StatisticalAnalyzer()
        metrics_calculator = MetricsCalculator()

    return statistical_analyzer, metrics_calculator


@current_app.task(bind=True, name="calculate_subreddit_analytics")
def calculate_subreddit_analytics(
    self, subreddit_name: str, period_days: int = 7
) -> Dict[str, Any]:
    """
    Calculate comprehensive subreddit analytics for a time period.

    Args:
        subreddit_name: Name of subreddit to analyze
        period_days: Number of days to analyze

    Returns:
        Subreddit analytics results
    """
    try:
        logger.info(
            f"Calculating analytics for r/{subreddit_name} ({period_days} days)"
        )

        _, metrics_calc = get_analyzers()
        db = next(get_db())

        # Define time period
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=period_days)

        # Get subreddit
        subreddit = (
            db.query(Subreddit).filter(Subreddit.display_name == subreddit_name).first()
        )

        if not subreddit:
            return {
                "task_id": self.request.id,
                "error": f"Subreddit r/{subreddit_name} not found",
                "subreddit": subreddit_name,
            }

        # Get posts and comments for the period
        posts = (
            db.query(Post)
            .filter(
                Post.subreddit_id == subreddit.id,
                func.date(Post.created_utc) >= start_date,
                func.date(Post.created_utc) <= end_date,
            )
            .all()
        )

        post_ids = [p.id for p in posts]
        comments = (
            db.query(Comment).filter(Comment.post_id.in_(post_ids)).all()
            if post_ids
            else []
        )

        # Prepare data for metrics calculation
        subreddit_data = {
            "subreddit_info": {
                "id": subreddit.id,
                "display_name": subreddit.display_name,
                "description": subreddit.description,
                "subscribers": subreddit.subscribers,
                "created_utc": subreddit.created_utc,
            },
            "posts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "selftext": p.selftext,
                    "url": p.url,
                    "score": p.score,
                    "upvote_ratio": p.upvote_ratio,
                    "num_comments": p.num_comments,
                    "created_utc": p.created_utc,
                    "is_self": p.is_self,
                    "is_nsfw": p.is_nsfw,
                    "is_locked": p.is_locked,
                }
                for p in posts
            ],
            "comments": [
                {
                    "id": c.id,
                    "post_id": c.post_id,
                    "body": c.body,
                    "score": c.score,
                    "created_utc": c.created_utc,
                }
                for c in comments
            ],
        }

        # Calculate comprehensive metrics
        analytics = metrics_calc.calculate_subreddit_metrics(subreddit_data)

        # Get sentiment data
        sentiment_data = self._get_sentiment_analytics(db, post_ids, comments)

        # Get top topics for the period
        top_topics = self._get_top_topics(db, subreddit_name, start_date, end_date)

        # Store analytics in database
        existing_analytics = (
            db.query(SubredditAnalytics)
            .filter(
                SubredditAnalytics.subreddit_name == subreddit_name,
                SubredditAnalytics.period_start == start_date,
                SubredditAnalytics.period_end == end_date,
            )
            .first()
        )

        if existing_analytics:
            # Update existing analytics
            self._update_subreddit_analytics(
                existing_analytics, analytics, sentiment_data, top_topics
            )
        else:
            # Create new analytics record
            subreddit_analytics = SubredditAnalytics(
                subreddit_name=subreddit_name,
                period_start=start_date,
                period_end=end_date,
                total_posts=len(posts),
                total_comments=len(comments),
                unique_authors=len(set([p.author_id for p in posts if p.author_id])),
                avg_score=analytics.get("engagement_metrics", {}).get(
                    "avg_post_score", 0
                ),
                avg_comments_per_post=analytics.get("activity_metrics", {}).get(
                    "comments_per_post", 0
                ),
                avg_upvote_ratio=analytics.get("engagement_metrics", {}).get(
                    "avg_upvote_ratio", 0.5
                ),
                avg_sentiment=sentiment_data.get("avg_sentiment", 0),
                sentiment_consistency=sentiment_data.get("sentiment_consistency", 0),
                health_score=analytics.get("health_score", 0),
                activity_level=analytics.get("activity_metrics", {}).get(
                    "avg_daily_posts", 0
                ),
                engagement_quality=analytics.get("engagement_metrics", {}).get(
                    "avg_engagement_score", 0
                ),
                growth_rate=analytics.get("growth_metrics", {}).get(
                    "activity_growth_rate", 0
                ),
                content_diversity=analytics.get("content_diversity", {}).get(
                    "diversity_score", 0
                ),
                gini_coefficient=analytics.get("influence_distribution", {}).get(
                    "gini_coefficient", 0
                ),
                top_contributor_ratio=analytics.get("influence_distribution", {}).get(
                    "top_contributor_ratio", 0
                ),
                moderation_activity=analytics.get("moderation_metrics", {}).get(
                    "moderation_activity", 0
                ),
                removal_rate=analytics.get("moderation_metrics", {}).get(
                    "removal_rate", 0
                ),
                top_topics=top_topics,
                engagement_metrics=analytics.get("engagement_metrics", {}),
                growth_metrics=analytics.get("growth_metrics", {}),
                user_distribution=analytics.get("influence_distribution", {}),
                content_distribution=analytics.get("content_diversity", {}),
                calculated_at=datetime.utcnow(),
            )
            db.add(subreddit_analytics)

        db.commit()
        db.close()

        result = {
            "task_id": self.request.id,
            "subreddit": subreddit_name,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_posts": len(posts),
            "total_comments": len(comments),
            "analytics_summary": {
                "health_score": analytics.get("health_score", 0),
                "activity_level": analytics.get("activity_metrics", {}).get(
                    "avg_daily_posts", 0
                ),
                "engagement_quality": analytics.get("engagement_metrics", {}).get(
                    "avg_engagement_score", 0
                ),
                "content_diversity": analytics.get("content_diversity", {}).get(
                    "diversity_score", 0
                ),
            },
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Subreddit analytics completed for r/{subreddit_name}")
        return result

    except Exception as e:
        logger.error(f"Subreddit analytics calculation failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=3)


@current_app.task(bind=True, name="run_statistical_analysis")
def run_statistical_analysis(self, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run statistical analysis on Reddit data.

    Args:
        analysis_config: Configuration for statistical analysis

    Returns:
        Statistical analysis results
    """
    try:
        logger.info(
            f"Running statistical analysis: {analysis_config.get('analysis_type')}"
        )

        stats_analyzer, _ = get_analyzers()
        db = next(get_db())

        analysis_type = analysis_config.get("analysis_type")
        subreddit_name = analysis_config.get("subreddit")
        time_period = analysis_config.get("time_period_days", 30)

        # Get data based on analysis type
        if analysis_type == "engagement_correlation":
            data = self._get_engagement_data(db, subreddit_name, time_period)

            # Run correlation analysis
            correlation_results = stats_analyzer.correlation_analysis(
                data,
                columns=["score", "num_comments", "upvote_ratio", "title_length"],
                methods=["pearson", "spearman"],
            )

            analysis_results = correlation_results

        elif analysis_type == "sentiment_trends":
            data = self._get_sentiment_trend_data(db, subreddit_name, time_period)

            # Run time series analysis
            ts_results = stats_analyzer.time_series_analysis(
                data,
                timestamp_column="created_date",
                value_column="sentiment_score",
                freq="D",
            )

            analysis_results = ts_results

        elif analysis_type == "user_behavior_comparison":
            data = self._get_user_behavior_data(db, subreddit_name, time_period)

            # Run group comparison
            comparison_results = stats_analyzer.group_comparison(
                data,
                group_column="user_type",
                value_columns=["avg_score", "posting_frequency", "comment_ratio"],
            )

            analysis_results = comparison_results

        else:
            analysis_results = {"error": f"Unknown analysis type: {analysis_type}"}

        db.close()

        result = {
            "task_id": self.request.id,
            "analysis_type": analysis_type,
            "analysis_config": analysis_config,
            "analysis_results": analysis_results,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Statistical analysis completed: {analysis_type}")
        return result

    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@current_app.task(bind=True, name="detect_trending_topics")
def detect_trending_topics(
    self, subreddit_name: Optional[str] = None, time_window_hours: int = 24
) -> Dict[str, Any]:
    """
    Detect trending topics in recent content.

    Args:
        subreddit_name: Specific subreddit (None for all)
        time_window_hours: Time window for trend detection

    Returns:
        Trending topics results
    """
    try:
        logger.info(
            f"Detecting trending topics for {subreddit_name or 'all subreddits'}"
        )

        db = next(get_db())

        # Define time window
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Get recent topics
        topics_query = db.query(Topic).filter(Topic.created_at >= cutoff_time)

        if subreddit_name:
            topics_query = topics_query.filter(Topic.subreddit_name == subreddit_name)

        recent_topics = topics_query.all()

        # Calculate trend scores based on recent activity
        trending_topics = []

        for topic in recent_topics:
            # Get recent posts related to this topic
            topic_keywords = (
                topic.topic_words if isinstance(topic.topic_words, list) else []
            )

            if not topic_keywords:
                continue

            # Simple trend calculation based on document count and recency
            recency_factor = 1.0 - (
                (datetime.utcnow() - topic.created_at).total_seconds()
                / (time_window_hours * 3600)
            )
            trend_score = (
                topic.document_count * recency_factor * (topic.topic_probability or 1.0)
            )

            trending_topics.append(
                {
                    "topic_id": topic.topic_id,
                    "topic_name": topic.topic_name,
                    "keywords": topic_keywords[:5],  # Top 5 keywords
                    "trend_score": trend_score,
                    "document_count": topic.document_count,
                    "subreddit": topic.subreddit_name,
                    "created_at": topic.created_at.isoformat(),
                }
            )

        # Sort by trend score
        trending_topics.sort(key=lambda x: x["trend_score"], reverse=True)

        # Update trend scores in database
        for i, topic_data in enumerate(trending_topics[:20]):  # Top 20
            topic = (
                db.query(Topic).filter(Topic.topic_id == topic_data["topic_id"]).first()
            )
            if topic:
                topic.trend_score = topic_data["trend_score"]

        db.commit()
        db.close()

        result = {
            "task_id": self.request.id,
            "subreddit": subreddit_name,
            "time_window_hours": time_window_hours,
            "trending_topics": trending_topics[:10],  # Top 10 for response
            "total_topics_analyzed": len(recent_topics),
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Trending topics detected: {len(trending_topics)} topics analyzed")
        return result

    except Exception as e:
        logger.error(f"Trending topics detection failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


def _get_sentiment_analytics(
    self, db: Session, post_ids: List[str], comments: List[Comment]
) -> Dict[str, Any]:
    """Get sentiment analytics for posts and comments."""
    try:
        # Get sentiment data from text analysis
        post_sentiment = (
            db.query(TextAnalysis.sentiment_score)
            .filter(
                TextAnalysis.post_id.in_(post_ids),
                TextAnalysis.sentiment_score.isnot(None),
            )
            .all()
        )

        comment_ids = [c.id for c in comments]
        comment_sentiment = (
            db.query(TextAnalysis.sentiment_score)
            .filter(
                TextAnalysis.comment_id.in_(comment_ids),
                TextAnalysis.sentiment_score.isnot(None),
            )
            .all()
            if comment_ids
            else []
        )

        all_sentiment_scores = [s[0] for s in post_sentiment] + [
            s[0] for s in comment_sentiment
        ]

        if not all_sentiment_scores:
            return {"avg_sentiment": 0.0, "sentiment_consistency": 0.0}

        import numpy as np

        avg_sentiment = np.mean(all_sentiment_scores)
        sentiment_std = np.std(all_sentiment_scores)
        sentiment_consistency = 1.0 - min(1.0, sentiment_std / 2)

        return {
            "avg_sentiment": float(avg_sentiment),
            "sentiment_consistency": float(sentiment_consistency),
            "sentiment_count": len(all_sentiment_scores),
        }

    except Exception as e:
        logger.warning(f"Sentiment analytics calculation failed: {e}")
        return {"avg_sentiment": 0.0, "sentiment_consistency": 0.0}


def _get_top_topics(
    self,
    db: Session,
    subreddit_name: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict[str, Any]]:
    """Get top topics for the time period."""
    try:
        topics = (
            db.query(Topic)
            .filter(
                Topic.subreddit_name == subreddit_name,
                Topic.time_period >= start_date,
                Topic.time_period <= end_date,
            )
            .order_by(Topic.topic_probability.desc())
            .limit(10)
            .all()
        )

        return [
            {
                "topic_id": t.topic_id,
                "topic_name": t.topic_name,
                "keywords": (
                    t.topic_words[:5] if isinstance(t.topic_words, list) else []
                ),
                "probability": t.topic_probability,
                "document_count": t.document_count,
            }
            for t in topics
        ]

    except Exception as e:
        logger.warning(f"Top topics calculation failed: {e}")
        return []


def _update_subreddit_analytics(
    self,
    analytics: SubredditAnalytics,
    metrics: Dict[str, Any],
    sentiment_data: Dict[str, Any],
    top_topics: List[Dict[str, Any]],
):
    """Update existing subreddit analytics record."""
    analytics.health_score = metrics.get("health_score", 0)
    analytics.activity_level = metrics.get("activity_metrics", {}).get(
        "avg_daily_posts", 0
    )
    analytics.engagement_quality = metrics.get("engagement_metrics", {}).get(
        "avg_engagement_score", 0
    )
    analytics.growth_rate = metrics.get("growth_metrics", {}).get(
        "activity_growth_rate", 0
    )
    analytics.content_diversity = metrics.get("content_diversity", {}).get(
        "diversity_score", 0
    )
    analytics.avg_sentiment = sentiment_data.get("avg_sentiment", 0)
    analytics.sentiment_consistency = sentiment_data.get("sentiment_consistency", 0)
    analytics.top_topics = top_topics
    analytics.engagement_metrics = metrics.get("engagement_metrics", {})
    analytics.growth_metrics = metrics.get("growth_metrics", {})
    analytics.calculated_at = datetime.utcnow()


def _get_engagement_data(
    self, db: Session, subreddit_name: Optional[str], time_period: int
) -> List[Dict[str, Any]]:
    """Get engagement data for correlation analysis."""
    cutoff_date = datetime.utcnow() - timedelta(days=time_period)

    query = db.query(Post).filter(Post.created_utc >= cutoff_date)
    if subreddit_name:
        query = query.filter(Post.subreddit.has(display_name=subreddit_name))

    posts = query.limit(1000).all()

    return [
        {
            "score": p.score,
            "num_comments": p.num_comments,
            "upvote_ratio": p.upvote_ratio,
            "title_length": len(p.title or ""),
            "content_length": len(p.selftext or ""),
            "is_self": 1 if p.is_self else 0,
            "hour_posted": p.created_utc.hour,
            "day_of_week": p.created_utc.weekday(),
        }
        for p in posts
    ]


def _get_sentiment_trend_data(
    self, db: Session, subreddit_name: Optional[str], time_period: int
) -> List[Dict[str, Any]]:
    """Get sentiment trend data for time series analysis."""
    cutoff_date = datetime.utcnow() - timedelta(days=time_period)

    # Get posts with sentiment analysis
    query = (
        db.query(Post, TextAnalysis)
        .join(TextAnalysis, Post.id == TextAnalysis.post_id)
        .filter(
            Post.created_utc >= cutoff_date, TextAnalysis.sentiment_score.isnot(None)
        )
    )

    if subreddit_name:
        query = query.filter(Post.subreddit.has(display_name=subreddit_name))

    results = query.all()

    return [
        {
            "created_date": p.created_utc.date(),
            "sentiment_score": ta.sentiment_score,
            "post_score": p.score,
            "num_comments": p.num_comments,
        }
        for p, ta in results
    ]


def _get_user_behavior_data(
    self, db: Session, subreddit_name: Optional[str], time_period: int
) -> List[Dict[str, Any]]:
    """Get user behavior data for group comparison."""
    cutoff_date = datetime.utcnow() - timedelta(days=time_period)

    # Get user metrics
    query = db.query(UserMetric).filter(UserMetric.calculated_at >= cutoff_date)

    if subreddit_name:
        query = query.filter(UserMetric.subreddit_name == subreddit_name)

    metrics = query.all()

    return [
        {
            "user_id": m.user_id,
            "user_type": self._classify_user_type(m),
            "avg_score": (
                m.detailed_metrics.get("engagement_metrics", {}).get(
                    "avg_post_score", 0
                )
                if m.detailed_metrics
                else 0
            ),
            "posting_frequency": (
                m.detailed_metrics.get("behavioral_metrics", {}).get(
                    "posting_regularity", 0
                )
                if m.detailed_metrics
                else 0
            ),
            "comment_ratio": (
                m.detailed_metrics.get("engagement_metrics", {}).get(
                    "comment_post_ratio", 0
                )
                if m.detailed_metrics
                else 0
            ),
            "activity_score": m.activity_score,
            "influence_score": m.influence_score,
        }
        for m in metrics
    ]


def _classify_user_type(self, metric: UserMetric) -> str:
    """Classify user type based on metrics."""
    if metric.activity_score > 0.8:
        return "power_user"
    elif metric.activity_score > 0.5:
        return "active_user"
    elif metric.activity_score > 0.2:
        return "casual_user"
    else:
        return "lurker"
