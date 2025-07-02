"""Unit tests for RedditClient comment collection functionality."""

import pytest
from unittest.mock import Mock, patch

from reddit_analyzer.services.reddit_client import RedditClient


class MockCommentForest:
    """Mock PRAW comment forest."""

    def __init__(self, comments):
        self._comments = comments

    def __iter__(self):
        return iter(self._comments)

    def replace_more(self, limit=0):
        pass


class TestRedditClientComments:
    """Test comment collection methods in RedditClient."""

    @pytest.fixture
    def reddit_client(self):
        """Create a RedditClient instance with mocked PRAW."""
        with patch("reddit_analyzer.services.reddit_client.praw.Reddit"):
            client = RedditClient()
            return client

    @pytest.fixture
    def mock_comment(self):
        """Create a mock comment object."""
        comment = Mock()
        comment.id = "test_comment_1"
        comment.author = Mock()
        comment.author.name = "test_user"  # Set name attribute properly
        comment.body = "This is a test comment"
        comment.score = 10
        comment.created_utc = 1234567890
        comment.edited = False
        comment.parent_id = "t3_test_post"
        comment.replies = []
        return comment

    @pytest.fixture
    def mock_nested_comments(self):
        """Create a mock nested comment structure."""
        # Level 0 comment
        c1 = Mock()
        c1.id = "c1"
        c1.author = Mock()
        c1.author.name = "user1"
        c1.body = "Top level comment"
        c1.score = 20
        c1.created_utc = 1234567890
        c1.edited = False
        c1.parent_id = "t3_post1"

        # Level 1 comment
        c2 = Mock()
        c2.id = "c2"
        c2.author = Mock()
        c2.author.name = "user2"
        c2.body = "First reply"
        c2.score = 15
        c2.created_utc = 1234567891
        c2.edited = True
        c2.parent_id = "t1_c1"

        # Level 2 comment
        c3 = Mock()
        c3.id = "c3"
        c3.author = Mock()
        c3.author.name = "user3"
        c3.body = "Nested reply"
        c3.score = 8
        c3.created_utc = 1234567892
        c3.edited = False
        c3.parent_id = "t1_c2"

        # Level 3 comment
        c4 = Mock()
        c4.id = "c4"
        c4.author = Mock()
        c4.author.name = "user4"
        c4.body = "Deep nested reply"
        c4.score = 3
        c4.created_utc = 1234567893
        c4.edited = False
        c4.parent_id = "t1_c3"

        # Set up reply structure
        c3.replies = [c4]
        c2.replies = [c3]
        c1.replies = [c2]

        return c1

    def test_get_post_comments_basic(self, reddit_client, mock_comment):
        """Test basic comment fetching for a post."""
        # Mock submission
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest([mock_comment])

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Fetch comments
        comments = reddit_client.get_post_comments("test_post", limit=50)

        # Verify
        assert len(comments) == 1
        assert comments[0]["id"] == "test_comment_1"
        assert comments[0]["author"] == "test_user"
        assert comments[0]["body"] == "This is a test comment"
        assert comments[0]["score"] == 10
        assert comments[0]["depth"] == 0
        assert not comments[0]["edited"]

    def test_get_post_comments_with_min_score(self, reddit_client):
        """Test comment fetching with min_score filter."""
        # Create comments with various scores
        comments_list = []
        for i, score in enumerate([15, 5, 20, 2, 10]):
            comment = Mock()
            comment.id = f"c{i}"
            comment.author = Mock()
            comment.author.name = f"user{i}"
            comment.body = f"Comment {i}"
            comment.score = score
            comment.created_utc = 1234567890 + i
            comment.edited = False
            comment.parent_id = "t3_test_post"
            comment.replies = []
            comments_list.append(comment)

        # Mock submission
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest(comments_list)

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Fetch with min_score = 10
        comments = reddit_client.get_post_comments("test_post", min_score=10)

        # Should get 3 comments with scores >= 10
        assert len(comments) == 3
        assert all(c["score"] >= 10 for c in comments)

    def test_get_post_comments_nested(self, reddit_client, mock_nested_comments):
        """Test nested comment tree handling."""
        # Mock submission
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest([mock_nested_comments])

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Test with depth = 2
        comments = reddit_client.get_post_comments("test_post", limit=10, depth=2)

        # Should get 3 comments (depth 0, 1, 2)
        assert len(comments) == 3
        assert comments[0]["id"] == "c1"
        assert comments[0]["depth"] == 0
        assert comments[1]["id"] == "c2"
        assert comments[1]["depth"] == 1
        assert comments[2]["id"] == "c3"
        assert comments[2]["depth"] == 2

        # Test with depth = 1
        comments = reddit_client.get_post_comments("test_post", limit=10, depth=1)

        # Should get 2 comments (depth 0, 1)
        assert len(comments) == 2
        assert all(c["depth"] <= 1 for c in comments)

    def test_get_post_comments_deleted(self, reddit_client):
        """Test handling of deleted comments."""
        # Create deleted comment
        deleted_comment = Mock()
        deleted_comment.id = "deleted1"
        deleted_comment.author = None  # Deleted author
        deleted_comment.body = "[deleted]"
        deleted_comment.score = 0
        deleted_comment.created_utc = 1234567890
        deleted_comment.edited = False
        deleted_comment.parent_id = "t3_test_post"
        deleted_comment.replies = []

        # Mock submission
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest([deleted_comment])

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Fetch comments
        comments = reddit_client.get_post_comments("test_post")

        # Verify deleted comment handling
        assert len(comments) == 1
        assert comments[0]["author"] == "[deleted]"
        assert comments[0]["body"] == "[deleted]"
        assert comments[0]["is_deleted"]

    def test_get_post_comments_no_replies(self, reddit_client):
        """Test posts with no comments."""
        # Mock submission with empty comments
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest([])

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Fetch comments
        comments = reddit_client.get_post_comments("test_post")

        # Should return empty list
        assert comments == []

    def test_get_post_comments_limit_reached(self, reddit_client):
        """Test comment limit parameter."""
        # Create many comments
        comments_list = []
        for i in range(20):
            comment = Mock()
            comment.id = f"c{i}"
            comment.author = Mock()
            comment.author.name = f"user{i}"
            comment.body = f"Comment {i}"
            comment.score = i
            comment.created_utc = 1234567890 + i
            comment.edited = False
            comment.parent_id = "t3_test_post"
            comment.replies = []
            comments_list.append(comment)

        # Mock submission
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest(comments_list)

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Fetch with limit = 5
        comments = reddit_client.get_post_comments("test_post", limit=5)

        # Should get exactly 5 comments
        assert len(comments) == 5

    def test_get_all_comments(self, reddit_client):
        """Test direct subreddit comment fetching."""
        # Create mock comments
        mock_comments = []
        for i in range(5):
            comment = Mock()
            comment.id = f"stream_c{i}"
            comment.author = Mock()
            comment.author.name = f"stream_user{i}"
            comment.body = f"Stream comment {i}"
            comment.score = i * 2
            comment.created_utc = 1234567890 + i
            comment.edited = i % 2 == 0
            comment.parent_id = f"t1_parent{i}"
            comment.submission = Mock(id=f"post{i}")
            mock_comments.append(comment)

        # Mock subreddit
        mock_subreddit = Mock()
        mock_subreddit.comments = Mock(return_value=iter(mock_comments))

        reddit_client.reddit.subreddit = Mock(return_value=mock_subreddit)

        # Fetch comments
        comments = reddit_client.get_all_comments("python", limit=3)

        # Should get 3 comments
        assert len(comments) == 3
        assert comments[0]["id"] == "stream_c0"
        assert comments[1]["post_id"] == "post1"
        assert comments[2]["edited"]

    def test_get_all_comments_with_invalid_comments(self, reddit_client):
        """Test handling of invalid comments in stream."""
        # Mix valid and invalid comments
        valid_comment = Mock()
        valid_comment.id = "valid1"
        valid_comment.body = "Valid comment"
        valid_comment.author = Mock()
        valid_comment.author.name = "user1"
        valid_comment.score = 5
        valid_comment.created_utc = 1234567890
        valid_comment.edited = False
        valid_comment.parent_id = "t1_parent"
        valid_comment.submission = Mock(id="post1")

        invalid_comment = Mock()
        # Missing body attribute
        del invalid_comment.body

        # Mock subreddit
        mock_subreddit = Mock()
        mock_subreddit.comments = Mock(
            return_value=iter([valid_comment, invalid_comment])
        )

        reddit_client.reddit.subreddit = Mock(return_value=mock_subreddit)

        # Fetch comments
        comments = reddit_client.get_all_comments("python", limit=10)

        # Should only get the valid comment
        assert len(comments) == 1
        assert comments[0]["id"] == "valid1"

    def test_get_post_comments_error_handling(self, reddit_client):
        """Test error handling in comment fetching."""
        # Mock submission that raises error
        reddit_client.reddit.submission = Mock(side_effect=Exception("API Error"))

        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            reddit_client.get_post_comments("test_post")

        assert "API Error" in str(exc_info.value)

    def test_get_post_comments_parent_id_processing(self, reddit_client):
        """Test parent_id processing for top-level vs nested comments."""
        # Create comments with different parent_id formats
        top_comment = Mock()
        top_comment.id = "top1"
        top_comment.author = Mock()
        top_comment.author.name = "user1"
        top_comment.body = "Top level"
        top_comment.score = 10
        top_comment.created_utc = 1234567890
        top_comment.edited = False
        top_comment.parent_id = "t3_post123"  # Post parent
        top_comment.replies = []

        nested_comment = Mock()
        nested_comment.id = "nested1"
        nested_comment.author = Mock()
        nested_comment.author.name = "user2"
        nested_comment.body = "Nested"
        nested_comment.score = 5
        nested_comment.created_utc = 1234567891
        nested_comment.edited = False
        nested_comment.parent_id = "t1_top1"  # Comment parent
        nested_comment.replies = []

        top_comment.replies = [nested_comment]

        # Mock submission
        mock_submission = Mock()
        mock_submission.comments = MockCommentForest([top_comment])

        reddit_client.reddit.submission = Mock(return_value=mock_submission)

        # Fetch comments
        comments = reddit_client.get_post_comments("post123")

        # Verify parent_id processing
        assert (
            comments[0]["parent_id"] == "t3_post123"
        )  # Top-level comment has post parent
        assert comments[1]["parent_id"] == "t1_top1"  # Nested comment keeps parent_id
