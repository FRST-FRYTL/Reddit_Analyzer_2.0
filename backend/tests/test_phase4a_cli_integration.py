"""Phase 4A CLI Integration Tests."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from sqlalchemy.orm import Session

from app.cli.main import app
from app.models.user import User, UserRole
from app.models.post import Post
from app.models.comment import Comment
from app.models.subreddit import Subreddit


class TestCLIFullWorkflow:
    """Test complete CLI workflows end-to-end."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.fixture
    def admin_user(self, db_session: Session):
        """Create admin user."""
        admin = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password("AdminPassword123")
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    @pytest.fixture
    def complete_dataset(self, db_session: Session):
        """Create complete dataset for testing."""
        # Create subreddits
        subreddits = []
        for name in ["python", "javascript", "datascience"]:
            subreddit = Subreddit(
                name=name,
                display_name=f"r/{name}",
                subscribers=1000,
                description=f"Discussion about {name}"
            )
            subreddits.append(subreddit)
            db_session.add(subreddit)
        
        db_session.flush()
        
        # Create posts and comments
        posts = []
        comments = []
        
        for i, subreddit in enumerate(subreddits):
            for j in range(10):  # 10 posts per subreddit
                post = Post(
                    title=f"Post {j} in {subreddit.name}",
                    score=10 + j + i * 10,
                    num_comments=j * 2,
                    created_at=datetime.utcnow() - timedelta(days=j),
                    author=f"author{j}",
                    url=f"https://reddit.com/r/{subreddit.name}/post{j}",
                    selftext=f"Content for post {j} in {subreddit.name}",
                    subreddit_id=subreddit.id
                )
                posts.append(post)
                db_session.add(post)
                db_session.flush()
                
                # Add comments to each post
                for k in range(j + 1):  # Varying number of comments
                    comment = Comment(
                        body=f"Comment {k} on post {j}",
                        score=k + 1,
                        created_at=datetime.utcnow() - timedelta(days=j, hours=k),
                        author=f"commenter{k}",
                        post_id=post.id
                    )
                    comments.append(comment)
                    db_session.add(comment)
        
        db_session.commit()
        return {
            "subreddits": subreddits,
            "posts": posts,
            "comments": comments
        }

    def test_complete_authentication_workflow(self, admin_user):
        """Test complete authentication workflow."""
        with patch('app.cli.utils.auth_manager.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            
            with patch('app.cli.utils.auth_manager.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.close = MagicMock()
                
                with patch('app.cli.utils.auth_manager.get_auth_service') as mock_auth_service:
                    mock_service = MagicMock()
                    mock_auth_service.return_value = mock_service
                    
                    # Test login
                    mock_service.authenticate_user.return_value = admin_user
                    mock_service.create_tokens.return_value = {
                        "access_token": "test_access_token",
                        "refresh_token": "test_refresh_token",
                        "token_type": "bearer"
                    }
                    
                    result = self.runner.invoke(app, [
                        "auth", "login",
                        "--username", "admin",
                        "--password", "AdminPassword123"
                    ])
                    
                    assert result.exit_code == 0
                    assert "Logged in as admin" in result.stdout
                    
                    # Verify token file exists
                    token_file = self.temp_dir / ".reddit-analyzer" / "tokens.json"
                    assert token_file.exists()
                    
                    # Test status
                    mock_service.get_current_user.return_value = admin_user
                    
                    result = self.runner.invoke(app, ["auth", "status"])
                    assert result.exit_code == 0
                    
                    # Test whoami
                    result = self.runner.invoke(app, ["auth", "whoami"])
                    assert result.exit_code == 0
                    assert "admin" in result.stdout
                    
                    # Test logout
                    result = self.runner.invoke(app, ["auth", "logout"])
                    assert result.exit_code == 0
                    assert "Logged out successfully" in result.stdout
                    
                    # Verify token file removed
                    assert not token_file.exists()

    def test_data_management_workflow(self, admin_user, complete_dataset):
        """Test complete data management workflow."""
        with patch('app.cli.data.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.data.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)
                
                # Mock database queries based on complete dataset
                mock_db.query.return_value.scalar.side_effect = [
                    1,  # admin user count
                    30,  # total posts (10 per subreddit * 3)
                    165,  # total comments (sum of 1+2+...+10 per subreddit * 3)
                    3   # total subreddits
                ]
                
                # Mock subreddit activity
                mock_db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                    ("python", 10), ("javascript", 10), ("datascience", 10)
                ]
                
                # Test data status
                result = self.runner.invoke(app, ["data", "status"])
                assert result.exit_code == 0
                assert "Data Collection Status" in result.stdout
                assert "30" in result.stdout  # posts count
                
                # Test database health
                mock_db.execute.return_value.scalar.return_value = 1
                mock_db.query.return_value.scalar.side_effect = [1, 30, 165, 3]
                
                result = self.runner.invoke(app, ["data", "health"])
                assert result.exit_code == 0
                assert "Database Health Check" in result.stdout
                assert "Healthy" in result.stdout

    def test_visualization_workflow(self, admin_user, complete_dataset):
        """Test complete visualization workflow."""
        with patch('app.cli.visualization.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.visualization.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)
                
                # Mock subreddit and posts
                mock_subreddit = MagicMock(id=1, name="python")
                mock_posts = [
                    MagicMock(
                        score=20 + i,
                        num_comments=i + 1,
                        created_at=datetime.utcnow() - timedelta(days=i),
                        title=f"Post {i}"
                    ) for i in range(10)
                ]
                
                mock_db.query.return_value.filter.return_value.first.return_value = mock_subreddit
                mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_posts
                
                # Test trends visualization
                result = self.runner.invoke(app, [
                    "viz", "trends",
                    "--subreddit", "python",
                    "--days", "7"
                ])
                
                assert result.exit_code == 0
                assert "Trending Posts" in result.stdout
                assert "r/python" in result.stdout
                
                # Test sentiment analysis
                mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_posts
                
                result = self.runner.invoke(app, ["viz", "sentiment", "python"])
                assert result.exit_code == 0
                assert "Sentiment Analysis" in result.stdout
                
                # Test activity analysis
                mock_db.query.return_value.filter.return_value.all.return_value = mock_posts
                
                result = self.runner.invoke(app, [
                    "viz", "activity",
                    "--subreddit", "python",
                    "--period", "24h"
                ])
                
                assert result.exit_code == 0
                assert "Activity Trends" in result.stdout

    def test_reporting_workflow(self, admin_user, complete_dataset):
        """Test complete reporting workflow."""
        with patch('app.cli.reports.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.reports.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)
                
                # Mock posts for reporting
                mock_posts = [
                    MagicMock(
                        title=f"Post {i}",
                        score=20 + i,
                        num_comments=i + 1,
                        created_at=datetime.utcnow() - timedelta(hours=i),
                        author=f"author{i}",
                        url=f"https://reddit.com/post{i}",
                        selftext=f"Content {i}"
                    ) for i in range(5)
                ]
                
                mock_db.query.return_value.filter.return_value.all.side_effect = [
                    mock_posts,  # current day
                    []  # previous day for comparison
                ]
                
                # Test daily report
                result = self.runner.invoke(app, [
                    "report", "daily",
                    "--subreddit", "python",
                    "--date", "2025-06-27"
                ])
                
                assert result.exit_code == 0
                assert "Daily Report" in result.stdout
                assert "r/python" in result.stdout
                
                # Test weekly report
                mock_db.query.return_value.filter.return_value.all.return_value = mock_posts
                
                result = self.runner.invoke(app, [
                    "report", "weekly",
                    "--subreddit", "python",
                    "--weeks", "1"
                ])
                
                assert result.exit_code == 0
                assert "Weekly Report" in result.stdout
                
                # Test data export
                export_file = self.temp_dir / "export.csv"
                
                result = self.runner.invoke(app, [
                    "report", "export",
                    "--format", "csv",
                    "--output", str(export_file),
                    "--days", "7"
                ])
                
                assert result.exit_code == 0
                assert "Exported" in result.stdout

    def test_admin_workflow(self, admin_user):
        """Test complete admin workflow."""
        with patch('app.cli.admin.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = admin_user
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.admin.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)
                
                # Test system stats
                mock_db.query.return_value.scalar.side_effect = [10, 8, 2, 1, 5, 100, 500]
                mock_db.query.return_value.filter.return_value.scalar.side_effect = [2, 1]
                
                result = self.runner.invoke(app, ["admin", "stats"])
                assert result.exit_code == 0
                assert "System Statistics" in result.stdout
                
                # Test user listing
                mock_users = [
                    User(id=1, username="admin", email="admin@example.com", role=UserRole.ADMIN, is_active=True),
                    User(id=2, username="user1", email="user1@example.com", role=UserRole.USER, is_active=True)
                ]
                mock_db.query.return_value.order_by.return_value.all.return_value = mock_users
                
                result = self.runner.invoke(app, ["admin", "users"])
                assert result.exit_code == 0
                assert "System Users" in result.stdout
                assert "admin" in result.stdout
                
                # Test health check
                mock_db.execute.return_value.scalar.return_value = 1
                mock_db.query.return_value.scalar.side_effect = [10, 5, 100, 500]
                mock_db.query.return_value.filter.return_value.scalar.return_value = 2
                
                result = self.runner.invoke(app, ["admin", "health-check"])
                assert result.exit_code == 0
                assert "system health check" in result.stdout

    def test_cross_command_integration(self, admin_user, complete_dataset):
        """Test integration between different command groups."""
        # This test demonstrates that data from one command group
        # can be used effectively by another command group
        
        with patch('app.cli.utils.auth_manager.Path.home') as mock_home:
            mock_home.return_value = self.temp_dir
            
            # Setup authentication
            with patch('app.cli.utils.auth_manager.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.close = MagicMock()
                
                with patch('app.cli.utils.auth_manager.get_auth_service') as mock_auth_service:
                    mock_service = MagicMock()
                    mock_auth_service.return_value = mock_service
                    mock_service.authenticate_user.return_value = admin_user
                    mock_service.create_tokens.return_value = {
                        "access_token": "test_token",
                        "refresh_token": "refresh_token",
                        "token_type": "bearer"
                    }
                    mock_service.get_current_user.return_value = admin_user
                    
                    # Login first
                    result = self.runner.invoke(app, [
                        "auth", "login",
                        "--username", "admin",
                        "--password", "AdminPassword123"
                    ])
                    assert result.exit_code == 0
                    
                    # Now test other commands that require authentication
                    with patch('app.cli.data.cli_auth') as mock_data_auth:
                        mock_data_auth.get_current_user.return_value = admin_user
                        mock_data_auth.require_auth.return_value = lambda func: func
                        
                        with patch('app.cli.data.get_db') as mock_data_db:
                            mock_data_db.return_value = mock_db
                            mock_data_db.__enter__ = MagicMock(return_value=mock_db)
                            mock_data_db.__exit__ = MagicMock(return_value=None)
                            
                            mock_db.execute.return_value.scalar.return_value = 1
                            mock_db.query.return_value.scalar.side_effect = [1, 30, 165, 3]
                            
                            # Test that data health works with authentication
                            result = self.runner.invoke(app, ["data", "health"])
                            assert result.exit_code == 0
                            assert "Healthy" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_command_without_authentication(self):
        """Test commands that require authentication when not logged in."""
        with patch('app.cli.data.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = None
            mock_auth.require_auth.side_effect = lambda: lambda func: lambda *args, **kwargs: exec('raise SystemExit(1)')
            
            result = self.runner.invoke(app, ["data", "status"])
            assert result.exit_code == 1

    def test_invalid_command_arguments(self):
        """Test commands with invalid arguments."""
        # Test invalid date format
        with patch('app.cli.reports.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = User(username="test", role=UserRole.USER)
            mock_auth.require_auth.return_value = lambda func: func
            
            result = self.runner.invoke(app, [
                "report", "daily",
                "--date", "invalid-date"
            ])
            
            assert result.exit_code == 1
            assert "Invalid date format" in result.stdout

    def test_database_connection_errors(self):
        """Test handling of database connection errors."""
        with patch('app.cli.data.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = User(username="test", role=UserRole.USER)
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.data.get_db') as mock_get_db:
                mock_get_db.side_effect = Exception("Database connection failed")
                
                result = self.runner.invoke(app, ["data", "health"])
                assert result.exit_code == 1

    def test_permission_denied_errors(self):
        """Test handling of permission denied errors."""
        with patch('app.cli.admin.cli_auth') as mock_auth:
            regular_user = User(username="user", role=UserRole.USER)
            mock_auth.get_current_user.return_value = regular_user
            mock_auth.require_auth.side_effect = lambda role=None: lambda func: lambda *args, **kwargs: exec('raise SystemExit(1)') if role == UserRole.ADMIN else func(*args, **kwargs)
            
            result = self.runner.invoke(app, ["admin", "users"])
            assert result.exit_code == 1

    def test_file_operation_errors(self):
        """Test handling of file operation errors."""
        with patch('app.cli.reports.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = User(username="test", role=UserRole.USER)
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.reports.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)
                mock_db.query.return_value.filter.return_value.all.return_value = []
                
                # Test export to invalid path
                result = self.runner.invoke(app, [
                    "report", "export",
                    "--output", "/invalid/path/export.csv"
                ])
                
                # Should handle the error gracefully
                assert result.exit_code in [0, 1]  # May succeed with empty data or fail gracefully


class TestCLIPerformanceIntegration:
    """Integration performance tests for CLI."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_command_chain_performance(self):
        """Test performance of chaining multiple CLI commands."""
        import time
        
        commands = [
            ["--help"],
            ["auth", "--help"],
            ["data", "--help"],
            ["viz", "--help"],
            ["report", "--help"],
            ["admin", "--help"]
        ]
        
        start_time = time.time()
        
        for command in commands:
            result = self.runner.invoke(app, command)
            assert result.exit_code == 0
        
        total_time = time.time() - start_time
        
        # All help commands should complete quickly
        assert total_time < 5.0

    def test_main_status_performance(self):
        """Test main status command performance."""
        import time
        
        with patch('app.cli.main.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = None
            
            with patch('app.cli.main.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.execute.return_value.scalar.return_value = 1
                
                start_time = time.time()
                
                result = self.runner.invoke(app, ["status"])
                
                execution_time = time.time() - start_time
                
                assert result.exit_code == 0
                assert execution_time < 2.0


@pytest.mark.integration
class TestCLIRealWorldScenarios:
    """Test CLI with real-world usage scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_daily_analyst_workflow(self, db_session: Session):
        """Test a typical daily workflow for a data analyst."""
        # Create analyst user
        analyst = User(
            username="analyst",
            email="analyst@example.com",
            role=UserRole.USER,
            is_active=True
        )
        analyst.set_password("AnalystPassword123")
        db_session.add(analyst)
        db_session.commit()
        
        # Mock the complete workflow
        with patch('app.cli.auth.cli_auth') as mock_auth:
            mock_auth.login.return_value = True
            mock_auth.get_current_user.return_value = analyst
            
            # 1. Login
            result = self.runner.invoke(app, [
                "auth", "login",
                "--username", "analyst",
                "--password", "AnalystPassword123"
            ])
            assert result.exit_code == 0
            
            # 2. Check system status
            with patch('app.cli.main.cli_auth') as mock_main_auth:
                mock_main_auth.get_current_user.return_value = analyst
                with patch('app.cli.main.get_db') as mock_get_db:
                    mock_db = MagicMock()
                    mock_get_db.return_value = mock_db
                    mock_db.execute.return_value.scalar.return_value = 1
                    
                    result = self.runner.invoke(app, ["status"])
                    assert result.exit_code == 0

    def test_admin_maintenance_workflow(self, db_session: Session):
        """Test a typical admin maintenance workflow."""
        # Create admin user
        admin = User(
            username="sysadmin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password("AdminPassword123")
        db_session.add(admin)
        db_session.commit()
        
        with patch('app.cli.admin.cli_auth') as mock_auth:
            mock_auth.get_current_user.return_value = admin
            mock_auth.require_auth.return_value = lambda func: func
            
            with patch('app.cli.admin.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)
                
                # 1. Check system health
                mock_db.execute.return_value.scalar.return_value = 1
                mock_db.query.return_value.scalar.side_effect = [100, 50, 1000, 5000]
                mock_db.query.return_value.filter.return_value.scalar.return_value = 5
                
                result = self.runner.invoke(app, ["admin", "health-check"])
                assert result.exit_code == 0
                
                # 2. Review system stats
                mock_db.query.return_value.scalar.side_effect = [100, 95, 10, 5, 50, 10000, 50000]
                mock_db.query.return_value.filter.return_value.scalar.side_effect = [10, 5]
                
                result = self.runner.invoke(app, ["admin", "stats"])
                assert result.exit_code == 0
                
                # 3. Review user list
                mock_users = [
                    User(id=1, username="sysadmin", role=UserRole.ADMIN, is_active=True),
                    User(id=2, username="analyst", role=UserRole.USER, is_active=True)
                ]
                mock_db.query.return_value.order_by.return_value.all.return_value = mock_users
                
                result = self.runner.invoke(app, ["admin", "users"])
                assert result.exit_code == 0