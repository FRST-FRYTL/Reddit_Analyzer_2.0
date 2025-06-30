"""
Text preprocessing and natural language processing pipeline.

This module provides comprehensive text processing capabilities including
cleaning, tokenization, language detection, and feature extraction.
"""

import re
import logging
from typing import Dict, List, Any
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import nltk

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Comprehensive text processing pipeline for Reddit content.

    Handles text cleaning, normalization, tokenization, language detection,
    and various NLP feature extractions.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the text processor with NLP models.

        Args:
            spacy_model: SpaCy model name to load
        """
        self.spacy_model_name = spacy_model
        self._nlp = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize NLP models and download required data."""
        try:
            self._nlp = spacy.load(self.spacy_model_name)
            logger.info(f"Loaded spaCy model: {self.spacy_model_name}")
        except OSError:
            logger.warning(f"Could not load spaCy model {self.spacy_model_name}")
            self._nlp = None

        # Download required NLTK data
        try:
            nltk.download("punkt", quiet=True)
            nltk.download("vader_lexicon", quiet=True)
            nltk.download("stopwords", quiet=True)
            logger.info("Downloaded required NLTK data")
        except Exception as e:
            logger.warning(f"Could not download NLTK data: {e}")

    @property
    def nlp(self):
        """Lazy loading of spaCy model."""
        if self._nlp is None:
            try:
                self._nlp = spacy.load(self.spacy_model_name)
            except OSError:
                logger.error(f"Cannot load spaCy model {self.spacy_model_name}")
                raise RuntimeError(f"spaCy model {self.spacy_model_name} not available")
        return self._nlp

    def clean_text(
        self,
        text: str,
        remove_urls: bool = True,
        remove_mentions: bool = True,
        remove_hashtags: bool = False,
        remove_extra_whitespace: bool = True,
    ) -> str:
        """
        Clean and preprocess text content.

        Args:
            text: Raw text to clean
            remove_urls: Remove URLs from text
            remove_mentions: Remove @mentions from text
            remove_hashtags: Remove hashtags from text
            remove_extra_whitespace: Normalize whitespace

        Returns:
            Cleaned text string
        """
        if not text or not isinstance(text, str):
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        if remove_urls:
            text = re.sub(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                "",
                text,
            )
            text = re.sub(
                r"www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                "",
                text,
            )

        # Remove mentions
        if remove_mentions:
            text = re.sub(r"@[A-Za-z0-9_]+", "", text)
            text = re.sub(r"/u/[A-Za-z0-9_]+", "", text)
            text = re.sub(r"u/[A-Za-z0-9_]+", "", text)

        # Remove hashtags
        if remove_hashtags:
            text = re.sub(r"#[A-Za-z0-9_]+", "", text)

        # Remove Reddit-specific formatting
        text = re.sub(r"/r/[A-Za-z0-9_]+", "", text)  # Subreddit links
        text = re.sub(r"r/[A-Za-z0-9_]+", "", text)  # Subreddit mentions
        text = re.sub(r"\*\*(.*?)\*\*", r"\\1", text)  # Bold formatting
        text = re.sub(r"\*(.*?)\*", r"\\1", text)  # Italic formatting
        text = re.sub(r"~~(.*?)~~", r"\\1", text)  # Strikethrough
        text = re.sub(r"`(.*?)`", r"\\1", text)  # Code formatting

        # Remove special characters and numbers (keep some punctuation)
        text = re.sub(r"[^a-zA-Z\\s\\.\\!\\?\\,\\;\\:]", "", text)

        # Remove extra whitespace
        if remove_extra_whitespace:
            text = re.sub(r"\\s+", " ", text).strip()

        return text

    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize text and optionally remove stopwords.

        Args:
            text: Text to tokenize
            remove_stopwords: Remove English stopwords

        Returns:
            List of tokens
        """
        if not text:
            return []

        # Use spaCy for tokenization if available
        if self._nlp:
            doc = self.nlp(text)
            tokens = [
                token.lemma_.lower()
                for token in doc
                if not token.is_punct and not token.is_space and token.text.strip()
            ]
        else:
            # Fallback to NLTK
            try:
                tokens = nltk.word_tokenize(text.lower())
            except Exception:
                # Simple split as last resort
                tokens = text.lower().split()

        # Remove stopwords
        if remove_stopwords:
            tokens = [token for token in tokens if token not in STOP_WORDS]

        # Filter out very short tokens
        tokens = [token for token in tokens if len(token) > 2]

        return tokens

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze

        Returns:
            List of entity dictionaries with text, label, and start/end positions
        """
        entities = []

        if not text or not self._nlp:
            return entities

        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append(
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "description": spacy.explain(ent.label_),
                    }
                )
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")

        return entities

    def extract_keywords(
        self, text: str, max_keywords: int = 10
    ) -> List[Dict[str, float]]:
        """
        Extract important keywords and phrases from text.

        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keyword dictionaries with text and importance scores
        """
        keywords = []

        if not text or not self._nlp:
            return keywords

        try:
            doc = self.nlp(text)

            # Calculate term frequency for content words
            word_freq = {}
            for token in doc:
                if (
                    not token.is_stop
                    and not token.is_punct
                    and not token.is_space
                    and len(token.text) > 2
                    and token.pos_ in ["NOUN", "VERB", "ADJ", "PROPN"]
                ):
                    lemma = token.lemma_.lower()
                    word_freq[lemma] = word_freq.get(lemma, 0) + 1

            # Sort by frequency and return top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

            for word, freq in sorted_words[:max_keywords]:
                keywords.append(
                    {
                        "keyword": word,
                        "frequency": freq,
                        "score": freq / len(doc),  # Normalized score
                    }
                )

        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")

        return keywords

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the text.

        Args:
            text: Text to analyze

        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        if not text:
            return "unknown"

        try:
            # TextBlob's detect_language may not be available in all installations
            # For now, default to English
            return "en"
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"  # Default to English

    def calculate_readability(self, text: str) -> Dict[str, float]:
        """
        Calculate readability metrics for text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with readability scores
        """
        if not text:
            return {}

        # Basic readability metrics
        sentences = text.split(".")
        words = text.split()

        if not sentences or not words:
            return {}

        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Simple readability score (lower is easier to read)
        readability_score = avg_sentence_length * avg_word_length / 100

        return {
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "readability_score": readability_score,
            "word_count": len(words),
            "sentence_count": len(sentences),
        }

    def process_text(
        self, text: str, include_sentiment: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive text processing pipeline.

        Args:
            text: Raw text to process
            include_sentiment: Whether to include sentiment analysis

        Returns:
            Dictionary with all extracted features
        """
        if not text:
            return {}

        # Clean text
        cleaned_text = self.clean_text(text)

        if not cleaned_text:
            return {"error": "No meaningful content after cleaning"}

        # Extract features
        features = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "language": self.detect_language(text),
            "entities": self.extract_entities(text),
            "keywords": self.extract_keywords(cleaned_text),
            "readability": self.calculate_readability(cleaned_text),
            "tokens": self.tokenize(cleaned_text),
            "processed_at": None,  # Will be set by caller
        }

        # Add basic statistics
        features["stats"] = {
            "original_length": len(text),
            "cleaned_length": len(cleaned_text),
            "token_count": len(features["tokens"]),
            "entity_count": len(features["entities"]),
            "keyword_count": len(features["keywords"]),
        }

        return features
