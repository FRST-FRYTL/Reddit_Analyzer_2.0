"""Tests for enhanced Reddit client functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.enhanced_reddit_client import EnhancedRedditClient
from app.core.rate_limiter import RateLimitConfig


class TestEnhancedRedditClient:
    """Test enhanced Reddit client functionality."""

    @pytest.fixture
    def mock_reddit(self):
        """Create a mock PRAW Reddit instance."""
        with patch("app.services.enhanced_reddit_client.praw.Reddit") as mock_reddit:
            mock_instance = Mock()
            mock_reddit.return_value = mock_instance

            # Mock authentication
            mock_instance.user.me.return_value = Mock()

            yield mock_instance

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        with patch("app.services.enhanced_reddit_client.get_config") as mock_config:
            config = Mock()
            config.REDDIT_CLIENT_ID = "test_id"
            config.REDDIT_CLIENT_SECRET = "test_secret"
            config.REDDIT_USER_AGENT = "test_agent"
            config.REDDIT_USERNAME = "test_user"
            config.REDDIT_PASSWORD = "test_pass"
            config.validate.return_value = None

            mock_config.return_value = config
            yield config

    @pytest.fixture
    def mock_cache(self):
        """Mock cache."""
        with patch("app.services.enhanced_reddit_client.get_cache") as mock_cache:
            cache = Mock()
            cache.get = AsyncMock(return_value=None)
            cache.set = AsyncMock(return_value=True)
            cache.health_check = AsyncMock(return_value={"status": "healthy"})
            cache.get_stats.return_value = {"keyspace_hits": 100}
            cache.close.return_value = None

            mock_cache.return_value = cache
            yield cache

    @pytest.fixture
    async def reddit_client(self, mock_reddit, mock_config, mock_cache):
        """Create enhanced Reddit client for testing."""
        rate_config = RateLimitConfig(requests_per_minute=10, burst_limit=3)
        client = EnhancedRedditClient(rate_config)
        yield client

    @pytest.mark.asyncio
    async def test_client_initialization(self, reddit_client, mock_reddit):
        """Test enhanced client initialization with dependencies."""
        assert reddit_client.reddit is not None
        assert reddit_client.rate_limiter is not None
        assert reddit_client.request_queue is not None
        assert reddit_client.cache is not None

    @pytest.mark.asyncio
    async def test_start_stop_client(self, reddit_client):
        """Test client start and stop functionality."""
        await reddit_client.start()
        assert reddit_client.request_queue.get_status()["running"] is True

        await reddit_client.stop()
        assert reddit_client.request_queue.get_status()["running"] is False

    @pytest.mark.asyncio
    async def test_get_subreddit_info_cached(self, reddit_client, mock_cache):
        """Test cached subreddit info retrieval."""
        # Mock cached response
        cached_data = {
            "name": "test",
            "display_name": "r/test",
            "subscribers": 1000,
            "created_utc": "2023-01-01T00:00:00",
            "is_nsfw": False,
        }
        mock_cache.get.return_value = cached_data

        result = await reddit_client.get_subreddit_info("test", use_cache=True)

        assert result == cached_data
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subreddit_info_uncached(
        self, reddit_client, mock_reddit, mock_cache
    ):
        """Test uncached subreddit info retrieval."""
        # Mock Reddit API response
        mock_subreddit = Mock()
        mock_subreddit.display_name = "test"
        mock_subreddit.display_name_prefixed = "r/test"
        mock_subreddit.description = "Test subreddit"
        mock_subreddit.public_description = "Test description"
        mock_subreddit.subscribers = 1000
        mock_subreddit.created_utc = 1640995200  # 2022-01-01
        mock_subreddit.over18 = False
        mock_subreddit.lang = "en"
        mock_subreddit.submission_type = "any"

        mock_reddit.subreddit.return_value = mock_subreddit
        mock_cache.get.return_value = None  # No cache hit

        result = await reddit_client.get_subreddit_info("test", use_cache=False)

        assert result["name"] == "test"
        assert result["subscribers"] == 1000
        assert result["is_nsfw"] is False

    @pytest.mark.asyncio
    async def test_get_subreddit_posts(self, reddit_client, mock_reddit, mock_cache):
        """Test subreddit posts retrieval."""
        # Mock posts
        mock_post = Mock()
        mock_post.id = "abc123"
        mock_post.title = "Test Post"
        mock_post.selftext = "Test content"
        mock_post.url = "https://reddit.com/test"
        mock_post.author.name = "test_user"
        mock_post.subreddit.display_name = "test"
        mock_post.score = 100
        mock_post.upvote_ratio = 0.95
        mock_post.num_comments = 10
        mock_post.created_utc = 1640995200
        mock_post.is_self = True
        mock_post.over_18 = False
        mock_post.locked = False
        mock_post.distinguished = None
        mock_post.stickied = False
        mock_post.link_flair_text = None

        mock_subreddit = Mock()
        mock_subreddit.hot.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_cache.get.return_value = None

        result = await reddit_client.get_subreddit_posts(
            "test", sort="hot", limit=10, use_cache=False
        )

        assert len(result) == 1
        assert result[0]["id"] == "abc123"
        assert result[0]["title"] == "Test Post"

    @pytest.mark.asyncio
    async def test_get_post_comments(self, reddit_client, mock_reddit, mock_cache):
        """Test post comments retrieval."""
        # Mock comment
        mock_comment = Mock()
        mock_comment.id = "comment123"
        mock_comment.parent_id = "abc123"
        mock_comment.author.name = "commenter"
        mock_comment.body = "Test comment"
        mock_comment.score = 5
        mock_comment.created_utc = 1640995300
        mock_comment.distinguished = None
        mock_comment.stickied = False
        mock_comment.depth = 0
        mock_comment.controversiality = 0

        mock_submission = Mock()
        mock_submission.comment_sort = "best"
        mock_submission.comments.replace_more.return_value = None
        mock_submission.comments.list.return_value = [mock_comment]

        mock_reddit.submission.return_value = mock_submission
        mock_cache.get.return_value = None

        result = await reddit_client.get_post_comments("abc123", use_cache=False)

        assert len(result) == 1
        assert result[0]["id"] == "comment123"
        assert result[0]["body"] == "Test comment"

    @pytest.mark.asyncio
    async def test_get_user_info(self, reddit_client, mock_reddit, mock_cache):
        """Test user info retrieval."""
        # Mock user
        mock_user = Mock()
        mock_user.name = "test_user"
        mock_user.created_utc = 1640995200
        mock_user.comment_karma = 1000
        mock_user.link_karma = 500
        mock_user.verified = False
        mock_user.has_verified_email = True
        mock_user.is_gold = False
        mock_user.is_mod = False

        mock_reddit.redditor.return_value = mock_user
        mock_cache.get.return_value = None

        result = await reddit_client.get_user_info("test_user", use_cache=False)

        assert result["username"] == "test_user"
        assert result["comment_karma"] == 1000
        assert result["link_karma"] == 500
        assert result["total_karma"] == 1500

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, reddit_client):
        """Test circuit breaker behavior on failures."""
        # Test that circuit breaker starts closed
        assert reddit_client.circuit_breaker["state"] == "closed"

        # Simulate failures to trigger circuit breaker
        reddit_client.circuit_breaker["failure_count"] = 5
        reddit_client.circuit_breaker["state"] = "open"

        # Test that circuit breaker prevents requests when open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            async with reddit_client.circuit_breaker_context():
                pass

    @pytest.mark.asyncio
    async def test_bulk_collection(self, reddit_client, mock_reddit, mock_cache):
        """Test bulk data collection from multiple subreddits."""
        # Mock subreddit and posts for bulk collection
        mock_subreddit = Mock()
        mock_subreddit.display_name = "test"
        mock_subreddit.description = "Test subreddit"
        mock_subreddit.subscribers = 1000
        mock_subreddit.created_utc = 1640995200
        mock_subreddit.over18 = False
        mock_subreddit.lang = "en"
        mock_subreddit.submission_type = "any"

        mock_post = Mock()
        mock_post.id = "abc123"
        mock_post.title = "Test Post"
        mock_post.selftext = "Test content"
        mock_post.url = "https://reddit.com/test"
        mock_post.author.name = "test_user"
        mock_post.subreddit.display_name = "test"
        mock_post.score = 100
        mock_post.upvote_ratio = 0.95
        mock_post.num_comments = 10
        mock_post.created_utc = 1640995200
        mock_post.is_self = True
        mock_post.over_18 = False
        mock_post.locked = False
        mock_post.distinguished = None
        mock_post.stickied = False
        mock_post.link_flair_text = None

        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_post]
        mock_cache.get.return_value = None

        result = await reddit_client.bulk_collect_subreddit_data(
            ["test"], posts_per_subreddit=1, collect_comments=False
        )

        assert "subreddits" in result
        assert "test" in result["subreddits"]
        assert result["total_posts"] == 1

    def test_get_client_stats(self, reddit_client):
        """Test client statistics retrieval."""
        stats = reddit_client.get_client_stats()

        required_keys = [
            "rate_limiter_status",
            "request_queue_status",
            "cache_stats",
            "circuit_breaker",
            "timestamp",
        ]

        for key in required_keys:
            assert key in stats

    @pytest.mark.asyncio
    async def test_health_check(self, reddit_client, mock_reddit, mock_cache):
        """Test comprehensive health check."""
        # Mock successful Reddit API call
        mock_subreddit = Mock()
        mock_subreddit.hot.return_value = [Mock()]
        mock_reddit.subreddit.return_value = mock_subreddit

        health_status = await reddit_client.health_check()

        assert "overall" in health_status
        assert "reddit_api" in health_status
        assert "cache" in health_status
        assert "rate_limiter" in health_status
        assert "request_queue" in health_status
