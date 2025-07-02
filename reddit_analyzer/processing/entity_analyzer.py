"""
Entity recognition and analysis module.

This module provides advanced entity recognition capabilities using spaCy
and transformers for identifying people, organizations, locations, and
other named entities in Reddit content.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
import spacy
import numpy as np

logger = logging.getLogger(__name__)


class EntityAnalyzer:
    """Advanced entity recognition and analysis."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize entity analyzer.

        Args:
            model_name: spaCy model to use (en_core_web_sm, en_core_web_md, en_core_web_lg)
        """
        self.model_name = model_name
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """Load spaCy model with error handling."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.warning(f"Model {self.model_name} not found, downloading...")
            try:
                import subprocess

                subprocess.run(
                    ["python", "-m", "spacy", "download", self.model_name], check=True
                )
                self.nlp = spacy.load(self.model_name)
                logger.info(f"Successfully downloaded and loaded {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                # Fallback to basic model
                if self.model_name != "en_core_web_sm":
                    logger.info("Falling back to en_core_web_sm")
                    self.model_name = "en_core_web_sm"
                    self._load_model()
                else:
                    raise

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            Dictionary with entity types as keys and list of entity info as values
        """
        if not self.nlp:
            return {}

        doc = self.nlp(text)
        entities = defaultdict(list)

        for ent in doc.ents:
            entity_info = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": self._get_entity_confidence(ent),
            }
            entities[ent.label_].append(entity_info)

        return dict(entities)

    def _get_entity_confidence(self, entity) -> float:
        """
        Calculate confidence score for an entity.

        Args:
            entity: spaCy entity object

        Returns:
            Confidence score between 0 and 1
        """
        # Simple heuristic based on entity length and context
        base_confidence = 0.7

        # Longer entities are generally more confident
        if len(entity.text.split()) > 1:
            base_confidence += 0.1

        # Common entity types have higher confidence
        if entity.label_ in ["PERSON", "ORG", "GPE", "DATE"]:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def analyze_entity_sentiment(
        self, text: str, entities: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment towards specific entities.

        Args:
            text: Input text
            entities: Pre-extracted entities (optional)

        Returns:
            Dictionary mapping entities to sentiment scores
        """
        if entities is None:
            entities = self.extract_entities(text)

        if not self.nlp:
            return {}

        doc = self.nlp(text)
        entity_sentiments = {}

        for ent_type, ent_list in entities.items():
            for entity in ent_list:
                # Find sentences containing this entity
                entity_text = entity["text"]
                sentiment_scores = []

                for sent in doc.sents:
                    if entity_text.lower() in sent.text.lower():
                        # Simple sentiment based on surrounding words
                        sentiment = self._analyze_sentence_sentiment(sent, entity_text)
                        sentiment_scores.append(sentiment)

                if sentiment_scores:
                    entity_sentiments[entity_text] = {
                        "type": ent_type,
                        "sentiment": np.mean(sentiment_scores),
                        "mentions": len(sentiment_scores),
                    }

        return entity_sentiments

    def _analyze_sentence_sentiment(self, sentence, entity: str) -> float:
        """
        Analyze sentiment of a sentence towards an entity.

        Args:
            sentence: spaCy sentence object
            entity: Entity text

        Returns:
            Sentiment score between -1 and 1
        """
        # Simple keyword-based sentiment
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "love",
            "best",
            "wonderful",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "hate",
            "worst",
            "horrible",
            "poor",
        }

        words = [token.text.lower() for token in sentence]

        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        if positive_count + negative_count == 0:
            return 0.0

        return (positive_count - negative_count) / (positive_count + negative_count)

    def find_entity_relationships(self, text: str) -> List[Dict[str, Any]]:
        """
        Find relationships between entities.

        Args:
            text: Input text

        Returns:
            List of entity relationships
        """
        if not self.nlp:
            return []

        doc = self.nlp(text)
        relationships = []

        # Find entities that appear in the same sentence
        for sent in doc.sents:
            sent_entities = [
                ent
                for ent in doc.ents
                if ent.start >= sent.start and ent.end <= sent.end
            ]

            if len(sent_entities) >= 2:
                # Look for relationships between entities
                for i, ent1 in enumerate(sent_entities):
                    for ent2 in sent_entities[i + 1 :]:
                        rel = self._extract_relationship(sent, ent1, ent2)
                        if rel:
                            relationships.append(
                                {
                                    "entity1": ent1.text,
                                    "entity1_type": ent1.label_,
                                    "entity2": ent2.text,
                                    "entity2_type": ent2.label_,
                                    "relationship": rel,
                                    "sentence": sent.text,
                                }
                            )

        return relationships

    def _extract_relationship(self, sentence, ent1, ent2) -> Optional[str]:
        """
        Extract relationship between two entities in a sentence.

        Args:
            sentence: spaCy sentence object
            ent1: First entity
            ent2: Second entity

        Returns:
            Relationship type or None
        """
        # Find tokens between entities
        start_idx = min(ent1.end, ent2.end)
        end_idx = max(ent1.start, ent2.start)

        if start_idx < end_idx:
            between_tokens = [
                token for token in sentence if start_idx <= token.i < end_idx
            ]

            # Look for verbs that indicate relationships
            for token in between_tokens:
                if token.pos_ == "VERB":
                    return token.lemma_

        return None

    def get_entity_statistics(self, texts: List[str]) -> Dict[str, Any]:
        """
        Get statistics about entities across multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            Dictionary with entity statistics
        """
        all_entities = defaultdict(Counter)
        entity_types = Counter()

        for text in texts:
            entities = self.extract_entities(text)
            for ent_type, ent_list in entities.items():
                entity_types[ent_type] += len(ent_list)
                for entity in ent_list:
                    all_entities[ent_type][entity["text"]] += 1

        # Get most common entities per type
        top_entities = {}
        for ent_type, counter in all_entities.items():
            top_entities[ent_type] = counter.most_common(10)

        return {
            "entity_type_counts": dict(entity_types),
            "top_entities": top_entities,
            "total_entities": sum(entity_types.values()),
            "unique_entities": sum(len(counter) for counter in all_entities.values()),
        }

    def extract_key_figures(
        self, text: str, context: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Extract key figures (people, organizations) relevant to the context.

        Args:
            text: Input text
            context: Context for relevance scoring (e.g., "politics", "technology")

        Returns:
            List of key figures with relevance scores
        """
        entities = self.extract_entities(text)
        key_figures = []

        # Focus on PERSON and ORG entities
        for ent_type in ["PERSON", "ORG"]:
            if ent_type in entities:
                for entity in entities[ent_type]:
                    relevance = self._calculate_relevance(entity, text, context)
                    if relevance > 0.5:  # Threshold for key figures
                        key_figures.append(
                            {
                                "name": entity["text"],
                                "type": ent_type,
                                "relevance": relevance,
                                "mentions": text.count(entity["text"]),
                            }
                        )

        # Sort by relevance
        key_figures.sort(key=lambda x: x["relevance"], reverse=True)
        return key_figures[:10]  # Top 10 key figures

    def _calculate_relevance(self, entity: Dict, text: str, context: str) -> float:
        """
        Calculate relevance score for an entity.

        Args:
            entity: Entity information
            text: Full text
            context: Context for relevance

        Returns:
            Relevance score between 0 and 1
        """
        base_relevance = 0.5

        # More mentions = higher relevance
        mention_count = text.count(entity["text"])
        base_relevance += min(mention_count * 0.1, 0.3)

        # Context-specific boosting
        context_keywords = {
            "politics": ["president", "senator", "congress", "election", "campaign"],
            "technology": ["ceo", "founder", "developer", "engineer", "startup"],
            "sports": ["player", "coach", "team", "championship", "game"],
        }

        if context in context_keywords:
            keywords = context_keywords[context]
            # Check if entity appears near context keywords
            entity_start = entity["start"]
            entity_end = entity["end"]

            # Look at surrounding text (100 chars before and after)
            surrounding = text[
                max(0, entity_start - 100) : min(len(text), entity_end + 100)
            ].lower()

            for keyword in keywords:
                if keyword in surrounding:
                    base_relevance += 0.1

        return min(base_relevance, 1.0)
