"""Main CLI application for Reddit Analyzer."""

import typer
from rich.console import Console

# Configure logging before importing other modules
from reddit_analyzer.cli.utils.logging_config import suppress_startup_warnings

suppress_startup_warnings()

from reddit_analyzer.cli.admin import admin_app  # noqa: E402
from reddit_analyzer.cli.auth import auth_app  # noqa: E402
from reddit_analyzer.cli.data import data_app  # noqa: E402
from reddit_analyzer.cli.nlp import nlp_app  # noqa: E402
from reddit_analyzer.cli.reports import report_app  # noqa: E402
from reddit_analyzer.cli.visualization import viz_app  # noqa: E402
from reddit_analyzer.cli.analyze import app as analyze_app  # noqa: E402

app = typer.Typer(
    name="reddit-analyzer",
    help="Reddit Analyzer CLI - Data exploration and visualization tool",
    add_completion=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()

# Global options
verbose_option = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
quiet_option = typer.Option(False, "--quiet", "-q", help="Suppress most output")


@app.callback()
def main_callback(
    verbose: bool = verbose_option,
    quiet: bool = quiet_option,
):
    """Configure global settings for the CLI."""
    from reddit_analyzer.cli.utils.logging_config import configure_cli_logging

    configure_cli_logging(verbose=verbose, quiet=quiet)


# Add command groups
app.add_typer(auth_app, name="auth")
app.add_typer(data_app, name="data")
app.add_typer(viz_app, name="viz")
app.add_typer(report_app, name="report")
app.add_typer(admin_app, name="admin")
app.add_typer(nlp_app, name="nlp")
app.add_typer(analyze_app, name="analyze")


@app.command()
def version():
    """Show version information."""
    console.print("🔍 Reddit Analyzer CLI v1.0.0", style="bold blue")
    console.print("Built with Python, Typer, and Rich", style="dim")


@app.command()
def status():
    """Show overall system status."""
    from reddit_analyzer.cli.utils.auth_manager import cli_auth

    console.print("📊 Reddit Analyzer Status", style="bold blue")

    # Check authentication status
    user = cli_auth.get_current_user()
    if user:
        console.print(
            f"👤 Logged in as: {user.username} ({user.role.value})", style="green"
        )
    else:
        console.print("🔐 Not authenticated", style="yellow")

    # Check database connection
    try:
        from reddit_analyzer.database import get_db
        from sqlalchemy import text

        db = next(get_db())
        db.execute(text("SELECT 1")).scalar()
        console.print("🗄️  Database: Connected", style="green")
    except Exception as e:
        console.print(f"🗄️  Database: Error - {e}", style="red")


if __name__ == "__main__":
    app()
