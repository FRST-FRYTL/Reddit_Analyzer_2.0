"""
Advanced NLP analysis CLI commands.

This module provides CLI commands for advanced text analysis features
including emotion detection, stance analysis, argument mining, and more.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json
from pathlib import Path

from reddit_analyzer.services.nlp_service import get_nlp_service
from reddit_analyzer.cli.utils.auth_manager import cli_auth
from reddit_analyzer.database import get_session
from reddit_analyzer.models import Post
from reddit_analyzer.config import get_settings

app = typer.Typer(help="Advanced NLP analysis commands")
console = Console()
settings = get_settings()


@app.command()
@cli_auth.require_auth()
def emotions(
    ctx: typer.Context,
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    limit: int = typer.Option(100, help="Number of posts to analyze"),
    output: Optional[Path] = typer.Option(None, help="Output file for results"),
    detailed: bool = typer.Option(False, help="Show detailed emotion analysis"),
):
    """Analyze emotions in subreddit posts."""
    console.print(f"[bold blue]Analyzing emotions in r/{subreddit}...[/bold blue]")

    # Initialize NLP service with heavy models if available
    nlp_service = get_nlp_service()
    if not settings.NLP_ENABLE_HEAVY_MODELS:
        console.print(
            "[yellow]Heavy models not enabled. Using basic emotion detection.[/yellow]"
        )

    with get_session() as db:
        # Get recent posts
        posts = (
            db.query(Post)
            .filter(Post.subreddit_name == subreddit)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .all()
        )

        if not posts:
            console.print(f"[red]No posts found for r/{subreddit}[/red]")
            return

        console.print(f"Found {len(posts)} posts to analyze")

        # Analyze emotions
        emotion_results = []
        all_emotions = {}

        with console.status("Analyzing emotions..."):
            for post in posts:
                text = f"{post.title}\n{post.body}" if post.body else post.title

                if detailed and nlp_service.emotion_analyzer:
                    result = nlp_service.analyze_emotions_detailed(text)
                else:
                    result = {
                        "emotions": nlp_service.sentiment_analyzer.analyze_emotions(
                            text
                        )
                    }

                emotion_results.append(
                    {
                        "post_id": post.id,
                        "title": (
                            post.title[:50] + "..."
                            if len(post.title) > 50
                            else post.title
                        ),
                        **result,
                    }
                )

                # Aggregate emotions
                for emotion, score in result.get("emotions", {}).items():
                    if emotion not in all_emotions:
                        all_emotions[emotion] = []
                    all_emotions[emotion].append(score)

        # Calculate averages
        emotion_averages = {
            emotion: sum(scores) / len(scores) if scores else 0
            for emotion, scores in all_emotions.items()
        }

        # Display results
        _display_emotion_results(emotion_averages, emotion_results[:10], detailed)

        # Save results if requested
        if output:
            results_data = {
                "subreddit": subreddit,
                "post_count": len(posts),
                "emotion_averages": emotion_averages,
                "detailed_results": emotion_results if detailed else None,
            }

            with open(output, "w") as f:
                json.dump(results_data, f, indent=2)
            console.print(f"[green]Results saved to {output}[/green]")


@app.command()
@cli_auth.require_auth()
def stance(
    ctx: typer.Context,
    text: str = typer.Argument(..., help="Text to analyze"),
    target: str = typer.Argument(..., help="Target topic or entity"),
    context: Optional[str] = typer.Option(None, help="Additional context"),
):
    """Detect stance towards a specific target."""
    if not settings.NLP_ENABLE_HEAVY_MODELS:
        console.print(
            "[red]Stance detection requires heavy models to be enabled.[/red]"
        )
        console.print("Set NLP_ENABLE_HEAVY_MODELS=true in your environment")
        return

    nlp_service = get_nlp_service()

    with console.status("Detecting stance..."):
        result = nlp_service.detect_stance(text, target, context)

    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    # Display results
    panel = Panel(
        f"[bold]Stance:[/bold] {result['stance'].upper()}\n"
        f"[bold]Confidence:[/bold] {result['confidence']:.2%}\n"
        f"[bold]Target:[/bold] {result['target']}",
        title="Stance Detection Result",
        box=box.ROUNDED,
    )
    console.print(panel)

    if result.get("evidence"):
        console.print("\n[bold]Evidence:[/bold]")
        for i, evidence in enumerate(result["evidence"], 1):
            console.print(f"{i}. {evidence}")


@app.command()
@cli_auth.require_auth()
def political(
    ctx: typer.Context,
    text: str = typer.Argument(..., help="Text to analyze"),
    issue: str = typer.Option(
        "general", help="Political issue (e.g., 'gun control', 'climate change')"
    ),
):
    """Analyze political stance on specific issues."""
    if not settings.NLP_ENABLE_HEAVY_MODELS:
        console.print(
            "[red]Political stance detection requires heavy models to be enabled.[/red]"
        )
        return

    nlp_service = get_nlp_service()

    with console.status("Analyzing political stance..."):
        result = nlp_service.analyze_political_stance(text, issue)

    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    # Display results
    panel = Panel(
        f"[bold]Issue:[/bold] {issue}\n"
        f"[bold]Stance:[/bold] {result.get('stance', 'unknown').upper()}\n"
        f"[bold]Political Leaning:[/bold] {result.get('political_leaning', 'neutral').upper()}\n"
        f"[bold]Confidence:[/bold] {result.get('confidence', 0):.2%}",
        title="Political Stance Analysis",
        box=box.ROUNDED,
    )
    console.print(panel)


@app.command()
@cli_auth.require_auth()
def entities(
    ctx: typer.Context,
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    limit: int = typer.Option(50, help="Number of posts to analyze"),
    top_n: int = typer.Option(20, help="Number of top entities to show"),
):
    """Extract and analyze entities in subreddit posts."""
    console.print(f"[bold blue]Extracting entities from r/{subreddit}...[/bold blue]")

    nlp_service = get_nlp_service()

    with get_session() as db:
        posts = (
            db.query(Post)
            .filter(Post.subreddit_name == subreddit)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .all()
        )

        if not posts:
            console.print(f"[red]No posts found for r/{subreddit}[/red]")
            return

        # Extract entities from all posts
        all_entities = {}

        with console.status("Extracting entities..."):
            for post in posts:
                text = f"{post.title}\n{post.body}" if post.body else post.title

                if nlp_service.entity_analyzer:
                    result = nlp_service.extract_entities_advanced(text)
                    entities = result.get("entities", {})
                else:
                    entities = nlp_service.text_processor.extract_entities(text)

                # Aggregate entities
                for ent_type, ent_list in entities.items():
                    if ent_type not in all_entities:
                        all_entities[ent_type] = {}

                    for entity in ent_list:
                        ent_text = (
                            entity.get("text", entity)
                            if isinstance(entity, dict)
                            else entity
                        )
                        all_entities[ent_type][ent_text] = (
                            all_entities[ent_type].get(ent_text, 0) + 1
                        )

        # Display top entities by type
        _display_entity_results(all_entities, top_n)


@app.command()
@cli_auth.require_auth()
def arguments(
    ctx: typer.Context,
    text: str = typer.Argument(..., help="Text to analyze"),
    evaluate: bool = typer.Option(True, help="Evaluate argument quality"),
):
    """Analyze argumentative structure in text."""
    if not settings.NLP_ENABLE_HEAVY_MODELS:
        console.print("[red]Argument mining requires heavy models to be enabled.[/red]")
        return

    nlp_service = get_nlp_service()

    with console.status("Analyzing arguments..."):
        result = nlp_service.analyze_arguments(text)

    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    # Display argument structure
    structure = result.get("structure", {})
    quality = result.get("quality", {})

    console.print("[bold]Argument Structure Analysis[/bold]\n")

    # Display components
    components = structure.get("components", [])
    if components:
        table = Table(title="Argument Components", box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Text", style="white", max_width=50)
        table.add_column("Confidence", style="green")

        for comp in components[:10]:  # Show top 10
            table.add_row(
                comp["type"],
                comp["text"][:50] + "..." if len(comp["text"]) > 50 else comp["text"],
                f"{comp['confidence']:.2f}",
            )

        console.print(table)

    # Display quality metrics
    if evaluate and quality:
        quality_panel = Panel(
            f"[bold]Overall Quality:[/bold] {quality.get('overall_quality', 0):.2%}\n"
            f"[bold]Logical Flow:[/bold] {quality.get('logical_flow', 0):.2%}\n"
            f"[bold]Evidence Support:[/bold] {quality.get('evidence_support', 0):.2%}\n"
            f"[bold]Balance:[/bold] {quality.get('balance', 0):.2%}\n"
            f"[bold]Clarity:[/bold] {quality.get('clarity', 0):.2%}",
            title="Argument Quality Metrics",
            box=box.ROUNDED,
        )
        console.print(quality_panel)

        # Display fallacies if found
        fallacies = quality.get("fallacies", [])
        if fallacies:
            console.print("\n[bold red]Potential Fallacies Detected:[/bold red]")
            for fallacy in fallacies:
                console.print(f"• {fallacy['type']}: {fallacy['description']}")


@app.command()
@cli_auth.require_auth()
def topics_advanced(
    ctx: typer.Context,
    subreddit: str = typer.Argument(..., help="Subreddit to analyze"),
    limit: int = typer.Option(500, help="Number of posts to analyze"),
    method: str = typer.Option(
        "bertopic", help="Topic modeling method (bertopic, nmf, lda)"
    ),
    num_topics: Optional[int] = typer.Option(
        None, help="Number of topics (auto-detected if not specified)"
    ),
):
    """Perform advanced topic modeling on subreddit content."""
    if not settings.NLP_ENABLE_HEAVY_MODELS:
        console.print(
            "[yellow]Heavy models not enabled. Using basic LDA topic modeling.[/yellow]"
        )
        method = "lda"

    console.print(
        f"[bold blue]Running {method.upper()} topic modeling on r/{subreddit}...[/bold blue]"
    )

    nlp_service = get_nlp_service()

    with get_session() as db:
        posts = (
            db.query(Post)
            .filter(Post.subreddit_name == subreddit)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .all()
        )

        if not posts:
            console.print(f"[red]No posts found for r/{subreddit}[/red]")
            return

        # Prepare texts
        texts = []
        for post in posts:
            text = f"{post.title}\n{post.body}" if post.body else post.title
            texts.append(text)

        console.print(f"Analyzing {len(texts)} posts...")

        # Fit topic model
        with console.status("Fitting topic model..."):
            if nlp_service.advanced_topic_modeler and method != "lda":
                # Use advanced topic modeler
                nlp_service.advanced_topic_modeler.method = method
                topics = nlp_service.advanced_topic_modeler.fit_transform(texts)
            else:
                # Use basic topic modeler
                success = nlp_service.fit_topic_model(texts, num_topics or 10)
                if success:
                    topics = {"topics": nlp_service.get_topics()}
                else:
                    console.print("[red]Topic modeling failed[/red]")
                    return

        # Display results
        _display_topic_results(topics, method)


def _display_emotion_results(averages: dict, sample_results: list, detailed: bool):
    """Display emotion analysis results."""
    # Create emotion chart
    table = Table(title="Average Emotion Scores", box=box.ROUNDED)
    table.add_column("Emotion", style="cyan")
    table.add_column("Score", style="white")
    table.add_column("Level", style="green")

    for emotion, score in sorted(averages.items(), key=lambda x: x[1], reverse=True):
        level = "■" * int(score * 10)
        table.add_row(emotion.capitalize(), f"{score:.3f}", level)

    console.print(table)

    # Show sample posts if detailed
    if detailed and sample_results:
        console.print("\n[bold]Sample Post Emotions:[/bold]")
        for result in sample_results:
            console.print(f"\n• {result['title']}")
            if "dominant_emotion" in result:
                console.print(f"  Dominant: {result['dominant_emotion']}")
                console.print(f"  Valence: {result.get('valence', 0):.2f}")


def _display_entity_results(entities: dict, top_n: int):
    """Display entity extraction results."""
    for ent_type, ent_dict in entities.items():
        if not ent_dict:
            continue

        table = Table(title=f"Top {ent_type} Entities", box=box.ROUNDED)
        table.add_column("Entity", style="cyan")
        table.add_column("Count", style="white")

        # Sort by count and get top N
        sorted_entities = sorted(ent_dict.items(), key=lambda x: x[1], reverse=True)
        for entity, count in sorted_entities[:top_n]:
            table.add_row(entity, str(count))

        console.print(table)
        console.print()


def _display_topic_results(topics: dict, method: str):
    """Display topic modeling results."""
    topic_list = topics.get("topics", [])

    if not topic_list:
        console.print("[yellow]No topics found[/yellow]")
        return

    console.print(
        f"\n[bold]Discovered {len(topic_list)} topics using {method.upper()}:[/bold]\n"
    )

    for topic in topic_list:
        topic_id = topic.get("topic_id", "?")
        size = topic.get("size", 0)

        # Get topic words
        topic_words = topics.get("topic_words", {}).get(topic_id, [])
        if topic_words:
            words = [w["word"] for w in topic_words[:5]]
            word_str = ", ".join(words)
        else:
            word_str = "No words available"

        console.print(f"[bold]Topic {topic_id}[/bold] ({size} documents)")
        console.print(f"Keywords: {word_str}")
        console.print()

    # Show topic diversity if available
    if topics.get("topic_words"):
        # Calculate simple diversity metric based on word overlap
        all_words = set()
        topic_word_sets = []
        for topic_id, words in topics["topic_words"].items():
            word_set = set(w["word"] for w in words[:10])
            topic_word_sets.append(word_set)
            all_words.update(word_set)

        if len(topic_word_sets) > 1:
            # Calculate Jaccard diversity
            overlaps = []
            for i in range(len(topic_word_sets)):
                for j in range(i + 1, len(topic_word_sets)):
                    intersection = len(topic_word_sets[i] & topic_word_sets[j])
                    union = len(topic_word_sets[i] | topic_word_sets[j])
                    if union > 0:
                        overlaps.append(intersection / union)

            if overlaps:
                diversity = 1 - (sum(overlaps) / len(overlaps))
                console.print(f"[bold]Topic Diversity:[/bold] {diversity:.2f}")


if __name__ == "__main__":
    app()
