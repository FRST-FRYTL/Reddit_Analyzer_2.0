"""User model."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from app.database import Base
from app.models.base import BaseModel


class User(Base, BaseModel):
    """Reddit user model."""

    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False, index=True)
    created_utc = Column(DateTime)
    comment_karma = Column(Integer, default=0)
    link_karma = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
