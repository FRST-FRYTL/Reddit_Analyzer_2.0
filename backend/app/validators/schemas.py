"""Pydantic schemas for data validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class SortMethod(str, Enum):
    hot = "hot"
    new = "new"
    top = "top"
    rising = "rising"


class TimeFilter(str, Enum):
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"
    all = "all"


class CollectionJobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    retrying = "retrying"


class RedditPostSchema(BaseModel):
    """Schema for validating Reddit post data."""

    id: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=300)
    selftext: Optional[str] = Field(None, max_length=10000)
    url: str = Field(..., max_length=2000)
    author: str = Field(..., min_length=1, max_length=50)
    subreddit: str = Field(..., min_length=1, max_length=50)
    score: int = Field(..., ge=-1000000)
    upvote_ratio: float = Field(..., ge=0.0, le=1.0)
    num_comments: int = Field(..., ge=0)
    created_utc: Union[datetime, str]
    is_self: bool
    is_nsfw: bool = False
    is_locked: bool = False
    distinguished: Optional[str] = None
    stickied: bool = False
    link_flair_text: Optional[str] = Field(None, max_length=100)
    post_hint: Optional[str] = None

    @validator("created_utc")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.fromisoformat(v)
        return v

    @validator("author")
    def validate_author(cls, v):
        if v.lower() in ["[deleted]", "[removed]", "automoderator"]:
            return v
        # Basic username validation
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid username format")
        return v

    @validator("subreddit")
    def validate_subreddit(cls, v):
        # Remove r/ prefix if present
        if v.startswith("r/"):
            v = v[2:]
        if not v.replace("_", "").isalnum():
            raise ValueError("Invalid subreddit name format")
        return v

    @validator("url")
    def validate_url(cls, v):
        if not (
            v.startswith("http://") or v.startswith("https://") or v.startswith("/r/")
        ):
            raise ValueError("Invalid URL format")
        return v

    class Config:
        schema_extra = {
            "example": {
                "id": "abc123",
                "title": "Example Reddit Post",
                "selftext": "This is the post content",
                "url": "https://reddit.com/r/example/comments/abc123/",
                "author": "example_user",
                "subreddit": "example",
                "score": 100,
                "upvote_ratio": 0.95,
                "num_comments": 25,
                "created_utc": "2023-01-01T12:00:00Z",
                "is_self": True,
                "is_nsfw": False,
                "is_locked": False,
            }
        }


class RedditCommentSchema(BaseModel):
    """Schema for validating Reddit comment data."""

    id: str = Field(..., min_length=1, max_length=20)
    post_id: str = Field(..., min_length=1, max_length=20)
    parent_id: Optional[str] = Field(None, max_length=20)
    author: str = Field(..., min_length=1, max_length=50)
    body: str = Field(..., min_length=1, max_length=10000)
    score: int = Field(..., ge=-1000000)
    created_utc: Union[datetime, str]
    is_deleted: bool = False
    distinguished: Optional[str] = None
    stickied: bool = False
    depth: int = Field(0, ge=0, le=20)
    controversiality: int = Field(0, ge=0, le=1)

    @validator("created_utc")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.fromisoformat(v)
        return v

    @validator("author")
    def validate_author(cls, v):
        if v.lower() in ["[deleted]", "[removed]", "automoderator"]:
            return v
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid username format")
        return v

    @validator("body")
    def validate_body(cls, v):
        if v.lower() in ["[deleted]", "[removed]"]:
            return v
        if len(v.strip()) == 0:
            raise ValueError("Comment body cannot be empty")
        return v

    class Config:
        schema_extra = {
            "example": {
                "id": "def456",
                "post_id": "abc123",
                "parent_id": "abc123",
                "author": "commenter_user",
                "body": "This is a comment",
                "score": 5,
                "created_utc": "2023-01-01T12:30:00Z",
                "is_deleted": False,
                "depth": 0,
            }
        }


class RedditUserSchema(BaseModel):
    """Schema for validating Reddit user data."""

    username: str = Field(..., min_length=1, max_length=50)
    created_utc: Union[datetime, str]
    comment_karma: int = Field(..., ge=0)
    link_karma: int = Field(..., ge=0)
    total_karma: Optional[int] = None
    is_verified: bool = False
    has_verified_email: Optional[bool] = None
    is_gold: bool = False
    is_mod: bool = False

    @validator("created_utc")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.fromisoformat(v)
        return v

    @validator("username")
    def validate_username(cls, v):
        if v.lower() in ["[deleted]", "[removed]"]:
            return v
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid username format")
        return v

    @root_validator
    def calculate_total_karma(cls, values):
        comment_karma = values.get("comment_karma", 0)
        link_karma = values.get("link_karma", 0)
        values["total_karma"] = comment_karma + link_karma
        return values

    class Config:
        schema_extra = {
            "example": {
                "username": "example_user",
                "created_utc": "2020-01-01T00:00:00Z",
                "comment_karma": 1500,
                "link_karma": 300,
                "is_verified": False,
                "is_gold": False,
            }
        }


class SubredditSchema(BaseModel):
    """Schema for validating subreddit data."""

    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    public_description: Optional[str] = Field(None, max_length=500)
    subscribers: Optional[int] = Field(None, ge=0)
    created_utc: Union[datetime, str]
    is_nsfw: bool = False
    lang: Optional[str] = Field(None, max_length=10)
    submission_type: Optional[str] = Field(None, max_length=20)

    @validator("created_utc")
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.fromisoformat(v)
        return v

    @validator("name", "display_name")
    def validate_subreddit_name(cls, v):
        # Remove r/ prefix if present
        if v.startswith("r/"):
            v = v[2:]
        if not v.replace("_", "").isalnum():
            raise ValueError("Invalid subreddit name format")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "example",
                "display_name": "r/example",
                "description": "An example subreddit",
                "subscribers": 10000,
                "created_utc": "2019-01-01T00:00:00Z",
                "is_nsfw": False,
                "lang": "en",
            }
        }


class CollectionConfigSchema(BaseModel):
    """Schema for collection job configuration."""

    subreddit_name: str = Field(..., min_length=1, max_length=50)
    post_limit: int = Field(100, ge=1, le=1000)
    sorting: SortMethod = SortMethod.hot
    time_filter: TimeFilter = TimeFilter.all
    collect_comments: bool = True
    comment_limit: int = Field(100, ge=1, le=500)
    comment_depth: int = Field(3, ge=1, le=10)
    comment_sort: str = Field("best", regex="^(best|top|new|controversial|old)$")
    priority: int = Field(5, ge=1, le=10)
    use_cache: bool = True
    cache_ttl: int = Field(900, ge=300, le=3600)  # 5 minutes to 1 hour

    @validator("subreddit_name")
    def validate_subreddit_name(cls, v):
        if v.startswith("r/"):
            v = v[2:]
        if not v.replace("_", "").isalnum():
            raise ValueError("Invalid subreddit name format")
        return v

    class Config:
        schema_extra = {
            "example": {
                "subreddit_name": "python",
                "post_limit": 100,
                "sorting": "hot",
                "collect_comments": True,
                "comment_limit": 50,
                "comment_depth": 3,
                "priority": 5,
            }
        }


class CollectionJobSchema(BaseModel):
    """Schema for collection job data."""

    job_type: str = Field(..., min_length=1, max_length=50)
    subreddit_name: Optional[str] = Field(None, max_length=50)
    status: CollectionJobStatus = CollectionJobStatus.pending
    config: Dict[str, Any]
    priority: int = Field(5, ge=1, le=10)
    task_id: Optional[str] = None
    worker_name: Optional[str] = None
    retry_count: int = Field(0, ge=0, le=10)

    @validator("job_type")
    def validate_job_type(cls, v):
        valid_types = [
            "collect_subreddit_posts",
            "collect_post_comments",
            "collect_user_data",
            "validate_data",
            "health_check",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid job type. Must be one of: {valid_types}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "job_type": "collect_subreddit_posts",
                "subreddit_name": "python",
                "status": "pending",
                "config": {"post_limit": 100, "sorting": "hot"},
                "priority": 5,
            }
        }


class DataValidationResult(BaseModel):
    """Schema for data validation results."""

    item_id: str
    item_type: str
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    quality_score: float = Field(..., ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "item_id": "abc123",
                "item_type": "post",
                "is_valid": True,
                "errors": [],
                "warnings": ["Low comment count"],
                "quality_score": 0.85,
            }
        }


class BulkCollectionRequest(BaseModel):
    """Schema for bulk collection requests."""

    subreddits: List[str] = Field(..., min_items=1, max_items=10)
    posts_per_subreddit: int = Field(100, ge=1, le=1000)
    collect_comments: bool = True
    max_comments_per_post: int = Field(50, ge=1, le=200)
    priority: int = Field(5, ge=1, le=10)

    @validator("subreddits")
    def validate_subreddits(cls, v):
        validated = []
        for subreddit in v:
            if subreddit.startswith("r/"):
                subreddit = subreddit[2:]
            if not subreddit.replace("_", "").isalnum():
                raise ValueError(f"Invalid subreddit name: {subreddit}")
            validated.append(subreddit)
        return validated

    class Config:
        schema_extra = {
            "example": {
                "subreddits": ["python", "datascience", "MachineLearning"],
                "posts_per_subreddit": 100,
                "collect_comments": True,
                "max_comments_per_post": 50,
                "priority": 5,
            }
        }
