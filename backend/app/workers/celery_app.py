"""Celery application configuration for Reddit Analyzer."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "reddit_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.workers.tasks.collect_subreddit_posts": {"queue": "data_collection"},
        "app.workers.tasks.collect_post_comments": {"queue": "data_collection"},
        "app.workers.tasks.collect_user_data": {"queue": "data_collection"},
        "app.workers.tasks.validate_collected_data": {"queue": "validation"},
        "app.workers.tasks.health_check": {"queue": "monitoring"},
    },
    # Task configuration
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Rate limiting
    task_annotations={
        "app.workers.tasks.collect_subreddit_posts": {"rate_limit": "30/m"},
        "app.workers.tasks.collect_post_comments": {"rate_limit": "60/m"},
        "app.workers.tasks.collect_user_data": {"rate_limit": "20/m"},
    },
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "health-check": {
            "task": "app.workers.tasks.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-old-results": {
            "task": "app.workers.tasks.cleanup_old_results",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# Optional: Configure Celery with Redis Sentinel for high availability
if hasattr(settings, "redis_sentinel_hosts") and settings.redis_sentinel_hosts:
    celery_app.conf.broker_transport_options = {
        "sentinels": settings.redis_sentinel_hosts,
        "service_name": "mymaster",
        "socket_keepalive": True,
        "socket_keepalive_options": {
            "TCP_KEEPIDLE": 1,
            "TCP_KEEPINTVL": 3,
            "TCP_KEEPCNT": 5,
        },
    }
