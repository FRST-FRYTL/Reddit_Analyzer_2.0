"""Tests for Phase 2 Pydantic schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.validators.schemas import (
    RedditPostSchema,
    RedditCommentSchema,
    RedditUserSchema,
    SubredditSchema,
    CollectionConfigSchema,
    CollectionJobSchema,
)


class TestPhase2Schemas:
    """Test Phase 2 validation schemas."""

    def test_reddit_post_schema_valid(self):
        """Test valid Reddit post schema validation."""
        valid_post = {
            "id": "abc123",
            "title": "Test Post Title",
            "selftext": "This is test content",
            "url": "https://reddit.com/r/test/comments/abc123/",
            "author": "test_user",
            "subreddit": "test",
            "score": 100,
            "upvote_ratio": 0.95,
            "num_comments": 25,
            "created_utc": "2023-01-01T12:00:00Z",
            "is_self": True,
            "is_nsfw": False,
            "is_locked": False,
        }

        post = RedditPostSchema(**valid_post)
        assert post.id == "abc123"
        assert post.title == "Test Post Title"
        assert post.score == 100

    def test_reddit_post_schema_invalid_score(self):
        """Test Reddit post schema with invalid score."""
        invalid_post = {
            "id": "abc123",
            "title": "Test Post",
            "url": "https://reddit.com/test",
            "author": "test_user",
            "subreddit": "test",
            "score": -2000000,  # Too low
            "upvote_ratio": 0.95,
            "num_comments": 25,
            "created_utc": "2023-01-01T12:00:00Z",
            "is_self": True,
            "is_nsfw": False,
            "is_locked": False,
        }

        with pytest.raises(ValidationError):
            RedditPostSchema(**invalid_post)

    def test_reddit_comment_schema_valid(self):
        """Test valid Reddit comment schema validation."""
        valid_comment = {
            "id": "comment123",
            "post_id": "abc123",
            "parent_id": "abc123",
            "author": "commenter",
            "body": "This is a test comment",
            "score": 5,
            "created_utc": "2023-01-01T12:30:00Z",
            "is_deleted": False,
            "depth": 0,
        }

        comment = RedditCommentSchema(**valid_comment)
        assert comment.id == "comment123"
        assert comment.post_id == "abc123"
        assert comment.body == "This is a test comment"

    def test_reddit_user_schema_valid(self):
        """Test valid Reddit user schema validation."""
        valid_user = {
            "username": "test_user",
            "created_utc": "2020-01-01T00:00:00Z",
            "comment_karma": 1500,
            "link_karma": 300,
            "is_verified": False,
            "is_gold": False,
        }

        user = RedditUserSchema(**valid_user)
        assert user.username == "test_user"
        assert user.total_karma == 1800  # Should be calculated

    def test_subreddit_schema_valid(self):
        """Test valid subreddit schema validation."""
        valid_subreddit = {
            "name": "test",
            "display_name": "r/test",
            "description": "Test subreddit",
            "subscribers": 10000,
            "created_utc": "2019-01-01T00:00:00Z",
            "is_nsfw": False,
            "lang": "en",
        }

        subreddit = SubredditSchema(**valid_subreddit)
        assert subreddit.name == "test"
        assert subreddit.subscribers == 10000

    def test_collection_config_schema_valid(self):
        """Test valid collection configuration schema."""
        valid_config = {
            "subreddit_name": "python",
            "post_limit": 100,
            "sorting": "hot",
            "collect_comments": True,
            "comment_limit": 50,
            "comment_depth": 3,
            "priority": 5,
        }

        config = CollectionConfigSchema(**valid_config)
        assert config.subreddit_name == "python"
        assert config.post_limit == 100
        assert config.sorting.value == "hot"

    def test_collection_job_schema_valid(self):
        """Test valid collection job schema."""
        valid_job = {
            "job_type": "collect_subreddit_posts",
            "subreddit_name": "python",
            "status": "pending",
            "config": {"post_limit": 100, "sorting": "hot"},
            "priority": 5,
        }

        job = CollectionJobSchema(**valid_job)
        assert job.job_type == "collect_subreddit_posts"
        assert job.subreddit_name == "python"
        assert job.status.value == "pending"

    def test_collection_job_invalid_type(self):
        """Test collection job with invalid job type."""
        invalid_job = {"job_type": "invalid_job_type", "config": {}, "priority": 5}

        with pytest.raises(ValidationError):
            CollectionJobSchema(**invalid_job)

    def test_datetime_parsing(self):
        """Test datetime parsing in schemas."""
        # Test ISO format with Z
        post_data = {
            "id": "abc123",
            "title": "Test",
            "url": "https://reddit.com/test",
            "author": "user",
            "subreddit": "test",
            "score": 100,
            "upvote_ratio": 0.95,
            "num_comments": 0,
            "created_utc": "2023-01-01T12:00:00Z",
            "is_self": True,
            "is_nsfw": False,
            "is_locked": False,
        }

        post = RedditPostSchema(**post_data)
        assert isinstance(post.created_utc, datetime)

    def test_username_validation(self):
        """Test username validation rules."""
        # Valid usernames
        valid_usernames = ["user123", "test_user", "user-name", "[deleted]"]

        for username in valid_usernames:
            user_data = {
                "username": username,
                "created_utc": "2020-01-01T00:00:00Z",
                "comment_karma": 100,
                "link_karma": 50,
            }
            user = RedditUserSchema(**user_data)
            assert user.username == username

    def test_subreddit_name_normalization(self):
        """Test subreddit name normalization."""
        # Test with r/ prefix
        config_data = {"subreddit_name": "r/python", "post_limit": 50}

        config = CollectionConfigSchema(**config_data)
        assert config.subreddit_name == "python"  # Should remove r/ prefix
