#!/usr/bin/env python3
"""Test script to verify both political compass and Phase 5 features are working."""

import subprocess
import sys
import os

# Set environment to skip auth
os.environ["SKIP_AUTH"] = "true"


def run_command(cmd):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"


def test_political_compass_features():
    """Test political compass (analyze) commands."""
    print("\n=== Testing Political Compass Features ===")

    commands = [
        ("Help", "uv run reddit-analyzer analyze --help"),
        ("Topics help", "uv run reddit-analyzer analyze topics --help"),
        ("Sentiment help", "uv run reddit-analyzer analyze sentiment --help"),
        (
            "Political compass help",
            "uv run reddit-analyzer analyze political-compass --help",
        ),
        ("Dimensions help", "uv run reddit-analyzer analyze dimensions --help"),
        ("Diversity help", "uv run reddit-analyzer analyze political-diversity --help"),
    ]

    results = []
    for name, cmd in commands:
        success, stdout, stderr = run_command(cmd)
        results.append((name, success, stdout, stderr))
        print(f"  {name}: {'✓' if success else '✗'}")

    return results


def test_phase5_features():
    """Test Phase 5 heavy model (analyze-heavy) commands."""
    print("\n=== Testing Phase 5 Heavy Model Features ===")

    commands = [
        ("Help", "uv run reddit-analyzer analyze-heavy --help"),
        ("Emotions help", "uv run reddit-analyzer analyze-heavy emotions --help"),
        ("Stance help", "uv run reddit-analyzer analyze-heavy stance --help"),
        ("Entities help", "uv run reddit-analyzer analyze-heavy entities --help"),
        ("Arguments help", "uv run reddit-analyzer analyze-heavy arguments --help"),
        (
            "Advanced topics help",
            "uv run reddit-analyzer analyze-heavy topics-advanced --help",
        ),
    ]

    results = []
    for name, cmd in commands:
        success, stdout, stderr = run_command(cmd)
        results.append((name, success, stdout, stderr))
        print(f"  {name}: {'✓' if success else '✗'}")

    return results


def test_service_imports():
    """Test that core services can be imported."""
    print("\n=== Testing Service Imports ===")

    services = [
        (
            "Topic Analyzer",
            "from reddit_analyzer.services.topic_analyzer import TopicAnalyzer",
        ),
        (
            "Political Dimensions",
            "from reddit_analyzer.services.political_dimensions_analyzer import PoliticalDimensionsAnalyzer",
        ),
        (
            "NLP Service",
            "from reddit_analyzer.services.nlp_service import get_nlp_service",
        ),
    ]

    results = []
    for name, import_stmt in services:
        try:
            exec(import_stmt)
            results.append((name, True))
            print(f"  {name}: ✓")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  {name}: ✗ ({e})")

    return results


def main():
    """Run all tests."""
    print("Testing Reddit Analyzer Feature Sets")
    print("=" * 40)

    # Test imports
    import_results = test_service_imports()

    # Test political compass features
    pc_results = test_political_compass_features()

    # Test Phase 5 features
    p5_results = test_phase5_features()

    # Summary
    print("\n=== Summary ===")

    import_success = sum(1 for _, success, *_ in import_results if success)
    print(f"Service imports: {import_success}/{len(import_results)} passed")

    pc_success = sum(1 for _, success, *_ in pc_results if success)
    print(f"Political compass commands: {pc_success}/{len(pc_results)} passed")

    p5_success = sum(1 for _, success, *_ in p5_results if success)
    print(f"Phase 5 commands: {p5_success}/{len(p5_results)} passed")

    total_tests = len(import_results) + len(pc_results) + len(p5_results)
    total_success = import_success + pc_success + p5_success

    print(f"\nTotal: {total_success}/{total_tests} tests passed")

    # Show any errors
    all_results = [
        ("Imports", import_results),
        ("Political Compass", pc_results),
        ("Phase 5", p5_results),
    ]

    errors_found = False
    for category, results in all_results:
        for result in results:
            if len(result) > 1 and not result[1]:  # Failed test
                if not errors_found:
                    print("\n=== Errors ===")
                    errors_found = True
                print(f"\n{category} - {result[0]}:")
                if len(result) > 3:
                    print(f"  stderr: {result[3]}")
                elif len(result) > 2:
                    print(f"  error: {result[2]}")

    return total_success == total_tests


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
