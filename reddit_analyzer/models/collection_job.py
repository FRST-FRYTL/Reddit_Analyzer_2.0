from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.sql import func
from reddit_analyzer.database import Base


class CollectionJob(Base):
    __tablename__ = "collection_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False, index=True)
    subreddit_name = Column(String(255), index=True)
    status = Column(String(20), default="pending", index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    items_collected = Column(Integer, default=0)
    items_stored = Column(Integer, default=0)
    error_message = Column(Text)
    config = Column(JSON)
    task_id = Column(String(255), unique=True, index=True)
    worker_name = Column(String(100))
    retry_count = Column(Integer, default=0)
    priority = Column(Integer, default=5)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<CollectionJob(id={self.id}, type={self.job_type}, status={self.status})>"
        )


class APIRequest(Base):
    __tablename__ = "api_requests"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, index=True)
    response_time_ms = Column(Integer)
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    error_message = Column(Text)
    user_agent = Column(String(255))
    rate_limited = Column(Boolean, default=False)
    cached_response = Column(Boolean, default=False)
    worker_name = Column(String(100))
    task_id = Column(String(255), index=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<APIRequest(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"


class DataQualityMetric(Base):
    __tablename__ = "data_quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), default="gauge")  # gauge, counter, histogram
    subreddit_name = Column(String(255), index=True)
    collection_job_id = Column(Integer, index=True)
    tags = Column(JSON)  # Additional metadata tags
    description = Column(Text)
    threshold_warning = Column(Float)
    threshold_critical = Column(Float)
    calculated_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return (
            f"<DataQualityMetric(name={self.metric_name}, value={self.metric_value})>"
        )


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), default="gauge")
    component = Column(String(100), index=True)  # reddit_client, cache, database, etc.
    worker_name = Column(String(100), index=True)
    tags = Column(JSON)
    created_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<SystemMetric(name={self.metric_name}, component={self.component})>"


class CollectionSummary(Base):
    __tablename__ = "collection_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    subreddit_name = Column(String(255), index=True)
    total_posts_collected = Column(Integer, default=0)
    total_comments_collected = Column(Integer, default=0)
    total_users_collected = Column(Integer, default=0)
    successful_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    average_response_time_ms = Column(Float)
    total_api_requests = Column(Integer, default=0)
    rate_limited_requests = Column(Integer, default=0)
    cached_requests = Column(Integer, default=0)
    data_quality_score = Column(Float)
    collection_efficiency = Column(Float)  # ratio of successful to total attempts
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<CollectionSummary(date={self.date}, subreddit={self.subreddit_name})>"
