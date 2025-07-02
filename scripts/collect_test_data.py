#!/usr/bin/env python3
"""
Collect real Reddit data for testing purposes.

This script downloads a curated set of Reddit posts and comments
for use in automated testing. The data is saved to a SQLite database
that can be used as a fixture in tests.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import praw

from reddit_analyzer.models import Base
from reddit_analyzer.models.user import User
from reddit_analyzer.models.subreddit import Subreddit
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.comment import Comment
from reddit_analyzer.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataCollector:
    """Collect curated Reddit data for testing."""

    def __init__(self, output_path: str = "tests/fixtures/test_data.db"):
        """Initialize the test data collector."""
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing test database
        if self.output_path.exists():
            self.output_path.unlink()
            logger.info(f"Removed existing test database: {self.output_path}")

        # Create new database
        self.engine = create_engine(f"sqlite:///{self.output_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT,
            username=Config.REDDIT_USERNAME,
            password=Config.REDDIT_PASSWORD,
        )

        # Define test data parameters
        self.test_config = {
            "subreddits": {
                "politics": {
                    "post_limit": 50,
                    "timeframe": "month",
                    "min_comments": 10,
                    "topics": [
                        "healthcare",
                        "economy",
                        "climate",
                        "immigration",
                        "education",
                    ],
                },
                "news": {
                    "post_limit": 30,
                    "timeframe": "month",
                    "min_comments": 5,
                    "topics": ["politics", "policy", "government"],
                },
                "worldnews": {
                    "post_limit": 20,
                    "timeframe": "month",
                    "min_comments": 5,
                    "topics": ["election", "democracy", "policy"],
                },
            },
            "target_metrics": {
                "total_posts": 100,
                "total_comments": 500,
                "political_diversity": 0.7,  # Mix of viewpoints
                "topic_coverage": 0.8,  # Coverage of defined topics
            },
        }

        self.collected_stats = {
            "posts": 0,
            "comments": 0,
            "users": set(),
            "topics": defaultdict(int),
            "sentiments": [],
        }

    def collect_data(self):
        """Collect test data from Reddit."""
        logger.info("Starting test data collection...")

        with self.Session() as session:
            for subreddit_name, config in self.test_config["subreddits"].items():
                logger.info(f"Collecting from r/{subreddit_name}...")
                self._collect_subreddit_data(session, subreddit_name, config)

        # Save manifest
        self._save_manifest()

        logger.info(f"Collection complete! Stats: {dict(self.collected_stats)}")

    def _collect_subreddit_data(self, session, subreddit_name: str, config: Dict):
        """Collect data from a specific subreddit."""
        # Get or create subreddit
        subreddit_obj = self.reddit.subreddit(subreddit_name)

        db_subreddit = session.query(Subreddit).filter_by(name=subreddit_name).first()

        if not db_subreddit:
            db_subreddit = Subreddit(
                name=subreddit_name,
                display_name=subreddit_obj.display_name,
                description=(
                    subreddit_obj.description[:500] if subreddit_obj.description else ""
                ),
                subscribers=subreddit_obj.subscribers,
                created_utc=datetime.fromtimestamp(subreddit_obj.created_utc),
                is_nsfw=subreddit_obj.over18,
            )
            session.add(db_subreddit)
            session.flush()

        # Collect posts
        posts_collected = 0
        time_filter = config["timeframe"]

        for submission in subreddit_obj.top(
            time_filter=time_filter, limit=config["post_limit"] * 2
        ):
            # Filter for quality posts
            if submission.num_comments < config["min_comments"]:
                continue

            # Check for topic relevance
            text = f"{submission.title} {submission.selftext}".lower()
            if not any(topic in text for topic in config["topics"]):
                continue

            # Get or create author
            author = self._get_or_create_user(session, submission.author)
            if not author:
                continue

            # Create post
            db_post = Post(
                id=submission.id,
                title=submission.title,
                selftext=submission.selftext,
                url=submission.url,
                score=submission.score,
                upvote_ratio=submission.upvote_ratio,
                num_comments=submission.num_comments,
                created_utc=datetime.fromtimestamp(submission.created_utc),
                author_id=author.id,
                subreddit_id=db_subreddit.id,
                is_self=submission.is_self,
                is_nsfw=submission.over_18,
                is_locked=submission.locked,
            )
            session.add(db_post)

            # Collect some comments
            self._collect_comments(session, submission, db_post.id, limit=10)

            posts_collected += 1
            self.collected_stats["posts"] += 1

            # Track topics
            for topic in config["topics"]:
                if topic in text:
                    self.collected_stats["topics"][topic] += 1

            if posts_collected >= config["post_limit"]:
                break

        session.commit()
        logger.info(f"Collected {posts_collected} posts from r/{subreddit_name}")

    def _collect_comments(self, session, submission, post_id: str, limit: int = 10):
        """Collect comments for a post."""
        submission.comments.replace_more(limit=0)
        comments = submission.comments.list()[:limit]

        for comment in comments:
            if not hasattr(comment, "body") or comment.body in [
                "[deleted]",
                "[removed]",
            ]:
                continue

            author = self._get_or_create_user(session, comment.author)
            if not author:
                continue

            db_comment = Comment(
                id=comment.id,
                body=comment.body[:10000],  # Limit length
                score=comment.score,
                created_utc=datetime.fromtimestamp(comment.created_utc),
                author_id=author.id,
                post_id=post_id,
                parent_id=(
                    comment.parent_id.split("_")[1]
                    if comment.parent_id != submission.id
                    else None
                ),
            )
            session.add(db_comment)
            self.collected_stats["comments"] += 1

    def _get_or_create_user(self, session, redditor) -> Optional[User]:
        """Get or create a user."""
        if not redditor or not hasattr(redditor, "name"):
            return None

        username = redditor.name
        if username in ["[deleted]", "AutoModerator"]:
            return None

        db_user = session.query(User).filter_by(username=username).first()

        if not db_user:
            try:
                db_user = User(
                    username=username,
                    comment_karma=getattr(redditor, "comment_karma", 0),
                    link_karma=getattr(redditor, "link_karma", 0),
                    created_utc=datetime.fromtimestamp(redditor.created_utc),
                    is_verified=getattr(redditor, "has_verified_email", False),
                )
                session.add(db_user)
                session.flush()
                self.collected_stats["users"].add(username)
            except Exception as e:
                logger.warning(f"Failed to create user {username}: {e}")
                return None

        return db_user

    def _save_manifest(self):
        """Save test data manifest."""
        manifest = {
            "created": datetime.now().isoformat(),
            "database": str(self.output_path),
            "config": self.test_config,
            "statistics": {
                "posts": self.collected_stats["posts"],
                "comments": self.collected_stats["comments"],
                "users": len(self.collected_stats["users"]),
                "topics": dict(self.collected_stats["topics"]),
            },
            "expected_results": {
                "top_topics": sorted(
                    self.collected_stats["topics"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5],
                "avg_comments_per_post": (
                    self.collected_stats["comments"] / self.collected_stats["posts"]
                    if self.collected_stats["posts"] > 0
                    else 0
                ),
            },
        }

        manifest_path = self.output_path.parent / "test_data_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Saved manifest to {manifest_path}")


def main():
    """Main entry point."""
    collector = TestDataCollector()

    try:
        collector.collect_data()
        logger.info("Test data collection completed successfully!")
    except Exception as e:
        logger.error(f"Failed to collect test data: {e}")
        raise


if __name__ == "__main__":
    main()
