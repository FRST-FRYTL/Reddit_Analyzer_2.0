"""
User metrics database model.

This module defines the database model for storing calculated user metrics
including activity scores, influence measures, and behavioral analysis.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from reddit_analyzer.database import Base


class UserMetric(Base):
    """
    Model for storing comprehensive user metrics and analysis.

    Stores calculated metrics for user activity, influence, behavior patterns,
    and community engagement across different time periods.
    """

    __tablename__ = "user_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subreddit_name = Column(
        String(255), nullable=True, index=True
    )  # Metrics for specific subreddit

    # Core metrics
    activity_score = Column(
        Float, nullable=False, default=0.0
    )  # Overall activity level
    influence_score = Column(
        Float, nullable=False, default=0.0
    )  # User influence measure
    reputation_score = Column(
        Float, nullable=False, default=0.0
    )  # Reputation/credibility

    # Engagement metrics
    engagement_rate = Column(Float, nullable=True)  # Response generation rate
    interaction_quality = Column(Float, nullable=True)  # Quality of interactions

    # Content metrics
    content_quality_score = Column(Float, nullable=True)  # Average content quality
    posting_frequency = Column(Float, nullable=True)  # Posts/comments per day

    # Behavioral metrics
    sentiment_trend = Column(Float, nullable=True)  # Average sentiment of content
    consistency_score = Column(Float, nullable=True)  # Behavioral consistency

    # Community metrics
    community_diversity = Column(Float, nullable=True)  # Engagement across communities
    crosspost_ratio = Column(Float, nullable=True)  # Cross-posting behavior

    # Detailed metrics (JSON format)
    detailed_metrics = Column(JSON, nullable=True)  # Additional detailed metrics

    # Time period for metrics
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Processing metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="metrics")

    def __repr__(self):
        return f"<UserMetric(user_id={self.user_id}, activity={self.activity_score:.2f}, influence={self.influence_score:.2f})>"
