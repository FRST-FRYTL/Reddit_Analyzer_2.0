"""
Text analysis results database model.

This module defines the database model for storing text analysis results
including sentiment analysis, topic modeling, and NLP feature extraction.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from reddit_analyzer.database import Base


class TextAnalysis(Base):
    """
    Model for storing comprehensive text analysis results.

    Stores sentiment analysis, NLP features, language detection,
    and other text processing results for posts and comments.
    """

    __tablename__ = "text_analysis"

    id = Column(Integer, primary_key=True, index=True)

    # References to source content
    post_id = Column(String(255), ForeignKey("posts.id"), nullable=True, index=True)
    comment_id = Column(
        String(255), ForeignKey("comments.id"), nullable=True, index=True
    )

    # Text analysis results
    sentiment_score = Column(Float, nullable=True)  # Compound sentiment score
    sentiment_label = Column(String(20), nullable=True)  # POSITIVE, NEGATIVE, NEUTRAL
    emotion_scores = Column(JSON, nullable=True)  # Joy, anger, fear, etc.

    # Language and basic features
    language = Column(String(10), nullable=True)  # Language code
    confidence_score = Column(Float, nullable=True)  # Analysis confidence

    # Text features
    keywords = Column(JSON, nullable=True)  # Extracted keywords with scores
    entities = Column(JSON, nullable=True)  # Named entities
    topics = Column(JSON, nullable=True)  # Topic modeling results

    # Quality metrics
    quality_score = Column(Float, nullable=True)  # Overall content quality
    readability_score = Column(Float, nullable=True)  # Text readability

    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post = relationship("Post", back_populates="text_analysis")
    comment = relationship("Comment", back_populates="text_analysis")

    def __repr__(self):
        return f"<TextAnalysis(id={self.id}, sentiment={self.sentiment_label}, quality={self.quality_score})>"
