"""Tests for data validation functionality."""

import pytest
from app.validators.data_validator import DataValidator


class TestDataValidator:
    """Test data validation functionality."""

    @pytest.fixture
    def validator(self):
        """Create data validator instance."""
        return DataValidator()

    @pytest.fixture
    def valid_post_data(self):
        """Sample valid post data."""
        return {
            "id": "abc123",
            "title": "Test Post Title",
            "selftext": "This is test content for the post",
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

    @pytest.fixture
    def valid_comment_data(self):
        """Sample valid comment data."""
        return {
            "id": "comment123",
            "post_id": "abc123",
            "parent_id": "abc123",
            "author": "commenter",
            "body": "This is a test comment with sufficient length",
            "score": 5,
            "created_utc": "2023-01-01T12:30:00Z",
            "is_deleted": False,
            "depth": 0,
        }

    @pytest.fixture
    def valid_user_data(self):
        """Sample valid user data."""
        return {
            "username": "test_user",
            "created_utc": "2020-01-01T00:00:00Z",
            "comment_karma": 1500,
            "link_karma": 300,
            "is_verified": False,
            "is_gold": False,
        }

    def test_validate_valid_post(self, validator, valid_post_data):
        """Test validation of valid post data."""
        result = validator.validate_post(valid_post_data)

        assert result.is_valid is True
        assert result.item_type == "post"
        assert result.item_id == "abc123"
        assert len(result.errors) == 0
        assert result.quality_score > 0.5

    def test_validate_invalid_post_missing_fields(self, validator):
        """Test validation of post with missing required fields."""
        invalid_post = {
            "id": "abc123",
            # Missing title, author, etc.
        }

        result = validator.validate_post(invalid_post)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.quality_score == 0.0

    def test_validate_post_with_warnings(self, validator, valid_post_data):
        """Test post validation that generates warnings."""
        # Create post with very short title
        post_data = valid_post_data.copy()
        post_data["title"] = "Hi"  # Very short title

        result = validator.validate_post(post_data)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert result.quality_score < 1.0

    def test_validate_valid_comment(self, validator, valid_comment_data):
        """Test validation of valid comment data."""
        result = validator.validate_comment(valid_comment_data)

        assert result.is_valid is True
        assert result.item_type == "comment"
        assert result.item_id == "comment123"
        assert len(result.errors) == 0
        assert result.quality_score > 0.5

    def test_validate_invalid_comment(self, validator):
        """Test validation of invalid comment data."""
        invalid_comment = {
            "id": "comment123",
            "body": "",  # Empty body
            # Missing other required fields
        }

        result = validator.validate_comment(invalid_comment)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_deleted_comment(self, validator, valid_comment_data):
        """Test validation of deleted comment."""
        comment_data = valid_comment_data.copy()
        comment_data["body"] = "[deleted]"
        comment_data["author"] = "[deleted]"

        result = validator.validate_comment(comment_data)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert result.quality_score < 1.0

    def test_validate_valid_user(self, validator, valid_user_data):
        """Test validation of valid user data."""
        result = validator.validate_user(valid_user_data)

        assert result.is_valid is True
        assert result.item_type == "user"
        assert result.item_id == "test_user"
        assert len(result.errors) == 0

    def test_validate_user_with_suspicious_username(self, validator, valid_user_data):
        """Test validation of user with suspicious username pattern."""
        user_data = valid_user_data.copy()
        user_data["username"] = "user1234567890"  # Suspicious pattern

        result = validator.validate_user(user_data)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert result.quality_score < 1.0

    def test_validate_batch_mixed_data(
        self, validator, valid_post_data, valid_comment_data
    ):
        """Test batch validation of mixed data types."""
        data_batch = [
            valid_post_data,
            valid_comment_data,
            {"id": "invalid", "type": "post"},  # Invalid post
        ]

        result = validator.validate_batch(data_batch)

        assert result["total_items"] == 3
        assert result["valid_items"] >= 2
        assert result["invalid_items"] >= 0
        assert "items_by_type" in result
        assert "summary" in result

    def test_spam_pattern_detection(self, validator):
        """Test spam pattern detection."""
        spam_text = "Click here for free money! Make $1000 working from home!"

        assert validator._contains_spam_patterns(spam_text) is True

        normal_text = "This is a normal comment about technology"
        assert validator._contains_spam_patterns(normal_text) is False

    def test_suspicious_username_detection(self, validator):
        """Test suspicious username pattern detection."""
        suspicious_usernames = [
            "user123456789",  # Username with many digits
            "botname",  # Contains 'bot'
            "testuser",  # Contains 'test'
        ]

        for username in suspicious_usernames:
            assert validator._is_suspicious_username(username) is True

        normal_username = "regular_user"
        assert validator._is_suspicious_username(normal_username) is False

    def test_suspicious_url_detection(self, validator):
        """Test suspicious URL detection."""
        suspicious_urls = [
            "https://bit.ly/shortened",
            "http://tinyurl.com/something",
            "https://goo.gl/maps/location",
        ]

        for url in suspicious_urls:
            assert validator._is_suspicious_url(url) is True

        normal_url = "https://github.com/user/repo"
        assert validator._is_suspicious_url(normal_url) is False

    def test_item_type_inference(
        self, validator, valid_post_data, valid_comment_data, valid_user_data
    ):
        """Test automatic item type inference."""
        assert validator._infer_item_type(valid_post_data) == "post"
        assert validator._infer_item_type(valid_comment_data) == "comment"
        assert validator._infer_item_type(valid_user_data) == "user"

        unknown_item = {"unknown_field": "value"}
        assert validator._infer_item_type(unknown_item) == "unknown"

    def test_validation_statistics(
        self, validator, valid_post_data, valid_comment_data
    ):
        """Test validation statistics calculation."""
        # Create some validation results
        results = [
            validator.validate_post(valid_post_data),
            validator.validate_comment(valid_comment_data),
        ]

        stats = validator.get_validation_stats(results)

        assert "total_items" in stats
        assert "valid_items" in stats
        assert "validation_rate" in stats
        assert "average_quality_score" in stats
        assert "quality_distribution" in stats

    def test_post_age_validation(self, validator, valid_post_data):
        """Test validation of very old posts."""
        post_data = valid_post_data.copy()
        post_data["created_utc"] = "2020-01-01T00:00:00Z"  # Very old post

        result = validator.validate_post(post_data)

        assert result.is_valid is True
        assert len(result.warnings) > 0  # Should warn about age
        assert result.quality_score < 1.0

    def test_low_score_validation(self, validator, valid_post_data):
        """Test validation of posts with very low scores."""
        post_data = valid_post_data.copy()
        post_data["score"] = -50  # Very low score

        result = validator.validate_post(post_data)

        assert result.is_valid is True
        assert len(result.warnings) > 0  # Should warn about low score
        assert result.quality_score < 1.0
