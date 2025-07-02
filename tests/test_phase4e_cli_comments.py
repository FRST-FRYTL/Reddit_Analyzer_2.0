"""Integration tests for CLI comment collection functionality."""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from datetime import datetime

from reddit_analyzer.cli.main import app
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.comment import Comment
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.models.subreddit import Subreddit


@pytest.fixture(autouse=True)
def enable_auth_test_mode():
    """Enable test mode for all tests in this module."""
    # Import and modify the global cli_auth instance
    from reddit_analyzer.cli.utils import auth_manager

    # Save original state
    original_skip_auth = getattr(auth_manager.cli_auth, "skip_auth", False)

    # Enable skip_auth on the existing instance
    auth_manager.cli_auth.skip_auth = True

    # Patch all CLI modules that might have already imported cli_auth
    import sys

    cli_modules = [
        "reddit_analyzer.cli.analyze",
        "reddit_analyzer.cli.admin",
        "reddit_analyzer.cli.data",
        "reddit_analyzer.cli.nlp",
        "reddit_analyzer.cli.reports",
        "reddit_analyzer.cli.visualization",
        "reddit_analyzer.cli.auth",
    ]

    for module_name in cli_modules:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, "cli_auth"):
                module.cli_auth.skip_auth = True

    yield

    # Restore original state
    auth_manager.cli_auth.skip_auth = original_skip_auth
    for module_name in cli_modules:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, "cli_auth"):
                module.cli_auth.skip_auth = original_skip_auth


class TestCLICommentCollection:
    """Test CLI data collection with comment support."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def auth_user(self):
        """Mock auth context for CLI."""
        # Simple mock since test mode is enabled
        auth_manager = Mock()
        auth_manager.skip_auth = True
        return {"auth_manager": auth_manager}

    @pytest.fixture
    def mock_reddit_client(self):
        """Mock RedditClient for testing."""
        with patch("reddit_analyzer.services.reddit_client.RedditClient") as mock:
            client = Mock()

            # Mock subreddit info
            client.get_subreddit_info.return_value = {
                "name": "python",
                "display_name": "r/python",
                "description": "Python programming",
                "subscribers": 1000000,
                "created_utc": datetime.utcnow(),
                "is_nsfw": False,
            }

            # Mock posts
            client.get_subreddit_posts.return_value = [
                {
                    "id": "post1",
                    "title": "Test Post 1",
                    "selftext": "Post content 1",
                    "url": "https://reddit.com/post1",
                    "author": "testuser1",
                    "subreddit": "python",
                    "score": 100,
                    "upvote_ratio": 0.95,
                    "num_comments": 25,
                    "created_utc": datetime.utcnow(),
                    "is_self": True,
                    "is_nsfw": False,
                    "is_locked": False,
                },
                {
                    "id": "post2",
                    "title": "Test Post 2",
                    "selftext": "Post content 2",
                    "url": "https://reddit.com/post2",
                    "author": "testuser2",
                    "subreddit": "python",
                    "score": 50,
                    "upvote_ratio": 0.90,
                    "num_comments": 10,
                    "created_utc": datetime.utcnow(),
                    "is_self": True,
                    "is_nsfw": False,
                    "is_locked": False,
                },
            ]

            # Mock comments
            def mock_get_comments(post_id, limit=50, depth=3, min_score=None):
                comments = []
                if post_id == "post1":
                    comments = [
                        {
                            "id": "c1",
                            "post_id": "post1",
                            "parent_id": None,
                            "author": "commentuser1",
                            "body": "Great post!",
                            "score": 15,
                            "created_utc": datetime.utcnow(),
                            "edited": False,
                            "is_deleted": False,
                            "depth": 0,
                        },
                        {
                            "id": "c2",
                            "post_id": "post1",
                            "parent_id": "t1_c1",
                            "author": "commentuser2",
                            "body": "I agree!",
                            "score": 8,
                            "created_utc": datetime.utcnow(),
                            "edited": True,
                            "is_deleted": False,
                            "depth": 1,
                        },
                        {
                            "id": "c3",
                            "post_id": "post1",
                            "parent_id": None,
                            "author": "commentuser3",
                            "body": "Interesting perspective",
                            "score": 3,
                            "created_utc": datetime.utcnow(),
                            "edited": False,
                            "is_deleted": False,
                            "depth": 0,
                        },
                    ]
                elif post_id == "post2":
                    comments = [
                        {
                            "id": "c4",
                            "post_id": "post2",
                            "parent_id": None,
                            "author": "commentuser4",
                            "body": "Thanks for sharing",
                            "score": 20,
                            "created_utc": datetime.utcnow(),
                            "edited": False,
                            "is_deleted": False,
                            "depth": 0,
                        }
                    ]

                # Apply filters
                if min_score is not None:
                    comments = [c for c in comments if c["score"] >= min_score]

                return comments[:limit]

            client.get_post_comments.side_effect = mock_get_comments

            # Mock user info
            def mock_user_info(username):
                return {
                    "username": username,
                    "created_utc": datetime.utcnow(),
                    "comment_karma": 1000,
                    "link_karma": 500,
                    "is_verified": False,
                }

            client.get_user_info.side_effect = mock_user_info

            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_nlp_service(self):
        """Mock NLP service."""
        with patch("reddit_analyzer.cli.data.get_nlp_service") as mock:
            service = Mock()
            service.analyze_text.return_value = {
                "sentiment": {"compound": 0.5, "label": "positive"},
                "keywords": ["test", "python"],
                "entities": [],
            }
            mock.return_value = service
            yield service

    def test_collect_with_comments(
        self, runner, mock_reddit_client, mock_nlp_service, auth_user, db_session
    ):
        """Test data collection with --with-comments flag."""
        # Run command
        result = runner.invoke(
            app,
            [
                "data",
                "collect",
                "python",
                "--limit",
                "2",
                "--with-comments",
                "--skip-nlp",
            ],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0
        assert (
            "Starting data collection from r/python (posts with comments)"
            in result.output
        )
        assert "Collected 2 new posts" in result.output
        assert "Collecting comments" in result.output
        assert "Collected 4 new comments" in result.output

        # Verify database
        posts = db_session.query(Post).all()
        assert len(posts) == 2

        comments = db_session.query(Comment).all()
        assert len(comments) == 4

        # Check comment relationships
        post1_comments = db_session.query(Comment).filter_by(post_id="post1").all()
        assert len(post1_comments) == 3

        # Check parent-child relationships
        c2 = db_session.query(Comment).filter_by(id="c2").first()
        assert c2.parent_id == "c1"

    def test_collect_comments_only(
        self, runner, mock_reddit_client, auth_user, db_session
    ):
        """Test --comments-only mode."""
        # First, add some posts to the database
        subreddit = Subreddit(
            name="python",
            display_name="r/python",
            description="Python programming",
            subscribers=1000000,
        )
        db_session.add(subreddit)

        post1 = Post(
            id="post1",
            title="Existing Post 1",
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
        )
        post2 = Post(
            id="post2",
            title="Existing Post 2",
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
        )
        db_session.add_all([post1, post2])
        db_session.commit()

        # Run command
        result = runner.invoke(
            app,
            ["data", "collect", "python", "--comments-only", "--skip-nlp"],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0
        assert "Starting data collection from r/python (comments only)" in result.output
        assert "Collecting comments" in result.output
        assert "Collected 4 new comments" in result.output

        # Verify no new posts added
        posts = db_session.query(Post).all()
        assert len(posts) == 2  # Same as before

        # Verify comments added
        comments = db_session.query(Comment).all()
        assert len(comments) == 4

    def test_comment_limit_option(
        self, runner, mock_reddit_client, auth_user, db_session
    ):
        """Test --comment-limit parameter."""
        # Run with comment limit
        result = runner.invoke(
            app,
            [
                "data",
                "collect",
                "python",
                "--limit",
                "1",
                "--with-comments",
                "--comment-limit",
                "2",
                "--skip-nlp",
            ],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0

        # Verify only 2 comments per post collected
        comments = db_session.query(Comment).filter_by(post_id="post1").all()
        assert len(comments) == 2  # Limited to 2 comments

    def test_min_comment_score_filter(
        self, runner, mock_reddit_client, auth_user, db_session
    ):
        """Test --min-comment-score filter."""
        # Run with min score filter
        result = runner.invoke(
            app,
            [
                "data",
                "collect",
                "python",
                "--limit",
                "2",
                "--with-comments",
                "--min-comment-score",
                "10",
                "--skip-nlp",
            ],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0

        # Verify only high-score comments collected
        comments = db_session.query(Comment).all()
        assert len(comments) == 2  # Only c1 (score 15) and c4 (score 20)

        for comment in comments:
            assert comment.score >= 10

    def test_conflicting_options_error(self, runner, auth_user):
        """Test error when using --with-comments and --comments-only together."""
        # Run with conflicting options
        result = runner.invoke(
            app,
            ["data", "collect", "python", "--with-comments", "--comments-only"],
            obj={"auth_manager": auth_user},
        )

        # Should fail
        assert result.exit_code == 1
        assert (
            "Cannot use --with-comments and --comments-only together" in result.output
        )

    def test_comments_only_no_posts(
        self, runner, mock_reddit_client, auth_user, db_session
    ):
        """Test --comments-only when no posts exist."""
        # Ensure subreddit exists but no posts
        subreddit = Subreddit(
            name="python",
            display_name="r/python",
            description="Python programming",
            subscribers=1000000,
        )
        db_session.add(subreddit)
        db_session.commit()

        # Run command
        result = runner.invoke(
            app,
            ["data", "collect", "python", "--comments-only", "--skip-nlp"],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0
        assert "No posts found to collect comments for" in result.output

    def test_comment_nlp_analysis(
        self, runner, mock_reddit_client, mock_nlp_service, auth_user, db_session
    ):
        """Test NLP analysis on comments."""
        # Run without skipping NLP
        result = runner.invoke(
            app,
            [
                "data",
                "collect",
                "python",
                "--limit",
                "1",
                "--with-comments",
                "--comment-limit",
                "2",
            ],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0
        assert "Processing NLP analysis for" in result.output
        assert "comments" in result.output

        # Verify NLP service was called for comments
        # Should be called for post and comments
        assert mock_nlp_service.analyze_text.call_count >= 3  # 1 post + 2 comments

    def test_multiple_options_combined(
        self, runner, mock_reddit_client, auth_user, db_session
    ):
        """Test combining multiple comment options."""
        # Run with all options
        result = runner.invoke(
            app,
            [
                "data",
                "collect",
                "python",
                "--limit",
                "2",
                "--with-comments",
                "--comment-limit",
                "1",
                "--comment-depth",
                "0",
                "--min-comment-score",
                "10",
                "--skip-nlp",
            ],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0

        # Verify constraints
        comments = db_session.query(Comment).all()

        # Should have max 1 comment per post, depth 0, score >= 10
        # Only c1 (score 15, depth 0) and c4 (score 20, depth 0) qualify
        assert len(comments) == 2

        for comment in comments:
            assert comment.score >= 10
            assert comment.depth == 0

    def test_comment_user_creation(
        self, runner, mock_reddit_client, auth_user, db_session
    ):
        """Test that comment authors are created as users."""
        # Run command
        result = runner.invoke(
            app,
            [
                "data",
                "collect",
                "python",
                "--limit",
                "1",
                "--with-comments",
                "--skip-nlp",
            ],
            obj={"auth_manager": auth_user},
        )

        # Check output
        assert result.exit_code == 0

        # Verify users created for post and comment authors
        users = db_session.query(User).filter(User.username.like("testuser%")).all()
        assert len(users) >= 1  # At least post author

        comment_users = (
            db_session.query(User).filter(User.username.like("commentuser%")).all()
        )
        assert len(comment_users) >= 1  # At least one comment author

        # Check user properties
        for user in comment_users:
            assert user.role == UserRole.USER
            assert user.is_active
            assert user.comment_karma == 1000  # From mock

    def test_deleted_comment_handling(self, runner, auth_user, db_session):
        """Test handling of deleted comments."""
        with patch(
            "reddit_analyzer.services.reddit_client.RedditClient"
        ) as mock_client:
            client = Mock()

            # Mock subreddit info
            client.get_subreddit_info.return_value = {
                "name": "python",
                "display_name": "r/python",
                "description": "Test",
                "subscribers": 1000,
                "created_utc": datetime.utcnow(),
                "is_nsfw": False,
            }

            # Mock posts
            client.get_subreddit_posts.return_value = [
                {
                    "id": "post1",
                    "title": "Test Post",
                    "selftext": "Content",
                    "url": "https://reddit.com/post1",
                    "author": "user1",
                    "subreddit": "python",
                    "score": 10,
                    "upvote_ratio": 0.9,
                    "num_comments": 1,
                    "created_utc": datetime.utcnow(),
                    "is_self": True,
                    "is_nsfw": False,
                    "is_locked": False,
                }
            ]

            # Mock deleted comment
            client.get_post_comments.return_value = [
                {
                    "id": "deleted1",
                    "post_id": "post1",
                    "parent_id": None,
                    "author": "[deleted]",
                    "body": "[deleted]",
                    "score": 0,
                    "created_utc": datetime.utcnow(),
                    "edited": False,
                    "is_deleted": True,
                    "depth": 0,
                }
            ]

            # Mock user info (should not be called for deleted user)
            client.get_user_info.side_effect = Exception(
                "Should not fetch deleted user"
            )

            mock_client.return_value = client

            # Run command
            result = runner.invoke(
                app,
                [
                    "data",
                    "collect",
                    "python",
                    "--limit",
                    "1",
                    "--with-comments",
                    "--skip-nlp",
                ],
                obj={"auth_manager": auth_user},
            )

            # Should succeed
            assert result.exit_code == 0

            # Verify deleted comment stored without user
            comment = db_session.query(Comment).filter_by(id="deleted1").first()
            assert comment is not None
            assert comment.author_id is None
            assert comment.body == "[deleted]"
