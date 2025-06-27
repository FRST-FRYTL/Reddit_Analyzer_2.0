"""Post model."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Post(Base, TimestampMixin):
    """Reddit post model."""

    __tablename__ = "posts"

    id = Column(String(255), primary_key=True)
    title = Column(String(500), nullable=False)
    selftext = Column(Text)
    url = Column(String(2000))
    author_id = Column(Integer, ForeignKey("users.id"))
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"))
    score = Column(Integer, default=0)
    upvote_ratio = Column(Float, default=0.5)
    num_comments = Column(Integer, default=0)
    created_utc = Column(DateTime, nullable=False)
    is_self = Column(Boolean, default=False)
    is_nsfw = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)

    # Relationships
    author = relationship("User", backref="posts")
    subreddit = relationship("Subreddit", backref="posts")

    def __repr__(self):
        return f"<Post(id='{self.id}', title='{self.title[:50]}...')>"
