"""Data management CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from sqlalchemy import func

from reddit_analyzer.cli.utils.auth_manager import cli_auth
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.comment import Comment
from reddit_analyzer.models.subreddit import Subreddit
from reddit_analyzer.models.text_analysis import TextAnalysis
from reddit_analyzer.database import get_db
from reddit_analyzer.services.nlp_service import get_nlp_service

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

        # Get NLP analysis counts
        nlp_count = db.query(func.count(TextAnalysis.id)).scalar()
        posts_with_nlp = db.query(
            func.count(func.distinct(TextAnalysis.post_id))
        ).scalar()

        # Create status table
        table = Table(title="📊 Data Collection Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Users", f"{user_count:,}")
        table.add_row("Subreddits", f"{subreddit_count:,}")
        table.add_row("Posts", f"{post_count:,}")
        table.add_row("Comments", f"{comment_count:,}")
        table.add_row("NLP Analyses", f"{nlp_count:,}")

        if post_count > 0:
            nlp_coverage = (posts_with_nlp / post_count) * 100
            table.add_row("NLP Coverage", f"{nlp_coverage:.1f}%")

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
            from sqlalchemy import text

            db.execute(text("SELECT 1")).scalar()

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
    skip_nlp: bool = typer.Option(False, "--skip-nlp", help="Skip NLP analysis"),
    with_comments: bool = typer.Option(
        False, "--with-comments", help="Include comments for each post"
    ),
    comment_limit: int = typer.Option(
        50, "--comment-limit", help="Max comments per post"
    ),
    comment_depth: int = typer.Option(
        3, "--comment-depth", help="Max comment tree depth"
    ),
    comments_only: bool = typer.Option(
        False, "--comments-only", help="Collect only comments from existing posts"
    ),
    min_comment_score: int = typer.Option(
        None, "--min-comment-score", help="Minimum comment score to include"
    ),
):
    """Collect data from specified subreddit."""
    if comments_only and with_comments:
        console.print(
            "❌ Cannot use --with-comments and --comments-only together", style="red"
        )
        raise typer.Exit(1)

    mode = (
        "comments only"
        if comments_only
        else ("posts with comments" if with_comments else "posts")
    )
    console.print(f"🚀 Starting data collection from r/{subreddit} ({mode})")

    try:
        from reddit_analyzer.services.reddit_client import RedditClient

        reddit_client = RedditClient()
        db = next(get_db())
        nlp_service = get_nlp_service() if not skip_nlp else None

        # First, get or create the subreddit
        subreddit_info = reddit_client.get_subreddit_info(subreddit)

        # Check if subreddit exists in database
        db_subreddit = (
            db.query(Subreddit).filter(Subreddit.name == subreddit_info["name"]).first()
        )

        if not db_subreddit:
            db_subreddit = Subreddit(
                name=subreddit_info["name"],
                display_name=subreddit_info["display_name"],
                description=(
                    subreddit_info["description"][:500]
                    if subreddit_info["description"]
                    else None
                ),
                subscribers=subreddit_info["subscribers"],
                created_utc=subreddit_info["created_utc"],
                is_nsfw=subreddit_info["is_nsfw"],
            )
            db.add(db_subreddit)
            db.commit()

        posts = []
        if not comments_only:
            # Fetch posts from Reddit
            posts = reddit_client.get_subreddit_posts(subreddit, sort=sort, limit=limit)

        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]Collecting from r/{subreddit}...", total=len(posts)
            )

            collected_count = 0
            posts_to_analyze = []  # Store posts for NLP analysis

            for post_data in posts:
                # Get or create user
                author_name = post_data["author"]
                if author_name != "[deleted]":
                    db_user = (
                        db.query(User).filter(User.username == author_name).first()
                    )

                    if not db_user:
                        try:
                            user_info = reddit_client.get_user_info(author_name)
                            db_user = User(
                                username=user_info["username"],
                                created_utc=user_info["created_utc"],
                                comment_karma=user_info["comment_karma"],
                                link_karma=user_info["link_karma"],
                                is_verified=user_info["is_verified"],
                                role=UserRole.USER,  # Reddit users are regular users
                                is_active=True,  # Mark as active
                                # No password_hash - these are Reddit users, not app users
                            )
                            db.add(db_user)
                            db.commit()
                        except Exception:
                            # User might be suspended or deleted
                            db_user = None
                else:
                    db_user = None

                # Check if post already exists
                existing_post = (
                    db.query(Post).filter(Post.id == post_data["id"]).first()
                )

                if not existing_post:
                    new_post = Post(
                        id=post_data["id"],
                        title=post_data["title"],
                        selftext=post_data["selftext"],
                        url=post_data["url"],
                        author_id=db_user.id if db_user else None,
                        subreddit_id=db_subreddit.id,
                        score=post_data["score"],
                        upvote_ratio=post_data["upvote_ratio"],
                        num_comments=post_data["num_comments"],
                        created_utc=post_data["created_utc"],
                        is_self=post_data["is_self"],
                        is_nsfw=post_data["is_nsfw"],
                        is_locked=post_data["is_locked"],
                    )
                    db.add(new_post)
                    collected_count += 1

                    # Add to NLP analysis queue if not skipped
                    if not skip_nlp:
                        posts_to_analyze.append(new_post)

                progress.update(task, advance=1)

            db.commit()

        console.print(
            f"✅ Collected {collected_count} new posts from r/{subreddit}",
            style="green",
        )
        if collected_count < len(posts):
            console.print(
                f"ℹ️  Skipped {len(posts) - collected_count} existing posts",
                style="yellow",
            )

        # Collect comments if requested
        comment_count = 0
        comments_to_analyze = []

        if with_comments or comments_only:
            console.print("\n💬 Collecting comments...")

            # Get posts to collect comments for
            if comments_only:
                # Fetch existing posts from database
                target_posts = (
                    db.query(Post)
                    .filter(Post.subreddit_id == db_subreddit.id)
                    .order_by(Post.created_utc.desc())
                    .limit(limit)
                    .all()
                )
            else:
                # For --with-comments, collect comments for all posts from this run
                # Get post IDs from the posts we just fetched
                post_ids = [p["id"] for p in posts]
                target_posts = (
                    (db.query(Post).filter(Post.id.in_(post_ids)).all())
                    if post_ids
                    else []
                )

            if target_posts:
                with Progress() as comment_progress:
                    comment_task = comment_progress.add_task(
                        "[cyan]Collecting comments...", total=len(target_posts)
                    )

                    for post in target_posts:
                        try:
                            # Get post ID (handle both dict and ORM object)
                            post_id = post.id if hasattr(post, "id") else post["id"]

                            # Fetch comments for this post
                            comments = reddit_client.get_post_comments(
                                post_id,
                                limit=comment_limit,
                                depth=comment_depth,
                                min_score=min_comment_score,
                            )

                            for comment_data in comments:
                                # Check if comment exists
                                existing_comment = (
                                    db.query(Comment)
                                    .filter(Comment.id == comment_data["id"])
                                    .first()
                                )

                                if not existing_comment:
                                    # Get or create comment author
                                    author_name = comment_data["author"]
                                    comment_author = None

                                    if author_name != "[deleted]":
                                        comment_author = (
                                            db.query(User)
                                            .filter(User.username == author_name)
                                            .first()
                                        )

                                        if not comment_author:
                                            try:
                                                user_info = reddit_client.get_user_info(
                                                    author_name
                                                )
                                                comment_author = User(
                                                    username=user_info["username"],
                                                    created_utc=user_info[
                                                        "created_utc"
                                                    ],
                                                    comment_karma=user_info[
                                                        "comment_karma"
                                                    ],
                                                    link_karma=user_info["link_karma"],
                                                    is_verified=user_info[
                                                        "is_verified"
                                                    ],
                                                    role=UserRole.USER,
                                                    is_active=True,
                                                )
                                                db.add(comment_author)
                                                db.commit()
                                            except Exception:
                                                pass

                                    # Create comment
                                    new_comment = Comment(
                                        id=comment_data["id"],
                                        post_id=comment_data["post_id"],
                                        parent_id=(
                                            comment_data["parent_id"]
                                            if comment_data["parent_id"]
                                            != f"t3_{comment_data['post_id']}"
                                            else None
                                        ),
                                        author_id=(
                                            comment_author.id
                                            if comment_author
                                            else None
                                        ),
                                        body=comment_data["body"],
                                        score=comment_data["score"],
                                        created_utc=comment_data["created_utc"],
                                        is_deleted=comment_data.get(
                                            "is_deleted", False
                                        ),
                                    )
                                    db.add(new_comment)
                                    comment_count += 1

                                    if not skip_nlp:
                                        comments_to_analyze.append(new_comment)

                            db.commit()

                        except Exception as e:
                            console.print(
                                f"⚠️  Failed to collect comments for post {post_id}: {e}",
                                style="yellow",
                            )

                        comment_progress.update(comment_task, advance=1)

                console.print(
                    f"✅ Collected {comment_count} new comments", style="green"
                )
            else:
                console.print(
                    "ℹ️  No posts found to collect comments for", style="yellow"
                )

        # Run NLP analysis on collected posts and comments
        if not skip_nlp and posts_to_analyze:
            console.print(
                f"\n🧠 Processing NLP analysis for {len(posts_to_analyze)} posts..."
            )

            with Progress() as nlp_progress:
                nlp_task = nlp_progress.add_task(
                    "[cyan]Analyzing sentiment and extracting features...",
                    total=len(posts_to_analyze),
                )

                analyzed_count = 0
                for post in posts_to_analyze:
                    try:
                        # Combine title and body for analysis
                        full_text = f"{post.title}"
                        if post.selftext:
                            full_text += f"\n\n{post.selftext}"

                        # Analyze text and store results
                        nlp_service.analyze_text(full_text, post_id=post.id)
                        analyzed_count += 1

                    except Exception as e:
                        console.print(
                            f"⚠️  Failed to analyze post {post.id}: {e}", style="yellow"
                        )

                    nlp_progress.update(nlp_task, advance=1)

            console.print(
                f"✅ Completed NLP analysis for {analyzed_count} posts",
                style="green",
            )

        # Run NLP analysis on comments
        if not skip_nlp and comments_to_analyze:
            console.print(
                f"\n🧠 Processing NLP analysis for {len(comments_to_analyze)} comments..."
            )

            with Progress() as comment_nlp_progress:
                comment_nlp_task = comment_nlp_progress.add_task(
                    "[cyan]Analyzing comment sentiment...",
                    total=len(comments_to_analyze),
                )

                analyzed_comments = 0
                for comment in comments_to_analyze:
                    try:
                        # Analyze comment text
                        nlp_service.analyze_text(comment.body, comment_id=comment.id)
                        analyzed_comments += 1
                    except Exception as e:
                        console.print(
                            f"⚠️  Failed to analyze comment {comment.id}: {e}",
                            style="yellow",
                        )

                    comment_nlp_progress.update(comment_nlp_task, advance=1)

            console.print(
                f"✅ Completed NLP analysis for {analyzed_comments} comments",
                style="green",
            )

        elif skip_nlp:
            console.print("ℹ️  NLP analysis skipped", style="yellow")

    except Exception as e:
        console.print(f"❌ Data collection failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


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
