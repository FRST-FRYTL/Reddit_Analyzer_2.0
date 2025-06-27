"""
Task management package for Reddit data processing and analysis.

This package contains Celery tasks for various data processing operations
including text analysis, sentiment analysis, topic modeling, and metrics calculation.
"""

from .processing_tasks import (
    process_text_batch,
    calculate_sentiment_trends,
    update_topic_models,
    train_ml_models,
    calculate_user_metrics,
)

from .analysis_tasks import (
    calculate_subreddit_analytics,
    run_statistical_analysis,
    detect_trending_topics,
)

__all__ = [
    "process_text_batch",
    "calculate_sentiment_trends",
    "update_topic_models",
    "train_ml_models",
    "calculate_user_metrics",
    "calculate_subreddit_analytics",
    "run_statistical_analysis",
    "detect_trending_topics",
]
