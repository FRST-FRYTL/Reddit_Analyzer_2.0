"""
Argument mining module for extracting claims, evidence, and reasoning.

This module identifies argumentative structures in text, including claims,
supporting evidence, counter-arguments, and logical relationships between
argumentative components.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import re
from dataclasses import dataclass, field
from enum import Enum
import spacy
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


class ArgumentType(Enum):
    """Types of argumentative components."""

    CLAIM = "claim"
    EVIDENCE = "evidence"
    PREMISE = "premise"
    COUNTER_CLAIM = "counter_claim"
    REBUTTAL = "rebuttal"
    CONCLUSION = "conclusion"


class RelationType(Enum):
    """Types of relationships between arguments."""

    SUPPORTS = "supports"
    ATTACKS = "attacks"
    REBUTS = "rebuts"
    QUALIFIES = "qualifies"


@dataclass
class ArgumentComponent:
    """Represents a single argumentative component."""

    text: str
    type: ArgumentType
    confidence: float
    position: Tuple[int, int]  # (start_char, end_char)
    keywords: List[str] = field(default_factory=list)


@dataclass
class ArgumentRelation:
    """Represents a relationship between two argument components."""

    source: ArgumentComponent
    target: ArgumentComponent
    relation_type: RelationType
    confidence: float


class ArgumentMiner:
    """Extract and analyze argumentative structures from text."""

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize argument miner.

        Args:
            spacy_model: spaCy model to use for linguistic analysis
        """
        self.nlp = None
        self._load_spacy_model(spacy_model)
        self._initialize_patterns()

    def _load_spacy_model(self, model_name: str):
        """Load spaCy model with error handling."""
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"Model {model_name} not found, using basic patterns only")

    def _initialize_patterns(self):
        """Initialize linguistic patterns for argument detection."""
        self.claim_indicators = [
            "believe",
            "think",
            "argue",
            "claim",
            "assert",
            "maintain",
            "contend",
            "propose",
            "suggest",
            "hold that",
            "view is",
            "position is",
            "opinion is",
            "convinced that",
        ]

        self.evidence_indicators = [
            "evidence",
            "study",
            "research",
            "data",
            "statistics",
            "according to",
            "report",
            "survey",
            "found that",
            "shows that",
            "demonstrates",
            "proves",
            "indicates",
            "for example",
            "for instance",
            "such as",
            "specifically",
        ]

        self.premise_indicators = [
            "because",
            "since",
            "as",
            "given that",
            "due to",
            "owing to",
            "in light of",
            "considering",
            "based on",
        ]

        self.counter_indicators = [
            "however",
            "but",
            "although",
            "while",
            "nevertheless",
            "on the other hand",
            "conversely",
            "yet",
            "despite",
            "in contrast",
            "alternatively",
        ]

        self.conclusion_indicators = [
            "therefore",
            "thus",
            "hence",
            "consequently",
            "so",
            "as a result",
            "accordingly",
            "it follows that",
            "in conclusion",
            "to conclude",
            "in summary",
        ]

    def extract_arguments(self, text: str) -> List[ArgumentComponent]:
        """
        Extract argumentative components from text.

        Args:
            text: Input text

        Returns:
            List of ArgumentComponent objects
        """
        arguments = []

        # Split into sentences
        sentences = self._split_sentences(text)

        for sent_start, sentence in sentences:
            # Check for different argument types
            arg_type, confidence, keywords = self._classify_sentence(sentence)

            if arg_type and confidence > 0.3:
                arguments.append(
                    ArgumentComponent(
                        text=sentence,
                        type=arg_type,
                        confidence=confidence,
                        position=(sent_start, sent_start + len(sentence)),
                        keywords=keywords,
                    )
                )

        return arguments

    def _split_sentences(self, text: str) -> List[Tuple[int, str]]:
        """Split text into sentences with position tracking."""
        if self.nlp:
            doc = self.nlp(text)
            return [(sent.start_char, sent.text) for sent in doc.sents]
        else:
            # Fallback to regex-based splitting
            sentences = []
            pattern = r"(?<=[.!?])\s+"
            parts = re.split(pattern, text)
            pos = 0
            for part in parts:
                sentences.append((pos, part))
                pos += len(part) + 1
            return sentences

    def _classify_sentence(
        self, sentence: str
    ) -> Tuple[Optional[ArgumentType], float, List[str]]:
        """
        Classify a sentence as an argument type.

        Args:
            sentence: Input sentence

        Returns:
            Tuple of (argument_type, confidence, keywords)
        """
        sentence_lower = sentence.lower()
        scores = {}
        found_keywords = defaultdict(list)

        # Check for claim indicators
        claim_score = sum(1 for ind in self.claim_indicators if ind in sentence_lower)
        if claim_score > 0:
            scores[ArgumentType.CLAIM] = claim_score
            found_keywords[ArgumentType.CLAIM] = [
                ind for ind in self.claim_indicators if ind in sentence_lower
            ]

        # Check for evidence indicators
        evidence_score = sum(
            1 for ind in self.evidence_indicators if ind in sentence_lower
        )
        if evidence_score > 0:
            scores[ArgumentType.EVIDENCE] = (
                evidence_score * 1.2
            )  # Slight boost for evidence
            found_keywords[ArgumentType.EVIDENCE] = [
                ind for ind in self.evidence_indicators if ind in sentence_lower
            ]

        # Check for premise indicators
        premise_score = sum(
            1 for ind in self.premise_indicators if ind in sentence_lower
        )
        if premise_score > 0:
            scores[ArgumentType.PREMISE] = premise_score
            found_keywords[ArgumentType.PREMISE] = [
                ind for ind in self.premise_indicators if ind in sentence_lower
            ]

        # Check for counter-argument indicators
        counter_score = sum(
            1 for ind in self.counter_indicators if ind in sentence_lower
        )
        if counter_score > 0:
            scores[ArgumentType.COUNTER_CLAIM] = counter_score
            found_keywords[ArgumentType.COUNTER_CLAIM] = [
                ind for ind in self.counter_indicators if ind in sentence_lower
            ]

        # Check for conclusion indicators
        conclusion_score = sum(
            1 for ind in self.conclusion_indicators if ind in sentence_lower
        )
        if conclusion_score > 0:
            scores[ArgumentType.CONCLUSION] = (
                conclusion_score * 1.3
            )  # Boost for conclusions
            found_keywords[ArgumentType.CONCLUSION] = [
                ind for ind in self.conclusion_indicators if ind in sentence_lower
            ]

        if scores:
            # Get the highest scoring type
            best_type = max(scores.items(), key=lambda x: x[1])
            confidence = min(best_type[1] / 3, 1.0)  # Normalize confidence
            return best_type[0], confidence, found_keywords[best_type[0]]

        return None, 0.0, []

    def extract_argument_structure(self, text: str) -> Dict[str, Any]:
        """
        Extract complete argument structure including relationships.

        Args:
            text: Input text

        Returns:
            Dictionary with argument structure
        """
        # Extract components
        components = self.extract_arguments(text)

        # Find relationships
        relations = self._find_relationships(components, text)

        # Build argument graph
        graph = self._build_argument_graph(components, relations)

        # Analyze structure
        structure_analysis = self._analyze_structure(graph, components)

        return {
            "components": [
                {
                    "text": comp.text,
                    "type": comp.type.value,
                    "confidence": comp.confidence,
                    "keywords": comp.keywords,
                }
                for comp in components
            ],
            "relations": [
                {
                    "source": rel.source.text,
                    "target": rel.target.text,
                    "type": rel.relation_type.value,
                    "confidence": rel.confidence,
                }
                for rel in relations
            ],
            "structure_analysis": structure_analysis,
        }

    def _find_relationships(
        self, components: List[ArgumentComponent], full_text: str
    ) -> List[ArgumentRelation]:
        """
        Find relationships between argument components.

        Args:
            components: List of argument components
            full_text: Original text for context

        Returns:
            List of ArgumentRelation objects
        """
        relations = []

        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i >= j:  # Avoid duplicates and self-relations
                    continue

                # Check proximity
                if (
                    abs(comp1.position[0] - comp2.position[1]) < 200
                ):  # Within ~200 chars
                    rel_type, confidence = self._determine_relationship(
                        comp1, comp2, full_text
                    )

                    if rel_type and confidence > 0.3:
                        relations.append(
                            ArgumentRelation(
                                source=comp1,
                                target=comp2,
                                relation_type=rel_type,
                                confidence=confidence,
                            )
                        )

        return relations

    def _determine_relationship(
        self, comp1: ArgumentComponent, comp2: ArgumentComponent, context: str
    ) -> Tuple[Optional[RelationType], float]:
        """
        Determine relationship type between two components.

        Args:
            comp1: First component
            comp2: Second component
            context: Full text for context

        Returns:
            Tuple of (relation_type, confidence)
        """
        # Heuristic rules for relationship detection

        # Premise/Evidence supporting Claim/Conclusion
        if comp1.type in [
            ArgumentType.PREMISE,
            ArgumentType.EVIDENCE,
        ] and comp2.type in [ArgumentType.CLAIM, ArgumentType.CONCLUSION]:
            return RelationType.SUPPORTS, 0.7

        # Counter-claim attacking claim
        if (
            comp1.type == ArgumentType.COUNTER_CLAIM
            and comp2.type == ArgumentType.CLAIM
        ):
            return RelationType.ATTACKS, 0.8

        # Rebuttal attacking counter-claim
        if (
            comp1.type == ArgumentType.REBUTTAL
            and comp2.type == ArgumentType.COUNTER_CLAIM
        ):
            return RelationType.REBUTS, 0.7

        # Sequential support (claim followed by evidence)
        if (
            comp1.position[1] < comp2.position[0]
            and comp1.type == ArgumentType.CLAIM
            and comp2.type == ArgumentType.EVIDENCE
        ):
            return RelationType.SUPPORTS, 0.6

        return None, 0.0

    def _build_argument_graph(
        self, components: List[ArgumentComponent], relations: List[ArgumentRelation]
    ) -> nx.DiGraph:
        """Build a directed graph of argument structure."""
        G = nx.DiGraph()

        # Add nodes
        for i, comp in enumerate(components):
            G.add_node(i, component=comp, text=comp.text, type=comp.type.value)

        # Add edges
        for rel in relations:
            source_idx = components.index(rel.source)
            target_idx = components.index(rel.target)
            G.add_edge(
                source_idx,
                target_idx,
                relation=rel.relation_type.value,
                confidence=rel.confidence,
            )

        return G

    def _analyze_structure(
        self, graph: nx.DiGraph, components: List[ArgumentComponent]
    ) -> Dict[str, Any]:
        """Analyze the argument structure."""
        if len(graph.nodes) == 0:
            return {"strength": 0.0, "coherence": 0.0, "complexity": 0.0}

        # Calculate metrics

        # Argument strength (based on evidence/premise support)
        support_edges = [
            e for e in graph.edges(data=True) if e[2].get("relation") == "supports"
        ]
        strength = len(support_edges) / max(len(components), 1)

        # Coherence (how well connected the arguments are)
        if len(graph.nodes) > 1:
            coherence = nx.density(graph)
        else:
            coherence = 0.0

        # Complexity (variety of argument types and relationships)
        unique_types = len(set(comp.type for comp in components))
        unique_relations = len(
            set(e[2].get("relation") for e in graph.edges(data=True))
        )
        complexity = (unique_types + unique_relations) / 10  # Normalize

        # Find main claims and conclusions
        main_claims = [comp for comp in components if comp.type == ArgumentType.CLAIM]
        conclusions = [
            comp for comp in components if comp.type == ArgumentType.CONCLUSION
        ]

        return {
            "strength": min(strength, 1.0),
            "coherence": coherence,
            "complexity": min(complexity, 1.0),
            "main_claims": [c.text for c in main_claims[:3]],  # Top 3
            "conclusions": [c.text for c in conclusions],
            "total_components": len(components),
            "total_relations": len(support_edges),
        }

    def evaluate_argument_quality(self, text: str) -> Dict[str, Any]:
        """
        Evaluate the quality of argumentation in text.

        Args:
            text: Input text

        Returns:
            Dictionary with quality metrics
        """
        # structure = self.extract_argument_structure(text)
        components = self.extract_arguments(text)

        # Quality metrics
        metrics = {
            "logical_flow": 0.0,
            "evidence_support": 0.0,
            "balance": 0.0,
            "clarity": 0.0,
            "fallacies": [],
        }

        if not components:
            return metrics

        # Logical flow (proper sequence of argument types)
        type_sequence = [comp.type for comp in components]
        logical_sequences = [
            [ArgumentType.CLAIM, ArgumentType.EVIDENCE, ArgumentType.CONCLUSION],
            [ArgumentType.PREMISE, ArgumentType.CLAIM, ArgumentType.CONCLUSION],
        ]

        # Check if sequence matches logical patterns
        for pattern in logical_sequences:
            if self._sequence_similarity(type_sequence, pattern) > 0.5:
                metrics["logical_flow"] = 0.8
                break

        # Evidence support (ratio of evidence to claims)
        claims = sum(1 for c in components if c.type == ArgumentType.CLAIM)
        evidence = sum(1 for c in components if c.type == ArgumentType.EVIDENCE)

        if claims > 0:
            metrics["evidence_support"] = min(evidence / claims, 1.0)

        # Balance (presence of counter-arguments)
        counter_args = sum(
            1 for c in components if c.type == ArgumentType.COUNTER_CLAIM
        )
        metrics["balance"] = min(counter_args / max(claims, 1), 1.0)

        # Clarity (based on confidence scores)
        avg_confidence = sum(c.confidence for c in components) / len(components)
        metrics["clarity"] = avg_confidence

        # Detect common fallacies
        metrics["fallacies"] = self._detect_fallacies(text, components)

        # Overall quality score
        metrics["overall_quality"] = (
            metrics["logical_flow"] * 0.25
            + metrics["evidence_support"] * 0.35
            + metrics["balance"] * 0.2
            + metrics["clarity"] * 0.2
        )

        return metrics

    def _sequence_similarity(
        self, seq1: List[ArgumentType], seq2: List[ArgumentType]
    ) -> float:
        """Calculate similarity between two sequences."""
        if not seq1 or not seq2:
            return 0.0

        matches = 0
        for i in range(len(seq1) - len(seq2) + 1):
            sub_matches = sum(
                1
                for j in range(len(seq2))
                if i + j < len(seq1) and seq1[i + j] == seq2[j]
            )
            matches = max(matches, sub_matches)

        return matches / len(seq2)

    def _detect_fallacies(
        self, text: str, components: List[ArgumentComponent]
    ) -> List[Dict[str, str]]:
        """Detect common logical fallacies."""
        fallacies = []
        text_lower = text.lower()

        # Ad hominem (attacking the person)
        ad_hominem_patterns = [
            "you are",
            "he is",
            "she is",
            "they are",
            "stupid",
            "idiot",
            "moron",
        ]
        if any(pattern in text_lower for pattern in ad_hominem_patterns):
            fallacies.append(
                {
                    "type": "ad_hominem",
                    "description": "Attacking the person rather than the argument",
                }
            )

        # Straw man (misrepresenting opponent's argument)
        straw_man_indicators = [
            "so you're saying",
            "what you're really saying",
            "in other words you think",
        ]
        if any(indicator in text_lower for indicator in straw_man_indicators):
            fallacies.append(
                {
                    "type": "straw_man",
                    "description": "Potentially misrepresenting the opponent's position",
                }
            )

        # Appeal to emotion (excessive emotional language)
        emotion_words = [
            "terrible",
            "horrible",
            "amazing",
            "incredible",
            "disaster",
            "catastrophe",
        ]
        emotion_count = sum(1 for word in emotion_words if word in text_lower)
        if emotion_count > 3:
            fallacies.append(
                {
                    "type": "appeal_to_emotion",
                    "description": "Excessive use of emotional language",
                }
            )

        # False dilemma (only two options presented)
        dilemma_patterns = [
            "either.*or",
            "you're either.*or you're",
            "only two options",
        ]
        for pattern in dilemma_patterns:
            if re.search(pattern, text_lower):
                fallacies.append(
                    {
                        "type": "false_dilemma",
                        "description": "Presenting only two options when more exist",
                    }
                )
                break

        return fallacies

    def compare_arguments(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare argumentation in two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Dictionary with comparison results
        """
        # Extract structures for both texts
        struct1 = self.extract_argument_structure(text1)
        struct2 = self.extract_argument_structure(text2)

        # Evaluate quality for both
        quality1 = self.evaluate_argument_quality(text1)
        quality2 = self.evaluate_argument_quality(text2)

        # Compare metrics
        comparison = {
            "text1_stronger": quality1["overall_quality"] > quality2["overall_quality"],
            "quality_difference": abs(
                quality1["overall_quality"] - quality2["overall_quality"]
            ),
            "text1_metrics": {
                "quality": quality1["overall_quality"],
                "evidence_support": quality1["evidence_support"],
                "logical_flow": quality1["logical_flow"],
            },
            "text2_metrics": {
                "quality": quality2["overall_quality"],
                "evidence_support": quality2["evidence_support"],
                "logical_flow": quality2["logical_flow"],
            },
            "common_claims": self._find_common_claims(
                struct1["components"], struct2["components"]
            ),
            "contrasting_claims": self._find_contrasting_claims(
                struct1["components"], struct2["components"]
            ),
        }

        return comparison

    def _find_common_claims(
        self, components1: List[Dict], components2: List[Dict]
    ) -> List[str]:
        """Find similar claims between two sets of components."""
        claims1 = [c["text"] for c in components1 if c["type"] == "claim"]
        claims2 = [c["text"] for c in components2 if c["type"] == "claim"]

        common = []
        for claim1 in claims1:
            for claim2 in claims2:
                # Simple similarity check (could be enhanced)
                if self._text_similarity(claim1, claim2) > 0.7:
                    common.append(f"{claim1} ~ {claim2}")

        return common

    def _find_contrasting_claims(
        self, components1: List[Dict], components2: List[Dict]
    ) -> List[Dict[str, str]]:
        """Find opposing claims between two sets of components."""
        claims1 = [c["text"] for c in components1 if c["type"] == "claim"]
        claims2 = [c["text"] for c in components2 if c["type"] == "claim"]

        contrasting = []
        negation_words = ["not", "no", "never", "don't", "doesn't", "isn't", "aren't"]

        for claim1 in claims1:
            for claim2 in claims2:
                # Check if one negates the other
                if any(
                    neg in claim2.lower() and neg not in claim1.lower()
                    for neg in negation_words
                ):
                    contrasting.append(
                        {"claim1": claim1, "claim2": claim2, "type": "negation"}
                    )

        return contrasting

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)
