"""
Subreddit analytics database model.

This module defines the database model for storing aggregated subreddit
analytics including health metrics, growth indicators, and community analysis.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Date
from datetime import datetime

from app.database import Base


class SubredditAnalytics(Base):
    """
    Model for storing comprehensive subreddit analytics.

    Stores aggregated metrics for subreddit health, activity patterns,
    growth indicators, and community characteristics over time periods.
    """

    __tablename__ = "subreddit_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # Subreddit identification
    subreddit_name = Column(String(255), nullable=False, index=True)

    # Time period for analytics
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)

    # Activity metrics
    total_posts = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    unique_authors = Column(Integer, default=0)

    # Engagement metrics
    avg_score = Column(Float, nullable=True)
    avg_comments_per_post = Column(Float, nullable=True)
    avg_upvote_ratio = Column(Float, nullable=True)

    # Sentiment metrics
    avg_sentiment = Column(Float, nullable=True)
    sentiment_consistency = Column(Float, nullable=True)

    # Health indicators
    health_score = Column(Float, nullable=True)  # Overall subreddit health
    activity_level = Column(Float, nullable=True)  # Activity level score
    engagement_quality = Column(Float, nullable=True)  # Quality of engagement

    # Growth metrics
    growth_rate = Column(Float, nullable=True)  # Activity growth rate
    subscriber_growth = Column(Float, nullable=True)  # Subscriber growth (if available)

    # Content analysis
    content_diversity = Column(Float, nullable=True)  # Content type diversity
    quality_trend = Column(Float, nullable=True)  # Content quality trend

    # Community metrics
    gini_coefficient = Column(Float, nullable=True)  # Contribution inequality
    top_contributor_ratio = Column(
        Float, nullable=True
    )  # Top contributor concentration

    # Moderation metrics
    moderation_activity = Column(Float, nullable=True)  # Moderation activity level
    removal_rate = Column(Float, nullable=True)  # Content removal rate

    # Detailed analytics (JSON format)
    top_topics = Column(JSON, nullable=True)  # Top topics for period
    engagement_metrics = Column(JSON, nullable=True)  # Detailed engagement data
    growth_metrics = Column(JSON, nullable=True)  # Detailed growth data
    user_distribution = Column(JSON, nullable=True)  # User activity distribution
    content_distribution = Column(JSON, nullable=True)  # Content type distribution

    # Processing metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SubredditAnalytics(subreddit={self.subreddit_name}, period={self.period_start}-{self.period_end}, health={self.health_score})>"
