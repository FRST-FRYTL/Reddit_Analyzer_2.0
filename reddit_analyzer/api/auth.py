"""Authentication API endpoints."""

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError
from reddit_analyzer.database import get_db
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.utils.auth import get_auth_service
from reddit_analyzer.middleware.auth import auth_required
from reddit_analyzer.validators.schemas import UserRegistrationSchema, UserLoginSchema
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate input
        try:
            validated_data = UserRegistrationSchema(**data).dict()
        except Exception as e:
            return jsonify({"error": "Validation failed", "details": str(e)}), 400

        db = next(get_db())

        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter(
                (User.username == validated_data["username"])
                | (User.email == validated_data.get("email"))
            )
            .first()
        )

        if existing_user:
            return jsonify({"error": "User already exists"}), 409

        # Create new user
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email"),
            role=UserRole.USER,
            is_active=True,
        )
        user.set_password(validated_data["password"])

        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate tokens
        auth_service = get_auth_service()
        tokens = auth_service.create_tokens(user)

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                    },
                    **tokens,
                }
            ),
            201,
        )

    except IntegrityError:
        db.rollback()
        return jsonify({"error": "User already exists"}), 409
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500
    finally:
        if "db" in locals():
            db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate input
        try:
            validated_data = UserLoginSchema(**data).dict()
        except Exception as e:
            return jsonify({"error": "Validation failed", "details": str(e)}), 400

        db = next(get_db())
        auth_service = get_auth_service()

        # Authenticate user
        user = auth_service.authenticate_user(
            validated_data["username"], validated_data["password"], db
        )

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate tokens
        tokens = auth_service.create_tokens(user)

        return (
            jsonify(
                {
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                    },
                    **tokens,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500
    finally:
        if "db" in locals():
            db.close()


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token."""
    try:
        data = request.get_json()
        if not data or "refresh_token" not in data:
            return jsonify({"error": "Refresh token required"}), 400

        db = next(get_db())
        auth_service = get_auth_service()

        # Refresh token
        new_tokens = auth_service.refresh_access_token(data["refresh_token"], db)

        return jsonify({"message": "Token refreshed successfully", **new_tokens}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Token refresh failed"}), 500
    finally:
        if "db" in locals():
            db.close()


@auth_bp.route("/me", methods=["GET"])
@auth_required
def get_current_user():
    """Get current user information."""
    try:
        user = g.current_user
        return (
            jsonify(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                        "is_active": user.is_active,
                        "created_at": (
                            user.created_at.isoformat() if user.created_at else None
                        ),
                        "comment_karma": user.comment_karma,
                        "link_karma": user.link_karma,
                        "is_verified": user.is_verified,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({"error": "Failed to get user information"}), 500


@auth_bp.route("/logout", methods=["POST"])
@auth_required
def logout():
    """User logout."""
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/change-password", methods=["POST"])
@auth_required
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        if not data or "current_password" not in data or "new_password" not in data:
            return jsonify({"error": "Current and new passwords required"}), 400

        user = g.current_user

        # Verify current password
        if not user.verify_password(data["current_password"]):
            return jsonify({"error": "Invalid current password"}), 401

        # Validate new password
        if len(data["new_password"]) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        db = next(get_db())

        # Update password
        user.set_password(data["new_password"])
        db.commit()

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({"error": "Password change failed"}), 500
    finally:
        if "db" in locals():
            db.close()
