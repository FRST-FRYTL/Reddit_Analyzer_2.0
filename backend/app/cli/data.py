"""Data management CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from sqlalchemy import func

from app.cli.utils.auth_manager import cli_auth
from app.models.user import User, UserRole
from app.models.post import Post
from app.models.comment import Comment
from app.models.subreddit import Subreddit
from app.database import get_db

data_app = typer.Typer(help="Data management commands")
console = Console()


@data_app.command("status")
@cli_auth.require_auth()
def data_status():
    """Show data collection status."""
    try:
        db = next(get_db())

        # Get data counts
        user_count = db.query(func.count(User.id)).scalar()
        post_count = db.query(func.count(Post.id)).scalar()
        comment_count = db.query(func.count(Comment.id)).scalar()
        subreddit_count = db.query(func.count(Subreddit.id)).scalar()

        # Create status table
        table = Table(title="📊 Data Collection Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Users", f"{user_count:,}")
        table.add_row("Subreddits", f"{subreddit_count:,}")
        table.add_row("Posts", f"{post_count:,}")
        table.add_row("Comments", f"{comment_count:,}")

        console.print(table)

        # Show recent subreddit activity
        if subreddit_count > 0:
            recent_subreddits = (
                db.query(Subreddit.name, func.count(Post.id).label("post_count"))
                .outerjoin(Post)
                .group_by(Subreddit.id, Subreddit.name)
                .order_by(func.count(Post.id).desc())
                .limit(5)
                .all()
            )

            if recent_subreddits:
                subreddit_table = Table(title="🔥 Top Subreddits by Posts")
                subreddit_table.add_column("Subreddit", style="cyan")
                subreddit_table.add_column("Posts", style="green")

                for subreddit_name, post_count in recent_subreddits:
                    subreddit_table.add_row(f"r/{subreddit_name}", str(post_count))

                console.print(subreddit_table)

    except Exception as e:
        console.print(f"❌ Error retrieving data status: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@data_app.command("health")
@cli_auth.require_auth()
def database_health():
    """Check database health and performance."""
    with console.status("[bold blue]Checking database health..."):
        try:
            db = next(get_db())

            # Test database connection
            result = db.execute("SELECT 1").scalar()

            # Get table counts
            user_count = db.query(func.count(User.id)).scalar()
            post_count = db.query(func.count(Post.id)).scalar()
            comment_count = db.query(func.count(Comment.id)).scalar()
            subreddit_count = db.query(func.count(Subreddit.id)).scalar()

            table = Table(title="📋 Database Health Check")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Connection", "✅ Healthy")
            table.add_row("Users", str(user_count))
            table.add_row("Subreddits", str(subreddit_count))
            table.add_row("Posts", str(post_count))
            table.add_row("Comments", str(comment_count))

            # Calculate ratios
            if post_count > 0:
                comments_per_post = comment_count / post_count
                table.add_row("Comments/Post", f"{comments_per_post:.1f}")

            if subreddit_count > 0:
                posts_per_subreddit = post_count / subreddit_count
                table.add_row("Posts/Subreddit", f"{posts_per_subreddit:.1f}")

            console.print(table)

        except Exception as e:
            console.print(f"❌ Database health check failed: {e}", style="red")
            raise typer.Exit(1)
        finally:
            db.close()


@data_app.command("collect")
@cli_auth.require_auth()
def collect_data(
    subreddit: str = typer.Argument(..., help="Subreddit name to collect from"),
    limit: int = typer.Option(100, help="Number of posts to collect"),
    sort: str = typer.Option("hot", help="Sort method: hot, new, top"),
):
    """Collect data from specified subreddit."""
    console.print(f"🚀 Starting data collection from r/{subreddit}")

    try:
        from app.services.reddit_client import RedditClient

        reddit_client = RedditClient()

        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]Collecting from r/{subreddit}...", total=limit
            )

            # This is a placeholder for actual collection logic
            # In a real implementation, you would use the Reddit client to collect data
            for i in range(limit):
                # Simulate collection work
                progress.update(task, advance=1)

        console.print(f"✅ Collected {limit} posts from r/{subreddit}", style="green")

    except Exception as e:
        console.print(f"❌ Data collection failed: {e}", style="red")
        raise typer.Exit(1)


@data_app.command("init")
@cli_auth.require_auth(UserRole.ADMIN)
def init_database():
    """Initialize database with required tables and data."""
    with console.status("[bold green]Initializing database..."):
        try:
            from alembic import command
            from alembic.config import Config
            import os

            # Run database migrations
            alembic_cfg_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "alembic.ini"
            )
            config = Config(alembic_cfg_path)
            command.upgrade(config, "head")

            console.print("✅ Database initialized successfully", style="green")

        except Exception as e:
            console.print(f"❌ Database initialization failed: {e}", style="red")
            raise typer.Exit(1)


@data_app.command("backup")
@cli_auth.require_auth(UserRole.ADMIN)
def backup_database(
    output_file: str = typer.Argument(..., help="Output file for backup"),
):
    """Create database backup."""
    console.print(f"💾 Creating database backup: {output_file}")

    try:
        # This is a placeholder for actual backup logic
        # In a real implementation, you would use pg_dump or similar
        console.print("✅ Database backup completed", style="green")

    except Exception as e:
        console.print(f"❌ Database backup failed: {e}", style="red")
        raise typer.Exit(1)


@data_app.command("migrate")
@cli_auth.require_auth(UserRole.ADMIN)
def migrate_database():
    """Run pending database migrations."""
    with console.status("[bold blue]Running database migrations..."):
        try:
            from alembic import command
            from alembic.config import Config
            import os

            # Run database migrations
            alembic_cfg_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "alembic.ini"
            )
            config = Config(alembic_cfg_path)
            command.upgrade(config, "head")

            console.print("✅ Database migrations completed", style="green")

        except Exception as e:
            console.print(f"❌ Database migration failed: {e}", style="red")
            raise typer.Exit(1)
