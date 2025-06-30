"""Test model classes."""

from datetime import datetime

from reddit_analyzer.models import User, Subreddit, Post, Comment


class TestUser:
    """Test User model."""

    def test_user_creation(self, test_db):
        """Test creating a user."""
        user = User(
            username="testuser", comment_karma=100, link_karma=200, is_verified=True
        )

        test_db.add(user)
        test_db.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.comment_karma == 100
        assert user.link_karma == 200
        assert user.is_verified is True
        assert user.created_at is not None

    def test_user_repr(self):
        """Test user string representation."""
        user = User(username="testuser")
        user.id = 1
        assert repr(user) == "<User(id=1, username='testuser')>"


class TestSubreddit:
    """Test Subreddit model."""

    def test_subreddit_creation(self, test_db):
        """Test creating a subreddit."""
        subreddit = Subreddit(
            name="python",
            display_name="Python",
            description="The official Python subreddit",
            subscribers=1000000,
            is_nsfw=False,
        )

        test_db.add(subreddit)
        test_db.commit()

        assert subreddit.id is not None
        assert subreddit.name == "python"
        assert subreddit.display_name == "Python"
        assert subreddit.subscribers == 1000000
        assert subreddit.is_nsfw is False

    def test_subreddit_repr(self):
        """Test subreddit string representation."""
        subreddit = Subreddit(name="python")
        subreddit.id = 1
        assert repr(subreddit) == "<Subreddit(id=1, name='python')>"


class TestPost:
    """Test Post model."""

    def test_post_creation(self, test_db):
        """Test creating a post."""
        # Create user and subreddit first
        user = User(username="testuser")
        subreddit = Subreddit(name="python")

        test_db.add(user)
        test_db.add(subreddit)
        test_db.commit()

        post = Post(
            id="abc123",
            title="Test Post",
            selftext="This is a test post",
            author_id=user.id,
            subreddit_id=subreddit.id,
            score=100,
            num_comments=10,
            created_utc=datetime.utcnow(),
        )

        test_db.add(post)
        test_db.commit()

        assert post.id == "abc123"
        assert post.title == "Test Post"
        assert post.score == 100
        assert post.author_id == user.id
        assert post.subreddit_id == subreddit.id

    def test_post_relationships(self, test_db):
        """Test post relationships."""
        user = User(username="testuser")
        subreddit = Subreddit(name="python")

        test_db.add(user)
        test_db.add(subreddit)
        test_db.commit()

        post = Post(
            id="abc123",
            title="Test Post",
            author_id=user.id,
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
        )

        test_db.add(post)
        test_db.commit()

        # Test relationships
        assert post.author.username == "testuser"
        assert post.subreddit.name == "python"


class TestComment:
    """Test Comment model."""

    def test_comment_creation(self, test_db):
        """Test creating a comment."""
        # Create dependencies
        user = User(username="testuser")
        subreddit = Subreddit(name="python")

        test_db.add(user)
        test_db.add(subreddit)
        test_db.commit()

        post = Post(
            id="abc123",
            title="Test Post",
            author_id=user.id,
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
        )

        test_db.add(post)
        test_db.commit()

        comment = Comment(
            id="def456",
            post_id=post.id,
            author_id=user.id,
            body="This is a test comment",
            score=50,
            created_utc=datetime.utcnow(),
        )

        test_db.add(comment)
        test_db.commit()

        assert comment.id == "def456"
        assert comment.post_id == post.id
        assert comment.body == "This is a test comment"
        assert comment.score == 50

    def test_comment_relationships(self, test_db):
        """Test comment relationships."""
        user = User(username="testuser")
        subreddit = Subreddit(name="python")

        test_db.add(user)
        test_db.add(subreddit)
        test_db.commit()

        post = Post(
            id="abc123",
            title="Test Post",
            author_id=user.id,
            subreddit_id=subreddit.id,
            created_utc=datetime.utcnow(),
        )

        test_db.add(post)
        test_db.commit()

        comment = Comment(
            id="def456",
            post_id=post.id,
            author_id=user.id,
            body="Test comment",
            created_utc=datetime.utcnow(),
        )

        test_db.add(comment)
        test_db.commit()

        # Test relationships
        assert comment.post.title == "Test Post"
        assert comment.author.username == "testuser"
