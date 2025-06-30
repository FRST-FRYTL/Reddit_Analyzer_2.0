"""Report generation CLI commands."""

import typer
import json
import csv
from rich.console import Console
from rich.table import Table
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import func

from app.cli.utils.auth_manager import cli_auth
from app.cli.utils.ascii_charts import ASCIIVisualizer
from app.models.post import Post
from app.models.comment import Comment
from app.models.subreddit import Subreddit
from app.database import get_db

report_app = typer.Typer(help="Reporting commands")
console = Console()
visualizer = ASCIIVisualizer()


@report_app.command("daily")
@cli_auth.require_auth()
def daily_report(
    subreddit: Optional[str] = typer.Option(None, help="Specific subreddit (without r/)"),
    date: Optional[str] = typer.Option(None, help="Date in YYYY-MM-DD format (default: yesterday)")
):
    """Generate daily report for subreddit activity."""
    try:
        db = next(get_db())
        
        # Parse date
        if date:
            try:
                report_date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                console.print("❌ Invalid date format. Use YYYY-MM-DD", style="red")
                raise typer.Exit(1)
        else:
            report_date = datetime.utcnow() - timedelta(days=1)
        
        start_date = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Base query
        post_query = db.query(Post).filter(
            Post.created_at >= start_date,
            Post.created_at < end_date
        )
        
        if subreddit:
            subreddit_obj = db.query(Subreddit).filter(Subreddit.name == subreddit).first()
            if not subreddit_obj:
                console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
                raise typer.Exit(1)
            post_query = post_query.filter(Post.subreddit_id == subreddit_obj.id)
            title_prefix = f"r/{subreddit}"
        else:
            title_prefix = "All Subreddits"
        
        posts = post_query.all()
        
        console.print(f"📋 Daily Report - {title_prefix} ({report_date.strftime('%Y-%m-%d')})")
        
        if not posts:
            console.print("📭 No posts found for this date", style="yellow")
            return
        
        # Calculate metrics
        total_posts = len(posts)
        total_comments = sum(post.num_comments for post in posts)
        total_score = sum(post.score for post in posts)
        avg_score = total_score / total_posts if total_posts > 0 else 0
        
        # Get previous day for comparison
        prev_start = start_date - timedelta(days=1)
        prev_end = start_date
        
        prev_query = db.query(Post).filter(
            Post.created_at >= prev_start,
            Post.created_at < prev_end
        )
        
        if subreddit:
            prev_query = prev_query.filter(Post.subreddit_id == subreddit_obj.id)
        
        prev_posts = prev_query.all()
        prev_total_posts = len(prev_posts)
        
        # Calculate changes
        post_change = ((total_posts - prev_total_posts) / prev_total_posts * 100) if prev_total_posts > 0 else 0
        
        # Summary table
        summary_data = {
            "Posts": f"{total_posts} ({post_change:+.1f}%)",
            "Comments": f"{total_comments:,}",
            "Total Score": f"{total_score:,}",
            "Average Score": f"{avg_score:.1f}",
        }
        
        summary_table = visualizer.create_summary_table(summary_data, "📊 Daily Summary")
        console.print(summary_table)
        
        # Top posts
        top_posts = sorted(posts, key=lambda p: p.score, reverse=True)[:5]
        
        if top_posts:
            top_table = Table(title="🏆 Top Posts")
            top_table.add_column("Title", style="cyan", max_width=50)
            top_table.add_column("Score", style="green")
            top_table.add_column("Comments", style="yellow")
            
            for post in top_posts:
                title = post.title[:47] + "..." if len(post.title) > 50 else post.title
                top_table.add_row(title, str(post.score), str(post.num_comments))
            
            console.print(top_table)
        
        # Hourly activity
        hourly_counts = {}
        for post in posts:
            hour = post.created_at.strftime('%H')
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        if hourly_counts:
            activity_chart = visualizer.horizontal_bar_chart(
                hourly_counts,
                "📈 Hourly Activity"
            )
            console.print(activity_chart)
        
    except Exception as e:
        console.print(f"❌ Error generating daily report: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@report_app.command("export")
@cli_auth.require_auth()
def export_data(
    format: str = typer.Option("csv", help="Export format: csv, json"),
    output: str = typer.Option("export.csv", help="Output file name"),
    subreddit: Optional[str] = typer.Option(None, help="Specific subreddit (without r/)"),
    days: int = typer.Option(7, help="Number of days to export")
):
    """Export data in various formats."""
    try:
        db = next(get_db())
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query
        post_query = db.query(Post).filter(Post.created_at >= start_date)
        
        if subreddit:
            subreddit_obj = db.query(Subreddit).filter(Subreddit.name == subreddit).first()
            if not subreddit_obj:
                console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
                raise typer.Exit(1)
            post_query = post_query.filter(Post.subreddit_id == subreddit_obj.id)
        
        posts = post_query.all()
        
        if not posts:
            console.print("📭 No data to export", style="yellow")
            return
        
        # Prepare data for export
        export_data = []
        for post in posts:
            post_data = {
                "title": post.title,
                "score": post.score,
                "num_comments": post.num_comments,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "author": post.author,
                "url": post.url,
                "selftext": post.selftext[:500] if post.selftext else "",  # Truncate long text
            }
            export_data.append(post_data)
        
        # Export based on format
        output_path = Path(output)
        
        if format.lower() == "csv":
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if export_data:
                    fieldnames = export_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(export_data)
            
            console.print(f"📊 Exported {len(export_data)} posts to {output_path}", style="green")
            
        elif format.lower() == "json":
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, default=str)
            
            console.print(f"📊 Exported {len(export_data)} posts to {output_path}", style="green")
            
        else:
            console.print(f"❌ Unsupported format: {format}", style="red")
            raise typer.Exit(1)
        
        # Show export summary
        summary = {
            "Records Exported": len(export_data),
            "File Size": f"{output_path.stat().st_size / 1024:.1f} KB",
            "Date Range": f"{days} days",
            "Format": format.upper(),
        }
        
        summary_table = visualizer.create_summary_table(summary, "📤 Export Summary")
        console.print(summary_table)
        
    except Exception as e:
        console.print(f"❌ Error exporting data: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@report_app.command("weekly")
@cli_auth.require_auth()
def weekly_report(
    subreddit: Optional[str] = typer.Option(None, help="Specific subreddit (without r/)"),
    weeks: int = typer.Option(1, help="Number of weeks back to analyze")
):
    """Generate weekly summary report."""
    try:
        db = next(get_db())
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Base query
        post_query = db.query(Post).filter(Post.created_at >= start_date)
        
        if subreddit:
            subreddit_obj = db.query(Subreddit).filter(Subreddit.name == subreddit).first()
            if not subreddit_obj:
                console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
                raise typer.Exit(1)
            post_query = post_query.filter(Post.subreddit_id == subreddit_obj.id)
            title_prefix = f"r/{subreddit}"
        else:
            title_prefix = "All Subreddits"
        
        posts = post_query.all()
        
        console.print(f"📅 Weekly Report - {title_prefix} (Last {weeks} week{'s' if weeks > 1 else ''})")
        
        if not posts:
            console.print("📭 No posts found for this period", style="yellow")
            return
        
        # Calculate metrics
        total_posts = len(posts)
        total_comments = sum(post.num_comments for post in posts)
        total_score = sum(post.score for post in posts)
        avg_score = total_score / total_posts if total_posts > 0 else 0
        
        # Daily breakdown
        daily_counts = {}
        for post in posts:
            day = post.created_at.strftime('%Y-%m-%d')
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        # Summary
        summary_data = {
            "Total Posts": f"{total_posts:,}",
            "Total Comments": f"{total_comments:,}",
            "Total Score": f"{total_score:,}",
            "Average Score": f"{avg_score:.1f}",
            "Posts per Day": f"{total_posts / (weeks * 7):.1f}",
        }
        
        summary_table = visualizer.create_summary_table(summary_data, "📊 Weekly Summary")
        console.print(summary_table)
        
        # Daily activity chart
        if daily_counts:
            activity_chart = visualizer.horizontal_bar_chart(
                daily_counts,
                "📈 Daily Activity"
            )
            console.print(activity_chart)
        
        # Top performers
        top_posts = sorted(posts, key=lambda p: p.score, reverse=True)[:10]
        
        if top_posts:
            top_table = Table(title="🏆 Top Posts of the Week")
            top_table.add_column("Rank", style="yellow")
            top_table.add_column("Title", style="cyan", max_width=40)
            top_table.add_column("Score", style="green")
            top_table.add_column("Comments", style="blue")
            
            for i, post in enumerate(top_posts, 1):
                title = post.title[:37] + "..." if len(post.title) > 40 else post.title
                top_table.add_row(
                    str(i),
                    title,
                    str(post.score),
                    str(post.num_comments)
                )
            
            console.print(top_table)
        
    except Exception as e:
        console.print(f"❌ Error generating weekly report: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@report_app.command("schedule")
@cli_auth.require_auth()
def schedule_report(
    frequency: str = typer.Option("weekly", help="Report frequency: daily, weekly, monthly"),
    subreddit: Optional[str] = typer.Option(None, help="Specific subreddit (without r/)"),
    email: Optional[str] = typer.Option(None, help="Email address for delivery"),
    format: str = typer.Option("console", help="Report format: console, csv, json")
):
    """Schedule automated report generation."""
    console.print(f"⏰ Scheduling {frequency} reports", style="blue")
    
    # This is a placeholder for actual scheduling implementation
    # In a real implementation, you would use a task scheduler like Celery
    
    schedule_info = {
        "Frequency": frequency.title(),
        "Subreddit": f"r/{subreddit}" if subreddit else "All",
        "Format": format.upper(),
        "Email": email or "Console only",
        "Status": "Scheduled",
        "Next Run": "To be implemented"
    }
    
    schedule_table = visualizer.create_summary_table(schedule_info, "📅 Report Schedule")
    console.print(schedule_table)
    
    console.print("💡 Note: Automated scheduling requires additional setup", style="yellow")