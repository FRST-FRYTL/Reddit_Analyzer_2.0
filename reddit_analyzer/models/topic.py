"""
Topic modeling results database model.

This module defines the database model for storing topic modeling results
including LDA and BERT-based topic discovery and analysis.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Date
from datetime import datetime

from reddit_analyzer.database import Base


class Topic(Base):
    """
    Model for storing topic modeling results.

    Stores discovered topics, their keywords, probabilities,
    and temporal analysis for different subreddits.
    """

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)

    # Topic identification
    topic_id = Column(String(50), nullable=False, index=True)  # Unique topic identifier
    topic_name = Column(String(255), nullable=True)  # Human-readable topic name

    # Scope and context
    subreddit_name = Column(String(255), nullable=True, index=True)
    model_type = Column(String(50), nullable=False)  # lda, bert, combined

    # Topic content
    topic_words = Column(JSON, nullable=False)  # Top words with weights
    topic_probability = Column(Float, nullable=True)  # Overall topic strength
    document_count = Column(Integer, default=0)  # Number of documents in topic

    # Temporal analysis
    time_period = Column(Date, nullable=True, index=True)  # Time period for topic
    trend_score = Column(Float, nullable=True)  # Trending strength

    # Topic characteristics
    coherence_score = Column(Float, nullable=True)  # Topic coherence measure
    diversity_score = Column(Float, nullable=True)  # Topic diversity measure

    # Representative content
    representative_posts = Column(JSON, nullable=True)  # Sample posts for topic

    # Processing metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_version = Column(String(50), nullable=True)  # Model version used

    def __repr__(self):
        return f"<Topic(id={self.topic_id}, subreddit={self.subreddit_name}, words={len(self.topic_words) if self.topic_words else 0})>"
