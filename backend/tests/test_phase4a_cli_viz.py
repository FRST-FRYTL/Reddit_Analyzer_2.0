"""Phase 4A CLI Visualization Tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from sqlalchemy.orm import Session

from app.cli.main import app
from app.cli.utils.ascii_charts import ASCIIVisualizer
from app.models.user import User, UserRole
from app.models.post import Post
from app.models.subreddit import Subreddit


class TestASCIIVisualizer:
    """Test ASCII visualization utilities."""

    def setup_method(self):
        """Set up test environment."""
        self.visualizer = ASCIIVisualizer()

    def test_sentiment_bar_chart(self):
        """Test sentiment bar chart generation."""
        data = {"positive": 150, "neutral": 80, "negative": 20}

        chart = self.visualizer.sentiment_bar_chart(data, "Test Sentiment")

        assert chart.title == "Test Sentiment"
        # Should have all sentiment categories
        chart_str = str(chart)
        assert "Positive" in chart_str
        assert "Neutral" in chart_str
        assert "Negative" in chart_str
        assert "60.0%" in chart_str  # 150/250 = 60%

    def test_horizontal_bar_chart(self):
        """Test horizontal bar chart generation."""
        data = {"Item A": 100, "Item B": 75, "Item C": 50}

        chart = self.visualizer.horizontal_bar_chart(data, "Test Chart")

        assert chart.title == "Test Chart"
        chart_str = str(chart)
        assert "Item A" in chart_str
        assert "100" in chart_str

    def test_trend_line_chart(self):
        """Test trend line chart generation."""
        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        values = [10, 20, 15]

        chart = self.visualizer.trend_line_chart(dates, values, "Test Trend")

        assert chart.title == "Test Trend"
        chart_str = str(chart)
        assert "10.0 - 20.0" in chart_str  # Range should be displayed

    def test_trend_line_chart_empty_data(self):
        """Test trend line chart with empty data."""
        chart = self.visualizer.trend_line_chart([], [], "Empty Data")

        assert "No data available" in str(chart)

    def test_trend_line_chart_same_values(self):
        """Test trend line chart with same values."""
        dates = ["2025-01-01", "2025-01-02"]
        values = [10, 10]

        chart = self.visualizer.trend_line_chart(dates, values, "Same Values")

        # Should handle case where all values are the same
        assert chart.title == "Same Values"

    def test_activity_heatmap(self):
        """Test activity heatmap generation."""
        data = {
            "Mon": {"00": 5, "01": 3, "02": 1},
            "Tue": {"00": 8, "01": 6, "02": 2},
            "Wed": {"00": 4, "01": 7, "02": 3},
        }

        heatmap = self.visualizer.activity_heatmap(data, "Test Heatmap")

        assert heatmap.title == "Test Heatmap"
        heatmap_str = str(heatmap)
        assert "Mon" in heatmap_str

    def test_activity_heatmap_empty_data(self):
        """Test activity heatmap with empty data."""
        heatmap = self.visualizer.activity_heatmap({}, "Empty Heatmap")

        assert "No data available" in str(heatmap)

    def test_create_summary_table(self):
        """Test summary table creation."""
        data = {
            "total_posts": 100,
            "avg_score": 15.5,
            "max_comments": 50,
            "status": "active",
        }

        table = self.visualizer.create_summary_table(data, "Test Summary")

        assert table.title == "Test Summary"
        table_str = str(table)
        assert "Total Posts" in table_str
        assert "100" in table_str
        assert "15.50" in table_str  # Float formatting
        assert "50" in table_str  # Int formatting

    def test_progress_bar_ascii(self):
        """Test ASCII progress bar."""
        # Test normal progress
        progress = self.visualizer.progress_bar_ascii(25, 100, 20)
        assert "25.0%" in progress
        assert "25/100" in progress
        assert "█" in progress  # Should have filled portion
        assert "░" in progress  # Should have empty portion

        # Test zero total
        progress = self.visualizer.progress_bar_ascii(0, 0, 20)
        assert "0.0%" in progress

        # Test complete progress
        progress = self.visualizer.progress_bar_ascii(100, 100, 20)
        assert "100.0%" in progress

    def test_export_chart(self, tmp_path):
        """Test chart export functionality."""
        data = {"A": 10, "B": 20, "C": 15}
        filename = tmp_path / "test_chart.png"

        with patch("matplotlib.pyplot.savefig") as mock_savefig:
            with patch("matplotlib.pyplot.close") as mock_close:
                self.visualizer.export_chart(data, "bar", str(filename), "Test Chart")

                mock_savefig.assert_called_once_with(
                    str(filename), dpi=300, bbox_inches="tight"
                )
                mock_close.assert_called_once()

    def test_export_chart_error(self, tmp_path):
        """Test chart export with error."""
        data = {"A": 10, "B": 20}
        filename = tmp_path / "test_chart.png"

        with patch("matplotlib.pyplot.savefig", side_effect=Exception("Export failed")):
            # Should handle export error gracefully
            self.visualizer.export_chart(data, "bar", str(filename))


class TestCLIVisualizationCommands:
    """Test CLI visualization commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_auth(self):
        """Mock CLI authentication."""
        with patch("app.cli.visualization.cli_auth") as mock_auth:
            test_user = User(username="testuser", role=UserRole.USER, is_active=True)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = lambda func: func
            yield mock_auth

    @pytest.fixture
    def sample_data(self, db_session: Session):
        """Create sample data for visualization tests."""
        # Create subreddit
        subreddit = Subreddit(name="python", display_name="r/Python")
        db_session.add(subreddit)
        db_session.flush()

        # Create posts with varying scores and dates
        posts = []
        for i in range(10):
            post = Post(
                title=f"Test Post {i}",
                score=10 + i * 5,
                num_comments=5 + i,
                created_at=datetime.utcnow() - timedelta(days=i % 7),
                author=f"author{i}",
                url=f"https://reddit.com/r/python/post{i}",
                subreddit_id=subreddit.id,
            )
            posts.append(post)
            db_session.add(post)

        db_session.commit()
        return {"subreddit": subreddit, "posts": posts}

    def test_trends_command(self, mock_auth, sample_data):
        """Test trends visualization command."""
        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock database queries
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = sample_data[
                "posts"
            ]
            mock_db.query.return_value.filter.return_value.first.return_value = (
                sample_data["subreddit"]
            )

            result = self.runner.invoke(
                app, ["viz", "trends", "--subreddit", "python", "--days", "7"]
            )

            assert result.exit_code == 0
            assert "Trending Posts" in result.stdout
            assert "r/python" in result.stdout

    def test_trends_command_no_subreddit(self, mock_auth):
        """Test trends command without specific subreddit."""
        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock posts from all subreddits
            mock_posts = [
                MagicMock(
                    score=50,
                    created_at=datetime.utcnow(),
                    title="Test Post",
                    num_comments=10,
                ),
                MagicMock(
                    score=30,
                    created_at=datetime.utcnow() - timedelta(days=1),
                    title="Another Post",
                    num_comments=5,
                ),
            ]
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_posts

            result = self.runner.invoke(app, ["viz", "trends", "--days", "3"])

            assert result.exit_code == 0
            assert "All Subreddits" in result.stdout

    def test_trends_command_with_export(self, mock_auth, tmp_path):
        """Test trends command with export option."""
        export_file = tmp_path / "trends.png"

        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_posts = [
                MagicMock(
                    score=50,
                    created_at=datetime.utcnow(),
                    title="Test",
                    num_comments=10,
                )
            ]
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_posts
            mock_db.query.return_value.filter.return_value.first.return_value = (
                MagicMock(id=1, name="python")
            )

            with patch("app.cli.visualization.visualizer.export_chart") as mock_export:
                result = self.runner.invoke(
                    app,
                    [
                        "viz",
                        "trends",
                        "--subreddit",
                        "python",
                        "--export",
                        str(export_file),
                    ],
                )

                assert result.exit_code == 0
                mock_export.assert_called_once()

    def test_sentiment_command(self, mock_auth, sample_data):
        """Test sentiment analysis command."""
        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_db.query.return_value.filter.return_value.first.return_value = (
                sample_data["subreddit"]
            )
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = sample_data[
                "posts"
            ]

            result = self.runner.invoke(app, ["viz", "sentiment", "python"])

            assert result.exit_code == 0
            assert "Sentiment Analysis" in result.stdout
            assert "r/python" in result.stdout

    def test_sentiment_command_subreddit_not_found(self, mock_auth):
        """Test sentiment command with non-existent subreddit."""
        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = self.runner.invoke(app, ["viz", "sentiment", "nonexistent"])

            assert result.exit_code == 1
            assert "not found" in result.stdout

    def test_activity_command(self, mock_auth, sample_data):
        """Test activity visualization command."""
        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_db.query.return_value.filter.return_value.first.return_value = (
                sample_data["subreddit"]
            )
            mock_db.query.return_value.filter.return_value.all.return_value = (
                sample_data["posts"]
            )

            result = self.runner.invoke(
                app, ["viz", "activity", "--subreddit", "python", "--period", "24h"]
            )

            assert result.exit_code == 0
            assert "Activity Trends" in result.stdout
            assert "r/python" in result.stdout

    def test_activity_command_invalid_period(self, mock_auth):
        """Test activity command with invalid period."""
        result = self.runner.invoke(app, ["viz", "activity", "--period", "invalid"])

        assert result.exit_code == 1
        assert "Invalid period" in result.stdout

    def test_subreddit_compare_command(self, mock_auth):
        """Test subreddit comparison command."""
        with patch("app.cli.visualization.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock subreddit lookups
            mock_subreddit1 = MagicMock(id=1, name="python")
            mock_subreddit2 = MagicMock(id=2, name="javascript")
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_subreddit1,
                mock_subreddit2,
            ]

            # Mock posts for each subreddit
            mock_posts1 = [MagicMock(score=10, num_comments=5) for _ in range(5)]
            mock_posts2 = [MagicMock(score=15, num_comments=8) for _ in range(3)]
            mock_db.query.return_value.filter.return_value.all.side_effect = [
                mock_posts1,
                mock_posts2,
            ]

            result = self.runner.invoke(
                app,
                [
                    "viz",
                    "subreddit-compare",
                    "python,javascript",
                    "--metric",
                    "posts",
                    "--days",
                    "7",
                ],
            )

            assert result.exit_code == 0
            assert "Subreddit Comparison" in result.stdout

    def test_subreddit_compare_insufficient_subreddits(self, mock_auth):
        """Test subreddit comparison with insufficient subreddits."""
        result = self.runner.invoke(app, ["viz", "subreddit-compare", "python"])

        assert result.exit_code == 1
        assert "at least 2 subreddits" in result.stdout

    def test_visualization_no_auth(self):
        """Test visualization commands without authentication."""
        with patch("app.cli.visualization.cli_auth") as mock_auth:
            mock_auth.get_current_user.return_value = None
            mock_auth.require_auth.side_effect = (
                lambda: lambda func: lambda *args, **kwargs: exec("raise SystemExit(1)")
            )

            result = self.runner.invoke(app, ["viz", "trends"])
            assert result.exit_code == 1


class TestCLIReportingCommands:
    """Test CLI reporting commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_auth(self):
        """Mock CLI authentication."""
        with patch("app.cli.reports.cli_auth") as mock_auth:
            test_user = User(username="testuser", role=UserRole.USER, is_active=True)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = lambda func: func
            yield mock_auth

    def test_daily_report_command(self, mock_auth):
        """Test daily report generation."""
        with patch("app.cli.reports.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            # Mock posts for the day
            mock_posts = [
                MagicMock(
                    title="Post 1",
                    score=50,
                    num_comments=10,
                    created_at=datetime.utcnow(),
                ),
                MagicMock(
                    title="Post 2",
                    score=30,
                    num_comments=5,
                    created_at=datetime.utcnow(),
                ),
            ]
            mock_db.query.return_value.filter.return_value.all.side_effect = [
                mock_posts,
                [],
            ]  # current and previous day

            result = self.runner.invoke(
                app,
                ["report", "daily", "--subreddit", "python", "--date", "2025-06-27"],
            )

            assert result.exit_code == 0
            assert "Daily Report" in result.stdout
            assert "r/python" in result.stdout

    def test_weekly_report_command(self, mock_auth):
        """Test weekly report generation."""
        with patch("app.cli.reports.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_posts = [
                MagicMock(
                    score=i * 10,
                    num_comments=i * 2,
                    created_at=datetime.utcnow() - timedelta(days=i),
                )
                for i in range(7)
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = mock_posts

            result = self.runner.invoke(app, ["report", "weekly", "--weeks", "2"])

            assert result.exit_code == 0
            assert "Weekly Report" in result.stdout

    def test_export_data_csv(self, mock_auth, tmp_path):
        """Test data export in CSV format."""
        output_file = tmp_path / "export.csv"

        with patch("app.cli.reports.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_posts = [
                MagicMock(
                    title="Test Post",
                    score=50,
                    num_comments=10,
                    created_at=datetime.utcnow(),
                    author="testuser",
                    url="https://reddit.com/test",
                    selftext="Test content",
                )
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = mock_posts

            result = self.runner.invoke(
                app,
                [
                    "report",
                    "export",
                    "--format",
                    "csv",
                    "--output",
                    str(output_file),
                    "--days",
                    "7",
                ],
            )

            assert result.exit_code == 0
            assert "Exported" in result.stdout
            assert output_file.exists()

    def test_export_data_json(self, mock_auth, tmp_path):
        """Test data export in JSON format."""
        output_file = tmp_path / "export.json"

        with patch("app.cli.reports.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=None)

            mock_posts = [
                MagicMock(
                    title="Test Post",
                    score=50,
                    num_comments=10,
                    created_at=datetime.utcnow(),
                    author="testuser",
                    url="https://reddit.com/test",
                    selftext="Test content",
                )
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = mock_posts

            result = self.runner.invoke(
                app,
                ["report", "export", "--format", "json", "--output", str(output_file)],
            )

            assert result.exit_code == 0
            assert "Exported" in result.stdout
            assert output_file.exists()

    def test_schedule_report_command(self, mock_auth):
        """Test report scheduling command."""
        result = self.runner.invoke(
            app,
            [
                "report",
                "schedule",
                "--frequency",
                "weekly",
                "--subreddit",
                "python",
                "--email",
                "test@example.com",
            ],
        )

        assert result.exit_code == 0
        assert "Scheduling weekly reports" in result.stdout
        assert "requires additional setup" in result.stdout


@pytest.mark.performance
class TestCLIVisualizationPerformance:
    """Performance tests for CLI visualization commands."""

    def test_trends_command_performance(self):
        """Test trends command performance with large dataset."""
        import time

        runner = CliRunner()

        with patch("app.cli.visualization.cli_auth") as mock_auth:
            test_user = User(username="testuser", role=UserRole.USER)
            mock_auth.get_current_user.return_value = test_user
            mock_auth.require_auth.return_value = lambda func: func

            with patch("app.cli.visualization.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=None)

                # Simulate large dataset
                large_posts = [
                    MagicMock(
                        score=i,
                        created_at=datetime.utcnow() - timedelta(hours=i % 24),
                        title=f"Post {i}",
                        num_comments=i % 100,
                    )
                    for i in range(1000)
                ]

                mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = large_posts

                start_time = time.time()

                result = runner.invoke(app, ["viz", "trends", "--days", "7"])

                execution_time = time.time() - start_time

                assert result.exit_code == 0
                assert (
                    execution_time < 3.0
                )  # Should handle large datasets within 3 seconds

    def test_ascii_chart_generation_performance(self):
        """Test ASCII chart generation performance."""
        import time

        visualizer = ASCIIVisualizer()

        # Large dataset for chart generation
        large_data = {f"Item {i}": i * 10 for i in range(100)}

        start_time = time.time()

        for _ in range(50):
            chart = visualizer.horizontal_bar_chart(large_data, "Performance Test")

        generation_time = time.time() - start_time

        assert generation_time < 2.0  # Should generate 50 charts quickly
