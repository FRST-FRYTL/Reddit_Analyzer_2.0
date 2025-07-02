"""
Stance detection module for identifying positions on topics.

This module detects whether text expresses support, opposition, or neutrality
towards specific topics, issues, or entities. Useful for political analysis,
opinion mining, and debate analysis.
"""

import logging
from typing import Dict, List, Any, Optional
import torch
from transformers import pipeline
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Stance(Enum):
    """Stance labels."""

    FAVOR = "favor"
    AGAINST = "against"
    NEUTRAL = "neutral"
    NONE = "none"  # No clear stance detected


@dataclass
class StanceResult:
    """Result of stance detection."""

    stance: Stance
    confidence: float
    target: str
    evidence: List[str]
    reasoning: Optional[str] = None


class StanceDetector:
    """Advanced stance detection using transformer models and zero-shot classification."""

    def __init__(
        self, model_name: str = "facebook/bart-large-mnli", use_gpu: bool = False
    ):
        """
        Initialize stance detector.

        Args:
            model_name: HuggingFace model for zero-shot classification
            use_gpu: Whether to use GPU if available
        """
        self.model_name = model_name
        self.device = self._get_device(use_gpu)
        self.classifier = None
        self.political_classifier = None
        self._load_models()

    def _get_device(self, use_gpu: bool) -> int:
        """Determine device to use for inference."""
        if use_gpu and torch.cuda.is_available():
            logger.info("Using GPU for stance detection")
            return 0
        else:
            logger.info("Using CPU for stance detection")
            return -1

    def _load_models(self):
        """Load stance detection models."""
        try:
            # Zero-shot classifier for general stance detection
            self.classifier = pipeline(
                "zero-shot-classification", model=self.model_name, device=self.device
            )
            logger.info(f"Loaded stance detection model: {self.model_name}")

            # Try to load political stance model if available
            try:
                political_model = "cardiffnlp/twitter-roberta-base-stance"
                self.political_classifier = pipeline(
                    "text-classification", model=political_model, device=self.device
                )
                logger.info(f"Loaded political stance model: {political_model}")
            except Exception:
                logger.info("Political stance model not available")

        except Exception as e:
            logger.error(f"Failed to load stance detection models: {e}")

    def detect_stance(
        self, text: str, target: str, context: Optional[str] = None
    ) -> StanceResult:
        """
        Detect stance towards a specific target.

        Args:
            text: Input text
            target: Target topic/entity to detect stance towards
            context: Additional context about the target

        Returns:
            StanceResult object
        """
        if not self.classifier:
            return StanceResult(Stance.NONE, 0.0, target, [])

        try:
            # Prepare hypothesis templates
            if context:
                hypothesis_template = f"This text expresses {{}} towards {target} in the context of {context}"
            else:
                hypothesis_template = f"This text expresses {{}} towards {target}"

            labels = ["support", "opposition", "neutrality"]
            hypotheses = [hypothesis_template.format(label) for label in labels]

            # Run zero-shot classification
            result = self.classifier(
                text, candidate_labels=hypotheses, multi_label=False
            )

            # Map results to stance
            top_label = result["labels"][0]
            confidence = result["scores"][0]

            if "support" in top_label:
                stance = Stance.FAVOR
            elif "opposition" in top_label:
                stance = Stance.AGAINST
            elif "neutrality" in top_label:
                stance = Stance.NEUTRAL
            else:
                stance = Stance.NONE

            # Extract evidence
            evidence = self._extract_evidence(text, target, stance)

            return StanceResult(
                stance=stance, confidence=confidence, target=target, evidence=evidence
            )

        except Exception as e:
            logger.error(f"Error in stance detection: {e}")
            return StanceResult(Stance.NONE, 0.0, target, [])

    def _extract_evidence(self, text: str, target: str, stance: Stance) -> List[str]:
        """
        Extract sentences that provide evidence for the detected stance.

        Args:
            text: Input text
            target: Target of stance
            stance: Detected stance

        Returns:
            List of evidence sentences
        """
        # Split into sentences (simple approach)
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        evidence = []

        # Keywords for different stances
        favor_keywords = [
            "support",
            "agree",
            "favor",
            "endorse",
            "approve",
            "positive",
            "good",
            "benefit",
        ]
        against_keywords = [
            "oppose",
            "against",
            "disagree",
            "reject",
            "negative",
            "bad",
            "harm",
            "problem",
        ]

        target_lower = target.lower()

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Check if sentence mentions target
            if target_lower in sentence_lower:
                # Check for stance indicators
                if stance == Stance.FAVOR and any(
                    kw in sentence_lower for kw in favor_keywords
                ):
                    evidence.append(sentence)
                elif stance == Stance.AGAINST and any(
                    kw in sentence_lower for kw in against_keywords
                ):
                    evidence.append(sentence)
                elif stance == Stance.NEUTRAL and len(sentence.split()) > 5:
                    # For neutral, include substantive sentences mentioning target
                    evidence.append(sentence)

        return evidence[:3]  # Return top 3 pieces of evidence

    def detect_political_stance(self, text: str, issue: str) -> Dict[str, Any]:
        """
        Detect political stance on specific issues.

        Args:
            text: Input text
            issue: Political issue (e.g., "gun control", "climate change")

        Returns:
            Dictionary with political stance information
        """
        # Map issues to political positions
        issue_positions = {
            "gun control": {
                "liberal": [
                    "gun control",
                    "gun safety",
                    "background checks",
                    "assault weapon ban",
                ],
                "conservative": [
                    "second amendment",
                    "gun rights",
                    "self-defense",
                    "constitutional right",
                ],
            },
            "climate change": {
                "liberal": [
                    "climate crisis",
                    "global warming",
                    "renewable energy",
                    "carbon emissions",
                ],
                "conservative": [
                    "economic impact",
                    "job losses",
                    "energy independence",
                    "overregulation",
                ],
            },
            "healthcare": {
                "liberal": [
                    "universal healthcare",
                    "medicare for all",
                    "public option",
                    "affordable care",
                ],
                "conservative": [
                    "free market",
                    "private insurance",
                    "patient choice",
                    "reduce costs",
                ],
            },
            "immigration": {
                "liberal": [
                    "path to citizenship",
                    "refugees",
                    "diversity",
                    "humanitarian",
                ],
                "conservative": [
                    "border security",
                    "illegal immigration",
                    "law enforcement",
                    "sovereignty",
                ],
            },
        }

        # Detect general stance first
        stance_result = self.detect_stance(text, issue)

        # Analyze political leaning
        political_leaning = "neutral"
        leaning_confidence = 0.0

        if issue.lower() in issue_positions:
            positions = issue_positions[issue.lower()]
            text_lower = text.lower()

            liberal_score = sum(
                1 for term in positions["liberal"] if term in text_lower
            )
            conservative_score = sum(
                1 for term in positions["conservative"] if term in text_lower
            )

            total_score = liberal_score + conservative_score
            if total_score > 0:
                if liberal_score > conservative_score:
                    political_leaning = "liberal"
                    leaning_confidence = liberal_score / total_score
                elif conservative_score > liberal_score:
                    political_leaning = "conservative"
                    leaning_confidence = conservative_score / total_score

        return {
            "stance": stance_result.stance.value,
            "confidence": stance_result.confidence,
            "political_leaning": political_leaning,
            "leaning_confidence": leaning_confidence,
            "evidence": stance_result.evidence,
        }

    def analyze_debate_positions(
        self, texts: List[Dict[str, str]], topic: str
    ) -> Dict[str, Any]:
        """
        Analyze positions in a debate or discussion.

        Args:
            texts: List of {"author": str, "text": str} dictionaries
            topic: Debate topic

        Returns:
            Dictionary with debate analysis
        """
        author_stances = defaultdict(list)
        stance_distribution = defaultdict(int)

        for entry in texts:
            author = entry["author"]
            text = entry["text"]

            stance_result = self.detect_stance(text, topic)

            author_stances[author].append(stance_result)
            stance_distribution[stance_result.stance.value] += 1

        # Analyze consistency of positions
        author_consistency = {}
        for author, stances in author_stances.items():
            if len(stances) > 1:
                # Check if author maintains consistent stance
                stance_values = [s.stance for s in stances]
                most_common = max(set(stance_values), key=stance_values.count)
                consistency = stance_values.count(most_common) / len(stance_values)

                author_consistency[author] = {
                    "dominant_stance": most_common.value,
                    "consistency": consistency,
                    "stance_changes": len(set(stance_values)) - 1,
                }

        # Find polarization level
        total_positions = sum(stance_distribution.values())
        if total_positions > 0:
            favor_ratio = stance_distribution["favor"] / total_positions
            against_ratio = stance_distribution["against"] / total_positions
            polarization = abs(favor_ratio - against_ratio)
        else:
            polarization = 0.0

        return {
            "stance_distribution": dict(stance_distribution),
            "author_consistency": author_consistency,
            "polarization_level": polarization,
            "total_contributions": total_positions,
        }

    def detect_stance_shifts(self, texts: List[str], target: str) -> Dict[str, Any]:
        """
        Detect shifts in stance over time.

        Args:
            texts: List of texts in chronological order
            target: Target to track stance towards

        Returns:
            Dictionary with stance shift analysis
        """
        stance_timeline = []
        shifts = []

        for i, text in enumerate(texts):
            stance_result = self.detect_stance(text, target)
            stance_timeline.append(
                {
                    "index": i,
                    "stance": stance_result.stance.value,
                    "confidence": stance_result.confidence,
                }
            )

            # Detect shifts
            if i > 0:
                prev_stance = stance_timeline[i - 1]["stance"]
                curr_stance = stance_result.stance.value

                if (
                    prev_stance != curr_stance
                    and prev_stance != "none"
                    and curr_stance != "none"
                ):
                    shifts.append(
                        {
                            "position": i,
                            "from": prev_stance,
                            "to": curr_stance,
                            "confidence": (
                                stance_timeline[i - 1]["confidence"]
                                + stance_result.confidence
                            )
                            / 2,
                        }
                    )

        # Calculate stance stability
        if len(stance_timeline) > 1:
            stance_values = [
                s["stance"] for s in stance_timeline if s["stance"] != "none"
            ]
            if stance_values:
                unique_stances = len(set(stance_values))
                stability = 1 - (unique_stances - 1) / len(stance_values)
            else:
                stability = 1.0
        else:
            stability = 1.0

        return {
            "timeline": stance_timeline,
            "shifts": shifts,
            "stability": stability,
            "shift_count": len(shifts),
        }

    def compare_stance_targets(self, text: str, targets: List[str]) -> Dict[str, Any]:
        """
        Compare stances towards multiple targets.

        Args:
            text: Input text
            targets: List of targets to analyze

        Returns:
            Dictionary with comparative stance analysis
        """
        results = {}
        stance_summary = defaultdict(list)

        for target in targets:
            stance_result = self.detect_stance(text, target)
            results[target] = {
                "stance": stance_result.stance.value,
                "confidence": stance_result.confidence,
                "evidence": stance_result.evidence,
            }

            stance_summary[stance_result.stance.value].append(target)

        # Analyze patterns
        patterns = {
            "uniform_stance": len(stance_summary) == 1,
            "primary_stance": max(
                stance_summary.keys(), key=lambda k: len(stance_summary[k])
            ),
            "stance_groups": dict(stance_summary),
        }

        return {"target_stances": results, "patterns": patterns}

    def extract_stance_reasons(
        self, text: str, target: str, stance: Stance
    ) -> List[str]:
        """
        Extract reasons for a particular stance.

        Args:
            text: Input text
            target: Target of stance
            stance: Detected stance

        Returns:
            List of reasons/arguments
        """
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        reasons = []

        # Reason indicators
        reason_markers = [
            "because",
            "since",
            "as",
            "due to",
            "given that",
            "considering",
        ]
        argument_markers = ["therefore", "thus", "hence", "so", "consequently"]

        target_lower = target.lower()

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Check if sentence contains reasoning
            if target_lower in sentence_lower:
                # Look for explicit reason markers
                if any(marker in sentence_lower for marker in reason_markers):
                    reasons.append(sentence)
                # Look for arguments following stance expression
                elif i > 0 and any(
                    marker in sentence_lower for marker in argument_markers
                ):
                    reasons.append(sentences[i - 1] + " " + sentence)

        return reasons[:3]  # Return top 3 reasons
