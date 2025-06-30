"""Test Reddit client."""

import pytest
from unittest.mock import Mock, patch

from reddit_analyzer.services.reddit_client import RedditClient
from reddit_analyzer.config import get_config


class TestRedditClient:
    """Test RedditClient class."""

    @patch("app.services.reddit_client.praw.Reddit")
    def test_client_initialization(self, mock_reddit):
        """Test Reddit client initialization."""
        # Mock Reddit instance
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance

        # Mock user authentication
        mock_user = Mock()
        mock_reddit_instance.user.me.return_value = mock_user

        # Create client
        RedditClient()

        # Verify Reddit instance was created with correct parameters
        config = get_config()
        mock_reddit.assert_called_once_with(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
        )

        # Verify authentication was tested
        mock_reddit_instance.user.me.assert_called_once()

    @patch("app.services.reddit_client.praw.Reddit")
    def test_get_subreddit_info(self, mock_reddit):
        """Test getting subreddit information."""
        # Mock Reddit instance and subreddit
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        mock_reddit_instance.user.me.return_value = Mock()

        mock_subreddit = Mock()
        mock_subreddit.display_name = "Python"
        mock_subreddit.display_name_prefixed = "r/Python"
        mock_subreddit.description = "Python programming"
        mock_subreddit.subscribers = 1000000
        mock_subreddit.created_utc = 1234567890
        mock_subreddit.over18 = False

        mock_reddit_instance.subreddit.return_value = mock_subreddit

        # Create client and test
        client = RedditClient()
        info = client.get_subreddit_info("python")

        # Verify results
        assert info["name"] == "Python"
        assert info["display_name"] == "r/Python"
        assert info["description"] == "Python programming"
        assert info["subscribers"] == 1000000
        assert info["is_nsfw"] is False

        # Verify subreddit was requested correctly
        mock_reddit_instance.subreddit.assert_called_with("python")

    @patch("app.services.reddit_client.praw.Reddit")
    def test_get_subreddit_posts(self, mock_reddit):
        """Test getting subreddit posts."""
        # Mock Reddit instance and subreddit
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        mock_reddit_instance.user.me.return_value = Mock()

        # Mock post
        mock_post = Mock()
        mock_post.id = "abc123"
        mock_post.title = "Test Post"
        mock_post.selftext = "This is a test"
        mock_post.url = "https://example.com"
        mock_post.author.name = "testuser"
        mock_post.subreddit.display_name = "python"
        mock_post.score = 100
        mock_post.upvote_ratio = 0.95
        mock_post.num_comments = 10
        mock_post.created_utc = 1234567890
        mock_post.is_self = True
        mock_post.over_18 = False
        mock_post.locked = False

        # Mock subreddit
        mock_subreddit = Mock()
        mock_subreddit.hot.return_value = [mock_post]
        mock_reddit_instance.subreddit.return_value = mock_subreddit

        # Create client and test
        client = RedditClient()
        posts = client.get_subreddit_posts("python", sort="hot", limit=1)

        # Verify results
        assert len(posts) == 1
        post = posts[0]
        assert post["id"] == "abc123"
        assert post["title"] == "Test Post"
        assert post["author"] == "testuser"
        assert post["score"] == 100
        assert post["is_nsfw"] is False

        # Verify subreddit was requested correctly
        mock_reddit_instance.subreddit.assert_called_with("python")
        mock_subreddit.hot.assert_called_with(limit=1)

    @patch("app.services.reddit_client.praw.Reddit")
    def test_test_connection(self, mock_reddit):
        """Test connection test method."""
        # Mock Reddit instance
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        mock_reddit_instance.user.me.return_value = Mock()

        # Mock subreddit and hot posts
        mock_subreddit = Mock()
        mock_post = Mock()
        mock_subreddit.hot.return_value = iter([mock_post])
        mock_reddit_instance.subreddit.return_value = mock_subreddit

        # Create client and test
        client = RedditClient()
        result = client.test_connection()

        # Verify connection test passed
        assert result is True
        mock_reddit_instance.subreddit.assert_called_with("announcements")

    @patch("app.services.reddit_client.praw.Reddit")
    def test_authentication_failure(self, mock_reddit):
        """Test authentication failure handling."""
        # Mock Reddit instance that fails authentication
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        mock_reddit_instance.user.me.side_effect = Exception("Authentication failed")

        # Verify exception is raised
        with pytest.raises(Exception, match="Authentication failed"):
            RedditClient()
