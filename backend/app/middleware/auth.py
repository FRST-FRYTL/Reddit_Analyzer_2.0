"""Authentication middleware."""

from typing import Optional, Callable
from functools import wraps
from flask import request, jsonify, g
from app.utils.auth import get_auth_service
from app.models.user import UserRole
from app.database import get_db


def extract_token_from_header() -> Optional[str]:
    """Extract token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def auth_required(f: Callable) -> Callable:
    """Decorator to require authentication."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()
        if not token:
            return jsonify({"error": "Missing authentication token"}), 401

        auth_service = get_auth_service()
        db = next(get_db())

        try:
            user = auth_service.get_current_user(token, db)
            if not user:
                return jsonify({"error": "Invalid authentication token"}), 401

            g.current_user = user
            return f(*args, **kwargs)
        except Exception:
            return jsonify({"error": "Authentication failed"}), 401
        finally:
            db.close()

    return decorated_function


def role_required(required_role: UserRole):
    """Decorator to require specific role."""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = extract_token_from_header()
            if not token:
                return jsonify({"error": "Missing authentication token"}), 401

            auth_service = get_auth_service()
            db = next(get_db())

            try:
                user = auth_service.get_current_user(token, db)
                if not user:
                    return jsonify({"error": "Invalid authentication token"}), 401

                if not auth_service.require_role(user, required_role):
                    return jsonify({"error": "Insufficient permissions"}), 403

                g.current_user = user
                return f(*args, **kwargs)
            except Exception:
                return jsonify({"error": "Authentication failed"}), 401
            finally:
                db.close()

        return decorated_function

    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator to require admin role."""
    return role_required(UserRole.ADMIN)(f)


def moderator_required(f: Callable) -> Callable:
    """Decorator to require moderator role or higher."""
    return role_required(UserRole.MODERATOR)(f)


class AuthMiddleware:
    """WSGI authentication middleware."""

    def __init__(self, app, secret_key: Optional[str] = None):
        self.app = app
        self.auth_service = get_auth_service(secret_key)

    def __call__(self, environ, start_response):
        """WSGI middleware call."""
        return self.app(environ, start_response)

    def authenticate_request(self, request) -> Optional[dict]:
        """Authenticate incoming request."""
        token = self.extract_token(request)
        if not token:
            return None

        try:
            db = next(get_db())
            user = self.auth_service.get_current_user(token, db)
            if user:
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role.value,
                    "is_active": user.is_active,
                }
        except Exception:
            pass
        finally:
            if "db" in locals():
                db.close()

        return None

    def extract_token(self, request) -> Optional[str]:
        """Extract token from request."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None
