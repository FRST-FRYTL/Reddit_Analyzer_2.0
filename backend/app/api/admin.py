"""Admin API endpoints."""

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from app.database import get_db
from app.models.user import User, UserRole
from app.models.collection_job import CollectionJob
from app.models.subreddit import Subreddit
from app.models.post import Post
from app.models.comment import Comment
from app.middleware.auth import admin_required, moderator_required
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """List all users (admin only)."""
    try:
        db = next(get_db())

        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)

        users_query = db.query(User).order_by(User.created_at.desc())
        total = users_query.count()
        users = users_query.offset((page - 1) * per_page).limit(per_page).all()

        return (
            jsonify(
                {
                    "users": [
                        {
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
                        for user in users
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": (total + per_page - 1) // per_page,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({"error": "Failed to list users"}), 500
    finally:
        if "db" in locals():
            db.close()


@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@admin_required
def update_user_role():
    """Update user role (admin only)."""
    try:
        data = request.get_json()
        if not data or "role" not in data:
            return jsonify({"error": "Role is required"}), 400

        try:
            new_role = UserRole(data["role"])
        except ValueError:
            return jsonify({"error": "Invalid role"}), 400

        user_id = request.view_args["user_id"]
        db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Prevent admin from changing their own role
        if user.id == g.current_user.id:
            return jsonify({"error": "Cannot modify your own role"}), 400

        user.role = new_role
        db.commit()

        return (
            jsonify(
                {
                    "message": "User role updated successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role.value,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Update user role error: {e}")
        return jsonify({"error": "Failed to update user role"}), 500
    finally:
        if "db" in locals():
            db.close()


@admin_bp.route("/users/<int:user_id>/activate", methods=["PUT"])
@admin_required
def activate_user():
    """Activate/deactivate user (admin only)."""
    try:
        data = request.get_json()
        if not data or "is_active" not in data:
            return jsonify({"error": "is_active field is required"}), 400

        user_id = request.view_args["user_id"]
        db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Prevent admin from deactivating themselves
        if user.id == g.current_user.id and not data["is_active"]:
            return jsonify({"error": "Cannot deactivate your own account"}), 400

        user.is_active = data["is_active"]
        db.commit()

        status = "activated" if user.is_active else "deactivated"

        return (
            jsonify(
                {
                    "message": f"User {status} successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "is_active": user.is_active,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Activate user error: {e}")
        return jsonify({"error": "Failed to update user status"}), 500
    finally:
        if "db" in locals():
            db.close()


@admin_bp.route("/stats", methods=["GET"])
@moderator_required
def get_system_stats():
    """Get system statistics (moderator or admin)."""
    try:
        db = next(get_db())

        # User statistics
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active).scalar()

        # Content statistics
        total_subreddits = db.query(func.count(Subreddit.id)).scalar()
        total_posts = db.query(func.count(Post.id)).scalar()
        total_comments = db.query(func.count(Comment.id)).scalar()

        # Collection job statistics
        pending_jobs = (
            db.query(func.count(CollectionJob.id))
            .filter(CollectionJob.status == "pending")
            .scalar()
        )
        running_jobs = (
            db.query(func.count(CollectionJob.id))
            .filter(CollectionJob.status == "running")
            .scalar()
        )
        completed_jobs = (
            db.query(func.count(CollectionJob.id))
            .filter(CollectionJob.status == "completed")
            .scalar()
        )
        failed_jobs = (
            db.query(func.count(CollectionJob.id))
            .filter(CollectionJob.status == "failed")
            .scalar()
        )

        return (
            jsonify(
                {
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "inactive": total_users - active_users,
                    },
                    "content": {
                        "subreddits": total_subreddits,
                        "posts": total_posts,
                        "comments": total_comments,
                    },
                    "jobs": {
                        "pending": pending_jobs,
                        "running": running_jobs,
                        "completed": completed_jobs,
                        "failed": failed_jobs,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get system stats error: {e}")
        return jsonify({"error": "Failed to get system statistics"}), 500
    finally:
        if "db" in locals():
            db.close()


@admin_bp.route("/health", methods=["GET"])
@moderator_required
def health_check():
    """Health check endpoint (moderator or admin)."""
    try:
        db = next(get_db())

        # Test database connection
        db.execute("SELECT 1")

        return (
            jsonify(
                {"status": "healthy", "database": "connected", "timestamp": func.now()}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return (
            jsonify({"status": "unhealthy", "database": "error", "error": str(e)}),
            500,
        )
    finally:
        if "db" in locals():
            db.close()
