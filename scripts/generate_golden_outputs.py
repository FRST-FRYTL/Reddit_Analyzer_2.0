#!/usr/bin/env python3
"""
Generate golden outputs from real test data.

This script runs various CLI commands on the test data and saves
the outputs as golden files for comparison in tests.
"""

import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Set environment variables BEFORE importing anything
os.environ["DATABASE_URL"] = "sqlite:///tests/fixtures/test_data.db"
os.environ["SKIP_AUTH"] = "true"

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AFTER setting environment variables
from typer.testing import CliRunner
from reddit_analyzer.cli.main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoldenOutputGenerator:
    """Generate golden outputs for testing."""

    def __init__(self):
        """Initialize the generator."""
        self.runner = CliRunner()
        self.output_dir = Path("tests/fixtures/golden_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load test data manifest
        manifest_path = Path("tests/fixtures/test_data_manifest.json")
        if not manifest_path.exists():
            raise FileNotFoundError(
                "Test data manifest not found. Run scripts/collect_test_data.py first."
            )

        with open(manifest_path) as f:
            self.manifest = json.load(f)

        self.subreddits = list(self.manifest["config"]["subreddits"].keys())

        # Define commands to generate outputs for
        self.commands = [
            {
                "name": "topics_analysis",
                "cmd": ["analyze", "topics", "{subreddit}", "--days", "30"],
                "save_metrics": True,
            },
            {
                "name": "sentiment_healthcare",
                "cmd": ["analyze", "sentiment", "{subreddit}", "--topic", "healthcare"],
                "save_metrics": True,
            },
            {
                "name": "quality_analysis",
                "cmd": ["analyze", "quality", "{subreddit}"],
                "save_metrics": True,
            },
            {
                "name": "dimensions_analysis",
                "cmd": ["analyze", "dimensions", "{subreddit}"],
                "save_metrics": True,
            },
            {
                "name": "political_diversity",
                "cmd": ["analyze", "political-diversity", "{subreddit}"],
                "save_metrics": True,
            },
            {
                "name": "help_topics",
                "cmd": ["analyze", "topics", "--help"],
                "save_metrics": False,
            },
        ]

    def generate_all(self):
        """Generate all golden outputs."""
        logger.info("Generating golden outputs...")

        # Generate outputs for first subreddit
        primary_subreddit = self.subreddits[0]

        for command_config in self.commands:
            self._generate_command_output(command_config, primary_subreddit)

        # Generate overlap analysis if we have multiple subreddits
        if len(self.subreddits) >= 2:
            self._generate_overlap_output()

        # Save generation metadata
        self._save_metadata()

        logger.info(f"Golden outputs saved to {self.output_dir}")

    def _generate_command_output(self, command_config: dict, subreddit: str):
        """Generate output for a single command."""
        name = command_config["name"]
        cmd = [arg.format(subreddit=subreddit) for arg in command_config["cmd"]]

        logger.info(f"Generating output for: {' '.join(cmd)}")

        # Run command
        result = self.runner.invoke(app, cmd)

        if result.exit_code != 0:
            logger.warning(f"Command failed with exit code {result.exit_code}")
            logger.warning(f"Output: {result.stdout}")

        # Save raw output
        output_file = self.output_dir / f"{name}_stdout.txt"
        with open(output_file, "w") as f:
            f.write(result.stdout)

        # Extract and save metrics if requested
        if command_config.get("save_metrics", False):
            metrics = self._extract_metrics(name, result.stdout)
            if metrics:
                metrics_file = self.output_dir / f"{name}_metrics.json"
                with open(metrics_file, "w") as f:
                    json.dump(metrics, f, indent=2)

    def _generate_overlap_output(self):
        """Generate overlap analysis output."""
        sub1, sub2 = self.subreddits[:2]
        cmd = ["analyze", "overlap", sub1, sub2]

        logger.info(f"Generating overlap output for: {sub1} and {sub2}")

        result = self.runner.invoke(app, cmd)

        output_file = self.output_dir / "overlap_analysis_stdout.txt"
        with open(output_file, "w") as f:
            f.write(result.stdout)

    def _extract_metrics(self, command_name: str, output: str) -> dict:
        """Extract key metrics from command output."""
        import re

        metrics = {}

        if "topics" in command_name:
            # Extract topic percentages
            topic_pattern = r"(\w+)\s+(\d+\.\d+)%"
            topics = re.findall(topic_pattern, output)
            if topics:
                metrics["topics"] = {topic: float(pct) for topic, pct in topics[:5]}

            # Extract post count
            post_match = re.search(r"Posts analyzed:\s*(\d+)", output)
            if post_match:
                metrics["posts_analyzed"] = int(post_match.group(1))

        elif "sentiment" in command_name:
            # Extract sentiment scores
            sentiment_pattern = r"(positive|negative|neutral):\s*(\d+\.\d+)"
            sentiments = re.findall(sentiment_pattern, output.lower())
            if sentiments:
                metrics["sentiments"] = {
                    sent: float(score) for sent, score in sentiments
                }

        elif "quality" in command_name:
            # Extract quality metrics
            quality_pattern = r"(constructiveness|civility|engagement):\s*(\d+\.\d+)"
            qualities = re.findall(quality_pattern, output.lower())
            if qualities:
                metrics["quality_scores"] = {
                    metric: float(score) for metric, score in qualities
                }

        elif "dimensions" in command_name:
            # Extract dimension scores
            dimension_pattern = r"(economic|social|governance).*?(-?\d+\.\d+)"
            dimensions = re.findall(dimension_pattern, output.lower())
            if dimensions:
                metrics["dimensions"] = {dim: float(score) for dim, score in dimensions}

        elif "diversity" in command_name:
            # Extract diversity index
            diversity_match = re.search(r"diversity.*?(\d+\.\d+)", output.lower())
            if diversity_match:
                metrics["diversity_index"] = float(diversity_match.group(1))

        return metrics

    def _save_metadata(self):
        """Save metadata about golden output generation."""
        metadata = {
            "generated": datetime.now().isoformat(),
            "test_data_manifest": self.manifest["created"],
            "subreddits": self.subreddits,
            "commands": len(self.commands),
            "files_generated": list(sorted(f.name for f in self.output_dir.glob("*"))),
        }

        metadata_file = self.output_dir / "generation_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)


def main():
    """Main entry point."""
    generator = GoldenOutputGenerator()

    try:
        generator.generate_all()
        logger.info("Golden output generation completed successfully!")
    except Exception as e:
        logger.error(f"Failed to generate golden outputs: {e}")
        raise


if __name__ == "__main__":
    main()
