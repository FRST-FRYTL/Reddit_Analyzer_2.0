#!/usr/bin/env python
"""Test script for Phase 5 heavy models implementation."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for testing
os.environ["NLP_ENABLE_HEAVY_MODELS"] = "true"
os.environ["NLP_ENABLE_GPU"] = "false"  # Set to true if you have GPU

from reddit_analyzer.services.nlp_service import get_nlp_service


def test_basic_functionality():
    """Test basic NLP service functionality."""
    print("Testing basic NLP service...")

    nlp = get_nlp_service()

    # Test basic sentiment analysis
    text = "I absolutely love this new feature! It's amazing and works perfectly."
    result = nlp.analyze_text(text)

    print(f"\nBasic analysis of: {text}")
    print(
        f"Sentiment: {result['sentiment']['sentiment_label']} ({result['sentiment']['confidence']:.2f})"
    )
    print(f"Keywords: {result['keywords']}")
    print(f"Processing time: {result['processing_time']:.2f}s")


def test_heavy_models():
    """Test heavy model features."""
    print("\n\nTesting heavy models...")

    nlp = get_nlp_service(enable_heavy_models=True)

    if not nlp.enable_heavy_models:
        print("Heavy models not available. Install with: uv sync --extra nlp-enhanced")
        return

    # Test emotion analysis
    text = "I'm so frustrated with this bug! It's been driving me crazy all day."
    emotions = nlp.analyze_emotions_detailed(text)

    print(f"\nEmotion analysis of: {text}")
    print(f"Dominant emotion: {emotions.get('dominant_emotion')}")
    print(f"Valence: {emotions.get('valence', 0):.2f}")
    print(f"All emotions: {emotions.get('emotions', {})}")

    # Test stance detection
    stance_text = "I strongly support renewable energy initiatives."
    stance_result = nlp.detect_stance(stance_text, "renewable energy")

    print(f"\nStance detection: {stance_text}")
    print("Target: renewable energy")
    print(
        f"Stance: {stance_result.get('stance')} ({stance_result.get('confidence', 0):.2f})"
    )

    # Test argument mining
    argument_text = """
    We should invest more in education because it leads to better economic outcomes.
    Studies show that countries with higher education spending have stronger economies.
    Therefore, increasing education funding is a wise policy decision.
    """

    argument_result = nlp.analyze_arguments(argument_text)

    print("\nArgument analysis:")
    print(f"Overall quality: {argument_result.get('overall_quality_score', 0):.2f}")
    if "structure" in argument_result:
        components = argument_result["structure"].get("components", [])
        print(f"Found {len(components)} argument components")


def test_advanced_entities():
    """Test advanced entity extraction."""
    print("\n\nTesting advanced entity extraction...")

    nlp = get_nlp_service(enable_heavy_models=True)

    text = """
    President Biden met with CEO Tim Cook at Apple headquarters in Cupertino.
    They discussed the company's plans for expanding manufacturing in the United States.
    """

    entities = nlp.extract_entities_advanced(text)

    print(f"\nEntity extraction from: {text[:50]}...")
    print(f"Total entities found: {entities.get('entity_count', 0)}")

    for entity_type, entity_list in entities.get("entities", {}).items():
        print(f"\n{entity_type}:")
        for entity in entity_list[:3]:  # Show first 3
            if isinstance(entity, dict):
                print(f"  - {entity.get('text', entity)}")
            else:
                print(f"  - {entity}")


def main():
    """Run all tests."""
    print("=== Phase 5 Heavy Models Test ===\n")

    try:
        test_basic_functionality()
        test_heavy_models()
        test_advanced_entities()

        print("\n✅ All tests completed!")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
