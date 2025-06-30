"""User model."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from app.database import Base
from app.models.base import BaseModel
import enum


class UserRole(enum.Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base, BaseModel):
    """Reddit user model with authentication support."""

    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)

    # Reddit-specific fields
    created_utc = Column(DateTime)
    comment_karma = Column(Integer, default=0)
    link_karma = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)

    # Relationships
    metrics = relationship("UserMetric", back_populates="user")

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify user password against hash."""
        if self.password_hash is None:
            return False
        return pwd_context.verify(password, str(self.password_hash))

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return bool(self.role == role)

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return bool(self.role == UserRole.ADMIN)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"
