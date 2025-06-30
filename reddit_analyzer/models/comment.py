"""Comment model."""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from reddit_analyzer.database import Base
from reddit_analyzer.models.base import TimestampMixin


class Comment(Base, TimestampMixin):
    """Reddit comment model."""

    __tablename__ = "comments"

    id = Column(String(255), primary_key=True)
    post_id = Column(String(255), ForeignKey("posts.id"))
    parent_id = Column(String(255))  # Can be another comment or post
    author_id = Column(Integer, ForeignKey("users.id"))
    body = Column(Text)
    score = Column(Integer, default=0)
    created_utc = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    post = relationship("Post", backref="comments")
    author = relationship("User", backref="comments")
    text_analysis = relationship(
        "TextAnalysis", back_populates="comment", uselist=False
    )

    def __repr__(self):
        return f"<Comment(id='{self.id}', post_id='{self.post_id}')>"
