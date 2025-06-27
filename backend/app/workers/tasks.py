"""Celery tasks for Reddit data collection."""

import asyncio
from datetime import datetime
from typing import Dict, List, Any
import structlog

from app.workers.celery_app import celery_app
from app.services.enhanced_reddit_client import EnhancedRedditClient
from app.core.rate_limiter import RateLimitConfig
from app.database import get_db_session
from app.models import Post, Comment, User, Subreddit

# Configure structured logging
logger = structlog.get_logger(__name__)


def get_reddit_client() -> EnhancedRedditClient:
    """Get configured Reddit client instance."""
    rate_config = RateLimitConfig(
        requests_per_minute=60, burst_limit=10, backoff_factor=2.0, max_retries=3
    )
    return EnhancedRedditClient(rate_config)


@celery_app.task(bind=True, max_retries=3)
def collect_subreddit_posts(
    self, subreddit_name: str, collection_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Collect posts from a subreddit."""
    try:
        logger.info(
            "Starting subreddit post collection",
            subreddit=subreddit_name,
            task_id=self.request.id,
            config=collection_config,
        )

        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Initializing Reddit client",
                "subreddit": subreddit_name,
                "progress": 0,
            },
        )

        client = get_reddit_client()

        # Extract configuration
        limit = collection_config.get("post_limit", 100)
        sort_method = collection_config.get("sorting", "hot")
        time_filter = collection_config.get("time_filter", "all")
        collect_comments = collection_config.get("collect_comments", False)

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Collecting posts",
                "subreddit": subreddit_name,
                "progress": 25,
            },
        )

        # Use asyncio to run async client methods
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Start the client
            loop.run_until_complete(client.start())

            # Collect posts
            posts = loop.run_until_complete(
                client.get_subreddit_posts(
                    subreddit_name=subreddit_name,
                    sort=sort_method,
                    limit=limit,
                    time_filter=time_filter,
                    use_cache=False,  # Don't use cache for scheduled collections
                )
            )

            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": "Storing posts to database",
                    "subreddit": subreddit_name,
                    "posts_collected": len(posts),
                    "progress": 50,
                },
            )

            # Store posts to database
            stored_count = 0
            with get_db_session() as db:
                for post_data in posts:
                    try:
                        # Check if post already exists
                        existing_post = (
                            db.query(Post)
                            .filter(Post.reddit_id == post_data["id"])
                            .first()
                        )

                        if not existing_post:
                            # Get or create subreddit
                            subreddit = (
                                db.query(Subreddit)
                                .filter(Subreddit.name == subreddit_name)
                                .first()
                            )

                            if not subreddit:
                                subreddit = Subreddit(
                                    name=subreddit_name, display_name=subreddit_name
                                )
                                db.add(subreddit)
                                db.flush()

                            # Get or create user
                            user = None
                            if post_data["author"] != "[deleted]":
                                user = (
                                    db.query(User)
                                    .filter(User.username == post_data["author"])
                                    .first()
                                )

                                if not user:
                                    user = User(username=post_data["author"])
                                    db.add(user)
                                    db.flush()

                            # Create post
                            post = Post(
                                reddit_id=post_data["id"],
                                title=post_data["title"],
                                selftext=post_data["selftext"],
                                url=post_data["url"],
                                score=post_data["score"],
                                upvote_ratio=post_data["upvote_ratio"],
                                num_comments=post_data["num_comments"],
                                created_utc=datetime.fromisoformat(
                                    post_data["created_utc"].replace("Z", "+00:00")
                                ),
                                is_self=post_data["is_self"],
                                is_nsfw=post_data["is_nsfw"],
                                is_locked=post_data["is_locked"],
                                subreddit_id=subreddit.id,
                                user_id=user.id if user else None,
                            )
                            db.add(post)
                            stored_count += 1

                            # Schedule comment collection if requested
                            if collect_comments:
                                collect_post_comments.delay(
                                    post_data["id"],
                                    collection_config.get("comment_config", {}),
                                )

                    except Exception as e:
                        logger.error(
                            "Error storing post",
                            post_id=post_data.get("id"),
                            error=str(e),
                        )
                        continue

                db.commit()

            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": "Collection completed",
                    "subreddit": subreddit_name,
                    "posts_collected": len(posts),
                    "posts_stored": stored_count,
                    "progress": 100,
                },
            )

            result = {
                "status": "success",
                "subreddit": subreddit_name,
                "posts_collected": len(posts),
                "posts_stored": stored_count,
                "collection_time": datetime.now().isoformat(),
                "task_id": self.request.id,
            }

            logger.info("Subreddit post collection completed", result=result)

            return result

        finally:
            # Always stop the client
            loop.run_until_complete(client.stop())
            loop.close()

    except Exception as exc:
        logger.error(
            "Subreddit post collection failed",
            subreddit=subreddit_name,
            error=str(exc),
            task_id=self.request.id,
        )

        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 60 * (2**self.request.retries)  # Exponential backoff
            raise self.retry(countdown=countdown, exc=exc)

        # Max retries exceeded
        return {
            "status": "failed",
            "error": str(exc),
            "subreddit": subreddit_name,
            "task_id": self.request.id,
        }


@celery_app.task(bind=True, max_retries=3)
def collect_post_comments(
    self, post_id: str, comment_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Collect comments for a specific post."""
    try:
        logger.info(
            "Starting comment collection", post_id=post_id, task_id=self.request.id
        )

        client = get_reddit_client()

        # Extract configuration
        limit = comment_config.get("limit", 100)
        depth = comment_config.get("depth", 3)
        sort_method = comment_config.get("sort", "best")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(client.start())

            comments = loop.run_until_complete(
                client.get_post_comments(
                    post_id=post_id,
                    limit=limit,
                    depth=depth,
                    sort=sort_method,
                    use_cache=False,
                )
            )

            # Store comments to database
            stored_count = 0
            with get_db_session() as db:
                # Get the post
                post = db.query(Post).filter(Post.reddit_id == post_id).first()

                if not post:
                    raise ValueError(f"Post {post_id} not found in database")

                for comment_data in comments:
                    try:
                        # Check if comment already exists
                        existing_comment = (
                            db.query(Comment)
                            .filter(Comment.reddit_id == comment_data["id"])
                            .first()
                        )

                        if not existing_comment:
                            # Get or create user
                            user = None
                            if comment_data["author"] != "[deleted]":
                                user = (
                                    db.query(User)
                                    .filter(User.username == comment_data["author"])
                                    .first()
                                )

                                if not user:
                                    user = User(username=comment_data["author"])
                                    db.add(user)
                                    db.flush()

                            comment = Comment(
                                reddit_id=comment_data["id"],
                                body=comment_data["body"],
                                score=comment_data["score"],
                                created_utc=datetime.fromisoformat(
                                    comment_data["created_utc"].replace("Z", "+00:00")
                                ),
                                post_id=post.id,
                                user_id=user.id if user else None,
                                parent_reddit_id=comment_data.get("parent_id"),
                            )
                            db.add(comment)
                            stored_count += 1

                    except Exception as e:
                        logger.error(
                            "Error storing comment",
                            comment_id=comment_data.get("id"),
                            error=str(e),
                        )
                        continue

                db.commit()

            result = {
                "status": "success",
                "post_id": post_id,
                "comments_collected": len(comments),
                "comments_stored": stored_count,
                "collection_time": datetime.now().isoformat(),
                "task_id": self.request.id,
            }

            logger.info("Comment collection completed", result=result)
            return result

        finally:
            loop.run_until_complete(client.stop())
            loop.close()

    except Exception as exc:
        logger.error(
            "Comment collection failed",
            post_id=post_id,
            error=str(exc),
            task_id=self.request.id,
        )

        if self.request.retries < self.max_retries:
            countdown = 60 * (2**self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)

        return {
            "status": "failed",
            "error": str(exc),
            "post_id": post_id,
            "task_id": self.request.id,
        }


@celery_app.task(bind=True, max_retries=3)
def collect_user_data(
    self, username: str, user_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Collect detailed user information."""
    try:
        logger.info(
            "Starting user data collection", username=username, task_id=self.request.id
        )

        client = get_reddit_client()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(client.start())

            user_info = loop.run_until_complete(
                client.get_user_info(username=username, use_cache=False)
            )

            # Update user in database
            with get_db_session() as db:
                user = db.query(User).filter(User.username == username).first()

                if user:
                    # Update existing user
                    user.comment_karma = user_info["comment_karma"]
                    user.link_karma = user_info["link_karma"]
                    user.created_utc = datetime.fromisoformat(
                        user_info["created_utc"].replace("Z", "+00:00")
                    )
                    user.is_verified = user_info.get("is_verified", False)
                    user.updated_at = datetime.now()
                else:
                    # Create new user
                    user = User(
                        username=username,
                        comment_karma=user_info["comment_karma"],
                        link_karma=user_info["link_karma"],
                        created_utc=datetime.fromisoformat(
                            user_info["created_utc"].replace("Z", "+00:00")
                        ),
                        is_verified=user_info.get("is_verified", False),
                    )
                    db.add(user)

                db.commit()

            result = {
                "status": "success",
                "username": username,
                "user_data": user_info,
                "collection_time": datetime.now().isoformat(),
                "task_id": self.request.id,
            }

            logger.info("User data collection completed", result=result)
            return result

        finally:
            loop.run_until_complete(client.stop())
            loop.close()

    except Exception as exc:
        logger.error(
            "User data collection failed",
            username=username,
            error=str(exc),
            task_id=self.request.id,
        )

        if self.request.retries < self.max_retries:
            countdown = 60 * (2**self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)

        return {
            "status": "failed",
            "error": str(exc),
            "username": username,
            "task_id": self.request.id,
        }


@celery_app.task
def validate_collected_data(data_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate a batch of collected data."""
    try:
        logger.info("Starting data validation", batch_size=len(data_batch))

        validation_results = {
            "total_items": len(data_batch),
            "valid_items": 0,
            "invalid_items": 0,
            "errors": [],
        }

        for item in data_batch:
            try:
                # Validate based on item type
                item_type = item.get("type", "unknown")

                if item_type == "post":
                    # Validate post data
                    required_fields = [
                        "id",
                        "title",
                        "author",
                        "subreddit",
                        "created_utc",
                    ]
                    for field in required_fields:
                        if field not in item or item[field] is None:
                            raise ValueError(f"Missing required field: {field}")

                    validation_results["valid_items"] += 1

                elif item_type == "comment":
                    # Validate comment data
                    required_fields = ["id", "post_id", "author", "body", "created_utc"]
                    for field in required_fields:
                        if field not in item or item[field] is None:
                            raise ValueError(f"Missing required field: {field}")

                    validation_results["valid_items"] += 1

                else:
                    raise ValueError(f"Unknown item type: {item_type}")

            except Exception as e:
                validation_results["invalid_items"] += 1
                validation_results["errors"].append(
                    {"item_id": item.get("id", "unknown"), "error": str(e)}
                )

        logger.info("Data validation completed", results=validation_results)

        return validation_results

    except Exception as exc:
        logger.error("Data validation failed", error=str(exc))
        return {"status": "failed", "error": str(exc)}


@celery_app.task
def health_check() -> Dict[str, Any]:
    """Perform system health check."""
    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {},
        }

        # Check database connectivity
        try:
            with get_db_session() as db:
                db.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"

        # Check Reddit API
        try:
            client = get_reddit_client()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(client.start())
                health_result = loop.run_until_complete(client.health_check())
                health_status["checks"]["reddit_api"] = health_result["overall"]
            finally:
                loop.run_until_complete(client.stop())
                loop.close()
        except Exception as e:
            health_status["checks"]["reddit_api"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"

        return health_status

    except Exception as exc:
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "error": str(exc),
        }


@celery_app.task
def cleanup_old_results() -> Dict[str, Any]:
    """Clean up old task results and data."""
    try:
        logger.info("Starting cleanup of old results")

        # Clean up old Celery results (older than 24 hours)
        # This would typically involve cleaning up the result backend
        # Implementation depends on the specific backend used

        cleanup_count = 0  # Placeholder

        logger.info("Cleanup completed", items_cleaned=cleanup_count)

        return {
            "status": "success",
            "items_cleaned": cleanup_count,
            "cleanup_time": datetime.now().isoformat(),
        }

    except Exception as exc:
        logger.error("Cleanup failed", error=str(exc))
        return {"status": "failed", "error": str(exc)}
