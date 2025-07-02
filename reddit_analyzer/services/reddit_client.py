"""Reddit API client using PRAW."""

import praw
from typing import List, Optional, Dict, Any
from datetime import datetime

from reddit_analyzer.config import get_config
from reddit_analyzer.utils.logging import LoggerMixin

config = get_config()


class RedditClient(LoggerMixin):
    """Reddit API client wrapper."""

    def __init__(self):
        """Initialize Reddit client."""
        self.logger.info("Initializing Reddit client")

        # Validate configuration
        config.validate()

        # Initialize PRAW Reddit instance
        self.reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
        )

        # Test authentication
        try:
            # This will raise an exception if authentication fails
            self.reddit.user.me()
            self.logger.info("Reddit authentication successful")
        except Exception as e:
            self.logger.error(f"Reddit authentication failed: {e}")
            raise

    def get_subreddit_info(self, subreddit_name: str) -> Dict[str, Any]:
        """Get subreddit information."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            return {
                "name": subreddit.display_name,
                "display_name": subreddit.display_name_prefixed,
                "description": subreddit.description,
                "subscribers": subreddit.subscribers,
                "created_utc": datetime.fromtimestamp(subreddit.created_utc),
                "is_nsfw": subreddit.over18,
            }
        except Exception as e:
            self.logger.error(
                f"Error fetching subreddit info for {subreddit_name}: {e}"
            )
            raise

    def get_subreddit_posts(
        self,
        subreddit_name: str,
        sort: str = "hot",
        limit: int = 100,
        time_filter: str = "all",
    ) -> List[Dict[str, Any]]:
        """Get posts from a subreddit."""
        try:
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
                    "created_utc": datetime.fromtimestamp(post.created_utc),
                    "is_self": post.is_self,
                    "is_nsfw": post.over_18,
                    "is_locked": post.locked,
                }
                post_data.append(post_dict)

            self.logger.info(f"Fetched {len(post_data)} posts from r/{subreddit_name}")
            return post_data

        except Exception as e:
            self.logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            raise

    def get_post_comments(
        self,
        post_id: str,
        limit: int = 50,
        depth: int = 3,
        min_score: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get comments for a specific post with enhanced options.

        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to fetch
            depth: Maximum comment tree depth
            min_score: Minimum comment score to include

        Returns:
            List of comment dictionaries with depth information
        """
        try:
            submission = self.reddit.submission(id=post_id)

            # Configure comment extraction
            submission.comment_limit = limit
            submission.comments.replace_more(limit=depth * 10)  # Expand based on depth

            comment_data = []

            def process_comment(comment, current_depth=0):
                """Recursively process comments and their replies."""
                if current_depth > depth:
                    return

                if not hasattr(comment, "body"):
                    return

                # Apply min_score filter
                if min_score is not None and comment.score < min_score:
                    return

                comment_dict = {
                    "id": comment.id,
                    "post_id": post_id,
                    "parent_id": comment.parent_id,
                    "author": (comment.author.name if comment.author else "[deleted]"),
                    "body": comment.body,
                    "score": comment.score,
                    "created_utc": datetime.fromtimestamp(comment.created_utc),
                    "edited": bool(comment.edited),
                    "is_deleted": comment.body == "[deleted]",
                    "depth": current_depth,
                }
                comment_data.append(comment_dict)

                # Process replies
                if hasattr(comment, "replies"):
                    for reply in comment.replies:
                        if len(comment_data) >= limit:
                            break
                        process_comment(reply, current_depth + 1)

            # Process all top-level comments
            for comment in submission.comments:
                if len(comment_data) >= limit:
                    break
                process_comment(comment)

            self.logger.info(
                f"Fetched {len(comment_data)} comments for post {post_id} "
                f"(max depth: {max(c['depth'] for c in comment_data) if comment_data else 0})"
            )
            return comment_data

        except Exception as e:
            self.logger.error(f"Error fetching comments for post {post_id}: {e}")
            raise

    def get_all_comments(
        self, subreddit_name: str, limit: int = 1000, time_filter: str = "all"
    ) -> List[Dict[str, Any]]:
        """Fetch comments directly from subreddit stream.

        Args:
            subreddit_name: Name of the subreddit
            limit: Maximum number of comments to fetch
            time_filter: Time filter for comments

        Returns:
            List of comment dictionaries
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            comment_data = []
            comment_count = 0

            # Use comment stream for recent comments
            for comment in subreddit.comments(limit=limit):
                if not hasattr(comment, "body"):
                    continue

                comment_dict = {
                    "id": comment.id,
                    "post_id": comment.submission.id,
                    "parent_id": comment.parent_id,
                    "author": (comment.author.name if comment.author else "[deleted]"),
                    "body": comment.body,
                    "score": comment.score,
                    "created_utc": datetime.fromtimestamp(comment.created_utc),
                    "edited": bool(comment.edited),
                    "is_deleted": comment.body == "[deleted]",
                    "depth": 0,  # Will be calculated later if needed
                }
                comment_data.append(comment_dict)
                comment_count += 1

                if comment_count >= limit:
                    break

            self.logger.info(
                f"Fetched {len(comment_data)} comments from r/{subreddit_name}"
            )
            return comment_data

        except Exception as e:
            self.logger.error(f"Error fetching comments from r/{subreddit_name}: {e}")
            raise

    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information."""
        try:
            redditor = self.reddit.redditor(username)

            return {
                "username": redditor.name,
                "created_utc": datetime.fromtimestamp(redditor.created_utc),
                "comment_karma": redditor.comment_karma,
                "link_karma": redditor.link_karma,
                "is_verified": (
                    redditor.verified if hasattr(redditor, "verified") else False
                ),
            }
        except Exception as e:
            self.logger.error(f"Error fetching user info for {username}: {e}")
            raise

    def test_connection(self) -> bool:
        """Test Reddit API connection."""
        try:
            # Try to fetch a simple post
            test_sub = self.reddit.subreddit("announcements")
            next(test_sub.hot(limit=1))
            self.logger.info("Reddit API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Reddit API connection test failed: {e}")
            return False
