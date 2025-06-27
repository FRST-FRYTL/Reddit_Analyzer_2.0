"""Subreddit model."""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from app.database import Base
from app.models.base import BaseModel


class Subreddit(Base, BaseModel):
    """Reddit subreddit model."""

    __tablename__ = "subreddits"

    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    subscribers = Column(Integer, default=0)
    created_utc = Column(DateTime)
    is_nsfw = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Subreddit(id={self.id}, name='{self.name}')>"
