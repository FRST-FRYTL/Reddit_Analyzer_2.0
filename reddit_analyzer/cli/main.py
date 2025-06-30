"""Main CLI application for Reddit Analyzer."""

import typer
from rich.console import Console

from reddit_analyzer.cli.auth import auth_app
from reddit_analyzer.cli.data import data_app
from reddit_analyzer.cli.visualization import viz_app
from reddit_analyzer.cli.reports import report_app
from reddit_analyzer.cli.admin import admin_app
from reddit_analyzer.cli.nlp import nlp_app

app = typer.Typer(
    name="reddit-analyzer",
    help="Reddit Analyzer CLI - Data exploration and visualization tool",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()

# Add command groups
app.add_typer(auth_app, name="auth")
app.add_typer(data_app, name="data")
app.add_typer(viz_app, name="viz")
app.add_typer(report_app, name="report")
app.add_typer(admin_app, name="admin")
app.add_typer(nlp_app, name="nlp")


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
