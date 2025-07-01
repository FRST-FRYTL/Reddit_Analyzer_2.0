"""
Political analysis database models.

This module defines database models for storing political topic analysis,
multi-dimensional political analysis, and community dynamics.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from reddit_analyzer.database import Base


class SubredditTopicProfile(Base):
    """
    Model for storing aggregate topic analysis for a subreddit.

    Stores topic distribution, sentiment analysis, and discussion quality
    metrics for a specific time period.
    """

    __tablename__ = "subreddit_topic_profiles"

    id = Column(Integer, primary_key=True, index=True)
    subreddit_id = Column(
        Integer, ForeignKey("subreddits.id"), nullable=False, index=True
    )

    # Time period
    analysis_start_date = Column(DateTime, nullable=False)
    analysis_end_date = Column(DateTime, nullable=False)

    # Topic metrics
    dominant_topics = Column(JSON, nullable=True)  # Top 5 topics by prevalence
    topic_distribution = Column(JSON, nullable=True)  # All topics with percentages
    topic_sentiment_map = Column(JSON, nullable=True)  # Sentiment by topic

    # Discussion quality
    avg_discussion_quality = Column(Float, nullable=True)
    civility_score = Column(Float, nullable=True)
    constructiveness_score = Column(Float, nullable=True)
    viewpoint_diversity = Column(Float, nullable=True)

    # Activity metrics
    total_posts_analyzed = Column(Integer, default=0)
    total_comments_analyzed = Column(Integer, default=0)
    unique_users_analyzed = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_level = Column(Float, nullable=True)  # Overall confidence in analysis

    # Relationships
    subreddit = relationship("Subreddit", back_populates="topic_profiles")

    def __repr__(self):
        return f"<SubredditTopicProfile(subreddit_id={self.subreddit_id}, period={self.analysis_start_date}-{self.analysis_end_date})>"


class CommunityOverlap(Base):
    """
    Model for tracking user overlap and engagement patterns between communities.
    """

    __tablename__ = "community_overlaps"

    id = Column(Integer, primary_key=True, index=True)
    subreddit_a_id = Column(
        Integer, ForeignKey("subreddits.id"), nullable=False, index=True
    )
    subreddit_b_id = Column(
        Integer, ForeignKey("subreddits.id"), nullable=False, index=True
    )

    # Overlap metrics
    user_overlap_count = Column(Integer, default=0)
    user_overlap_percentage = Column(Float, nullable=True)
    shared_topics = Column(JSON, nullable=True)

    # Engagement patterns
    cross_posting_count = Column(Integer, default=0)
    sentiment_differential = Column(
        Float, nullable=True
    )  # How differently topics are discussed

    analysis_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subreddit_a = relationship("Subreddit", foreign_keys=[subreddit_a_id])
    subreddit_b = relationship("Subreddit", foreign_keys=[subreddit_b_id])

    def __repr__(self):
        return f"<CommunityOverlap(a={self.subreddit_a_id}, b={self.subreddit_b_id}, overlap={self.user_overlap_percentage})>"


class PoliticalDimensionsAnalysis(Base):
    """
    Model for storing multi-dimensional political analysis results.

    Stores scores across economic, social, and governance dimensions
    with confidence levels and supporting evidence.
    """

    __tablename__ = "political_dimensions_analyses"

    id = Column(Integer, primary_key=True, index=True)
    text_analysis_id = Column(
        Integer, ForeignKey("text_analysis.id"), nullable=False, index=True
    )

    # Economic dimension
    economic_score = Column(Float, nullable=True)  # -1.0 (planned) to 1.0 (market)
    economic_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    economic_label = Column(String(50), nullable=True)
    economic_evidence = Column(
        JSON, nullable=True
    )  # Keywords/phrases that influenced score

    # Social dimension
    social_score = Column(Float, nullable=True)  # -1.0 (authority) to 1.0 (liberty)
    social_confidence = Column(Float, nullable=True)
    social_label = Column(String(50), nullable=True)
    social_evidence = Column(JSON, nullable=True)

    # Governance dimension
    governance_score = Column(
        Float, nullable=True
    )  # -1.0 (centralized) to 1.0 (decentralized)
    governance_confidence = Column(Float, nullable=True)
    governance_label = Column(String(50), nullable=True)
    governance_evidence = Column(JSON, nullable=True)

    # Overall metrics
    analysis_quality = Column(
        Float, nullable=True
    )  # Overall confidence in the analysis
    dominant_dimension = Column(
        String(20), nullable=True
    )  # Which dimension had strongest signal

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    text_analysis = relationship("TextAnalysis", back_populates="political_dimensions")

    def __repr__(self):
        return f"<PoliticalDimensionsAnalysis(id={self.id}, quality={self.analysis_quality})>"


class SubredditPoliticalDimensions(Base):
    """
    Model for storing aggregate political dimensions for a subreddit.

    Stores average scores, distributions, and clustering information
    for political analysis across time periods.
    """

    __tablename__ = "subreddit_political_dimensions"

    id = Column(Integer, primary_key=True, index=True)
    subreddit_id = Column(
        Integer, ForeignKey("subreddits.id"), nullable=False, index=True
    )

    # Time period
    analysis_start_date = Column(DateTime, nullable=False)
    analysis_end_date = Column(DateTime, nullable=False)

    # Aggregate scores for each dimension
    avg_economic_score = Column(Float, nullable=True)
    economic_std_dev = Column(Float, nullable=True)
    economic_distribution = Column(JSON, nullable=True)  # Histogram data

    avg_social_score = Column(Float, nullable=True)
    social_std_dev = Column(Float, nullable=True)
    social_distribution = Column(JSON, nullable=True)

    avg_governance_score = Column(Float, nullable=True)
    governance_std_dev = Column(Float, nullable=True)
    governance_distribution = Column(JSON, nullable=True)

    # Political diversity metrics
    political_diversity_index = Column(Float, nullable=True)  # 0.0 to 1.0
    dimension_correlation = Column(
        JSON, nullable=True
    )  # Correlation between dimensions

    # Cluster analysis
    political_clusters = Column(JSON, nullable=True)  # Identified political groupings
    cluster_sizes = Column(JSON, nullable=True)  # Size of each cluster

    # Metadata
    total_posts_analyzed = Column(Integer, default=0)
    total_comments_analyzed = Column(Integer, default=0)
    avg_confidence_level = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subreddit = relationship("Subreddit", back_populates="political_dimensions")

    def __repr__(self):
        return f"<SubredditPoliticalDimensions(subreddit_id={self.subreddit_id}, diversity={self.political_diversity_index})>"
