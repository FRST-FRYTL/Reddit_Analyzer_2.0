"""Enhanced Reddit API client with rate limiting, caching, and advanced features."""

import asyncio
import praw
from typing import List, Optional, Dict, Any, AsyncGenerator, Callable
from datetime import datetime
import time
from contextlib import asynccontextmanager

from app.config import get_config
from app.utils.logging import LoggerMixin
from app.core.rate_limiter import RateLimiter, RateLimitConfig
from app.core.request_queue import RequestQueue
from app.core.cache import get_cache


class EnhancedRedditClient(LoggerMixin):
    """Enhanced Reddit API client with rate limiting, caching, and pagination."""

    def __init__(self, rate_limit_config: Optional[RateLimitConfig] = None):
        """Initialize enhanced Reddit client."""
        self.logger.info("Initializing Enhanced Reddit client")

        config = get_config()
        config.validate()

        # Initialize PRAW Reddit instance
        self.reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
        )

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())

        # Initialize request queue
        self.request_queue = RequestQueue(max_concurrent=3)

        # Initialize cache
        self.cache = get_cache()

        # Circuit breaker state
        self.circuit_breaker = {
            "failure_count": 0,
            "failure_threshold": 5,
            "reset_timeout": 300,  # 5 minutes
            "last_failure_time": 0,
            "state": "closed",  # closed, open, half-open
        }

        # Test authentication
        try:
            self.reddit.user.me()
            self.logger.info("Enhanced Reddit authentication successful")
        except Exception as e:
            self.logger.error(f"Enhanced Reddit authentication failed: {e}")
            raise

    async def start(self):
        """Start the enhanced client background services."""
        await self.request_queue.start_workers()
        self.logger.info("Enhanced Reddit client started")

    async def stop(self):
        """Stop the enhanced client background services."""
        await self.request_queue.stop_workers()
        self.cache.close()
        self.logger.info("Enhanced Reddit client stopped")

    @asynccontextmanager
    async def circuit_breaker_context(self):
        """Circuit breaker context manager."""
        if self.circuit_breaker["state"] == "open":
            time_since_failure = time.time() - self.circuit_breaker["last_failure_time"]
            if time_since_failure < self.circuit_breaker["reset_timeout"]:
                raise Exception("Circuit breaker is open")
            else:
                self.circuit_breaker["state"] = "half-open"

        try:
            yield
            # Success - reset circuit breaker if it was half-open
            if self.circuit_breaker["state"] == "half-open":
                self.circuit_breaker["state"] = "closed"
                self.circuit_breaker["failure_count"] = 0

        except Exception as e:
            self.circuit_breaker["failure_count"] += 1
            self.circuit_breaker["last_failure_time"] = time.time()

            if (
                self.circuit_breaker["failure_count"]
                >= self.circuit_breaker["failure_threshold"]
            ):
                self.circuit_breaker["state"] = "open"
                self.logger.warning("Circuit breaker opened due to repeated failures")

            raise e

    async def _cached_request(
        self, cache_key: str, cache_ttl: int, request_func: Callable, *args, **kwargs
    ) -> Any:
        """Execute a request with caching."""
        # Try cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            self.logger.debug(f"Cache hit for key: {cache_key}")
            return cached_result

        # Execute request with rate limiting and circuit breaker
        await self.rate_limiter.wait_if_needed("reddit_api")

        async with self.circuit_breaker_context():
            result = await asyncio.get_event_loop().run_in_executor(
                None, request_func, *args, **kwargs
            )

        # Cache the result
        await self.cache.set(cache_key, result, ttl=cache_ttl)
        return result

    async def get_subreddit_info(
        self, subreddit_name: str, use_cache: bool = True, cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """Get subreddit information with caching."""
        cache_key = f"subreddit_info:{subreddit_name}"

        def _get_subreddit_info():
            subreddit = self.reddit.subreddit(subreddit_name)
            return {
                "name": subreddit.display_name,
                "display_name": subreddit.display_name_prefixed,
                "description": subreddit.description,
                "public_description": subreddit.public_description,
                "subscribers": subreddit.subscribers,
                "created_utc": datetime.fromtimestamp(
                    subreddit.created_utc
                ).isoformat(),
                "is_nsfw": subreddit.over18,
                "lang": subreddit.lang,
                "submission_type": subreddit.submission_type,
                "fetched_at": datetime.now().isoformat(),
            }

        if use_cache:
            return await self._cached_request(cache_key, cache_ttl, _get_subreddit_info)
        else:
            await self.rate_limiter.wait_if_needed("reddit_api")
            async with self.circuit_breaker_context():
                return await asyncio.get_event_loop().run_in_executor(
                    None, _get_subreddit_info
                )

    async def get_subreddit_posts(
        self,
        subreddit_name: str,
        sort: str = "hot",
        limit: int = 100,
        time_filter: str = "all",
        use_cache: bool = True,
        cache_ttl: int = 900,  # 15 minutes
    ) -> List[Dict[str, Any]]:
        """Get posts from a subreddit with caching and pagination."""
        cache_key = f"posts:{subreddit_name}:{sort}:{limit}:{time_filter}"

        def _get_posts():
            subreddit = self.reddit.subreddit(subreddit_name)

            # Choose sorting method
            if sort == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort == "new":
                posts = subreddit.new(limit=limit)
            elif sort == "top":
                posts = subreddit.top(limit=limit, time_filter=time_filter)
            elif sort == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                raise ValueError(f"Invalid sort method: {sort}")

            post_data = []
            for post in posts:
                try:
                    post_dict = {
                        "id": post.id,
                        "title": post.title,
                        "selftext": post.selftext,
                        "url": post.url,
                        "author": post.author.name if post.author else "[deleted]",
                        "subreddit": post.subreddit.display_name,
                        "score": post.score,
                        "upvote_ratio": post.upvote_ratio,
                        "num_comments": post.num_comments,
                        "created_utc": datetime.fromtimestamp(
                            post.created_utc
                        ).isoformat(),
                        "is_self": post.is_self,
                        "is_nsfw": post.over_18,
                        "is_locked": post.locked,
                        "distinguished": post.distinguished,
                        "stickied": post.stickied,
                        "link_flair_text": post.link_flair_text,
                        "post_hint": getattr(post, "post_hint", None),
                        "fetched_at": datetime.now().isoformat(),
                    }
                    post_data.append(post_dict)
                except Exception as e:
                    self.logger.warning(f"Error processing post {post.id}: {e}")
                    continue

            return post_data

        if use_cache:
            return await self._cached_request(cache_key, cache_ttl, _get_posts)
        else:
            await self.rate_limiter.wait_if_needed("reddit_api")
            async with self.circuit_breaker_context():
                return await asyncio.get_event_loop().run_in_executor(None, _get_posts)

    async def get_post_comments(
        self,
        post_id: str,
        limit: Optional[int] = None,
        depth: Optional[int] = None,
        sort: str = "best",
        use_cache: bool = True,
        cache_ttl: int = 1800,  # 30 minutes
    ) -> List[Dict[str, Any]]:
        """Get comments for a specific post with depth control."""
        cache_key = f"comments:{post_id}:{limit}:{depth}:{sort}"

        def _get_comments():
            submission = self.reddit.submission(id=post_id)

            # Set comment sort
            submission.comment_sort = sort

            # Handle more comments based on depth
            if depth is not None:
                submission.comments.replace_more(limit=depth)
            else:
                submission.comments.replace_more(limit=0)

            comment_data = []
            comments_list = submission.comments.list()

            for comment in comments_list:
                try:
                    if hasattr(comment, "body") and comment.body not in [
                        "[deleted]",
                        "[removed]",
                    ]:
                        comment_dict = {
                            "id": comment.id,
                            "post_id": post_id,
                            "parent_id": comment.parent_id,
                            "author": (
                                comment.author.name if comment.author else "[deleted]"
                            ),
                            "body": comment.body,
                            "score": comment.score,
                            "created_utc": datetime.fromtimestamp(
                                comment.created_utc
                            ).isoformat(),
                            "is_deleted": comment.body in ["[deleted]", "[removed]"],
                            "distinguished": comment.distinguished,
                            "stickied": comment.stickied,
                            "depth": comment.depth if hasattr(comment, "depth") else 0,
                            "controversiality": comment.controversiality,
                            "fetched_at": datetime.now().isoformat(),
                        }
                        comment_data.append(comment_dict)

                        if limit and len(comment_data) >= limit:
                            break
                except Exception as e:
                    self.logger.warning(f"Error processing comment {comment.id}: {e}")
                    continue

            return comment_data

        if use_cache:
            return await self._cached_request(cache_key, cache_ttl, _get_comments)
        else:
            await self.rate_limiter.wait_if_needed("reddit_api")
            async with self.circuit_breaker_context():
                return await asyncio.get_event_loop().run_in_executor(
                    None, _get_comments
                )

    async def get_user_info(
        self, username: str, use_cache: bool = True, cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """Get user information with caching."""
        cache_key = f"user_info:{username}"

        def _get_user_info():
            redditor = self.reddit.redditor(username)
            return {
                "username": redditor.name,
                "created_utc": datetime.fromtimestamp(redditor.created_utc).isoformat(),
                "comment_karma": redditor.comment_karma,
                "link_karma": redditor.link_karma,
                "total_karma": redditor.comment_karma + redditor.link_karma,
                "is_verified": getattr(redditor, "verified", False),
                "has_verified_email": getattr(redditor, "has_verified_email", None),
                "is_gold": getattr(redditor, "is_gold", False),
                "is_mod": getattr(redditor, "is_mod", False),
                "fetched_at": datetime.now().isoformat(),
            }

        if use_cache:
            return await self._cached_request(cache_key, cache_ttl, _get_user_info)
        else:
            await self.rate_limiter.wait_if_needed("reddit_api")
            async with self.circuit_breaker_context():
                return await asyncio.get_event_loop().run_in_executor(
                    None, _get_user_info
                )

    async def stream_subreddit_posts(
        self,
        subreddit_name: str,
        callback: Callable[[Dict[str, Any]], None],
        pause_after: Optional[int] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream new posts from a subreddit in real-time."""
        subreddit = self.reddit.subreddit(subreddit_name)
        seen_posts = set()

        self.logger.info(f"Starting stream for r/{subreddit_name}")

        while True:
            try:
                await self.rate_limiter.wait_if_needed("reddit_stream")

                async with self.circuit_breaker_context():
                    new_posts = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: list(subreddit.new(limit=25))
                    )

                for post in new_posts:
                    if post.id not in seen_posts:
                        seen_posts.add(post.id)

                        post_data = {
                            "id": post.id,
                            "title": post.title,
                            "author": post.author.name if post.author else "[deleted]",
                            "subreddit": post.subreddit.display_name,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "created_utc": datetime.fromtimestamp(
                                post.created_utc
                            ).isoformat(),
                            "url": post.url,
                            "selftext": post.selftext,
                            "is_self": post.is_self,
                            "stream_timestamp": datetime.now().isoformat(),
                        }

                        if callback:
                            try:
                                await asyncio.get_event_loop().run_in_executor(
                                    None, callback, post_data
                                )
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")

                        yield post_data

                # Clean up old seen posts to prevent memory growth
                if len(seen_posts) > 1000:
                    seen_posts = set(list(seen_posts)[-500:])

                # Wait before next iteration
                await asyncio.sleep(pause_after or 30)

            except Exception as e:
                self.logger.error(f"Stream error for r/{subreddit_name}: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def bulk_collect_subreddit_data(
        self,
        subreddit_names: List[str],
        posts_per_subreddit: int = 100,
        collect_comments: bool = True,
        max_comments_per_post: int = 50,
    ) -> Dict[str, Any]:
        """Collect data from multiple subreddits efficiently."""
        results = {
            "subreddits": {},
            "total_posts": 0,
            "total_comments": 0,
            "collection_timestamp": datetime.now().isoformat(),
        }

        for subreddit_name in subreddit_names:
            try:
                self.logger.info(f"Collecting data from r/{subreddit_name}")

                # Get subreddit info
                subreddit_info = await self.get_subreddit_info(subreddit_name)

                # Get posts
                posts = await self.get_subreddit_posts(
                    subreddit_name, limit=posts_per_subreddit
                )

                comments_collected = 0
                if collect_comments:
                    for post in posts[
                        :10
                    ]:  # Limit comment collection to first 10 posts
                        try:
                            post_comments = await self.get_post_comments(
                                post["id"], limit=max_comments_per_post
                            )
                            post["comments"] = post_comments
                            comments_collected += len(post_comments)
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to get comments for post {post['id']}: {e}"
                            )
                            post["comments"] = []

                results["subreddits"][subreddit_name] = {
                    "info": subreddit_info,
                    "posts": posts,
                    "posts_count": len(posts),
                    "comments_count": comments_collected,
                }

                results["total_posts"] += len(posts)
                results["total_comments"] += comments_collected

            except Exception as e:
                self.logger.error(
                    f"Failed to collect data from r/{subreddit_name}: {e}"
                )
                results["subreddits"][subreddit_name] = {
                    "error": str(e),
                    "posts_count": 0,
                    "comments_count": 0,
                }

        return results

    def get_client_stats(self) -> Dict[str, Any]:
        """Get client performance and status statistics."""
        return {
            "rate_limiter_status": self.rate_limiter.get_status(),
            "request_queue_status": self.request_queue.get_status(),
            "cache_stats": self.cache.get_stats(),
            "circuit_breaker": self.circuit_breaker,
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check."""
        health_status = {
            "overall": "healthy",
            "reddit_api": "unknown",
            "rate_limiter": "unknown",
            "cache": "unknown",
            "request_queue": "unknown",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Test Reddit API
            test_sub = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.reddit.subreddit("announcements")
            )
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: next(test_sub.hot(limit=1))
            )
            health_status["reddit_api"] = "healthy"
        except Exception as e:
            health_status["reddit_api"] = f"unhealthy: {e}"
            health_status["overall"] = "degraded"

        # Test cache
        cache_health = await self.cache.health_check()
        health_status["cache"] = cache_health["status"]
        if cache_health["status"] != "healthy":
            health_status["overall"] = "degraded"

        # Check rate limiter
        rate_status = self.rate_limiter.get_status()
        health_status["rate_limiter"] = (
            "healthy" if rate_status["remaining_requests"] > 0 else "limited"
        )

        # Check request queue
        queue_status = self.request_queue.get_status()
        health_status["request_queue"] = (
            "healthy" if queue_status["running"] else "stopped"
        )

        return health_status
