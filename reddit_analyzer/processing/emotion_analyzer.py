"""
Emotion analysis module using transformer models.

This module provides fine-grained emotion detection beyond simple sentiment,
identifying emotions like joy, sadness, anger, fear, surprise, and disgust.
"""

import logging
from typing import Dict, List, Any
import torch
from transformers import (
    pipeline,
)
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """Advanced emotion detection using transformer models."""

    # Emotion categories based on Ekman's basic emotions + additional
    EMOTION_CATEGORIES = [
        "joy",
        "sadness",
        "anger",
        "fear",
        "surprise",
        "disgust",
        "love",
        "optimism",
        "pessimism",
        "trust",
    ]

    def __init__(
        self,
        model_name: str = "j-hartmann/emotion-english-distilroberta-base",
        use_gpu: bool = False,
    ):
        """
        Initialize emotion analyzer.

        Args:
            model_name: HuggingFace model for emotion classification
            use_gpu: Whether to use GPU if available
        """
        self.model_name = model_name
        self.device = self._get_device(use_gpu)
        self.emotion_pipeline = None
        self.fallback_analyzer = None
        self._load_models()

    def _get_device(self, use_gpu: bool) -> int:
        """Determine device to use for inference."""
        if use_gpu and torch.cuda.is_available():
            logger.info("Using GPU for emotion analysis")
            return 0  # GPU 0
        else:
            logger.info("Using CPU for emotion analysis")
            return -1  # CPU

    def _load_models(self):
        """Load emotion detection models with fallback options."""
        try:
            # Primary model
            self.emotion_pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                device=self.device,
                top_k=None,  # Return all emotions with scores
            )
            logger.info(f"Loaded primary emotion model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load primary model: {e}")
            self._load_fallback_model()

    def _load_fallback_model(self):
        """Load a fallback emotion model."""
        try:
            # Try alternative model
            fallback_model = "bhadresh-savani/distilbert-base-uncased-emotion"
            self.emotion_pipeline = pipeline(
                "text-classification",
                model=fallback_model,
                device=self.device,
                top_k=None,
            )
            logger.info(f"Loaded fallback emotion model: {fallback_model}")
        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            # Ultimate fallback: rule-based
            self.fallback_analyzer = RuleBasedEmotionAnalyzer()

    def analyze_emotions(self, text: str) -> Dict[str, float]:
        """
        Analyze emotions in text.

        Args:
            text: Input text

        Returns:
            Dictionary mapping emotions to confidence scores
        """
        if not text or not text.strip():
            return {}

        try:
            if self.emotion_pipeline:
                # Use transformer model
                results = self.emotion_pipeline(
                    text[:512]
                )  # Truncate to model max length

                # Convert to consistent format
                emotions = {}
                for result_list in results:
                    for item in result_list:
                        emotion = item["label"].lower()
                        score = item["score"]
                        emotions[emotion] = score

                return emotions
            elif self.fallback_analyzer:
                # Use rule-based fallback
                return self.fallback_analyzer.analyze(text)
            else:
                return {}

        except Exception as e:
            logger.error(f"Error in emotion analysis: {e}")
            return {}

    def analyze_emotion_intensity(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotion intensity and valence.

        Args:
            text: Input text

        Returns:
            Dictionary with emotion intensity metrics
        """
        emotions = self.analyze_emotions(text)

        if not emotions:
            return {
                "dominant_emotion": None,
                "intensity": 0.0,
                "valence": 0.0,
                "arousal": 0.0,
            }

        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])

        # Calculate intensity (strength of dominant emotion)
        intensity = dominant_emotion[1]

        # Calculate valence (positive vs negative)
        positive_emotions = ["joy", "love", "optimism", "trust", "surprise"]
        negative_emotions = ["sadness", "anger", "fear", "disgust", "pessimism"]

        positive_score = sum(emotions.get(e, 0) for e in positive_emotions)
        negative_score = sum(emotions.get(e, 0) for e in negative_emotions)

        total_score = positive_score + negative_score
        valence = (
            (positive_score - negative_score) / total_score if total_score > 0 else 0
        )

        # Calculate arousal (high vs low energy emotions)
        high_arousal = ["anger", "fear", "surprise", "joy"]
        low_arousal = ["sadness", "disgust", "trust"]

        high_score = sum(emotions.get(e, 0) for e in high_arousal)
        low_score = sum(emotions.get(e, 0) for e in low_arousal)

        arousal_total = high_score + low_score
        arousal = (high_score - low_score) / arousal_total if arousal_total > 0 else 0

        return {
            "dominant_emotion": dominant_emotion[0],
            "intensity": intensity,
            "valence": valence,
            "arousal": arousal,
            "all_emotions": emotions,
        }

    def track_emotion_progression(self, texts: List[str]) -> Dict[str, Any]:
        """
        Track how emotions change across a sequence of texts.

        Args:
            texts: List of texts in chronological order

        Returns:
            Dictionary with emotion progression data
        """
        emotion_timeline = []
        emotion_changes = defaultdict(list)

        for i, text in enumerate(texts):
            emotions = self.analyze_emotions(text)
            intensity = self.analyze_emotion_intensity(text)

            emotion_timeline.append(
                {
                    "index": i,
                    "emotions": emotions,
                    "dominant": intensity["dominant_emotion"],
                    "valence": intensity["valence"],
                    "arousal": intensity["arousal"],
                }
            )

            # Track changes for each emotion
            for emotion, score in emotions.items():
                emotion_changes[emotion].append(score)

        # Calculate emotion volatility
        volatility = {}
        for emotion, scores in emotion_changes.items():
            if len(scores) > 1:
                volatility[emotion] = np.std(scores)

        # Detect emotion shifts
        shifts = []
        for i in range(1, len(emotion_timeline)):
            prev_dominant = emotion_timeline[i - 1]["dominant"]
            curr_dominant = emotion_timeline[i]["dominant"]

            if prev_dominant != curr_dominant:
                shifts.append(
                    {"position": i, "from": prev_dominant, "to": curr_dominant}
                )

        return {
            "timeline": emotion_timeline,
            "volatility": volatility,
            "shifts": shifts,
            "average_valence": np.mean([e["valence"] for e in emotion_timeline]),
            "average_arousal": np.mean([e["arousal"] for e in emotion_timeline]),
        }

    def detect_emotional_patterns(self, texts: List[str]) -> Dict[str, Any]:
        """
        Detect patterns in emotional expression.

        Args:
            texts: List of texts to analyze

        Returns:
            Dictionary with emotional patterns
        """
        all_emotions = defaultdict(list)
        emotion_pairs = defaultdict(int)

        for text in texts:
            emotions = self.analyze_emotions(text)

            # Collect all emotion scores
            for emotion, score in emotions.items():
                all_emotions[emotion].append(score)

            # Find co-occurring emotions (both above threshold)
            threshold = 0.3
            active_emotions = [e for e, s in emotions.items() if s > threshold]

            for i, emotion1 in enumerate(active_emotions):
                for emotion2 in active_emotions[i + 1 :]:
                    pair = tuple(sorted([emotion1, emotion2]))
                    emotion_pairs[pair] += 1

        # Calculate patterns
        patterns = {
            "emotion_frequency": {},
            "emotion_average_intensity": {},
            "common_pairs": [],
            "emotional_diversity": 0.0,
        }

        # Emotion frequency and intensity
        for emotion, scores in all_emotions.items():
            patterns["emotion_frequency"][emotion] = len([s for s in scores if s > 0.1])
            patterns["emotion_average_intensity"][emotion] = (
                np.mean(scores) if scores else 0
            )

        # Most common emotion pairs
        if emotion_pairs:
            sorted_pairs = sorted(
                emotion_pairs.items(), key=lambda x: x[1], reverse=True
            )
            patterns["common_pairs"] = [
                {"emotions": list(pair), "count": count}
                for pair, count in sorted_pairs[:5]
            ]

        # Emotional diversity (entropy-based)
        if patterns["emotion_frequency"]:
            total = sum(patterns["emotion_frequency"].values())
            if total > 0:
                probs = [
                    count / total for count in patterns["emotion_frequency"].values()
                ]
                entropy = -sum(p * np.log(p) for p in probs if p > 0)
                patterns["emotional_diversity"] = entropy / np.log(
                    len(self.EMOTION_CATEGORIES)
                )

        return patterns

    def analyze_emotional_contagion(
        self, conversation: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Analyze emotional contagion in conversations.

        Args:
            conversation: List of {"author": str, "text": str} dictionaries

        Returns:
            Dictionary with contagion analysis
        """
        author_emotions = defaultdict(list)
        emotion_flow = []

        for i, message in enumerate(conversation):
            author = message["author"]
            text = message["text"]

            emotions = self.analyze_emotions(text)
            intensity = self.analyze_emotion_intensity(text)

            author_emotions[author].append(intensity)

            if i > 0:
                # Check if current emotion matches previous
                prev_emotion = emotion_flow[-1]["dominant_emotion"]
                curr_emotion = intensity["dominant_emotion"]

                contagion_score = 0.0
                if prev_emotion == curr_emotion:
                    contagion_score = 1.0
                elif prev_emotion and curr_emotion:
                    # Partial contagion for related emotions
                    related_emotions = {
                        "joy": ["love", "optimism", "trust"],
                        "sadness": ["pessimism", "fear"],
                        "anger": ["disgust", "fear"],
                    }

                    if curr_emotion in related_emotions.get(prev_emotion, []):
                        contagion_score = 0.5

                emotion_flow.append(
                    {
                        "author": author,
                        "dominant_emotion": curr_emotion,
                        "contagion_score": contagion_score,
                    }
                )
            else:
                emotion_flow.append(
                    {
                        "author": author,
                        "dominant_emotion": intensity["dominant_emotion"],
                        "contagion_score": 0.0,
                    }
                )

        # Calculate overall contagion metric
        contagion_scores = [e["contagion_score"] for e in emotion_flow[1:]]
        average_contagion = np.mean(contagion_scores) if contagion_scores else 0.0

        # Analyze author emotional stability
        author_stability = {}
        for author, emotions in author_emotions.items():
            if len(emotions) > 1:
                valences = [e["valence"] for e in emotions]
                author_stability[author] = {
                    "valence_stability": 1 - np.std(valences),
                    "average_valence": np.mean(valences),
                }

        return {
            "average_contagion": average_contagion,
            "emotion_flow": emotion_flow,
            "author_stability": author_stability,
        }


class RuleBasedEmotionAnalyzer:
    """Fallback rule-based emotion analyzer."""

    def __init__(self):
        """Initialize with emotion keyword dictionaries."""
        self.emotion_keywords = {
            "joy": [
                "happy",
                "joy",
                "excited",
                "delighted",
                "cheerful",
                "elated",
                "glad",
                "thrilled",
            ],
            "sadness": [
                "sad",
                "depressed",
                "unhappy",
                "miserable",
                "sorrowful",
                "gloomy",
                "melancholy",
            ],
            "anger": [
                "angry",
                "furious",
                "mad",
                "enraged",
                "annoyed",
                "irritated",
                "outraged",
                "hostile",
            ],
            "fear": [
                "afraid",
                "scared",
                "terrified",
                "anxious",
                "worried",
                "nervous",
                "frightened",
                "panicked",
            ],
            "surprise": [
                "surprised",
                "amazed",
                "astonished",
                "shocked",
                "stunned",
                "astounded",
                "startled",
            ],
            "disgust": [
                "disgusted",
                "revolted",
                "repulsed",
                "nauseated",
                "appalled",
                "sickened",
            ],
            "love": [
                "love",
                "adore",
                "cherish",
                "affection",
                "caring",
                "devoted",
                "fond",
            ],
            "optimism": [
                "hopeful",
                "optimistic",
                "confident",
                "positive",
                "encouraged",
                "upbeat",
            ],
            "pessimism": [
                "pessimistic",
                "hopeless",
                "negative",
                "doubtful",
                "cynical",
                "despairing",
            ],
            "trust": [
                "trust",
                "believe",
                "confident",
                "reliable",
                "faithful",
                "dependable",
            ],
        }

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze emotions using keyword matching.

        Args:
            text: Input text

        Returns:
            Dictionary mapping emotions to scores
        """
        text_lower = text.lower()
        emotion_scores = {}

        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            # Normalize by text length
            score = min(score / (len(text.split()) / 10), 1.0)
            emotion_scores[emotion] = score

        # Normalize scores
        total = sum(emotion_scores.values())
        if total > 0:
            emotion_scores = {e: s / total for e, s in emotion_scores.items()}

        return emotion_scores
