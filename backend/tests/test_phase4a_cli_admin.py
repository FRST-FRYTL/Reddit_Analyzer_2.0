"""Phase 4A CLI Admin Tests."""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from sqlalchemy.orm import Session

from app.cli.main import app
from app.models.user import User, UserRole


class TestCLIAdminCommands:
    """Test CLI admin commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_admin_auth(self):
        """Mock CLI authentication for admin user."""
        with patch("app.cli.admin.cli_auth") as mock_auth:
            admin_user = User(username="admin", role=UserRole.ADMIN, is_active=True)
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func
            yield mock_auth

    @pytest.fixture
    def mock_user_auth(self):
        """Mock CLI authentication for regular user."""
        with patch("app.cli.admin.cli_auth") as mock_auth:
            regular_user = User(username="user", role=UserRole.USER, is_active=True)
            mock_auth.get_current_user.return_value = regular_user
            mock_auth.require_auth.side_effect = (
                lambda role=None: lambda func: lambda *args, **kwargs: (
                    exec("raise SystemExit(1)")
                    if role in [UserRole.ADMIN, UserRole.MODERATOR]
                    else func(*args, **kwargs)
                )
            )
            yield mock_auth

    def test_list_users_command(self, mock_admin_auth):
        """Test list users command."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock user list
            mock_users = [
                User(
                    id=1,
                    username="admin",
                    email="admin@example.com",
                    role=UserRole.ADMIN,
                    is_active=True,
                ),
                User(
                    id=2,
                    username="user1",
                    email="user1@example.com",
                    role=UserRole.USER,
                    is_active=True,
                ),
                User(
                    id=3,
                    username="user2",
                    email="user2@example.com",
                    role=UserRole.USER,
                    is_active=False,
                ),
            ]
            mock_db.query.return_value.order_by.return_value.all.return_value = (
                mock_users
            )

            result = self.runner.invoke(app, ["admin", "users"])

            assert result.exit_code == 0
            assert "System Users" in result.stdout
            assert "admin" in result.stdout
            assert "user1" in result.stdout

    def test_list_users_with_role_filter(self, mock_admin_auth):
        """Test list users command with role filter."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock filtered user list
            mock_users = [
                User(
                    id=1,
                    username="admin",
                    email="admin@example.com",
                    role=UserRole.ADMIN,
                    is_active=True,
                )
            ]
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_users

            result = self.runner.invoke(app, ["admin", "users", "--role", "admin"])

            assert result.exit_code == 0
            assert "admin" in result.stdout

    def test_list_users_invalid_role(self, mock_admin_auth):
        """Test list users command with invalid role."""
        result = self.runner.invoke(app, ["admin", "users", "--role", "invalid"])

        assert result.exit_code == 1
        assert "Invalid role" in result.stdout

    def test_list_users_non_admin(self, mock_user_auth):
        """Test list users command as non-admin user."""
        result = self.runner.invoke(app, ["admin", "users"])
        assert result.exit_code == 1

    def test_create_user_command(self, mock_admin_auth):
        """Test create user command."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock no existing user
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Mock user creation
            new_user = User(
                id=10, username="newuser", email="new@example.com", role=UserRole.USER
            )
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()
            mock_db.refresh.side_effect = lambda user: setattr(user, "id", 10)

            result = self.runner.invoke(
                app,
                [
                    "admin",
                    "create-user",
                    "--username",
                    "newuser",
                    "--email",
                    "new@example.com",
                    "--role",
                    "user",
                ],
                input="password123\\n",
            )

            assert result.exit_code == 0
            assert "Created user 'newuser'" in result.stdout

    def test_create_user_with_generated_password(self, mock_admin_auth):
        """Test create user command with generated password."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            result = self.runner.invoke(
                app,
                [
                    "admin",
                    "create-user",
                    "--username",
                    "newuser",
                    "--role",
                    "user",
                    "--generate-password",
                ],
            )

            assert result.exit_code == 0
            assert "Generated password:" in result.stdout

    def test_create_user_existing_username(self, mock_admin_auth):
        """Test create user with existing username."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock existing user
            existing_user = User(username="existing", email="existing@example.com")
            mock_db.query.return_value.filter.return_value.first.return_value = (
                existing_user
            )

            result = self.runner.invoke(
                app, ["admin", "create-user", "--username", "existing"]
            )

            assert result.exit_code == 1
            assert "already exists" in result.stdout

    def test_update_user_role_command(self, mock_admin_auth):
        """Test update user role command."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock user to update
            user_to_update = User(username="user1", role=UserRole.USER)
            mock_db.query.return_value.filter.return_value.first.return_value = (
                user_to_update
            )
            mock_db.commit = MagicMock()

            result = self.runner.invoke(
                app,
                ["admin", "update-role", "--username", "user1", "--role", "moderator"],
            )

            assert result.exit_code == 0
            assert "Updated user1 role" in result.stdout
            assert user_to_update.role == UserRole.MODERATOR

    def test_update_user_role_user_not_found(self, mock_admin_auth):
        """Test update user role for non-existent user."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = self.runner.invoke(
                app,
                [
                    "admin",
                    "update-role",
                    "--username",
                    "nonexistent",
                    "--role",
                    "admin",
                ],
            )

            assert result.exit_code == 1
            assert "not found" in result.stdout

    def test_deactivate_user_command(self, mock_admin_auth):
        """Test deactivate user command."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock active user
            active_user = User(username="activeuser", is_active=True)
            mock_db.query.return_value.filter.return_value.first.return_value = (
                active_user
            )
            mock_db.commit = MagicMock()

            result = self.runner.invoke(
                app,
                ["admin", "deactivate-user", "--username", "activeuser"],
                input="y\\n",
            )

            assert result.exit_code == 0
            assert "Deactivated user 'activeuser'" in result.stdout
            assert active_user.is_active is False

    def test_deactivate_user_already_inactive(self, mock_admin_auth):
        """Test deactivate user that's already inactive."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock inactive user
            inactive_user = User(username="inactiveuser", is_active=False)
            mock_db.query.return_value.filter.return_value.first.return_value = (
                inactive_user
            )

            result = self.runner.invoke(
                app, ["admin", "deactivate-user", "--username", "inactiveuser"]
            )

            assert result.exit_code == 0
            assert "already inactive" in result.stdout

    def test_system_stats_command_admin(self, mock_admin_auth):
        """Test system stats command as admin."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock database statistics
            mock_db.query.return_value.scalar.side_effect = [
                100,
                80,
                5,
                3,
                50,
                1000,
                5000,
            ]
            mock_db.query.return_value.filter.return_value.scalar.side_effect = [
                80,
                5,
                3,
            ]

            result = self.runner.invoke(app, ["admin", "stats"])

            assert result.exit_code == 0
            assert "System Statistics" in result.stdout
            assert "Total Users" in result.stdout

    def test_system_stats_command_moderator(self):
        """Test system stats command as moderator."""
        with patch("app.cli.admin.cli_auth") as mock_auth:
            mod_user = User(username="mod", role=UserRole.MODERATOR, is_active=True)
            mock_auth.get_current_user.return_value = mod_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.admin.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                mock_db.query.return_value.scalar.side_effect = [
                    100,
                    80,
                    5,
                    3,
                    50,
                    1000,
                    5000,
                ]
                mock_db.query.return_value.filter.return_value.scalar.side_effect = [
                    80,
                    5,
                    3,
                ]

                result = self.runner.invoke(app, ["admin", "stats"])

                assert result.exit_code == 0

    def test_cleanup_data_dry_run(self, mock_admin_auth):
        """Test data cleanup in dry run mode."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock old data counts
            mock_db.query.return_value.filter.return_value.count.side_effect = [50, 200]

            result = self.runner.invoke(
                app, ["admin", "cleanup", "--days", "90", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Cleanup Report" in result.stdout
            assert "Would delete" in result.stdout
            assert "dry run" in result.stdout

    def test_cleanup_data_actual(self, mock_admin_auth):
        """Test actual data cleanup."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock old data counts and deletion
            mock_db.query.return_value.filter.return_value.count.side_effect = [50, 200]
            mock_db.query.return_value.filter.return_value.delete.side_effect = [
                200,
                50,
            ]
            mock_db.commit = MagicMock()

            result = self.runner.invoke(
                app, ["admin", "cleanup", "--days", "90", "--no-dry-run"], input="y\\n"
            )

            assert result.exit_code == 0
            assert "Deleted" in result.stdout

    def test_health_check_basic(self, mock_admin_auth):
        """Test basic health check."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock successful database connection
            mock_db.execute.return_value.scalar.return_value = 1
            mock_db.query.return_value.scalar.side_effect = [100, 50, 1000, 5000]
            mock_db.query.return_value.filter.return_value.scalar.return_value = 5

            result = self.runner.invoke(app, ["admin", "health-check"])

            assert result.exit_code == 0
            assert "system health check" in result.stdout
            assert "Database connection: OK" in result.stdout

    def test_health_check_full(self, mock_admin_auth):
        """Test full health check with performance tests."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock database operations
            mock_db.execute.return_value.scalar.return_value = 1
            mock_db.query.return_value.scalar.side_effect = [100, 50, 1000, 5000]
            mock_db.query.return_value.filter.return_value.scalar.return_value = 5
            mock_db.query.return_value.limit.return_value.all.return_value = []

            result = self.runner.invoke(app, ["admin", "health-check", "--full"])

            assert result.exit_code == 0
            assert "extended health checks" in result.stdout
            assert "Query performance" in result.stdout

    def test_health_check_connection_error(self, mock_admin_auth):
        """Test health check with database connection error."""
        with patch("app.cli.admin.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock database connection error
            mock_db.execute.side_effect = Exception("Connection failed")

            result = self.runner.invoke(app, ["admin", "health-check"])

            assert result.exit_code == 1
            assert "Health check failed" in result.stdout


class TestCLIAdminIntegration:
    """Integration tests for CLI admin commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def admin_user(self, db_session: Session):
        """Create admin user in database."""
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
    def sample_users(self, db_session: Session):
        """Create sample users in database."""
        users = []
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                role=UserRole.USER if i < 4 else UserRole.MODERATOR,
                is_active=i < 4,  # Last user is inactive
            )
            user.set_password(f"Password{i}")
            users.append(user)
            db_session.add(user)

        db_session.commit()
        return users

    def test_integrated_user_management(self, admin_user, sample_users):
        """Test integrated user management workflow."""
        with patch("app.cli.admin.cli_auth") as mock_auth:
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.admin.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Mock user listing
                mock_db.query.return_value.order_by.return_value.all.return_value = (
                    sample_users
                )

                # Test listing users
                result = self.runner.invoke(app, ["admin", "users"])

                assert result.exit_code == 0
                assert "user0" in result.stdout
                assert "user4" in result.stdout  # Moderator user

    def test_integrated_system_stats(self, admin_user, sample_users):
        """Test integrated system statistics."""
        with patch("app.cli.admin.cli_auth") as mock_auth:
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.admin.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Mock realistic statistics
                mock_db.query.return_value.scalar.side_effect = [
                    6,
                    5,
                    1,
                    1,
                    100,
                    1000,
                    5000,
                ]  # total_users, active, admin, mod, subreddits, posts, comments
                mock_db.query.return_value.filter.return_value.scalar.side_effect = [
                    1,
                    1,
                ]  # admin and mod counts

                result = self.runner.invoke(app, ["admin", "stats"])

                assert result.exit_code == 0
                assert "System Statistics" in result.stdout


@pytest.mark.performance
class TestCLIAdminPerformance:
    """Performance tests for CLI admin commands."""

    def test_user_listing_performance(self):
        """Test user listing performance with large user base."""
        import time

        runner = CliRunner()

        with patch("app.cli.admin.cli_auth") as mock_auth:
            admin_user = User(username="admin", role=UserRole.ADMIN)
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.admin.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Simulate large user base
                large_user_list = [
                    User(
                        id=i,
                        username=f"user{i}",
                        email=f"user{i}@example.com",
                        role=UserRole.USER,
                        is_active=True,
                    )
                    for i in range(1000)
                ]

                mock_db.query.return_value.order_by.return_value.all.return_value = (
                    large_user_list
                )

                start_time = time.time()

                result = runner.invoke(app, ["admin", "users"])

                execution_time = time.time() - start_time

                assert result.exit_code == 0
                assert execution_time < 3.0  # Should handle 1000 users within 3 seconds

    def test_system_stats_performance(self):
        """Test system stats performance."""
        import time

        runner = CliRunner()

        with patch("app.cli.admin.cli_auth") as mock_auth:
            admin_user = User(username="admin", role=UserRole.ADMIN)
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.admin.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Mock database queries with realistic large numbers
                mock_db.query.return_value.scalar.side_effect = [
                    10000,
                    9500,
                    100,
                    50,
                    1000,
                    500000,
                    2000000,
                ]
                mock_db.query.return_value.filter.return_value.scalar.side_effect = [
                    100,
                    50,
                ]

                start_time = time.time()

                result = runner.invoke(app, ["admin", "stats"])

                execution_time = time.time() - start_time

                assert result.exit_code == 0
                assert (
                    execution_time < 2.0
                )  # Should complete quickly even with large stats
