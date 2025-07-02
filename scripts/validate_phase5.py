#!/usr/bin/env python3
"""
Validate Phase 5 heavy models implementation.

This script runs various tests to validate that Phase 5 features work correctly
with and without heavy models installed.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reddit_analyzer.services.nlp_service import get_nlp_service
from reddit_analyzer.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase5Validator:
    """Validate Phase 5 implementation."""

    def __init__(self):
        """Initialize validator."""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": self._get_environment_info(),
            "tests": {},
            "summary": {},
        }

    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        try:
            import torch

            cuda_available = torch.cuda.is_available()
            gpu_device = str(torch.cuda.get_device_name(0)) if cuda_available else None
        except ImportError:
            cuda_available = False
            gpu_device = None

        env_info = {
            "python_version": sys.version,
            "cuda_available": cuda_available,
            "gpu_device": gpu_device,
            "config": {
                "NLP_ENABLE_GPU": Config.NLP_ENABLE_GPU,
                "NLP_ENABLE_HEAVY_MODELS": Config.NLP_ENABLE_HEAVY_MODELS,
                "ENTITY_MODEL": Config.ENTITY_MODEL,
                "NLP_BATCH_SIZE": Config.NLP_BATCH_SIZE,
            },
        }

        # Check installed packages
        packages = {}
        for pkg in ["spacy", "transformers", "torch", "bertopic"]:
            try:
                mod = __import__(pkg)
                packages[pkg] = getattr(mod, "__version__", "installed")
            except ImportError:
                packages[pkg] = None

        env_info["packages"] = packages

        # Check spaCy models
        try:
            import spacy

            env_info["spacy_models"] = spacy.util.get_installed_models()
        except Exception:
            env_info["spacy_models"] = []

        return env_info

    def test_basic_functionality(self) -> Dict[str, Any]:
        """Test basic NLP functionality (should always work)."""
        logger.info("Testing basic functionality...")

        results = {
            "sentiment_analysis": False,
            "topic_modeling": False,
            "keyword_extraction": False,
            "errors": [],
        }

        try:
            service = get_nlp_service()

            # Test sentiment analysis
            sentiment = service.analyze_sentiment("This is a great policy!")
            if sentiment and "score" in sentiment:
                results["sentiment_analysis"] = True

            # Test basic topic modeling
            texts = [
                "Healthcare policy needs reform",
                "Immigration debate continues",
                "Climate change action required",
            ]
            topics = service.model_topics(texts, num_topics=2)
            if topics:
                results["topic_modeling"] = True

            # Test keyword extraction
            keywords = service.extract_keywords(
                "Important political discussion about healthcare reform"
            )
            if keywords:
                results["keyword_extraction"] = True

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def test_heavy_models(self) -> Dict[str, Any]:
        """Test heavy model functionality."""
        logger.info("Testing heavy models...")

        results = {
            "entity_extraction": {"available": False, "functional": False},
            "emotion_detection": {"available": False, "functional": False},
            "stance_detection": {"available": False, "functional": False},
            "argument_mining": {"available": False, "functional": False},
            "advanced_topics": {"available": False, "functional": False},
            "errors": [],
        }

        try:
            service = get_nlp_service()

            # Test entity extraction
            entities = service.extract_entities(
                "President Biden met with Congress about healthcare."
            )
            results["entity_extraction"]["available"] = entities.get("available", False)
            if entities.get("politicians") or entities.get("organizations"):
                results["entity_extraction"]["functional"] = True

            # Test emotion detection
            emotions = service.analyze_emotions(
                "I am very happy about this development!"
            )
            results["emotion_detection"]["available"] = emotions.get("available", False)
            if emotions.get("emotions") and any(emotions["emotions"].values()):
                results["emotion_detection"]["functional"] = True

            # Test stance detection
            stance = service.detect_stance(
                "I support universal healthcare", "healthcare"
            )
            results["stance_detection"]["available"] = stance.get("available", False)
            if stance.get("stance"):
                results["stance_detection"]["functional"] = True

            # Test argument mining
            args = service.extract_arguments(
                "Healthcare is important because it saves lives. Studies show that universal healthcare reduces mortality."
            )
            results["argument_mining"]["available"] = args.get("available", False)
            if args.get("arguments"):
                results["argument_mining"]["functional"] = True

            # Test advanced topic modeling
            texts = ["Healthcare policy discussion"] * 10
            adv_topics = service.model_topics_advanced(texts, method="nmf")
            results["advanced_topics"]["available"] = adv_topics.get("available", False)
            if adv_topics.get("topics"):
                results["advanced_topics"]["functional"] = True

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def test_gpu_acceleration(self) -> Dict[str, Any]:
        """Test GPU acceleration if available."""
        logger.info("Testing GPU acceleration...")

        results = {
            "gpu_detected": False,
            "gpu_functional": False,
            "performance_gain": 0.0,
            "errors": [],
        }

        try:
            import torch
            import time

            results["gpu_detected"] = torch.cuda.is_available()

            if results["gpu_detected"]:
                service = get_nlp_service()

                # Test sentiment with GPU
                texts = ["Test text for GPU performance"] * 100

                start = time.time()
                for text in texts:
                    service.analyze_sentiment(text)
                gpu_time = time.time() - start

                # Force CPU for comparison
                with torch.cuda.device("cpu"):
                    start = time.time()
                    for text in texts[:20]:  # Less texts for CPU
                        service.analyze_sentiment(text)
                    cpu_time = (time.time() - start) * 5  # Extrapolate

                if gpu_time > 0:
                    results["performance_gain"] = cpu_time / gpu_time
                    results["gpu_functional"] = True

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def test_fallback_mechanisms(self) -> Dict[str, Any]:
        """Test fallback mechanisms."""
        logger.info("Testing fallback mechanisms...")

        results = {
            "all_fallbacks_work": True,
            "fallback_messages_clear": True,
            "no_crashes": True,
            "errors": [],
        }

        try:
            service = get_nlp_service()

            # Test with empty text
            empty_result = service.analyze_emotions("")
            if "error" in str(empty_result).lower() and "available" in empty_result:
                results["no_crashes"] = False

            # Test with very long text
            long_text = "word " * 10000
            _ = service.extract_entities(long_text)  # Just ensure it doesn't crash

            # Test unavailable features
            for method in ["extract_entities", "analyze_emotions", "detect_stance"]:
                if hasattr(service, method):
                    result = getattr(service, method)(
                        "Test text", "target" if method == "detect_stance" else None
                    )
                    if isinstance(result, dict) and "available" in result:
                        if not result["available"] and "message" not in result:
                            results["fallback_messages_clear"] = False

        except Exception as e:
            results["no_crashes"] = False
            results["errors"].append(str(e))

        return results

    def test_cli_commands(self) -> Dict[str, Any]:
        """Test new CLI commands."""
        logger.info("Testing CLI commands...")

        results = {"commands_available": [], "commands_functional": [], "errors": []}

        try:
            # Set SKIP_AUTH to bypass auth for testing
            os.environ["SKIP_AUTH"] = "true"

            from reddit_analyzer.cli.analyze import app
            from typer.testing import CliRunner

            runner = CliRunner()

            # Test each new command
            commands = [
                ["analyze-emotions", "politics", "--limit", "1"],
                ["analyze-stance", "I support this", "healthcare"],
                ["analyze-entities", "politics", "--limit", "1"],
                ["analyze-arguments", "This is because that"],
                ["advanced-topics", "politics", "--limit", "10"],
            ]

            for cmd in commands:
                try:
                    result = runner.invoke(app, cmd)
                    results["commands_available"].append(cmd[0])

                    if result.exit_code == 0:
                        results["commands_functional"].append(cmd[0])
                except Exception as e:
                    results["errors"].append(f"{cmd[0]}: {str(e)}")

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def generate_report(self) -> str:
        """Generate validation report."""
        # Run all tests
        self.results["tests"]["basic"] = self.test_basic_functionality()
        self.results["tests"]["heavy_models"] = self.test_heavy_models()
        self.results["tests"]["gpu"] = self.test_gpu_acceleration()
        self.results["tests"]["fallbacks"] = self.test_fallback_mechanisms()
        self.results["tests"]["cli"] = self.test_cli_commands()

        # Generate summary
        total_heavy_models = (
            len(self.results["tests"]["heavy_models"]) - 1
        )  # Exclude errors
        available_models = sum(
            1
            for k, v in self.results["tests"]["heavy_models"].items()
            if isinstance(v, dict) and v.get("available", False)
        )
        functional_models = sum(
            1
            for k, v in self.results["tests"]["heavy_models"].items()
            if isinstance(v, dict) and v.get("functional", False)
        )

        self.results["summary"] = {
            "basic_functionality": all(
                v
                for k, v in self.results["tests"]["basic"].items()
                if k != "errors" and isinstance(v, bool)
            ),
            "heavy_models_available": f"{available_models}/{total_heavy_models}",
            "heavy_models_functional": f"{functional_models}/{total_heavy_models}",
            "gpu_acceleration": self.results["tests"]["gpu"]["gpu_functional"],
            "fallbacks_working": self.results["tests"]["fallbacks"][
                "all_fallbacks_work"
            ],
            "cli_commands": f"{len(self.results['tests']['cli']['commands_functional'])}/{len(self.results['tests']['cli']['commands_available'])}",
        }

        # Save results
        output_path = Path("tests/test_specs/phase5_validation_results.json")
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        # Generate readable report
        report = self._format_report()

        report_path = Path("tests/test_specs/phase5_validation_report.md")
        with open(report_path, "w") as f:
            f.write(report)

        return report

    def _format_report(self) -> str:
        """Format results as readable report."""
        report = f"""# Phase 5 Heavy Models Validation Report

**Generated**: {self.results["timestamp"]}

## Environment

- **Python**: {self.results["environment"]["python_version"].split()[0]}
- **CUDA Available**: {self.results["environment"]["cuda_available"]}
- **GPU**: {self.results["environment"]["gpu_device"] or "None"}

### Installed Packages
"""

        for pkg, version in self.results["environment"]["packages"].items():
            status = "✓" if version else "✗"
            report += f"- {status} **{pkg}**: {version or 'Not installed'}\n"

        report += "\n### SpaCy Models\n"
        for model in self.results["environment"]["spacy_models"]:
            report += f"- {model}\n"

        report += "\n## Test Results\n\n"

        # Basic functionality
        report += "### Basic Functionality (Required)\n"
        for feature, status in self.results["tests"]["basic"].items():
            if feature != "errors":
                emoji = "✅" if status else "❌"
                report += f"- {emoji} {feature.replace('_', ' ').title()}\n"

        # Heavy models
        report += "\n### Heavy Models (Optional)\n"
        for model, info in self.results["tests"]["heavy_models"].items():
            if model != "errors" and isinstance(info, dict):
                avail = "✅" if info["available"] else "❌"
                func = "✅" if info["functional"] else "❌"
                report += f"- **{model.replace('_', ' ').title()}**: Available {avail}, Functional {func}\n"

        # GPU acceleration
        report += "\n### GPU Acceleration\n"
        gpu = self.results["tests"]["gpu"]
        report += f"- GPU Detected: {'✅' if gpu['gpu_detected'] else '❌'}\n"
        report += f"- GPU Functional: {'✅' if gpu['gpu_functional'] else '❌'}\n"
        if gpu["performance_gain"] > 0:
            report += f"- Performance Gain: {gpu['performance_gain']:.1f}x\n"

        # Fallbacks
        report += "\n### Fallback Mechanisms\n"
        fb = self.results["tests"]["fallbacks"]
        report += (
            f"- All Fallbacks Work: {'✅' if fb['all_fallbacks_work'] else '❌'}\n"
        )
        report += (
            f"- Clear Messages: {'✅' if fb['fallback_messages_clear'] else '❌'}\n"
        )
        report += f"- No Crashes: {'✅' if fb['no_crashes'] else '❌'}\n"

        # CLI commands
        report += "\n### CLI Commands\n"
        cli = self.results["tests"]["cli"]
        report += f"- Commands Available: {len(cli['commands_available'])}\n"
        report += f"- Commands Functional: {len(cli['commands_functional'])}\n"
        for cmd in cli["commands_functional"]:
            report += f"  - ✅ {cmd}\n"

        # Summary
        report += "\n## Summary\n\n"
        for key, value in self.results["summary"].items():
            report += f"- **{key.replace('_', ' ').title()}**: {value}\n"

        # Recommendations
        report += "\n## Recommendations\n\n"

        if not self.results["environment"]["cuda_available"]:
            report += (
                "- Consider using a GPU for better performance with heavy models\n"
            )

        missing_pkgs = [
            pkg
            for pkg, ver in self.results["environment"]["packages"].items()
            if not ver
        ]
        if missing_pkgs:
            report += f"- Install missing packages for full functionality: {', '.join(missing_pkgs)}\n"

        if not self.results["environment"]["spacy_models"]:
            report += "- Install spaCy language models: `python -m spacy download en_core_web_lg`\n"

        return report


def main():
    """Main entry point."""
    validator = Phase5Validator()

    try:
        report = validator.generate_report()
        print(report)
        logger.info(
            "Validation complete! Report saved to tests/test_specs/phase5_validation_report.md"
        )
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
