"""Analysis commands for political topics and dimensions."""

import typer
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
import json
import numpy as np

from reddit_analyzer.database import get_session
from reddit_analyzer.models import (
    Subreddit,
    Post,
    Comment,
    SubredditPoliticalDimensions,
)
from reddit_analyzer.services.topic_analyzer import TopicAnalyzer
from reddit_analyzer.services.political_dimensions_analyzer import (
    PoliticalDimensionsAnalyzer,
    calculate_political_diversity,
    identify_political_clusters,
)
from reddit_analyzer.cli.utils.auth_manager import require_auth
import structlog

logger = structlog.get_logger(__name__)
console = Console()

app = typer.Typer(
    name="analyze",
    help="Analyze political topics and discourse in subreddits",
    no_args_is_help=True,
)


def _validate_subreddit(subreddit_name: str) -> Optional[Subreddit]:
    """Validate that a subreddit exists in the database."""
    with get_session() as session:
        subreddit = session.query(Subreddit).filter_by(name=subreddit_name).first()
        if not subreddit:
            console.print(
                f"[red]Error: Subreddit r/{subreddit_name} not found in database.[/red]"
            )
            console.print(
                "[yellow]Tip: Use 'reddit-analyzer data collect' to fetch data first.[/yellow]"
            )
            return None
        return subreddit


@app.command(name="topics")
@require_auth
def analyze_topics(
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Limit number of posts to analyze"
    ),
    save_report: Optional[str] = typer.Option(
        None, "--save", "-s", help="Save report to file"
    ),
    ctx: typer.Context = typer.Context,
):
    """Analyze political topics in a subreddit."""
    # Validate subreddit
    sub = _validate_subreddit(subreddit)
    if not sub:
        raise typer.Exit(1)

    # Initialize analyzer
    analyzer = TopicAnalyzer()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Fetch posts and comments
        task = progress.add_task("Fetching posts and comments...", total=None)

        with get_session() as session:
            # Get posts from date range
            posts_query = (
                session.query(Post)
                .filter(
                    Post.subreddit_id == sub.id,
                    Post.created_utc >= start_date,
                    Post.created_utc <= end_date,
                )
                .order_by(Post.created_utc.desc())
            )

            if limit:
                posts_query = posts_query.limit(limit)

            posts = posts_query.all()

            # Get comments for these posts
            post_ids = [p.id for p in posts]
            comments = (
                session.query(Comment).filter(Comment.post_id.in_(post_ids)).all()
            )

        progress.update(
            task,
            description=f"Analyzing {len(posts)} posts and {len(comments)} comments...",
        )

        # Analyze topics
        topic_scores = {}
        topic_sentiments = {}
        analyzed_count = 0

        # Analyze posts
        for post in posts:
            if post.title:
                topics = analyzer.detect_political_topics(post.title)
                if post.selftext:
                    body_topics = analyzer.detect_political_topics(post.selftext)
                    # Merge topics, taking max score
                    for topic, score in body_topics.items():
                        topics[topic] = max(topics.get(topic, 0), score)

                for topic, score in topics.items():
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                        topic_sentiments[topic] = []
                    topic_scores[topic].append(score)

                    # Analyze sentiment for this topic
                    text = f"{post.title} {post.selftext or ''}"
                    sentiment = analyzer.analyze_topic_sentiment(text, topic)
                    if sentiment["confidence"] > 0:
                        topic_sentiments[topic].append(sentiment["sentiment"])

                analyzed_count += 1

        # Analyze comments
        comment_texts = []
        for comment in comments[:1000]:  # Limit for performance
            if comment.body and len(comment.body) > 20:
                topics = analyzer.detect_political_topics(comment.body)
                comment_texts.append(comment.body)

                for topic, score in topics.items():
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                        topic_sentiments[topic] = []
                    topic_scores[topic].append(score)

                    # Analyze sentiment
                    sentiment = analyzer.analyze_topic_sentiment(comment.body, topic)
                    if sentiment["confidence"] > 0:
                        topic_sentiments[topic].append(sentiment["sentiment"])

        # Calculate discussion quality
        quality_metrics = analyzer.calculate_discussion_quality(comment_texts[:100])

        progress.update(task, description="Generating report...")

    # Generate report
    _display_topic_analysis_report(
        subreddit,
        topic_scores,
        topic_sentiments,
        quality_metrics,
        analyzed_count,
        len(comments),
        start_date,
        end_date,
    )

    # Save report if requested
    if save_report:
        report_data = {
            "subreddit": subreddit,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "posts_analyzed": analyzed_count,
            "comments_analyzed": len(comment_texts),
            "topic_distribution": {
                topic: {
                    "prevalence": (
                        len(scores) / analyzed_count if analyzed_count > 0 else 0
                    ),
                    "avg_confidence": sum(scores) / len(scores) if scores else 0,
                    "sentiment": (
                        sum(topic_sentiments.get(topic, []))
                        / len(topic_sentiments.get(topic, []))
                        if topic_sentiments.get(topic)
                        else 0
                    ),
                }
                for topic, scores in topic_scores.items()
            },
            "discussion_quality": quality_metrics,
        }

        with open(save_report, "w") as f:
            json.dump(report_data, f, indent=2)
        console.print(f"\n[green]Report saved to {save_report}[/green]")


@app.command(name="sentiment")
@require_auth
def analyze_sentiment(
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    topic: str = typer.Option(
        ..., "--topic", "-t", help="Political topic to analyze sentiment for"
    ),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    ctx: typer.Context = typer.Context,
):
    """Analyze sentiment around a specific political topic."""
    from reddit_analyzer.data.political_topics import get_all_topics

    # Validate topic
    valid_topics = get_all_topics()
    if topic not in valid_topics:
        console.print(f"[red]Error: '{topic}' is not a valid political topic.[/red]")
        console.print(f"[yellow]Valid topics: {', '.join(valid_topics)}[/yellow]")
        raise typer.Exit(1)

    # Validate subreddit
    sub = _validate_subreddit(subreddit)
    if not sub:
        raise typer.Exit(1)

    analyzer = TopicAnalyzer()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Analyzing sentiment for '{topic}' topic...", total=None)

        with get_session() as session:
            # Get posts mentioning this topic
            posts = (
                session.query(Post)
                .filter(
                    Post.subreddit_id == sub.id,
                    Post.created_utc >= start_date,
                    Post.created_utc <= end_date,
                )
                .all()
            )

            sentiments = []
            examples = {"positive": [], "negative": [], "neutral": []}

            for post in posts:
                text = f"{post.title} {post.selftext or ''}"
                topics = analyzer.detect_political_topics(text)

                if topic in topics and topics[topic] > 0.3:  # Significant presence
                    sentiment_result = analyzer.analyze_topic_sentiment(text, topic)
                    if sentiment_result["confidence"] > 0.5:
                        sentiments.append(sentiment_result["sentiment"])

                        # Collect examples
                        if sentiment_result["sentiment"] > 0.3:
                            if len(examples["positive"]) < 3:
                                examples["positive"].append(post.title[:100])
                        elif sentiment_result["sentiment"] < -0.3:
                            if len(examples["negative"]) < 3:
                                examples["negative"].append(post.title[:100])
                        else:
                            if len(examples["neutral"]) < 3:
                                examples["neutral"].append(post.title[:100])

    # Display results
    _display_sentiment_analysis(
        topic, sentiments, examples, subreddit, start_date, end_date
    )


@app.command(name="quality")
@require_auth
def analyze_quality(
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    min_comments: int = typer.Option(
        50, "--min-comments", "-m", help="Minimum comments per post"
    ),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to analyze"),
    ctx: typer.Context = typer.Context,
):
    """Assess discussion quality in a subreddit."""
    # Validate subreddit
    sub = _validate_subreddit(subreddit)
    if not sub:
        raise typer.Exit(1)

    analyzer = TopicAnalyzer()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Analyzing discussion quality...", total=None)

        with get_session() as session:
            # Get posts with many comments
            posts = (
                session.query(Post)
                .filter(
                    Post.subreddit_id == sub.id,
                    Post.created_utc >= start_date,
                    Post.created_utc <= end_date,
                    Post.num_comments >= min_comments,
                )
                .order_by(Post.num_comments.desc())
                .limit(20)
                .all()
            )

            if not posts:
                console.print(
                    f"[yellow]No posts found with at least {min_comments} comments in the last {days} days.[/yellow]"
                )
                raise typer.Exit(0)

            quality_scores = []
            post_analyses = []

            for post in posts:
                # Get comments for this post
                comments = (
                    session.query(Comment)
                    .filter(Comment.post_id == post.id)
                    .limit(100)
                    .all()
                )

                comment_texts = [
                    c.body for c in comments if c.body and len(c.body) > 20
                ]

                if len(comment_texts) >= 10:
                    quality = analyzer.calculate_discussion_quality(comment_texts)
                    quality_scores.append(quality)
                    post_analyses.append(
                        {
                            "title": post.title,
                            "num_comments": post.num_comments,
                            "quality": quality,
                        }
                    )

    # Display results
    _display_quality_analysis(
        post_analyses, quality_scores, subreddit, start_date, end_date
    )


@app.command(name="overlap")
@require_auth
def analyze_overlap(
    subreddit1: str = typer.Argument(..., help="First subreddit"),
    subreddit2: str = typer.Argument(..., help="Second subreddit"),
    include_topics: bool = typer.Option(
        True, "--include-topics", help="Include shared topics analysis"
    ),
    ctx: typer.Context = typer.Context,
):
    """Compare community overlap between two subreddits."""
    # Validate subreddits
    sub1 = _validate_subreddit(subreddit1)
    sub2 = _validate_subreddit(subreddit2)

    if not sub1 or not sub2:
        raise typer.Exit(1)

    if sub1.id == sub2.id:
        console.print("[red]Error: Cannot compare a subreddit with itself.[/red]")
        raise typer.Exit(1)

    analyzer = TopicAnalyzer()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing community overlap...", total=None)

        with get_session() as session:
            # Get recent posts from both subreddits
            days = 30
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            posts1 = (
                session.query(Post)
                .filter(Post.subreddit_id == sub1.id, Post.created_utc >= start_date)
                .limit(100)
                .all()
            )

            posts2 = (
                session.query(Post)
                .filter(Post.subreddit_id == sub2.id, Post.created_utc >= start_date)
                .limit(100)
                .all()
            )

            # Get unique authors
            authors1 = set(p.author_name for p in posts1 if p.author_name)
            authors2 = set(p.author_name for p in posts2 if p.author_name)

            # Calculate overlap
            shared_authors = authors1 & authors2
            total_authors = len(authors1 | authors2)

            overlap_data = {
                "shared_authors": len(shared_authors),
                "total_authors": total_authors,
                "overlap_percentage": (
                    (len(shared_authors) / total_authors * 100)
                    if total_authors > 0
                    else 0
                ),
                "sub1_unique": len(authors1 - authors2),
                "sub2_unique": len(authors2 - authors1),
            }

            # Analyze shared topics if requested
            topic_data = None
            if include_topics:
                progress.update(task, description="Analyzing shared topics...")

                # Analyze topics in both subreddits
                topics1 = {}
                topics2 = {}

                for post in posts1:
                    text = f"{post.title} {post.selftext or ''}"
                    post_topics = analyzer.detect_political_topics(text)
                    for topic, score in post_topics.items():
                        if topic not in topics1:
                            topics1[topic] = []
                        topics1[topic].append(score)

                for post in posts2:
                    text = f"{post.title} {post.selftext or ''}"
                    post_topics = analyzer.detect_political_topics(text)
                    for topic, score in post_topics.items():
                        if topic not in topics2:
                            topics2[topic] = []
                        topics2[topic].append(score)

                # Find shared topics
                shared_topics = set(topics1.keys()) & set(topics2.keys())

                topic_data = {
                    "shared_topics": list(shared_topics),
                    "sub1_unique_topics": list(set(topics1.keys()) - shared_topics),
                    "sub2_unique_topics": list(set(topics2.keys()) - shared_topics),
                    "topic_prevalence": {
                        topic: {
                            sub1.name: len(topics1.get(topic, [])) / len(posts1),
                            sub2.name: len(topics2.get(topic, [])) / len(posts2),
                        }
                        for topic in shared_topics
                    },
                }

    # Display results
    _display_overlap_analysis(sub1.name, sub2.name, overlap_data, topic_data)


def _display_topic_analysis_report(
    subreddit: str,
    topic_scores: dict,
    topic_sentiments: dict,
    quality_metrics: dict,
    posts_analyzed: int,
    comments_analyzed: int,
    start_date: datetime,
    end_date: datetime,
):
    """Display comprehensive topic analysis report."""
    console.print(f"\n[bold]Political Topic Analysis for r/{subreddit}[/bold]")
    console.print(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    console.print(
        f"Posts analyzed: {posts_analyzed} | Comments analyzed: {comments_analyzed}\n"
    )

    # Topic distribution table
    table = Table(title="Topic Distribution", show_header=True)
    table.add_column("Topic", style="cyan", width=20)
    table.add_column("Prevalence", justify="right", style="green")
    table.add_column("Avg Confidence", justify="right")
    table.add_column("Sentiment", justify="right")
    table.add_column("Visual", width=20)

    # Sort topics by prevalence
    sorted_topics = sorted(topic_scores.items(), key=lambda x: len(x[1]), reverse=True)[
        :10
    ]  # Top 10 topics

    max_prevalence = (
        max(len(scores) for _, scores in sorted_topics) if sorted_topics else 1
    )

    for topic, scores in sorted_topics:
        prevalence = len(scores) / posts_analyzed if posts_analyzed > 0 else 0
        avg_confidence = sum(scores) / len(scores) if scores else 0

        # Calculate average sentiment
        sentiments = topic_sentiments.get(topic, [])
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        # Create visual bar
        bar_length = int((len(scores) / max_prevalence) * 20)
        bar = "█" * bar_length

        # Format sentiment with color
        if avg_sentiment > 0.2:
            sentiment_str = f"[green]+{avg_sentiment:.2f}[/green]"
        elif avg_sentiment < -0.2:
            sentiment_str = f"[red]{avg_sentiment:.2f}[/red]"
        else:
            sentiment_str = f"[yellow]{avg_sentiment:.2f}[/yellow]"

        table.add_row(
            topic.capitalize(),
            f"{prevalence:.1%}",
            f"{avg_confidence:.2f}",
            sentiment_str,
            f"[blue]{bar}[/blue]",
        )

    console.print(table)

    # Discussion quality panel
    quality_text = Text()
    quality_text.append("Discussion Quality Metrics\n\n", style="bold")
    quality_text.append(
        f"Overall Quality: {quality_metrics['overall_quality']:.2f}/1.0\n"
    )
    quality_text.append(
        f"Civility Score: {quality_metrics['civility_score']:.2f}/1.0\n"
    )
    quality_text.append(
        f"Constructiveness: {quality_metrics['constructiveness_score']:.2f}/1.0\n"
    )
    quality_text.append(
        f"Viewpoint Diversity: {quality_metrics['viewpoint_diversity']:.2f}/1.0\n"
    )
    quality_text.append(
        f"Engagement Quality: {quality_metrics['engagement_quality']:.2f}/1.0\n"
    )
    quality_text.append(f"\nConfidence: {quality_metrics['confidence']:.1%}")

    console.print(Panel(quality_text, title="Discussion Quality", border_style="green"))


def _display_sentiment_analysis(
    topic: str,
    sentiments: List[float],
    examples: dict,
    subreddit: str,
    start_date: datetime,
    end_date: datetime,
):
    """Display sentiment analysis results."""
    if not sentiments:
        console.print(
            f"[yellow]No significant discussions about '{topic}' found in r/{subreddit}[/yellow]"
        )
        return

    console.print(f"\n[bold]Sentiment Analysis: '{topic}' in r/{subreddit}[/bold]")
    console.print(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    console.print(f"Posts analyzed: {len(sentiments)}\n")

    # Calculate sentiment distribution
    positive = sum(1 for s in sentiments if s > 0.3)
    negative = sum(1 for s in sentiments if s < -0.3)
    neutral = len(sentiments) - positive - negative

    avg_sentiment = sum(sentiments) / len(sentiments)

    # Sentiment summary
    table = Table(show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Average Sentiment", f"{avg_sentiment:.3f}")
    table.add_row("Positive", f"{positive} ({positive / len(sentiments):.1%})")
    table.add_row("Neutral", f"{neutral} ({neutral / len(sentiments):.1%})")
    table.add_row("Negative", f"{negative} ({negative / len(sentiments):.1%})")

    console.print(table)

    # Show examples
    console.print("\n[bold]Example Posts:[/bold]")

    if examples["positive"]:
        console.print("\n[green]Positive:[/green]")
        for ex in examples["positive"]:
            console.print(f"  • {ex}")

    if examples["negative"]:
        console.print("\n[red]Negative:[/red]")
        for ex in examples["negative"]:
            console.print(f"  • {ex}")

    if examples["neutral"]:
        console.print("\n[yellow]Neutral:[/yellow]")
        for ex in examples["neutral"]:
            console.print(f"  • {ex}")


def _display_quality_analysis(
    post_analyses: List[dict],
    quality_scores: List[dict],
    subreddit: str,
    start_date: datetime,
    end_date: datetime,
):
    """Display discussion quality analysis."""
    console.print(f"\n[bold]Discussion Quality Analysis for r/{subreddit}[/bold]")
    console.print(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    console.print(f"Posts analyzed: {len(post_analyses)}\n")

    # Overall averages
    if quality_scores:
        avg_quality = sum(q["overall_quality"] for q in quality_scores) / len(
            quality_scores
        )
        avg_civility = sum(q["civility_score"] for q in quality_scores) / len(
            quality_scores
        )
        avg_constructive = sum(
            q["constructiveness_score"] for q in quality_scores
        ) / len(quality_scores)
        avg_diversity = sum(q["viewpoint_diversity"] for q in quality_scores) / len(
            quality_scores
        )

        # Summary panel
        summary_text = Text()
        summary_text.append("Overall Averages\n\n", style="bold")
        summary_text.append(f"Quality Score: {avg_quality:.2f}/1.0\n")
        summary_text.append(f"Civility: {avg_civility:.2f}/1.0\n")
        summary_text.append(f"Constructiveness: {avg_constructive:.2f}/1.0\n")
        summary_text.append(f"Viewpoint Diversity: {avg_diversity:.2f}/1.0\n")

        console.print(Panel(summary_text, title="Summary", border_style="green"))

    # Top quality discussions
    console.print("\n[bold]Top Quality Discussions:[/bold]")

    table = Table(show_header=True)
    table.add_column("Post Title", style="cyan", width=50)
    table.add_column("Comments", justify="right")
    table.add_column("Quality", justify="right")
    table.add_column("Civility", justify="right")
    table.add_column("Diversity", justify="right")

    # Sort by quality score
    sorted_posts = sorted(
        post_analyses, key=lambda x: x["quality"]["overall_quality"], reverse=True
    )

    for post in sorted_posts[:10]:
        quality = post["quality"]
        table.add_row(
            post["title"][:50] + "..." if len(post["title"]) > 50 else post["title"],
            str(post["num_comments"]),
            f"{quality['overall_quality']:.2f}",
            f"{quality['civility_score']:.2f}",
            f"{quality['viewpoint_diversity']:.2f}",
        )

    console.print(table)


def _display_overlap_analysis(
    subreddit1: str, subreddit2: str, overlap_data: dict, topic_data: Optional[dict]
):
    """Display community overlap analysis."""
    console.print("\n[bold]Community Overlap Analysis[/bold]")
    console.print(f"Comparing r/{subreddit1} and r/{subreddit2}\n")

    # User overlap
    table = Table(title="User Overlap", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Shared Users", str(overlap_data["shared_authors"]))
    table.add_row("Total Unique Users", str(overlap_data["total_authors"]))
    table.add_row("Overlap Percentage", f"{overlap_data['overlap_percentage']:.1f}%")
    table.add_row(f"Unique to r/{subreddit1}", str(overlap_data["sub1_unique"]))
    table.add_row(f"Unique to r/{subreddit2}", str(overlap_data["sub2_unique"]))

    console.print(table)

    # Topic overlap
    if topic_data:
        console.print("\n[bold]Shared Political Topics:[/bold]")

        if topic_data["shared_topics"]:
            topic_table = Table(show_header=True)
            topic_table.add_column("Topic", style="cyan")
            topic_table.add_column(f"r/{subreddit1}", justify="right")
            topic_table.add_column(f"r/{subreddit2}", justify="right")
            topic_table.add_column("Difference", justify="right")

            for topic in sorted(topic_data["shared_topics"]):
                prev1 = topic_data["topic_prevalence"][topic][subreddit1]
                prev2 = topic_data["topic_prevalence"][topic][subreddit2]
                diff = abs(prev1 - prev2)

                topic_table.add_row(
                    topic.capitalize(), f"{prev1:.1%}", f"{prev2:.1%}", f"{diff:.1%}"
                )

            console.print(topic_table)
        else:
            console.print("[yellow]No shared political topics found.[/yellow]")

        # Unique topics
        if topic_data["sub1_unique_topics"]:
            console.print(f"\n[bold]Topics unique to r/{subreddit1}:[/bold]")
            console.print(
                ", ".join(t.capitalize() for t in topic_data["sub1_unique_topics"])
            )

        if topic_data["sub2_unique_topics"]:
            console.print(f"\n[bold]Topics unique to r/{subreddit2}:[/bold]")
            console.print(
                ", ".join(t.capitalize() for t in topic_data["sub2_unique_topics"])
            )


@app.command(name="dimensions")
@require_auth
def analyze_dimensions(
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Limit number of posts to analyze"
    ),
    save_analysis: bool = typer.Option(
        False, "--save", "-s", help="Save analysis to database"
    ),
    ctx: typer.Context = typer.Context,
):
    """Analyze political dimensions of a subreddit."""
    # Validate subreddit
    sub = _validate_subreddit(subreddit)
    if not sub:
        raise typer.Exit(1)

    # Initialize analyzer
    analyzer = PoliticalDimensionsAnalyzer()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing political dimensions...", total=None)

        with get_session() as session:
            # Get posts from date range
            posts_query = (
                session.query(Post)
                .filter(
                    Post.subreddit_id == sub.id,
                    Post.created_utc >= start_date,
                    Post.created_utc <= end_date,
                )
                .order_by(Post.created_utc.desc())
            )

            if limit:
                posts_query = posts_query.limit(limit)

            posts = posts_query.all()

            # Analyze each post
            analyses = []
            dimension_scores = {"economic": [], "social": [], "governance": []}

            for post in posts:
                text = f"{post.title} {post.selftext or ''}"
                if len(text) > 50:  # Minimum text length
                    result = analyzer.analyze_political_dimensions(text)

                    if result.analysis_quality > 0.3:  # Minimum quality threshold
                        analyses.append(
                            {
                                "economic": result.dimensions.get("economic", {}),
                                "social": result.dimensions.get("social", {}),
                                "governance": result.dimensions.get("governance", {}),
                                "analysis_quality": result.analysis_quality,
                                "topics": result.dominant_topics,
                            }
                        )

                        # Collect scores for aggregation
                        for dim in ["economic", "social", "governance"]:
                            if dim in result.dimensions:
                                dimension_scores[dim].append(
                                    result.dimensions[dim]["score"]
                                )

            progress.update(task, description="Calculating political diversity...")

            # Calculate aggregate metrics
            diversity = calculate_political_diversity(analyses)
            clusters = identify_political_clusters(analyses)

    # Display results
    _display_political_dimensions_analysis(
        subreddit,
        analyses,
        dimension_scores,
        diversity,
        clusters,
        start_date,
        end_date,
        analyzer,
    )

    # Save to database if requested
    if save_analysis and analyses:
        _save_political_dimensions_analysis(
            sub.id,
            analyses,
            dimension_scores,
            diversity,
            clusters,
            start_date,
            end_date,
        )
        console.print("\n[green]Analysis saved to database.[/green]")


@app.command(name="political-compass")
@require_auth
def political_compass(
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save visualization to file"
    ),
    ctx: typer.Context = typer.Context,
):
    """Generate political compass visualization for a subreddit."""
    # Validate subreddit
    sub = _validate_subreddit(subreddit)
    if not sub:
        raise typer.Exit(1)

    # Check if we have existing analysis
    with get_session() as session:
        recent_analysis = (
            session.query(SubredditPoliticalDimensions)
            .filter(
                SubredditPoliticalDimensions.subreddit_id == sub.id,
                SubredditPoliticalDimensions.analysis_end_date
                >= datetime.utcnow() - timedelta(days=7),
            )
            .order_by(SubredditPoliticalDimensions.created_at.desc())
            .first()
        )

        if recent_analysis:
            _display_political_compass(subreddit, recent_analysis)
        else:
            console.print(
                "[yellow]No recent political analysis found. Run 'analyze dimensions' first.[/yellow]"
            )
            raise typer.Exit(1)


@app.command(name="political-diversity")
@require_auth
def analyze_political_diversity(
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    ctx: typer.Context = typer.Context,
):
    """Analyze political diversity in a subreddit."""
    # Validate subreddit
    sub = _validate_subreddit(subreddit)
    if not sub:
        raise typer.Exit(1)

    # Initialize analyzer
    analyzer = PoliticalDimensionsAnalyzer()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Analyzing political diversity...", total=None)

        with get_session() as session:
            # Get posts
            posts = (
                session.query(Post)
                .filter(
                    Post.subreddit_id == sub.id,
                    Post.created_utc >= start_date,
                    Post.created_utc <= end_date,
                )
                .limit(200)
                .all()
            )

            # Get comments
            post_ids = [p.id for p in posts]
            comments = (
                session.query(Comment)
                .filter(Comment.post_id.in_(post_ids))
                .limit(500)
                .all()
            )

            # Analyze all content
            analyses = []

            for post in posts:
                text = f"{post.title} {post.selftext or ''}"
                result = analyzer.analyze_political_dimensions(text)
                if result.analysis_quality > 0.3:
                    analyses.append(
                        {
                            "economic": result.dimensions.get("economic", {}),
                            "social": result.dimensions.get("social", {}),
                            "governance": result.dimensions.get("governance", {}),
                            "analysis_quality": result.analysis_quality,
                            "type": "post",
                        }
                    )

            for comment in comments[:200]:  # Limit for performance
                if comment.body and len(comment.body) > 50:
                    result = analyzer.analyze_political_dimensions(comment.body)
                    if result.analysis_quality > 0.3:
                        analyses.append(
                            {
                                "economic": result.dimensions.get("economic", {}),
                                "social": result.dimensions.get("social", {}),
                                "governance": result.dimensions.get("governance", {}),
                                "analysis_quality": result.analysis_quality,
                                "type": "comment",
                            }
                        )

            # Calculate diversity metrics
            diversity = calculate_political_diversity(analyses)
            clusters = identify_political_clusters(analyses)

    # Display results
    _display_diversity_analysis(
        subreddit, analyses, diversity, clusters, start_date, end_date
    )


def _display_political_dimensions_analysis(
    subreddit: str,
    analyses: List[Dict],
    dimension_scores: Dict[str, List[float]],
    diversity: float,
    clusters: Dict,
    start_date: datetime,
    end_date: datetime,
    analyzer: PoliticalDimensionsAnalyzer,
):
    """Display political dimensions analysis results."""
    console.print(f"\n[bold]Political Dimensions Analysis for r/{subreddit}[/bold]")
    console.print(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    console.print(f"Posts analyzed: {len(analyses)}\n")

    # Dimension averages
    table = Table(title="Average Political Positions", show_header=True)
    table.add_column("Dimension", style="cyan")
    table.add_column("Average Score", justify="right")
    table.add_column("Position", style="yellow")
    table.add_column("Std Dev", justify="right")

    for dim_name, scores in dimension_scores.items():
        if scores:
            avg_score = np.mean(scores)
            std_dev = np.std(scores)

            # Get label for average position
            if dim_name == "economic":
                dimension = analyzer.dimensions["economic"]
            elif dim_name == "social":
                dimension = analyzer.dimensions["social"]
            else:
                dimension = analyzer.dimensions["governance"]

            label = dimension.get_label(avg_score)

            table.add_row(
                dim_name.capitalize(), f"{avg_score:+.3f}", label, f"{std_dev:.3f}"
            )

    console.print(table)

    # Political diversity
    diversity_panel = Panel(
        f"Political Diversity Index: {diversity:.2f}/1.0\n"
        f"Interpretation: {'High' if diversity > 0.7 else 'Moderate' if diversity > 0.4 else 'Low'} diversity",
        title="Diversity Metrics",
        border_style="green",
    )
    console.print(diversity_panel)

    # Political clusters
    if clusters["clusters"]:
        console.print("\n[bold]Political Clusters Identified:[/bold]")
        cluster_table = Table(show_header=True)
        cluster_table.add_column("Cluster", style="cyan")
        cluster_table.add_column("Size", justify="right")
        cluster_table.add_column("Percentage", justify="right")
        cluster_table.add_column("Description")

        for cluster_name, cluster_data in clusters["clusters"].items():
            cluster_table.add_row(
                cluster_data["label"],
                str(cluster_data["size"]),
                f"{cluster_data['percentage']:.1f}%",
                cluster_name.replace("_", " ").title(),
            )

        console.print(cluster_table)


def _display_political_compass(subreddit: str, analysis: SubredditPoliticalDimensions):
    """Display ASCII political compass visualization."""
    console.print(f"\n[bold]Political Compass for r/{subreddit}[/bold]")
    console.print(
        f"Period: {analysis.analysis_start_date.strftime('%Y-%m-%d')} to {analysis.analysis_end_date.strftime('%Y-%m-%d')}\n"
    )

    # Create ASCII compass
    compass_text = """
                        Liberty (+1.0)
                             |
                             |
    Planned (-1.0) ----------+---------- Market (+1.0)
                             |
                             |
                        Authority (-1.0)
    """

    console.print(compass_text)

    # Position summary
    position_text = f"""
    Average Position:
    - Economic: {analysis.avg_economic_score:+.3f} ({"Market" if analysis.avg_economic_score > 0 else "Planned"}-leaning)
    - Social: {analysis.avg_social_score:+.3f} ({"Liberty" if analysis.avg_social_score > 0 else "Authority"}-leaning)

    Governance: {analysis.avg_governance_score:+.3f} ({"Decentralized" if analysis.avg_governance_score > 0 else "Centralized"})

    Political Diversity: {analysis.political_diversity_index:.2f}/1.0
    Confidence Level: {analysis.avg_confidence_level:.1%}
    """

    console.print(position_text)


def _display_diversity_analysis(
    subreddit: str,
    analyses: List[Dict],
    diversity: float,
    clusters: Dict,
    start_date: datetime,
    end_date: datetime,
):
    """Display political diversity analysis."""
    console.print(f"\n[bold]Political Diversity Analysis for r/{subreddit}[/bold]")
    console.print(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    console.print(f"Content analyzed: {len(analyses)} items\n")

    # Diversity score with interpretation
    interpretation = (
        "High" if diversity > 0.7 else "Moderate" if diversity > 0.4 else "Low"
    )
    color = "green" if diversity > 0.7 else "yellow" if diversity > 0.4 else "red"

    diversity_text = Text()
    diversity_text.append(
        f"Political Diversity Index: {diversity:.3f}/1.0\n", style="bold"
    )
    diversity_text.append(
        f"Interpretation: {interpretation} political diversity\n", style=color
    )
    diversity_text.append("\n")

    if diversity > 0.7:
        diversity_text.append(
            "This community shows a wide range of political viewpoints across multiple dimensions."
        )
    elif diversity > 0.4:
        diversity_text.append(
            "This community has moderate political diversity with some clustering of viewpoints."
        )
    else:
        diversity_text.append(
            "This community shows low political diversity, suggesting an echo chamber effect."
        )

    console.print(
        Panel(diversity_text, title="Diversity Assessment", border_style=color)
    )

    # Show dimension spreads
    if analyses:
        console.print("\n[bold]Dimension Spreads:[/bold]")

        for dimension in ["economic", "social", "governance"]:
            scores = [
                a[dimension]["score"]
                for a in analyses
                if dimension in a and "score" in a[dimension]
            ]
            if scores:
                min_score = min(scores)
                max_score = max(scores)
                spread = max_score - min_score

                console.print(f"\n{dimension.capitalize()}:")
                console.print(f"  Range: [{min_score:.2f}, {max_score:.2f}]")
                console.print(f"  Spread: {spread:.2f}")

                # Visual representation
                histogram = _create_simple_histogram(scores, bins=5)
                console.print(f"  Distribution: {histogram}")

    # Political groups
    if clusters["clusters"]:
        console.print("\n[bold]Distinct Political Groups:[/bold]")

        for cluster_name, cluster_data in sorted(
            clusters["clusters"].items(), key=lambda x: x[1]["size"], reverse=True
        ):
            console.print(
                f"\n• {cluster_data['label']} ({cluster_data['percentage']:.1f}%)"
            )
            console.print(f"  Economic: {cluster_data['centroid']['economic']:+.2f}")
            console.print(f"  Social: {cluster_data['centroid']['social']:+.2f}")
            console.print(
                f"  Governance: {cluster_data['centroid']['governance']:+.2f}"
            )


def _create_simple_histogram(values: List[float], bins: int = 5) -> str:
    """Create a simple ASCII histogram."""
    if not values:
        return ""

    # Create bins
    min_val = min(values)
    max_val = max(values)
    bin_width = (max_val - min_val) / bins if max_val > min_val else 1

    # Count values in each bin
    bin_counts = [0] * bins
    for value in values:
        bin_idx = min(int((value - min_val) / bin_width), bins - 1)
        bin_counts[bin_idx] += 1

    # Create visual
    max_count = max(bin_counts) if bin_counts else 1
    histogram = ""

    for count in bin_counts:
        bar_length = int((count / max_count) * 10)
        histogram += "█" * bar_length + "░" * (10 - bar_length) + " "

    return histogram.strip()


def _save_political_dimensions_analysis(
    subreddit_id: int,
    analyses: List[Dict],
    dimension_scores: Dict[str, List[float]],
    diversity: float,
    clusters: Dict,
    start_date: datetime,
    end_date: datetime,
):
    """Save political dimensions analysis to database."""
    with get_session() as session:
        # Create aggregate analysis record
        political_dims = SubredditPoliticalDimensions(
            subreddit_id=subreddit_id,
            analysis_start_date=start_date,
            analysis_end_date=end_date,
            avg_economic_score=(
                np.mean(dimension_scores["economic"])
                if dimension_scores["economic"]
                else 0.0
            ),
            economic_std_dev=(
                np.std(dimension_scores["economic"])
                if dimension_scores["economic"]
                else 0.0
            ),
            avg_social_score=(
                np.mean(dimension_scores["social"])
                if dimension_scores["social"]
                else 0.0
            ),
            social_std_dev=(
                np.std(dimension_scores["social"])
                if dimension_scores["social"]
                else 0.0
            ),
            avg_governance_score=(
                np.mean(dimension_scores["governance"])
                if dimension_scores["governance"]
                else 0.0
            ),
            governance_std_dev=(
                np.std(dimension_scores["governance"])
                if dimension_scores["governance"]
                else 0.0
            ),
            political_diversity_index=diversity,
            political_clusters=clusters["clusters"] if clusters else {},
            total_posts_analyzed=len(analyses),
            avg_confidence_level=(
                np.mean([a["analysis_quality"] for a in analyses]) if analyses else 0.0
            ),
        )

        session.add(political_dims)
        session.commit()


if __name__ == "__main__":
    app()
