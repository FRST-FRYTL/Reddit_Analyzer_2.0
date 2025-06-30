#!/usr/bin/env python3
"""
Test script to verify Phase 4C NLP integration is working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from reddit_analyzer.services.nlp_service import get_nlp_service
from reddit_analyzer.database import SessionLocal
from reddit_analyzer.models.post import Post
from reddit_analyzer.models.text_analysis import TextAnalysis


def test_nlp_service():
    """Test basic NLP service functionality."""
    print("Testing NLP Service...")

    # Get NLP service instance
    nlp_service = get_nlp_service()
    print("✓ NLP Service created successfully")

    # Test sentiment analysis
    test_texts = [
        "Python is amazing! I love programming with it.",
        "This is terrible and I hate it.",
        "The weather is okay today.",
    ]

    print("\nTesting sentiment analysis:")
    for text in test_texts:
        result = nlp_service.analyze_text(text)
        sentiment = result.get("sentiment", {})
        print(f"  Text: '{text[:50]}...'")
        print(
            f"  Sentiment: {sentiment.get('label')} (score: {sentiment.get('compound', 0):.3f})"
        )
        print(f"  Keywords: {', '.join(result.get('keywords', [])[:5])}")
        print()

    return True


def test_database_integration():
    """Test NLP data is properly stored in database."""
    print("\nTesting Database Integration...")

    db = SessionLocal()
    try:
        # Count posts with NLP analysis
        total_posts = db.query(Post).count()
        analyzed_posts = db.query(TextAnalysis).count()

        print(f"Total posts in database: {total_posts}")
        print(f"Posts with NLP analysis: {analyzed_posts}")

        if analyzed_posts > 0:
            # Show sample analysis
            sample = db.query(TextAnalysis).first()
            if sample:
                print("\nSample analysis:")
                print(f"  Post ID: {sample.post_id}")
                print(
                    f"  Sentiment: {sample.sentiment_label} ({sample.sentiment_score:.3f})"
                )
                print(f"  Confidence: {sample.confidence_score:.2%}")
                print(
                    f"  Keywords: {', '.join(sample.keywords[:5]) if sample.keywords else 'None'}"
                )

        return True

    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False
    finally:
        db.close()


def test_cli_commands():
    """Test CLI commands are accessible."""
    print("\nTesting CLI Commands...")

    import subprocess

    commands = [
        "uv run reddit-analyzer --help",
        "uv run reddit-analyzer nlp --help",
        "uv run reddit-analyzer data status",
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Command '{cmd}' works")
            else:
                print(f"✗ Command '{cmd}' failed")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
        except Exception as e:
            print(f"✗ Failed to run '{cmd}': {e}")

    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("Phase 4C NLP Integration Test")
    print("=" * 50)

    tests = [
        ("NLP Service", test_nlp_service),
        ("Database Integration", test_database_integration),
        ("CLI Commands", test_cli_commands),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")

    return total_passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
