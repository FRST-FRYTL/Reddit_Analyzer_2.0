"""NLP analysis CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from typing import Optional
from datetime import datetime
from sqlalchemy import func
import logging

from reddit_analyzer.cli.utils.auth_manager import cli_auth
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.subreddit import Subreddit
from reddit_analyzer.models.text_analysis import TextAnalysis
from reddit_analyzer.models.topic import Topic
from reddit_analyzer.database import get_db
from reddit_analyzer.services.nlp_service import get_nlp_service

nlp_app = typer.Typer(help="NLP analysis commands")
console = Console()
logger = logging.getLogger(__name__)


@nlp_app.command("analyze")
@cli_auth.require_auth()
def analyze_posts(
    subreddit: Optional[str] = typer.Option(None, help="Specific subreddit to analyze"),
    limit: int = typer.Option(100, help="Maximum number of posts to analyze"),
    reanalyze: bool = typer.Option(
        False, "--reanalyze", help="Re-analyze posts with existing analysis"
    ),
    all_posts: bool = typer.Option(
        False, "--all", help="Analyze all posts without NLP data"
    ),
):
    """Analyze posts without NLP data or re-analyze existing posts."""
    try:
        db = next(get_db())
        nlp_service = get_nlp_service()

        # Build query for posts
        query = db.query(Post)

        # Filter by subreddit if specified
        if subreddit:
            subreddit_obj = (
                db.query(Subreddit)
                .filter(func.lower(Subreddit.name) == subreddit.lower())
                .first()
            )
            if not subreddit_obj:
                console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
                raise typer.Exit(1)
            query = query.filter(Post.subreddit_id == subreddit_obj.id)

        # Filter posts based on analysis status
        if not reanalyze:
            # Get posts without analysis
            analyzed_post_ids = db.query(TextAnalysis.post_id).subquery()
            query = query.filter(~Post.id.in_(analyzed_post_ids))

        # Apply limit unless --all is specified
        if not all_posts:
            query = query.limit(limit)

        posts = query.all()

        if not posts:
            if reanalyze:
                console.print("📭 No posts found to re-analyze", style="yellow")
            else:
                console.print("✅ All posts already have NLP analysis", style="green")
            return

        console.print(
            f"🧠 {'Re-analyzing' if reanalyze else 'Analyzing'} {len(posts)} posts..."
        )

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Processing NLP analysis...", total=len(posts)
            )

            analyzed_count = 0
            failed_count = 0

            for post in posts:
                try:
                    # Combine title and body for analysis
                    full_text = f"{post.title}"
                    if post.selftext:
                        full_text += f"\n\n{post.selftext}"

                    # Analyze text
                    result = nlp_service.analyze_text(full_text, post_id=post.id)

                    if result.get("sentiment"):
                        analyzed_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    console.print(
                        f"⚠️  Failed to analyze post {post.id}: {e}", style="yellow"
                    )
                    failed_count += 1

                progress.update(task, advance=1)

        console.print(f"✅ Successfully analyzed {analyzed_count} posts", style="green")
        if failed_count > 0:
            console.print(f"⚠️  Failed to analyze {failed_count} posts", style="yellow")

    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@nlp_app.command("topics")
@cli_auth.require_auth()
def show_topics(
    subreddit: str = typer.Argument(..., help="Subreddit name to analyze"),
    num_topics: int = typer.Option(10, help="Number of topics to discover"),
    num_words: int = typer.Option(10, help="Number of words per topic"),
):
    """Discover and display topics in a subreddit."""
    try:
        db = next(get_db())
        nlp_service = get_nlp_service()

        # Find subreddit
        subreddit_obj = (
            db.query(Subreddit)
            .filter(func.lower(Subreddit.name) == subreddit.lower())
            .first()
        )
        if not subreddit_obj:
            console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
            raise typer.Exit(1)

        # Get posts with text
        posts = (
            db.query(Post)
            .filter(Post.subreddit_id == subreddit_obj.id)
            .filter(Post.selftext != "")
            .limit(1000)
            .all()
        )

        if len(posts) < 10:
            console.print(
                f"❌ Not enough posts with text content in r/{subreddit} for topic modeling",
                style="red",
            )
            console.print(
                f"💡 Need at least 10 posts, found {len(posts)}", style="yellow"
            )
            return

        console.print(f"🔍 Discovering topics in r/{subreddit}...")

        # Prepare texts for topic modeling
        texts = []
        for post in posts:
            full_text = f"{post.title}"
            if post.selftext:
                full_text += f"\n\n{post.selftext}"
            texts.append(full_text)

        # Fit topic model
        with console.status("[cyan]Training topic model..."):
            success = nlp_service.fit_topic_model(texts, num_topics=num_topics)
            if not success:
                console.print("❌ Failed to train topic model", style="red")
                return

        # Get topics
        topics = nlp_service.get_topics(num_words=num_words)

        if not topics:
            console.print("❌ No topics discovered", style="red")
            return

        # Display topics
        console.print(f"\n📚 Topic Analysis for r/{subreddit}")
        console.print("═" * 50)

        for i, topic in enumerate(topics):
            # Topic header
            console.print(f"\n[bold cyan]Topic {i + 1}[/bold cyan]")

            # Keywords table
            keywords_table = Table(show_header=False, box=None)
            keywords_table.add_column("Keyword", style="green")
            keywords_table.add_column("Weight", style="yellow")

            for word, weight in topic.get("words", [])[:num_words]:
                keywords_table.add_row(word, f"{weight:.3f}")

            console.print(keywords_table)

            # Find sample posts for this topic
            # This is a simplified approach - in production, you'd use the topic model's predictions
            sample_posts = []
            topic_words = [w[0] for w in topic.get("words", [])[:5]]

            for post in posts[:100]:  # Check first 100 posts
                text_lower = f"{post.title} {post.selftext}".lower()
                word_count = sum(1 for word in topic_words if word in text_lower)
                if word_count >= 2:  # At least 2 topic words
                    sample_posts.append(
                        post.title[:60] + "..." if len(post.title) > 60 else post.title
                    )
                    if len(sample_posts) >= 3:
                        break

            if sample_posts:
                console.print("\n[dim]Sample posts:[/dim]")
                for j, title in enumerate(sample_posts, 1):
                    console.print(f"  {j}. {title}", style="dim")

        # Save topics to database
        console.print("\n💾 Saving topics to database...")

        for i, topic_data in enumerate(topics):
            topic = Topic(
                subreddit_id=subreddit_obj.id,
                topic_id=i,
                keywords=[w[0] for w in topic_data.get("words", [])[:20]],
                keyword_weights=[w[1] for w in topic_data.get("words", [])[:20]],
                coherence_score=topic_data.get("coherence", 0.0),
                created_at=datetime.utcnow(),
            )
            db.add(topic)

        db.commit()
        console.print("✅ Topics saved successfully", style="green")

    except Exception as e:
        console.print(f"❌ Topic analysis failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@nlp_app.command("keywords")
@cli_auth.require_auth()
def extract_keywords(
    subreddit: str = typer.Argument(..., help="Subreddit name to analyze"),
    top_n: int = typer.Option(20, help="Number of top keywords to show"),
    days: int = typer.Option(7, help="Number of days to analyze"),
):
    """Extract top keywords from a subreddit."""
    try:
        db = next(get_db())
        nlp_service = get_nlp_service()

        # Find subreddit
        subreddit_obj = (
            db.query(Subreddit)
            .filter(func.lower(Subreddit.name) == subreddit.lower())
            .first()
        )
        if not subreddit_obj:
            console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
            raise typer.Exit(1)

        # Get recent posts
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        posts = (
            db.query(Post)
            .filter(Post.subreddit_id == subreddit_obj.id)
            .filter(Post.created_at >= cutoff_date)
            .all()
        )

        if not posts:
            console.print(
                f"📭 No posts found in r/{subreddit} from the last {days} days",
                style="yellow",
            )
            return

        console.print(
            f"🔤 Extracting keywords from {len(posts)} posts in r/{subreddit}..."
        )

        # Combine all post texts
        all_texts = []
        for post in posts:
            full_text = f"{post.title}"
            if post.selftext:
                full_text += f" {post.selftext}"
            all_texts.append(full_text)

        # Extract keywords
        with console.status("[cyan]Analyzing keywords..."):
            keywords = nlp_service.extract_keywords(all_texts, num_keywords=top_n)

        if not keywords:
            console.print("❌ No keywords extracted", style="red")
            return

        # Display keywords
        console.print(f"\n🔑 Top Keywords in r/{subreddit}")
        console.print("═" * 40)
        console.print(
            f"[dim]Based on {len(posts)} posts from the last {days} days[/dim]\n"
        )

        # Create keywords table
        keywords_table = Table(title="Keywords by Frequency")
        keywords_table.add_column("Rank", style="cyan", width=6)
        keywords_table.add_column("Keyword", style="green")
        keywords_table.add_column("Occurrences", style="yellow")

        # Count keyword occurrences (simplified - in production use TF-IDF scores)
        combined_text = " ".join(all_texts).lower()
        keyword_counts = []

        for keyword in keywords:
            count = combined_text.count(keyword.lower())
            keyword_counts.append((keyword, count))

        # Sort by count and display
        keyword_counts.sort(key=lambda x: x[1], reverse=True)

        for i, (keyword, count) in enumerate(keyword_counts[:top_n], 1):
            keywords_table.add_row(str(i), keyword, f"{count:,}")

        console.print(keywords_table)

        # Show trending keywords from TextAnalysis if available
        keyword_analysis = (
            db.query(TextAnalysis.keywords)
            .join(Post)
            .filter(Post.subreddit_id == subreddit_obj.id)
            .filter(Post.created_at >= cutoff_date)
            .limit(100)
            .all()
        )

        if keyword_analysis:
            # Aggregate keywords from analyses
            all_analyzed_keywords = []
            for analysis in keyword_analysis:
                if analysis.keywords:
                    all_analyzed_keywords.extend(analysis.keywords)

            if all_analyzed_keywords:
                # Count frequency
                from collections import Counter

                keyword_freq = Counter(all_analyzed_keywords)

                console.print("\n📈 Trending Keywords (from NLP analysis)")
                trending_table = Table()
                trending_table.add_column("Keyword", style="cyan")
                trending_table.add_column("Frequency", style="green")

                for keyword, freq in keyword_freq.most_common(10):
                    trending_table.add_row(keyword, str(freq))

                console.print(trending_table)

    except Exception as e:
        console.print(f"❌ Keyword extraction failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@nlp_app.command("emotions")
@cli_auth.require_auth()
def analyze_emotions(
    subreddit: Optional[str] = typer.Option(None, help="Subreddit to analyze"),
    post_id: Optional[str] = typer.Option(None, help="Specific post ID to analyze"),
):
    """Show emotion analysis for posts."""
    try:
        db = next(get_db())

        if post_id:
            # Analyze specific post
            analysis = (
                db.query(TextAnalysis).filter(TextAnalysis.post_id == post_id).first()
            )

            if not analysis:
                console.print(f"❌ No analysis found for post {post_id}", style="red")
                console.print(
                    "💡 Run 'reddit-analyzer nlp analyze' first", style="yellow"
                )
                return

            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                console.print(f"❌ Post {post_id} not found", style="red")
                return

            # Display emotion analysis
            console.print("\n😊 Emotion Analysis")
            console.print("═" * 40)
            console.print(f"\n[bold]Post:[/bold] {post.title[:80]}...")

            if analysis.emotion_scores:
                emotion_table = Table(title="Emotions Detected")
                emotion_table.add_column("Emotion", style="cyan")
                emotion_table.add_column("Intensity", style="green")
                emotion_table.add_column("Bar", style="yellow")

                # Sort emotions by intensity
                sorted_emotions = sorted(
                    analysis.emotion_scores.items(), key=lambda x: x[1], reverse=True
                )

                for emotion, intensity in sorted_emotions:
                    bar = "█" * int(intensity * 20)
                    emotion_table.add_row(emotion.capitalize(), f"{intensity:.1%}", bar)

                console.print(emotion_table)

                # Dominant emotion
                if sorted_emotions:
                    dominant = sorted_emotions[0]
                    console.print(
                        f"\n[bold]Dominant emotion:[/bold] {dominant[0].capitalize()} ({dominant[1]:.1%})"
                    )
            else:
                console.print("❌ No emotion data available", style="yellow")

        elif subreddit:
            # Analyze subreddit emotions
            subreddit_obj = (
                db.query(Subreddit)
                .filter(func.lower(Subreddit.name) == subreddit.lower())
                .first()
            )
            if not subreddit_obj:
                console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
                raise typer.Exit(1)

            # Get all text analyses for this subreddit
            all_analyses = (
                db.query(TextAnalysis)
                .join(Post)
                .filter(Post.subreddit_id == subreddit_obj.id)
                .limit(1000)
                .all()
            )

            if not all_analyses:
                console.print(f"📭 No posts found for r/{subreddit}", style="yellow")
                return

            # Check which analyses have emotion data
            analyses_with_emotions = []
            analyses_without_emotions = []

            for analysis in all_analyses:
                if analysis.emotion_scores and any(analysis.emotion_scores.values()):
                    analyses_with_emotions.append(analysis)
                else:
                    analyses_without_emotions.append(analysis)

            # If we have analyses without emotions, analyze them now
            if analyses_without_emotions:
                console.print(
                    f"🔄 Analyzing emotions for {len(analyses_without_emotions)} posts..."
                )

                from reddit_analyzer.processing.emotion_analyzer import EmotionAnalyzer

                emotion_analyzer = EmotionAnalyzer()

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "Analyzing emotions...", total=len(analyses_without_emotions)
                    )

                    for analysis in analyses_without_emotions:
                        try:
                            # Get the post text
                            post = (
                                db.query(Post)
                                .filter(Post.id == analysis.post_id)
                                .first()
                            )
                            if post:
                                text = f"{post.title} {post.selftext or ''}"
                                emotions = emotion_analyzer.analyze_emotions(text)

                                # Update the analysis with emotion scores
                                analysis.emotion_scores = emotions
                                analyses_with_emotions.append(analysis)

                            progress.update(task, advance=1)
                        except Exception as e:
                            logger.warning(
                                f"Failed to analyze emotions for post {analysis.post_id}: {e}"
                            )
                            progress.update(task, advance=1)

                # Commit the updates
                try:
                    db.commit()
                    console.print(
                        f"✅ Emotion analysis complete for {len(analyses_without_emotions)} posts"
                    )
                except Exception as e:
                    logger.error(f"Failed to save emotion analysis: {e}")
                    db.rollback()

            # Use all analyses that now have emotions
            analyses = analyses_with_emotions

            if not analyses:
                console.print(
                    f"📭 No emotion analysis could be performed for r/{subreddit}",
                    style="yellow",
                )
                return

            # Aggregate emotions
            emotion_totals = {}
            emotion_counts = {}

            for analysis in analyses:
                for emotion, intensity in analysis.emotion_scores.items():
                    emotion_totals[emotion] = emotion_totals.get(emotion, 0) + intensity
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            # Calculate averages
            emotion_averages = {
                emotion: total / emotion_counts[emotion]
                for emotion, total in emotion_totals.items()
            }

            # Display results
            console.print(f"\n😊 Emotion Summary for r/{subreddit}")
            console.print("═" * 50)
            console.print(
                f"[dim]Based on {len(analyses)} posts with emotion data[/dim]\n"
            )

            # Overall distribution
            total_intensity = sum(emotion_averages.values())

            dist_table = Table(title="Overall Emotion Distribution")
            dist_table.add_column("Emotion", style="cyan")
            dist_table.add_column("Average Intensity", style="green")
            dist_table.add_column("Distribution", style="yellow")

            for emotion, avg in sorted(
                emotion_averages.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (avg / total_intensity) * 100 if total_intensity > 0 else 0
                bar = "█" * int(percentage / 2)
                dist_table.add_row(
                    emotion.capitalize(), f"{avg:.1%}", f"{bar} {percentage:.1f}%"
                )

            console.print(dist_table)

            # Find most emotional posts
            most_emotional = []
            for analysis in analyses:
                if analysis.emotion_scores:
                    max_emotion = max(
                        analysis.emotion_scores.items(), key=lambda x: x[1]
                    )
                    if max_emotion[1] > 0.7:  # High intensity
                        post = (
                            db.query(Post).filter(Post.id == analysis.post_id).first()
                        )
                        if post:
                            most_emotional.append(
                                {
                                    "title": (
                                        post.title[:60] + "..."
                                        if len(post.title) > 60
                                        else post.title
                                    ),
                                    "emotion": max_emotion[0],
                                    "intensity": max_emotion[1],
                                }
                            )

            if most_emotional:
                # Sort by intensity and show top 5
                most_emotional.sort(key=lambda x: x["intensity"], reverse=True)

                emotional_table = Table(title="🎭 Most Emotional Posts")
                emotional_table.add_column("Post", style="cyan", max_width=60)
                emotional_table.add_column("Dominant Emotion", style="green")
                emotional_table.add_column("Intensity", style="yellow")

                for post_info in most_emotional[:5]:
                    emotional_table.add_row(
                        post_info["title"],
                        post_info["emotion"].capitalize(),
                        f"{post_info['intensity']:.1%}",
                    )

                console.print(emotional_table)

        else:
            console.print(
                "❌ Please specify either --subreddit or --post-id", style="red"
            )

    except Exception as e:
        console.print(f"❌ Emotion analysis failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


@nlp_app.command("export")
@cli_auth.require_auth()
def export_nlp_data(
    subreddit: str = typer.Argument(..., help="Subreddit to export"),
    format: str = typer.Option("csv", help="Export format: csv or json"),
    output: str = typer.Option(..., help="Output file path"),
    limit: int = typer.Option(1000, help="Maximum number of records to export"),
):
    """Export NLP analysis results."""
    try:
        db = next(get_db())

        # Find subreddit
        subreddit_obj = (
            db.query(Subreddit)
            .filter(func.lower(Subreddit.name) == subreddit.lower())
            .first()
        )
        if not subreddit_obj:
            console.print(f"❌ Subreddit r/{subreddit} not found", style="red")
            raise typer.Exit(1)

        # Get posts with NLP analysis
        results = (
            db.query(Post, TextAnalysis)
            .join(TextAnalysis, Post.id == TextAnalysis.post_id)
            .filter(Post.subreddit_id == subreddit_obj.id)
            .limit(limit)
            .all()
        )

        if not results:
            console.print(f"📭 No NLP data found for r/{subreddit}", style="yellow")
            return

        console.print(f"📤 Exporting {len(results)} records to {output}...")

        if format.lower() == "csv":
            import csv

            with open(output, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "post_id",
                    "title",
                    "created_at",
                    "score",
                    "num_comments",
                    "sentiment_score",
                    "sentiment_label",
                    "confidence",
                    "keywords",
                    "dominant_emotion",
                    "language",
                    "readability",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for post, analysis in results:
                    # Get dominant emotion
                    dominant_emotion = ""
                    if analysis.emotion_scores:
                        emotion_sorted = sorted(
                            analysis.emotion_scores.items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                        if emotion_sorted:
                            dominant_emotion = (
                                f"{emotion_sorted[0][0]}:{emotion_sorted[0][1]:.2f}"
                            )

                    writer.writerow(
                        {
                            "post_id": post.id,
                            "title": post.title,
                            "created_at": post.created_at.isoformat(),
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "sentiment_score": analysis.sentiment_score,
                            "sentiment_label": analysis.sentiment_label,
                            "confidence": analysis.confidence_score,
                            "keywords": (
                                ";".join(analysis.keywords[:5])
                                if analysis.keywords
                                else ""
                            ),
                            "dominant_emotion": dominant_emotion,
                            "language": analysis.language,
                            "readability": analysis.readability_score,
                        }
                    )

        elif format.lower() == "json":
            import json

            export_data = []
            for post, analysis in results:
                export_data.append(
                    {
                        "post": {
                            "id": post.id,
                            "title": post.title,
                            "body": (
                                post.selftext[:200] + "..."
                                if post.selftext and len(post.selftext) > 200
                                else post.selftext
                            ),
                            "created_at": post.created_at.isoformat(),
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "url": post.url,
                        },
                        "nlp_analysis": {
                            "sentiment": {
                                "score": analysis.sentiment_score,
                                "label": analysis.sentiment_label,
                                "confidence": analysis.confidence_score,
                            },
                            "keywords": (
                                analysis.keywords[:10] if analysis.keywords else []
                            ),
                            "entities": (
                                analysis.entities[:10] if analysis.entities else []
                            ),
                            "emotions": (
                                analysis.emotion_scores
                                if analysis.emotion_scores
                                else {}
                            ),
                            "language": analysis.language,
                            "readability_score": analysis.readability_score,
                            "processed_at": analysis.processed_at.isoformat(),
                        },
                    }
                )

            with open(output, "w", encoding="utf-8") as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

        else:
            console.print(
                f"❌ Unsupported format: {format}. Use 'csv' or 'json'", style="red"
            )
            return

        console.print(f"✅ Exported {len(results)} records to {output}", style="green")

    except Exception as e:
        console.print(f"❌ Export failed: {e}", style="red")
        raise typer.Exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    nlp_app()
