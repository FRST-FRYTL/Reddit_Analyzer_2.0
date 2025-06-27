"""Base model classes."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class BaseModel(TimestampMixin):
    """Base model class with common functionality."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
