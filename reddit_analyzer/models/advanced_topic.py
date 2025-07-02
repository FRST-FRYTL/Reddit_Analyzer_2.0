"""
Advanced topic modeling results database model.

This module defines database models for storing results from
advanced topic modeling techniques like BERTopic and neural models.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from reddit_analyzer.database import Base


class AdvancedTopic(Base):
    """
    Model for storing advanced topic modeling results.

    Stores topics discovered by advanced models like BERTopic,
    including embeddings, hierarchical structures, and evolution.
    """

    __tablename__ = "advanced_topics"

    id = Column(Integer, primary_key=True, index=True)

    # Topic identification
    topic_id = Column(Integer, nullable=False, index=True)
    topic_label = Column(String(255), nullable=True)  # Human-readable label

    # Topic metadata
    subreddit_name = Column(String(255), ForeignKey("subreddits.name"), nullable=True)
    model_type = Column(String(50), nullable=False)  # bertopic, nmf, neural
    model_version = Column(String(50), nullable=True)

    # Topic content
    top_words = Column(JSON, nullable=False)  # List of top words with scores
    representative_docs = Column(JSON, nullable=True)  # Sample documents
    embedding = Column(JSON, nullable=True)  # Topic embedding vector

    # Topic statistics
    document_count = Column(Integer, nullable=False)
    coherence_score = Column(Float, nullable=True)
    diversity_score = Column(Float, nullable=True)

    # Hierarchical information
    parent_topic_id = Column(Integer, nullable=True)
    hierarchy_level = Column(Integer, nullable=True)

    # Temporal information
    time_period_start = Column(DateTime, nullable=True)
    time_period_end = Column(DateTime, nullable=True)

    # Processing metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subreddit = relationship("Subreddit", back_populates="advanced_topics")
    topic_evolution = relationship("TopicEvolution", back_populates="topic")

    def __repr__(self):
        return f"<AdvancedTopic(id={self.id}, label={self.topic_label}, docs={self.document_count})>"


class TopicEvolution(Base):
    """
    Model for tracking topic evolution over time.

    Stores how topics change, merge, split, or disappear over time.
    """

    __tablename__ = "topic_evolution"

    id = Column(Integer, primary_key=True, index=True)

    # Topic reference
    topic_id = Column(Integer, ForeignKey("advanced_topics.id"), nullable=False)

    # Time information
    timestamp = Column(DateTime, nullable=False, index=True)
    time_bin = Column(Integer, nullable=False)  # Discrete time period

    # Evolution metrics
    document_count = Column(Integer, nullable=False)
    relative_frequency = Column(Float, nullable=False)  # Proportion of docs

    # Topic changes
    word_changes = Column(JSON, nullable=True)  # Words added/removed
    sentiment_shift = Column(Float, nullable=True)  # Change in sentiment

    # Related topics
    merged_with = Column(JSON, nullable=True)  # Topics merged into this
    split_into = Column(JSON, nullable=True)  # Topics split from this

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    topic = relationship("AdvancedTopic", back_populates="topic_evolution")

    def __repr__(self):
        return f"<TopicEvolution(id={self.id}, topic={self.topic_id}, time={self.timestamp})>"


class ArgumentStructure(Base):
    """
    Model for storing argument mining results.

    Stores extracted argumentative structures including claims,
    evidence, reasoning patterns, and logical relationships.
    """

    __tablename__ = "argument_structures"

    id = Column(Integer, primary_key=True, index=True)

    # Source reference
    post_id = Column(String(255), ForeignKey("posts.id"), nullable=True)
    comment_id = Column(String(255), ForeignKey("comments.id"), nullable=True)

    # Argument components
    components = Column(JSON, nullable=False)  # List of argument components
    relationships = Column(JSON, nullable=True)  # Relations between components

    # Quality metrics
    overall_quality = Column(Float, nullable=True)
    logical_flow_score = Column(Float, nullable=True)
    evidence_support_score = Column(Float, nullable=True)
    balance_score = Column(Float, nullable=True)
    clarity_score = Column(Float, nullable=True)

    # Argument summary
    main_claims = Column(JSON, nullable=True)  # Primary claims
    conclusions = Column(JSON, nullable=True)  # Conclusions reached
    fallacies_detected = Column(JSON, nullable=True)  # Logical fallacies

    # Metadata
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post = relationship("Post", backref="argument_structures")
    comment = relationship("Comment", backref="argument_structures")

    def __repr__(self):
        return f"<ArgumentStructure(id={self.id}, quality={self.overall_quality})>"
