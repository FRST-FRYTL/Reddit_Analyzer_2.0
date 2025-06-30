"""Phase 4A CLI Data Management Tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from sqlalchemy.orm import Session

from reddit_analyzer.cli.main import app
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.comment import Comment
from reddit_analyzer.models.subreddit import Subreddit


class TestCLIDataCommands:
    """Test CLI data management commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_auth(self):
        """Mock CLI authentication."""
        with patch("app.cli.data.cli_auth") as mock_auth:
            # Mock authenticated user
            test_user = User(username="testuser", role=UserRole.USER, is_active=True)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = (
                lambda func: func
            )  # Pass-through decorator
            yield mock_auth

    @pytest.fixture
    def sample_data(self, db_session: Session):
        """Create sample data for testing."""
        # Create subreddit
        subreddit = Subreddit(name="python", display_name="r/Python")
        db_session.add(subreddit)
        db_session.flush()

        # Create posts
        posts = []
        for i in range(5):
            post = Post(
                title=f"Test Post {i}",
                score=10 + i,
                num_comments=5 + i,
                created_at=datetime.utcnow() - timedelta(days=i),
                author=f"author{i}",
                url=f"https://reddit.com/r/python/post{i}",
                subreddit_id=subreddit.id,
            )
            posts.append(post)
            db_session.add(post)

        db_session.commit()
        return {"subreddit": subreddit, "posts": posts}

    def test_data_status_command(self, mock_auth, sample_data):
        """Test data status command."""
        with patch("app.cli.data.get_db") as mock_get_db:
            mock_get_db.return_value = mock_get_db
            mock_get_db.__enter__ = MagicMock(return_value=mock_get_db)
            mock_get_db.__exit__ = MagicMock(return_value=None)

            # Mock database queries
            mock_get_db.query.return_value.scalar.side_effect = [
                5,
                5,
                10,
                1,
            ]  # users, posts, comments, subreddits
            mock_get_db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                ("python", 5)
            ]

            result = self.runner.invoke(app, ["data", "status"])

            assert result.exit_code == 0
            assert "Data Collection Status" in result.stdout
            assert "Users" in result.stdout
            assert "Posts" in result.stdout

    def test_data_status_no_auth(self):
        """Test data status command without authentication."""
        with patch("app.cli.data.cli_auth") as mock_auth:
            mock_auth.get_current_user.return_value = None
            mock_auth.require_auth.side_effect = (
                lambda: lambda func: lambda *args, **kwargs: exec("raise SystemExit(1)")
            )

            result = self.runner.invoke(app, ["data", "status"])
            assert result.exit_code == 1

    def test_database_health_command(self, mock_auth):
        """Test database health command."""
        with patch("app.cli.data.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock successful database connection
            mock_db.execute.return_value.scalar.return_value = 1
            mock_db.query.return_value.scalar.side_effect = [
                10,
                100,
                500,
                5,
            ]  # users, posts, comments, subreddits

            result = self.runner.invoke(app, ["data", "health"])

            assert result.exit_code == 0
            assert "Database Health Check" in result.stdout
            assert "Connection" in result.stdout
            assert "Healthy" in result.stdout

    def test_database_health_connection_error(self, mock_auth):
        """Test database health command with connection error."""
        with patch("app.cli.data.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock database connection error
            mock_db.execute.side_effect = Exception("Connection failed")

            result = self.runner.invoke(app, ["data", "health"])

            assert result.exit_code == 1
            assert "Database health check failed" in result.stdout

    def test_collect_data_command(self, mock_auth):
        """Test data collection command."""
        with patch("app.cli.data.RedditClient") as mock_reddit_client:
            mock_client = MagicMock()
            mock_reddit_client.return_value = mock_client

            result = self.runner.invoke(
                app, ["data", "collect", "python", "--limit", "50", "--sort", "hot"]
            )

            assert result.exit_code == 0
            assert "Starting data collection from r/python" in result.stdout
            assert "Collected 50 posts" in result.stdout

    def test_collect_data_command_error(self, mock_auth):
        """Test data collection command with error."""
        with patch("app.cli.data.RedditClient") as mock_reddit_client:
            mock_reddit_client.side_effect = Exception("Reddit API error")

            result = self.runner.invoke(app, ["data", "collect", "python"])

            assert result.exit_code == 1
            assert "Data collection failed" in result.stdout

    def test_init_database_command_admin(self, mock_auth):
        """Test database initialization command as admin."""
        # Mock admin user
        admin_user = User(username="admin", role=UserRole.ADMIN, is_active=True)
        mock_auth.get_current_user.return_value = admin_user

        with patch("app.cli.data.command") as mock_alembic_command:
            with patch("app.cli.data.Config") as mock_config:
                mock_alembic_command.upgrade = MagicMock()

                result = self.runner.invoke(app, ["data", "init"])

                assert result.exit_code == 0
                assert "Database initialized successfully" in result.stdout
                mock_alembic_command.upgrade.assert_called_once()

    def test_init_database_command_non_admin(self, mock_auth):
        """Test database initialization command as non-admin."""
        # Mock regular user
        regular_user = User(username="user", role=UserRole.USER, is_active=True)
        mock_auth.get_current_user.return_value = regular_user
        mock_auth.require_auth.side_effect = (
            lambda role: lambda func: lambda *args, **kwargs: (
                exec("raise SystemExit(1)")
                if role == UserRole.ADMIN
                else func(*args, **kwargs)
            )
        )

        result = self.runner.invoke(app, ["data", "init"])

        assert result.exit_code == 1

    def test_backup_database_command(self, mock_auth):
        """Test database backup command."""
        # Mock admin user
        admin_user = User(username="admin", role=UserRole.ADMIN, is_active=True)
        mock_auth.get_current_user.return_value = admin_user

        result = self.runner.invoke(app, ["data", "backup", "test_backup.sql"])

        assert result.exit_code == 0
        assert "Creating database backup" in result.stdout
        assert "Database backup completed" in result.stdout

    def test_migrate_database_command(self, mock_auth):
        """Test database migration command."""
        # Mock admin user
        admin_user = User(username="admin", role=UserRole.ADMIN, is_active=True)
        mock_auth.get_current_user.return_value = admin_user

        with patch("app.cli.data.command") as mock_alembic_command:
            with patch("app.cli.data.Config") as mock_config:
                mock_alembic_command.upgrade = MagicMock()

                result = self.runner.invoke(app, ["data", "migrate"])

                assert result.exit_code == 0
                assert "Database migrations completed" in result.stdout
                mock_alembic_command.upgrade.assert_called_once()

    def test_migrate_database_command_error(self, mock_auth):
        """Test database migration command with error."""
        # Mock admin user
        admin_user = User(username="admin", role=UserRole.ADMIN, is_active=True)
        mock_auth.get_current_user.return_value = admin_user

        with patch("app.cli.data.command") as mock_alembic_command:
            with patch("app.cli.data.Config") as mock_config:
                mock_alembic_command.upgrade.side_effect = Exception("Migration failed")

                result = self.runner.invoke(app, ["data", "migrate"])

                assert result.exit_code == 1
                assert "Database migration failed" in result.stdout


class TestCLIDataIntegration:
    """Integration tests for CLI data commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def authenticated_admin(self, db_session: Session):
        """Create authenticated admin user."""
        admin = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
        )
        admin.set_password("AdminPassword123")
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    @pytest.fixture
    def sample_database(self, db_session: Session):
        """Create sample database content."""
        # Create users
        users = []
        for i in range(3):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                role=UserRole.USER,
                is_active=True,
            )
            users.append(user)
            db_session.add(user)

        # Create subreddit
        subreddit = Subreddit(
            name="testsubreddit",
            display_name="r/TestSubreddit",
            subscribers=1000,
            description="Test subreddit for CLI testing",
        )
        db_session.add(subreddit)
        db_session.flush()

        # Create posts
        posts = []
        for i in range(10):
            post = Post(
                title=f"Test Post {i}",
                score=10 + i * 5,
                num_comments=i * 2,
                created_at=datetime.utcnow() - timedelta(hours=i),
                author=f"user{i % 3}",
                url=f"https://reddit.com/r/testsubreddit/post{i}",
                selftext=f"This is test post content {i}",
                subreddit_id=subreddit.id,
            )
            posts.append(post)
            db_session.add(post)

        # Create comments
        comments = []
        for i, post in enumerate(posts[:5]):  # Only add comments to first 5 posts
            for j in range(i + 1):
                comment = Comment(
                    body=f"This is comment {j} on post {i}",
                    score=5 + j,
                    created_at=datetime.utcnow() - timedelta(hours=i, minutes=j * 10),
                    author=f"user{j % 3}",
                    post_id=post.id,
                )
                comments.append(comment)
                db_session.add(comment)

        db_session.commit()
        return {
            "users": users,
            "subreddit": subreddit,
            "posts": posts,
            "comments": comments,
        }

    def test_integrated_data_status(self, authenticated_admin, sample_database):
        """Test data status with real database content."""
        with patch("app.cli.data.cli_auth") as mock_auth:
            mock_auth.get_current_user.return_value = authenticated_admin
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.data.get_db") as mock_get_db:
                # Use real database session
                mock_get_db.return_value = sample_database
                mock_get_db.__enter__ = MagicMock(return_value=sample_database)
                mock_get_db.__exit__ = MagicMock(return_value=None)

                # Mock the query results based on our sample data
                mock_query = MagicMock()
                sample_database.query = MagicMock(return_value=mock_query)
                mock_query.scalar.side_effect = [
                    3,
                    10,
                    15,
                    1,
                ]  # users, posts, comments, subreddits

                # Mock subreddit query
                mock_query.outerjoin.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                    ("testsubreddit", 10)
                ]

                result = self.runner.invoke(app, ["data", "status"])

                assert result.exit_code == 0
                assert "Data Collection Status" in result.stdout
                assert "testsubreddit" in result.stdout

    def test_integrated_database_health(self, authenticated_admin, sample_database):
        """Test database health with real database."""
        with patch("app.cli.data.cli_auth") as mock_auth:
            mock_auth.get_current_user.return_value = authenticated_admin
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.data.get_db") as mock_get_db:
                mock_get_db.return_value = sample_database
                mock_get_db.__enter__ = MagicMock(return_value=sample_database)
                mock_get_db.__exit__ = MagicMock(return_value=None)

                # Mock database operations
                sample_database.execute = MagicMock()
                sample_database.execute.return_value.scalar.return_value = 1

                mock_query = MagicMock()
                sample_database.query = MagicMock(return_value=mock_query)
                mock_query.scalar.side_effect = [3, 10, 15, 1]

                result = self.runner.invoke(app, ["data", "health"])

                assert result.exit_code == 0
                assert "Database Health Check" in result.stdout
                assert "Healthy" in result.stdout


@pytest.mark.performance
class TestCLIDataPerformance:
    """Performance tests for CLI data commands."""

    def test_data_status_performance(self):
        """Test data status command performance."""
        import time

        runner = CliRunner()

        with patch("app.cli.data.cli_auth") as mock_auth:
            test_user = User(username="testuser", role=UserRole.USER)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.data.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Mock fast database queries
                mock_db.query.return_value.scalar.side_effect = [100, 1000, 5000, 10]
                mock_db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                    ("python", 500),
                    ("javascript", 300),
                ]

                start_time = time.time()

                result = runner.invoke(app, ["data", "status"])

                execution_time = time.time() - start_time

                assert result.exit_code == 0
                assert execution_time < 2.0  # Should complete within 2 seconds

    def test_database_health_performance(self):
        """Test database health command performance."""
        import time

        runner = CliRunner()

        with patch("app.cli.data.cli_auth") as mock_auth:
            test_user = User(username="testuser", role=UserRole.USER)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.data.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Mock database operations
                mock_db.execute.return_value.scalar.return_value = 1
                mock_db.query.return_value.scalar.side_effect = [100, 1000, 5000, 10]

                start_time = time.time()

                result = runner.invoke(app, ["data", "health"])

                execution_time = time.time() - start_time

                assert result.exit_code == 0
                assert execution_time < 2.0  # Should complete within 2 seconds

    def test_large_dataset_handling(self):
        """Test CLI performance with large dataset simulation."""
        runner = CliRunner()

        with patch("app.cli.data.cli_auth") as mock_auth:
            test_user = User(username="testuser", role=UserRole.USER)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.data.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Simulate large dataset
                large_counts = [
                    10000,
                    500000,
                    2000000,
                    1000,
                ]  # users, posts, comments, subreddits
                mock_db.query.return_value.scalar.side_effect = large_counts

                # Large subreddit list
                large_subreddit_list = [(f"subreddit{i}", 1000 + i) for i in range(50)]
                mock_db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = large_subreddit_list

                import time

                start_time = time.time()

                result = runner.invoke(app, ["data", "status"])

                execution_time = time.time() - start_time

                assert result.exit_code == 0
                assert (
                    execution_time < 3.0
                )  # Should handle large datasets within 3 seconds
                assert "500,000" in result.stdout  # Check large number formatting
