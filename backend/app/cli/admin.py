"""Admin CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional
from sqlalchemy import func
import secrets

from app.cli.utils.auth_manager import cli_auth
from app.cli.utils.ascii_charts import ASCIIVisualizer
from app.models.user import User, UserRole
from app.models.post import Post
from app.models.comment import Comment
from app.models.subreddit import Subreddit
from app.database import get_db

admin_app = typer.Typer(help="Admin commands (requires admin role)")
console = Console()
visualizer = ASCIIVisualizer()


@admin_app.command("users")
@cli_auth.require_auth(UserRole.ADMIN)
def list_users(
    role: Optional[str] = typer.Option(None, help="Filter by role: user, moderator, admin"),
    active: Optional[bool] = typer.Option(None, help="Filter by active status")
):
    """List all users in the system."""
    try:
        db = next(get_db())
        
        query = db.query(User)
        
        if role:
            try:
                user_role = UserRole(role.lower())
                query = query.filter(User.role == user_role)
            except ValueError:
                console.print(f"❌ Invalid role: {role}", style="red")
                raise typer.Exit(1)
        
        if active is not None:
            query = query.filter(User.is_active == active)
        
        users = query.order_by(User.id).all()
        
        if not users:
            console.print("👥 No users found", style="yellow")
            return
        
        # Create users table
        table = Table(title="👥 System Users")
        table.add_column("ID", style="yellow")
        table.add_column("Username", style="cyan")
        table.add_column("Email", style="blue")
        table.add_column("Role", style="green")
        table.add_column("Active", style="magenta")
        table.add_column("Verified", style="white")
        
        for user in users:
            table.add_row(
                str(user.id),
                user.username,
                user.email or "Not set",
                user.role.value.title(),
                "✅" if user.is_active else "❌",
                "✅" if user.is_verified else "❌"
            )
        
        console.print(table)
        
        # Summary
        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active)
        console.print(f"\n📊 Total: {total_users} users, {active_users} active", style="dim")
        
    except Exception as e:
        console.print(f"❌ Error listing users: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@admin_app.command("create-user")
@cli_auth.require_auth(UserRole.ADMIN)
def create_user(
    username: str = typer.Option(..., help="Username for new user"),
    email: Optional[str] = typer.Option(None, help="Email address"),
    role: str = typer.Option("user", help="User role: user, moderator, admin"),
    generate_password: bool = typer.Option(False, help="Generate random password")
):
    """Create a new user account."""
    try:
        db = next(get_db())
        
        # Validate role
        try:
            user_role = UserRole(role.lower())
        except ValueError:
            console.print(f"❌ Invalid role: {role}", style="red")
            raise typer.Exit(1)
        
        # Check if username exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            console.print(f"❌ Username '{username}' already exists", style="red")
            raise typer.Exit(1)
        
        # Check if email exists (if provided)
        if email:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                console.print(f"❌ Email '{email}' already exists", style="red")
                raise typer.Exit(1)
        
        # Generate or prompt for password
        if generate_password:
            password = secrets.token_urlsafe(16)
            console.print(f"🔐 Generated password: {password}", style="yellow")
        else:
            password = Prompt.ask("Password", password=True)
            if not password:
                console.print("❌ Password cannot be empty", style="red")
                raise typer.Exit(1)
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            role=user_role,
            is_active=True
        )
        new_user.set_password(password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        console.print(f"✅ Created user '{username}' with role '{role}'", style="green")
        
        # Show user details
        user_table = Table(title="👤 New User Details")
        user_table.add_column("Field", style="cyan")
        user_table.add_column("Value", style="green")
        
        user_table.add_row("ID", str(new_user.id))
        user_table.add_row("Username", new_user.username)
        user_table.add_row("Email", new_user.email or "Not set")
        user_table.add_row("Role", new_user.role.value.title())
        user_table.add_row("Active", "Yes")
        
        console.print(user_table)
        
    except Exception as e:
        console.print(f"❌ Error creating user: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@admin_app.command("update-role")
@cli_auth.require_auth(UserRole.ADMIN)
def update_user_role(
    username: str = typer.Option(..., help="Username to update"),
    role: str = typer.Option(..., help="New role: user, moderator, admin")
):
    """Update user role."""
    try:
        db = next(get_db())
        
        # Validate role
        try:
            new_role = UserRole(role.lower())
        except ValueError:
            console.print(f"❌ Invalid role: {role}", style="red")
            raise typer.Exit(1)
        
        # Find user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            console.print(f"❌ User '{username}' not found", style="red")
            raise typer.Exit(1)
        
        old_role = user.role
        user.role = new_role
        db.commit()
        
        console.print(f"✅ Updated {username} role from {old_role.value} to {new_role.value}", style="green")
        
    except Exception as e:
        console.print(f"❌ Error updating user role: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@admin_app.command("deactivate-user")
@cli_auth.require_auth(UserRole.ADMIN)
def deactivate_user(
    username: str = typer.Option(..., help="Username to deactivate")
):
    """Deactivate a user account."""
    try:
        db = next(get_db())
        
        # Find user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            console.print(f"❌ User '{username}' not found", style="red")
            raise typer.Exit(1)
        
        if not user.is_active:
            console.print(f"⚠️  User '{username}' is already inactive", style="yellow")
            return
        
        # Confirm action
        if not Confirm.ask(f"Are you sure you want to deactivate user '{username}'?"):
            console.print("❌ Operation cancelled", style="yellow")
            return
        
        user.is_active = False
        db.commit()
        
        console.print(f"✅ Deactivated user '{username}'", style="green")
        
    except Exception as e:
        console.print(f"❌ Error deactivating user: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@admin_app.command("stats")
@cli_auth.require_auth(UserRole.MODERATOR)  # Moderators can view stats
def system_stats():
    """Show system statistics."""
    try:
        db = next(get_db())
        
        # Get counts
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        admin_users = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar()
        mod_users = db.query(func.count(User.id)).filter(User.role == UserRole.MODERATOR).scalar()
        
        total_subreddits = db.query(func.count(Subreddit.id)).scalar()
        total_posts = db.query(func.count(Post.id)).scalar()
        total_comments = db.query(func.count(Comment.id)).scalar()
        
        # Create stats table
        table = Table(title="📊 System Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Users", f"{total_users:,}")
        table.add_row("Active Users", f"{active_users:,}")
        table.add_row("Admin Users", f"{admin_users:,}")
        table.add_row("Moderator Users", f"{mod_users:,}")
        table.add_row("", "")  # Separator
        table.add_row("Total Subreddits", f"{total_subreddits:,}")
        table.add_row("Total Posts", f"{total_posts:,}")
        table.add_row("Total Comments", f"{total_comments:,}")
        
        # Calculate ratios
        if total_posts > 0:
            table.add_row("Comments per Post", f"{total_comments / total_posts:.1f}")
        
        if total_subreddits > 0:
            table.add_row("Posts per Subreddit", f"{total_posts / total_subreddits:.1f}")
        
        console.print(table)
        
        # User role distribution
        role_data = {
            "Users": db.query(func.count(User.id)).filter(User.role == UserRole.USER).scalar(),
            "Moderators": mod_users,
            "Admins": admin_users
        }
        
        role_chart = visualizer.horizontal_bar_chart(role_data, "👥 User Role Distribution")
        console.print(role_chart)
        
    except Exception as e:
        console.print(f"❌ Error generating system stats: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@admin_app.command("cleanup")
@cli_auth.require_auth(UserRole.ADMIN)
def cleanup_data(
    days: int = typer.Option(90, help="Delete data older than X days"),
    dry_run: bool = typer.Option(True, help="Show what would be deleted without deleting")
):
    """Clean up old data from the database."""
    try:
        db = next(get_db())
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find old data
        old_posts = db.query(Post).filter(Post.created_at < cutoff_date).count()
        old_comments = db.query(Comment).filter(Comment.created_at < cutoff_date).count()
        
        console.print(f"🗑️  Cleanup Report (older than {days} days)")
        
        cleanup_table = Table(title="Cleanup Preview")
        cleanup_table.add_column("Data Type", style="cyan")
        cleanup_table.add_column("Count", style="yellow")
        cleanup_table.add_column("Action", style="red" if not dry_run else "blue")
        
        cleanup_table.add_row("Posts", str(old_posts), "Would delete" if dry_run else "Deleting")
        cleanup_table.add_row("Comments", str(old_comments), "Would delete" if dry_run else "Deleting")
        
        console.print(cleanup_table)
        
        if dry_run:
            console.print("💡 This is a dry run. Use --no-dry-run to actually delete data", style="yellow")
        else:
            if not Confirm.ask(f"Are you sure you want to delete {old_posts + old_comments} records?"):
                console.print("❌ Operation cancelled", style="yellow")
                return
            
            # Perform cleanup
            deleted_comments = db.query(Comment).filter(Comment.created_at < cutoff_date).delete()
            deleted_posts = db.query(Post).filter(Post.created_at < cutoff_date).delete()
            db.commit()
            
            console.print(f"✅ Deleted {deleted_posts} posts and {deleted_comments} comments", style="green")
        
    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@admin_app.command("health-check")
@cli_auth.require_auth(UserRole.ADMIN)
def health_check(
    full: bool = typer.Option(False, help="Perform full health check including performance tests")
):
    """Perform comprehensive system health check."""
    console.print("🔍 Performing system health check...", style="blue")
    
    try:
        db = next(get_db())
        
        # Basic connectivity
        db.execute("SELECT 1").scalar()
        console.print("✅ Database connection: OK", style="green")
        
        # Check essential tables
        tables_to_check = [User, Subreddit, Post, Comment]
        for model in tables_to_check:
            try:
                count = db.query(func.count(model.id)).scalar()
                console.print(f"✅ {model.__tablename__} table: {count:,} records", style="green")
            except Exception as e:
                console.print(f"❌ {model.__tablename__} table: Error - {e}", style="red")
        
        # Check admin users
        admin_count = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN, User.is_active == True).scalar()
        if admin_count > 0:
            console.print(f"✅ Active admin users: {admin_count}", style="green")
        else:
            console.print("⚠️  No active admin users found", style="yellow")
        
        if full:
            console.print("\n🔬 Performing extended health checks...", style="blue")
            
            # Performance test
            import time
            start_time = time.time()
            db.query(Post).limit(1000).all()
            query_time = time.time() - start_time
            
            if query_time < 1.0:
                console.print(f"✅ Query performance: {query_time:.3f}s (Good)", style="green")
            elif query_time < 3.0:
                console.print(f"⚠️  Query performance: {query_time:.3f}s (Slow)", style="yellow")
            else:
                console.print(f"❌ Query performance: {query_time:.3f}s (Poor)", style="red")
        
        console.print("\n🎉 Health check completed", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Health check failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()