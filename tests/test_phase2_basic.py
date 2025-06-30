"""Basic tests for Phase 2 components."""

from unittest.mock import Mock, patch
from reddit_analyzer.core.rate_limiter import RateLimitConfig
from reddit_analyzer.models.collection_job import (
    CollectionJob,
    APIRequest,
    DataQualityMetric,
)


class TestPhase2Basic:
    """Basic tests for Phase 2 functionality."""

    def test_rate_limit_config_creation(self):
        """Test rate limit configuration creation."""
        config = RateLimitConfig(
            requests_per_minute=60, burst_limit=10, backoff_factor=2.0, max_retries=3
        )

        assert config.requests_per_minute == 60
        assert config.burst_limit == 10
        assert config.backoff_factor == 2.0
        assert config.max_retries == 3

    def test_collection_job_model(self):
        """Test collection job model creation."""
        job = CollectionJob(
            job_type="collect_subreddit_posts",
            subreddit_name="python",
            status="pending",
            items_collected=0,
            config={"post_limit": 100},
        )

        assert job.job_type == "collect_subreddit_posts"
        assert job.subreddit_name == "python"
        assert job.status == "pending"
        assert job.items_collected == 0

    def test_api_request_model(self):
        """Test API request model creation."""
        api_request = APIRequest(
            endpoint="/r/python/hot",
            method="GET",
            status_code=200,
            response_time_ms=150,
        )

        assert api_request.endpoint == "/r/python/hot"
        assert api_request.method == "GET"
        assert api_request.status_code == 200
        assert api_request.response_time_ms == 150

    def test_data_quality_metric_model(self):
        """Test data quality metric model creation."""
        metric = DataQualityMetric(
            metric_name="post_quality_score", metric_value=0.85, subreddit_name="python"
        )

        assert metric.metric_name == "post_quality_score"
        assert metric.metric_value == 0.85
        assert metric.subreddit_name == "python"

    def test_collection_job_repr(self):
        """Test collection job string representation."""
        job = CollectionJob(id=1, job_type="collect_posts", status="completed")

        repr_str = repr(job)
        assert "CollectionJob" in repr_str
        assert "id=1" in repr_str
        assert "collect_posts" in repr_str
        assert "completed" in repr_str

    def test_api_request_repr(self):
        """Test API request string representation."""
        request = APIRequest(id=1, endpoint="/test", status_code=200)

        repr_str = repr(request)
        assert "APIRequest" in repr_str
        assert "id=1" in repr_str
        assert "/test" in repr_str
        assert "200" in repr_str

    @patch("app.config.get_config")
    def test_enhanced_client_import(self, mock_config):
        """Test that enhanced Reddit client can be imported."""
        # Mock the config to avoid Reddit API calls
        mock_config_obj = Mock()
        mock_config_obj.validate.return_value = None
        mock_config_obj.REDDIT_CLIENT_ID = "test"
        mock_config_obj.REDDIT_CLIENT_SECRET = "test"
        mock_config_obj.REDDIT_USER_AGENT = "test"
        mock_config_obj.REDDIT_USERNAME = "test"
        mock_config_obj.REDDIT_PASSWORD = "test"
        mock_config.return_value = mock_config_obj

        with patch("praw.Reddit") as mock_reddit:
            mock_reddit_instance = Mock()
            mock_reddit_instance.user.me.return_value = Mock()
            mock_reddit.return_value = mock_reddit_instance

            with patch("app.core.cache.get_cache") as mock_cache:
                mock_cache.return_value = Mock()

                from reddit_analyzer.services.enhanced_reddit_client import (
                    EnhancedRedditClient,
                )

                rate_config = RateLimitConfig()
                client = EnhancedRedditClient(rate_config)

                assert client is not None
                assert hasattr(client, "reddit")
                assert hasattr(client, "rate_limiter")
                assert hasattr(client, "request_queue")
                assert hasattr(client, "cache")

    def test_celery_app_import(self):
        """Test that Celery app can be imported."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost:6379/0"

            from reddit_analyzer.workers.celery_app import celery_app

            assert celery_app is not None
            assert celery_app.main == "reddit_analyzer"

    def test_data_validator_import(self):
        """Test that data validator can be imported."""
        from reddit_analyzer.validators.data_validator import DataValidator

        validator = DataValidator()
        assert validator is not None
        assert hasattr(validator, "validation_rules")
        assert hasattr(validator, "quality_thresholds")

    def test_cache_config_import(self):
        """Test that cache configuration can be imported."""
        from reddit_analyzer.core.cache import CacheConfig

        config = CacheConfig(
            default_ttl=3600, max_key_length=250, compress_threshold=1024
        )

        assert config.default_ttl == 3600
        assert config.max_key_length == 250
        assert config.compress_threshold == 1024

    def test_request_queue_import(self):
        """Test that request queue can be imported."""
        from reddit_analyzer.core.request_queue import (
            RequestQueue,
            RequestPriority,
            RequestStatus,
        )

        queue = RequestQueue(max_concurrent=3)
        assert queue is not None
        assert queue.max_concurrent == 3
        assert hasattr(queue, "queues")

        # Test enums
        assert RequestPriority.HIGH.value > RequestPriority.LOW.value
        assert RequestStatus.PENDING.value == "pending"
        assert RequestStatus.COMPLETED.value == "completed"

    def test_workers_task_import(self):
        """Test that worker tasks can be imported."""
        from reddit_analyzer.workers.tasks import collect_subreddit_posts

        assert collect_subreddit_posts is not None
        assert hasattr(collect_subreddit_posts, "delay")  # Celery task method
