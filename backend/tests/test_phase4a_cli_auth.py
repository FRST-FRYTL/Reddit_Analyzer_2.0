"""Phase 4A CLI Authentication Tests."""

import pytest
import json
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from sqlalchemy.orm import Session

from app.cli.main import app
from app.cli.utils.auth_manager import CLIAuth
from app.models.user import User, UserRole


class TestCLIAuthManager:
    """Test CLI authentication manager."""

    @pytest.fixture
    def cli_auth(self, tmp_path):
        """Create CLI auth instance with temporary config directory."""
        with patch.object(CLIAuth, "__init__", lambda self: None):
            auth = CLIAuth()
            auth.config_dir = tmp_path / ".reddit-analyzer"
            auth.token_file = auth.config_dir / "tokens.json"
            auth.config_dir.mkdir(exist_ok=True)

            # Mock auth service
            auth.auth_service = MagicMock()
            return auth

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create test user."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
        )
        user.set_password("TestPassword123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_cli_auth_init(self):
        """Test CLI auth initialization."""
        with patch("app.cli.utils.auth_manager.get_auth_service") as mock_service:
            auth = CLIAuth()

            assert auth.config_dir.name == ".reddit-analyzer"
            assert auth.token_file.name == "tokens.json"
            assert auth.config_dir.exists()
            mock_service.assert_called_once()

    def test_store_tokens(self, cli_auth):
        """Test token storage."""
        tokens = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
        }

        cli_auth._store_tokens(tokens)

        # Check file exists and has correct permissions
        assert cli_auth.token_file.exists()
        assert oct(cli_auth.token_file.stat().st_mode)[-3:] == "600"

        # Check content
        with open(cli_auth.token_file, "r") as f:
            stored_tokens = json.load(f)

        assert stored_tokens == tokens

    def test_get_access_token(self, cli_auth):
        """Test access token retrieval."""
        # No token file
        assert cli_auth.get_access_token() is None

        # With token file
        tokens = {"access_token": "test_token", "refresh_token": "refresh_token"}
        cli_auth._store_tokens(tokens)

        assert cli_auth.get_access_token() == "test_token"

    def test_login_success(self, cli_auth, test_user):
        """Test successful login."""
        # Mock successful authentication
        cli_auth.auth_service.authenticate_user.return_value = test_user
        cli_auth.auth_service.create_tokens.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
        }

        with patch("app.cli.utils.auth_manager.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = cli_auth.login("testuser", "TestPassword123")

            assert result is True
            assert cli_auth.token_file.exists()

            # Verify tokens were stored
            with open(cli_auth.token_file, "r") as f:
                stored_tokens = json.load(f)
            assert "access_token" in stored_tokens

    def test_login_failure(self, cli_auth):
        """Test failed login."""
        # Mock failed authentication
        cli_auth.auth_service.authenticate_user.return_value = None

        with patch("app.cli.utils.auth_manager.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = cli_auth.login("wronguser", "wrongpassword")

            assert result is False
            assert not cli_auth.token_file.exists()

    def test_logout(self, cli_auth):
        """Test logout functionality."""
        # Create token file
        tokens = {"access_token": "test_token"}
        cli_auth._store_tokens(tokens)
        assert cli_auth.token_file.exists()

        # Logout
        result = cli_auth.logout()

        assert result is True
        assert not cli_auth.token_file.exists()

    def test_get_current_user(self, cli_auth, test_user):
        """Test getting current user."""
        # No token file
        assert cli_auth.get_current_user() is None

        # With valid token
        tokens = {"access_token": "valid_token"}
        cli_auth._store_tokens(tokens)
        cli_auth.auth_service.get_current_user.return_value = test_user

        with patch("app.cli.utils.auth_manager.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            user = cli_auth.get_current_user()

            assert user == test_user
            cli_auth.auth_service.get_current_user.assert_called_with(
                "valid_token", mock_db
            )

    def test_require_auth_decorator(self, cli_auth, test_user):
        """Test authentication requirement decorator."""

        @cli_auth.require_auth()
        def test_function():
            return "success"

        # No authentication
        cli_auth.get_current_user = MagicMock(return_value=None)

        with pytest.raises(SystemExit):
            test_function()

        # With authentication
        cli_auth.get_current_user = MagicMock(return_value=test_user)

        result = test_function()
        assert result == "success"

    def test_require_role_decorator(self, cli_auth):
        """Test role requirement decorator."""

        @cli_auth.require_auth(UserRole.ADMIN)
        def admin_function():
            return "admin_success"

        # User without admin role
        regular_user = User(username="regular", role=UserRole.USER)
        cli_auth.get_current_user = MagicMock(return_value=regular_user)
        cli_auth.auth_service.require_role.return_value = False

        with pytest.raises(SystemExit):
            admin_function()

        # User with admin role
        admin_user = User(username="admin", role=UserRole.ADMIN)
        cli_auth.get_current_user = MagicMock(return_value=admin_user)
        cli_auth.auth_service.require_role.return_value = True

        result = admin_function()
        assert result == "admin_success"


class TestCLIAuthCommands:
    """Test CLI authentication commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_cli_auth(self):
        """Mock CLI auth manager."""
        with patch("app.cli.auth.cli_auth") as mock_auth:
            yield mock_auth

    def test_login_command_success(self, mock_cli_auth):
        """Test successful login command."""
        mock_cli_auth.login.return_value = True

        result = self.runner.invoke(
            app, ["auth", "login", "--username", "testuser", "--password", "testpass"]
        )

        assert result.exit_code == 0
        mock_cli_auth.login.assert_called_once_with("testuser", "testpass")

    def test_login_command_failure(self, mock_cli_auth):
        """Test failed login command."""
        mock_cli_auth.login.return_value = False

        result = self.runner.invoke(
            app, ["auth", "login", "--username", "wronguser", "--password", "wrongpass"]
        )

        assert result.exit_code == 1
        mock_cli_auth.login.assert_called_once_with("wronguser", "wrongpass")

    def test_login_command_interactive(self, mock_cli_auth):
        """Test interactive login command."""
        mock_cli_auth.login.return_value = True

        # Test with input prompts
        result = self.runner.invoke(
            app, ["auth", "login"], input="testuser\\ntestpass\\n"
        )

        assert result.exit_code == 0
        mock_cli_auth.login.assert_called_once()

    def test_logout_command(self, mock_cli_auth):
        """Test logout command."""
        mock_cli_auth.logout.return_value = True

        result = self.runner.invoke(app, ["auth", "logout"])

        assert result.exit_code == 0
        mock_cli_auth.logout.assert_called_once()

    def test_status_command(self, mock_cli_auth):
        """Test status command."""
        result = self.runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        mock_cli_auth.auth_status.assert_called_once()

    def test_whoami_command_authenticated(self, mock_cli_auth):
        """Test whoami command when authenticated."""
        test_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
            comment_karma=100,
            link_karma=50,
        )
        test_user.id = 1

        mock_cli_auth.get_current_user.return_value = test_user

        result = self.runner.invoke(app, ["auth", "whoami"])

        assert result.exit_code == 0
        assert "testuser" in result.stdout
        assert "User" in result.stdout

    def test_whoami_command_not_authenticated(self, mock_cli_auth):
        """Test whoami command when not authenticated."""
        mock_cli_auth.get_current_user.return_value = None

        result = self.runner.invoke(app, ["auth", "whoami"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.stdout


class TestCLIAuthIntegration:
    """Integration tests for CLI authentication."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create test user."""
        user = User(
            username="integrationuser",
            email="integration@example.com",
            role=UserRole.USER,
            is_active=True,
        )
        user.set_password("IntegrationTest123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_full_auth_flow(self, test_user, tmp_path):
        """Test complete authentication flow through CLI."""
        with patch("app.cli.utils.auth_manager.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            # Override get_db to use test database
            with patch("app.cli.utils.auth_manager.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Mock auth service
                with patch(
                    "app.cli.utils.auth_manager.get_auth_service"
                ) as mock_auth_service:
                    mock_service = MagicMock()
                    mock_auth_service.return_value = mock_service
                    mock_service.authenticate_user.return_value = test_user
                    mock_service.create_tokens.return_value = {
                        "access_token": "test_token",
                        "refresh_token": "refresh_token",
                        "token_type": "bearer",
                    }

                    # Test login
                    result = self.runner.invoke(
                        app,
                        [
                            "auth",
                            "login",
                            "--username",
                            "integrationuser",
                            "--password",
                            "IntegrationTest123",
                        ],
                    )

                    assert result.exit_code == 0
                    assert "Logged in as integrationuser" in result.stdout

                    # Check token file was created
                    config_dir = tmp_path / ".reddit-analyzer"
                    token_file = config_dir / "tokens.json"
                    assert token_file.exists()

                    # Test status while logged in
                    mock_service.get_current_user.return_value = test_user

                    result = self.runner.invoke(app, ["auth", "status"])
                    assert result.exit_code == 0

                    # Test logout
                    result = self.runner.invoke(app, ["auth", "logout"])
                    assert result.exit_code == 0
                    assert "Logged out successfully" in result.stdout

                    # Check token file was removed
                    assert not token_file.exists()

    def test_main_status_command(self, test_user, tmp_path):
        """Test main status command with authentication."""
        with patch("app.cli.utils.auth_manager.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            with patch("app.cli.main.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.execute.return_value.scalar.return_value = 1

                with patch("app.cli.main.cli_auth") as mock_cli_auth:
                    mock_cli_auth.get_current_user.return_value = test_user

                    result = self.runner.invoke(app, ["status"])

                    assert result.exit_code == 0
                    assert "Reddit Analyzer Status" in result.stdout
                    assert "integrationuser" in result.stdout
                    assert "Database: Connected" in result.stdout


@pytest.mark.performance
class TestCLIAuthPerformance:
    """Performance tests for CLI authentication."""

    def test_login_performance(self):
        """Test login command performance."""
        import time

        runner = CliRunner()

        with patch("app.cli.auth.cli_auth") as mock_auth:
            mock_auth.login.return_value = True

            start_time = time.time()

            result = runner.invoke(
                app,
                ["auth", "login", "--username", "testuser", "--password", "testpass"],
            )

            execution_time = time.time() - start_time

            assert result.exit_code == 0
            assert execution_time < 2.0  # Should complete within 2 seconds

    def test_token_operations_performance(self, tmp_path):
        """Test token storage and retrieval performance."""
        import time

        with patch("app.cli.utils.auth_manager.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            auth = CLIAuth()
            tokens = {
                "access_token": "test_token",
                "refresh_token": "refresh_token",
                "token_type": "bearer",
            }

            # Test token storage performance
            start_time = time.time()
            for _ in range(100):
                auth._store_tokens(tokens)
            storage_time = time.time() - start_time

            assert storage_time < 1.0  # Should store 100 tokens quickly

            # Test token retrieval performance
            start_time = time.time()
            for _ in range(100):
                auth.get_access_token()
            retrieval_time = time.time() - start_time

            assert retrieval_time < 1.0  # Should retrieve 100 tokens quickly
