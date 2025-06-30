"""Authentication utilities."""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from reddit_analyzer.models.user import User, UserRole


class AuthTokenManager:
    """JWT token management."""

    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "exp": datetime.utcnow()
            + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "type": "access",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user."""
        payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "type": "refresh",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify access token and return payload."""
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify refresh token and return payload."""
        payload = self.decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload


class AuthService:
    """Authentication service."""

    def __init__(self, token_manager: AuthTokenManager):
        self.token_manager = token_manager

    def authenticate_user(
        self, username: str, password: str, db_session
    ) -> Optional[User]:
        """Authenticate user with username and password."""
        user = (
            db_session.query(User)
            .filter(User.username == username, User.is_active)
            .first()
        )

        if user and user.verify_password(password):
            return user
        return None

    def create_tokens(self, user: User) -> Dict[str, str]:
        """Create access and refresh tokens for user."""
        return {
            "access_token": self.token_manager.create_access_token(user),
            "refresh_token": self.token_manager.create_refresh_token(user),
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str, db_session) -> Dict[str, str]:
        """Create new access token using refresh token."""
        payload = self.token_manager.verify_refresh_token(refresh_token)
        user_id = payload.get("sub")

        user = db_session.query(User).filter(User.id == user_id, User.is_active).first()

        if not user:
            raise ValueError("User not found or inactive")

        return {
            "access_token": self.token_manager.create_access_token(user),
            "token_type": "bearer",
        }

    def get_current_user(self, token: str, db_session) -> Optional[User]:
        """Get current user from access token."""
        try:
            payload = self.token_manager.verify_access_token(token)
            user_id = payload.get("sub")

            user = (
                db_session.query(User)
                .filter(User.id == user_id, User.is_active)
                .first()
            )

            return user
        except ValueError:
            return None

    def require_role(self, user: User, required_role: UserRole) -> bool:
        """Check if user has required role."""
        if not user:
            return False

        role_hierarchy = {UserRole.USER: 1, UserRole.MODERATOR: 2, UserRole.ADMIN: 3}

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level


def get_auth_service(secret_key: Optional[str] = None) -> AuthService:
    """Get configured authentication service."""
    from reddit_analyzer.config import get_config

    config = get_config()

    # Use secret key from configuration if not provided
    if secret_key is None:
        secret_key = config.SECRET_KEY

    token_manager = AuthTokenManager(secret_key)
    return AuthService(token_manager)
