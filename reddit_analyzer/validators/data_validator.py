"""Data validation utilities and quality checks."""

from typing import Dict, List, Any, Tuple
from datetime import datetime
import re
from pydantic import ValidationError
import structlog

from reddit_analyzer.validators.schemas import (
    RedditPostSchema,
    RedditCommentSchema,
    RedditUserSchema,
    DataValidationResult,
)

logger = structlog.get_logger(__name__)


class DataValidator:
    """Comprehensive data validator for Reddit content."""

    def __init__(self):
        self.validation_rules = {
            "post": self._validate_post_content,
            "comment": self._validate_comment_content,
            "user": self._validate_user_content,
            "subreddit": self._validate_subreddit_content,
        }

        # Quality thresholds
        self.quality_thresholds = {
            "min_title_length": 5,
            "max_title_length": 300,
            "min_comment_length": 3,
            "max_comment_length": 10000,
            "min_post_score": -1000,
            "max_post_age_days": 365,
            "min_karma_threshold": -1000,
            "suspicious_username_patterns": [
                r"^[a-zA-Z]+\d{4,}$",  # Username followed by many digits
                r".*bot.*",  # Contains 'bot'
                r".*test.*",  # Contains 'test'
            ],
        }

    def validate_post(self, post_data: Dict[str, Any]) -> DataValidationResult:
        """Validate a Reddit post."""
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            # Schema validation
            validated_post = RedditPostSchema(**post_data)
            post_dict = validated_post.dict()

            # Content validation
            content_errors, content_warnings, content_score = (
                self._validate_post_content(post_dict)
            )
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            quality_score *= content_score

        except ValidationError as e:
            errors = [
                f"Schema validation failed: {error['msg']}" for error in e.errors()
            ]
            quality_score = 0.0

        return DataValidationResult(
            item_id=post_data.get("id", "unknown"),
            item_type="post",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0.0, quality_score),
        )

    def validate_comment(self, comment_data: Dict[str, Any]) -> DataValidationResult:
        """Validate a Reddit comment."""
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            # Schema validation
            validated_comment = RedditCommentSchema(**comment_data)
            comment_dict = validated_comment.dict()

            # Content validation
            content_errors, content_warnings, content_score = (
                self._validate_comment_content(comment_dict)
            )
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            quality_score *= content_score

        except ValidationError as e:
            errors = [
                f"Schema validation failed: {error['msg']}" for error in e.errors()
            ]
            quality_score = 0.0

        return DataValidationResult(
            item_id=comment_data.get("id", "unknown"),
            item_type="comment",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0.0, quality_score),
        )

    def validate_user(self, user_data: Dict[str, Any]) -> DataValidationResult:
        """Validate Reddit user data."""
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            # Schema validation
            validated_user = RedditUserSchema(**user_data)
            user_dict = validated_user.dict()

            # Content validation
            content_errors, content_warnings, content_score = (
                self._validate_user_content(user_dict)
            )
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            quality_score *= content_score

        except ValidationError as e:
            errors = [
                f"Schema validation failed: {error['msg']}" for error in e.errors()
            ]
            quality_score = 0.0

        return DataValidationResult(
            item_id=user_data.get("username", "unknown"),
            item_type="user",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0.0, quality_score),
        )

    def validate_batch(self, data_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of mixed data items."""
        results = {
            "total_items": len(data_batch),
            "valid_items": 0,
            "invalid_items": 0,
            "items_by_type": {},
            "quality_scores": [],
            "validation_results": [],
            "summary": {},
        }

        for item in data_batch:
            item_type = item.get("type", self._infer_item_type(item))

            if item_type in self.validation_rules:
                if item_type == "post":
                    validation_result = self.validate_post(item)
                elif item_type == "comment":
                    validation_result = self.validate_comment(item)
                elif item_type == "user":
                    validation_result = self.validate_user(item)
                else:
                    # Generic validation
                    validation_result = DataValidationResult(
                        item_id=item.get("id", "unknown"),
                        item_type=item_type,
                        is_valid=True,
                        quality_score=0.5,
                    )

                results["validation_results"].append(validation_result)
                results["quality_scores"].append(validation_result.quality_score)

                if validation_result.is_valid:
                    results["valid_items"] += 1
                else:
                    results["invalid_items"] += 1

                # Track by type
                if item_type not in results["items_by_type"]:
                    results["items_by_type"][item_type] = {"valid": 0, "invalid": 0}

                if validation_result.is_valid:
                    results["items_by_type"][item_type]["valid"] += 1
                else:
                    results["items_by_type"][item_type]["invalid"] += 1

        # Calculate summary statistics
        if results["quality_scores"]:
            results["summary"] = {
                "average_quality_score": sum(results["quality_scores"])
                / len(results["quality_scores"]),
                "min_quality_score": min(results["quality_scores"]),
                "max_quality_score": max(results["quality_scores"]),
                "validation_success_rate": (
                    results["valid_items"] / results["total_items"]
                    if results["total_items"] > 0
                    else 0
                ),
            }

        return results

    def _validate_post_content(
        self, post: Dict[str, Any]
    ) -> Tuple[List[str], List[str], float]:
        """Validate post content quality."""
        errors = []
        warnings = []
        quality_score = 1.0

        # Title validation
        title = post.get("title", "")
        if len(title) < self.quality_thresholds["min_title_length"]:
            warnings.append("Title is very short")
            quality_score *= 0.8
        elif len(title) > self.quality_thresholds["max_title_length"]:
            warnings.append("Title is very long")
            quality_score *= 0.9

        # Check for spam patterns in title
        if self._contains_spam_patterns(title):
            warnings.append("Title contains potential spam patterns")
            quality_score *= 0.7

        # Score validation
        score = post.get("score", 0)
        if score < self.quality_thresholds["min_post_score"]:
            warnings.append("Post has very low score")
            quality_score *= 0.6

        # Age validation
        created_utc = post.get("created_utc")
        if created_utc:
            if isinstance(created_utc, str):
                try:
                    created_utc = datetime.fromisoformat(
                        created_utc.replace("Z", "+00:00")
                    )
                except ValueError:
                    created_utc = None

            if created_utc:
                post_age = datetime.now() - created_utc.replace(tzinfo=None)
                if post_age.days > self.quality_thresholds["max_post_age_days"]:
                    warnings.append("Post is very old")
                    quality_score *= 0.9

        # Author validation
        author = post.get("author", "")
        if author.lower() in ["[deleted]", "[removed]"]:
            warnings.append("Post author is deleted/removed")
            quality_score *= 0.8
        elif self._is_suspicious_username(author):
            warnings.append("Author has suspicious username pattern")
            quality_score *= 0.7

        # Content validation
        selftext = post.get("selftext", "")
        if selftext and len(selftext) > 0:
            if self._contains_spam_patterns(selftext):
                warnings.append("Post content contains potential spam patterns")
                quality_score *= 0.6

        # URL validation
        url = post.get("url", "")
        if url:
            if self._is_suspicious_url(url):
                warnings.append("Post contains suspicious URL")
                quality_score *= 0.7

        return errors, warnings, quality_score

    def _validate_comment_content(
        self, comment: Dict[str, Any]
    ) -> Tuple[List[str], List[str], float]:
        """Validate comment content quality."""
        errors = []
        warnings = []
        quality_score = 1.0

        # Body validation
        body = comment.get("body", "")
        if body.lower() in ["[deleted]", "[removed]"]:
            warnings.append("Comment is deleted/removed")
            quality_score *= 0.5
            return errors, warnings, quality_score

        if len(body) < self.quality_thresholds["min_comment_length"]:
            warnings.append("Comment is very short")
            quality_score *= 0.8
        elif len(body) > self.quality_thresholds["max_comment_length"]:
            warnings.append("Comment is very long")
            quality_score *= 0.9

        # Spam detection
        if self._contains_spam_patterns(body):
            warnings.append("Comment contains potential spam patterns")
            quality_score *= 0.6

        # Author validation
        author = comment.get("author", "")
        if author.lower() in ["[deleted]", "[removed]"]:
            warnings.append("Comment author is deleted/removed")
            quality_score *= 0.8
        elif self._is_suspicious_username(author):
            warnings.append("Author has suspicious username pattern")
            quality_score *= 0.7

        # Score validation
        score = comment.get("score", 0)
        if score < -10:
            warnings.append("Comment has very low score")
            quality_score *= 0.7

        return errors, warnings, quality_score

    def _validate_user_content(
        self, user: Dict[str, Any]
    ) -> Tuple[List[str], List[str], float]:
        """Validate user data quality."""
        errors = []
        warnings = []
        quality_score = 1.0

        username = user.get("username", "")
        if username.lower() in ["[deleted]", "[removed]"]:
            warnings.append("User is deleted/removed")
            quality_score *= 0.5
            return errors, warnings, quality_score

        # Username pattern validation
        if self._is_suspicious_username(username):
            warnings.append("Username has suspicious pattern")
            quality_score *= 0.7

        # Karma validation
        comment_karma = user.get("comment_karma", 0)
        link_karma = user.get("link_karma", 0)
        total_karma = comment_karma + link_karma

        if total_karma < self.quality_thresholds["min_karma_threshold"]:
            warnings.append("User has very low karma")
            quality_score *= 0.6

        # Account age validation
        created_utc = user.get("created_utc")
        if created_utc:
            if isinstance(created_utc, str):
                try:
                    created_utc = datetime.fromisoformat(
                        created_utc.replace("Z", "+00:00")
                    )
                except ValueError:
                    created_utc = None

            if created_utc:
                account_age = datetime.now() - created_utc.replace(tzinfo=None)
                if account_age.days < 30:
                    warnings.append("Account is very new")
                    quality_score *= 0.8

        return errors, warnings, quality_score

    def _validate_subreddit_content(
        self, subreddit: Dict[str, Any]
    ) -> Tuple[List[str], List[str], float]:
        """Validate subreddit data quality."""
        errors = []
        warnings = []
        quality_score = 1.0

        # Subscriber count validation
        subscribers = subreddit.get("subscribers", 0)
        if subscribers is not None and subscribers < 1000:
            warnings.append("Subreddit has very few subscribers")
            quality_score *= 0.8

        return errors, warnings, quality_score

    def _infer_item_type(self, item: Dict[str, Any]) -> str:
        """Infer the type of data item."""
        if "title" in item and "subreddit" in item:
            return "post"
        elif "body" in item and "post_id" in item:
            return "comment"
        elif "username" in item and "comment_karma" in item:
            return "user"
        elif "subscribers" in item and "display_name" in item:
            return "subreddit"
        else:
            return "unknown"

    def _contains_spam_patterns(self, text: str) -> bool:
        """Check if text contains spam patterns."""
        spam_patterns = [
            r"(?i)click here",
            r"(?i)free money",
            r"(?i)make \$\d+",
            r"(?i)work from home",
            r"(?i)buy now",
            r"(?i)limited time",
            r"http[s]?://bit\.ly",
            r"http[s]?://tinyurl",
            r"(?i)subscribe to my",
            r"(?i)check out my",
        ]

        for pattern in spam_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _is_suspicious_username(self, username: str) -> bool:
        """Check if username matches suspicious patterns."""
        for pattern in self.quality_thresholds["suspicious_username_patterns"]:
            if re.match(pattern, username, re.IGNORECASE):
                return True
        return False

    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is suspicious."""
        suspicious_domains = ["bit.ly", "tinyurl.com", "goo.gl", "t.co"]

        for domain in suspicious_domains:
            if domain in url.lower():
                return True
        return False

    def get_validation_stats(
        self, validation_results: List[DataValidationResult]
    ) -> Dict[str, Any]:
        """Calculate validation statistics."""
        if not validation_results:
            return {}

        total_items = len(validation_results)
        valid_items = sum(1 for r in validation_results if r.is_valid)
        invalid_items = total_items - valid_items

        quality_scores = [r.quality_score for r in validation_results]

        return {
            "total_items": total_items,
            "valid_items": valid_items,
            "invalid_items": invalid_items,
            "validation_rate": valid_items / total_items,
            "average_quality_score": sum(quality_scores) / len(quality_scores),
            "min_quality_score": min(quality_scores),
            "max_quality_score": max(quality_scores),
            "quality_distribution": {
                "excellent": sum(1 for s in quality_scores if s >= 0.9),
                "good": sum(1 for s in quality_scores if 0.7 <= s < 0.9),
                "fair": sum(1 for s in quality_scores if 0.5 <= s < 0.7),
                "poor": sum(1 for s in quality_scores if s < 0.5),
            },
        }
