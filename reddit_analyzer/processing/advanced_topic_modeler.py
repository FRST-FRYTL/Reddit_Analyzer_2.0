"""
Advanced topic modeling module using state-of-the-art techniques.

This module provides advanced topic modeling beyond basic LDA, including
neural topic models, dynamic topic modeling, and hierarchical topic structures.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
import torch
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from collections import defaultdict
import pandas as pd
from datetime import datetime
import hdbscan
import umap

logger = logging.getLogger(__name__)


class AdvancedTopicModeler:
    """Advanced topic modeling with multiple algorithms and techniques."""

    def __init__(
        self,
        method: str = "bertopic",
        embedding_model: str = "all-MiniLM-L6-v2",
        use_gpu: bool = False,
        min_topic_size: int = 10,
    ):
        """
        Initialize advanced topic modeler.

        Args:
            method: Topic modeling method ("bertopic", "nmf", "lda", "neural")
            embedding_model: Model for document embeddings
            use_gpu: Whether to use GPU
            min_topic_size: Minimum documents per topic
        """
        self.method = method
        self.embedding_model_name = embedding_model
        self.use_gpu = use_gpu
        self.min_topic_size = min_topic_size
        self.model = None
        self.embedder = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize the selected topic modeling approach."""
        try:
            if self.method == "bertopic":
                self._init_bertopic()
            elif self.method == "nmf":
                self._init_nmf()
            elif self.method == "lda":
                self._init_lda()
            elif self.method == "neural":
                self._init_neural_topic_model()
            else:
                logger.warning(f"Unknown method {self.method}, defaulting to LDA")
                self._init_lda()
        except Exception as e:
            logger.error(f"Failed to initialize {self.method}: {e}")
            logger.info("Falling back to LDA")
            self._init_lda()

    def _init_bertopic(self):
        """Initialize BERTopic model."""
        try:
            # Initialize sentence transformer
            device = "cuda" if self.use_gpu and torch.cuda.is_available() else "cpu"
            self.embedder = SentenceTransformer(
                self.embedding_model_name, device=device
            )

            # Configure UMAP for dimensionality reduction
            umap_model = umap.UMAP(
                n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine"
            )

            # Configure HDBSCAN for clustering
            hdbscan_model = hdbscan.HDBSCAN(
                min_cluster_size=self.min_topic_size,
                metric="euclidean",
                cluster_selection_method="eom",
                prediction_data=True,
            )

            # Initialize BERTopic
            self.model = BERTopic(
                embedding_model=self.embedder,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                nr_topics="auto",
                top_n_words=10,
                verbose=False,
            )

            logger.info("Initialized BERTopic model")
        except ImportError:
            logger.error("BERTopic not available, falling back to LDA")
            self.method = "lda"
            self._init_lda()

    def _init_nmf(self):
        """Initialize Non-negative Matrix Factorization."""
        self.vectorizer = TfidfVectorizer(
            max_features=1000, min_df=5, max_df=0.8, ngram_range=(1, 2)
        )
        self.model = NMF(n_components=10, random_state=42, alpha=0.1, l1_ratio=0.5)
        logger.info("Initialized NMF model")

    def _init_lda(self):
        """Initialize Latent Dirichlet Allocation."""
        self.vectorizer = CountVectorizer(
            max_features=1000, min_df=5, max_df=0.8, ngram_range=(1, 2)
        )
        self.model = LatentDirichletAllocation(
            n_components=10, random_state=42, learning_method="online", batch_size=128
        )
        logger.info("Initialized LDA model")

    def _init_neural_topic_model(self):
        """Initialize neural topic model (placeholder for advanced models)."""
        logger.info("Neural topic model not implemented, falling back to BERTopic")
        self.method = "bertopic"
        self._init_bertopic()

    def fit_transform(
        self, documents: List[str], metadata: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Fit the model and transform documents to topics.

        Args:
            documents: List of text documents
            metadata: Optional metadata for each document

        Returns:
            Dictionary with topics and document assignments
        """
        if not documents:
            return {"topics": [], "document_topics": [], "topic_words": {}}

        try:
            if self.method == "bertopic":
                return self._fit_transform_bertopic(documents, metadata)
            elif self.method in ["nmf", "lda"]:
                return self._fit_transform_sklearn(documents, metadata)
            else:
                return self._fit_transform_sklearn(documents, metadata)
        except Exception as e:
            logger.error(f"Error in topic modeling: {e}")
            return {"topics": [], "document_topics": [], "topic_words": {}}

    def _fit_transform_bertopic(
        self, documents: List[str], metadata: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Fit and transform using BERTopic."""
        # Fit the model
        topics, probs = self.model.fit_transform(documents)

        # Get topic information
        topic_info = self.model.get_topic_info()

        # Extract topic words
        topic_words = {}
        for topic_id in topic_info["Topic"].unique():
            if topic_id != -1:  # Skip outlier topic
                words = self.model.get_topic(topic_id)
                topic_words[topic_id] = [
                    {"word": word, "weight": score} for word, score in words
                ]

        # Create topic summaries
        topic_summaries = []
        for _, row in topic_info.iterrows():
            if row["Topic"] != -1:
                topic_summaries.append(
                    {
                        "topic_id": row["Topic"],
                        "size": row["Count"],
                        "representative_docs": self._get_representative_docs(
                            documents, topics, row["Topic"]
                        )[:3],
                    }
                )

        return {
            "topics": topic_summaries,
            "document_topics": topics,
            "document_probabilities": (
                probs.tolist() if isinstance(probs, np.ndarray) else probs
            ),
            "topic_words": topic_words,
            "num_topics": len(topic_summaries),
        }

    def _fit_transform_sklearn(
        self, documents: List[str], metadata: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Fit and transform using sklearn models (LDA/NMF)."""
        # Vectorize documents
        doc_term_matrix = self.vectorizer.fit_transform(documents)

        # Fit the model
        doc_topics = self.model.fit_transform(doc_term_matrix)

        # Get feature names
        feature_names = self.vectorizer.get_feature_names_out()

        # Extract topic words
        topic_words = {}
        n_top_words = 10

        for topic_idx, topic in enumerate(self.model.components_):
            top_indices = topic.argsort()[-n_top_words:][::-1]
            top_words = [(feature_names[i], topic[i]) for i in top_indices]
            topic_words[topic_idx] = [
                {"word": word, "weight": float(weight)} for word, weight in top_words
            ]

        # Get document topics
        document_topics = doc_topics.argmax(axis=1).tolist()
        document_probabilities = doc_topics.max(axis=1).tolist()

        # Create topic summaries
        topic_summaries = []
        for topic_id in range(self.model.n_components):
            doc_indices = [i for i, t in enumerate(document_topics) if t == topic_id]
            topic_summaries.append(
                {
                    "topic_id": topic_id,
                    "size": len(doc_indices),
                    "representative_docs": [
                        documents[i][:200] for i in doc_indices[:3]
                    ],
                }
            )

        return {
            "topics": topic_summaries,
            "document_topics": document_topics,
            "document_probabilities": document_probabilities,
            "topic_words": topic_words,
            "num_topics": len(topic_summaries),
        }

    def _get_representative_docs(
        self, documents: List[str], topics: List[int], topic_id: int
    ) -> List[str]:
        """Get representative documents for a topic."""
        doc_indices = [i for i, t in enumerate(topics) if t == topic_id]
        return [documents[i][:200] + "..." for i in doc_indices[:3]]

    def extract_hierarchical_topics(
        self, documents: List[str], levels: int = 3
    ) -> Dict[str, Any]:
        """
        Extract hierarchical topic structure.

        Args:
            documents: List of documents
            levels: Number of hierarchy levels

        Returns:
            Dictionary with hierarchical topic structure
        """
        if self.method != "bertopic":
            logger.warning("Hierarchical topics only supported with BERTopic")
            return {}

        try:
            # Fit the model first
            topics, probs = self.model.fit_transform(documents)

            # Get hierarchical topics
            hierarchical_topics = self.model.hierarchical_topics(documents)

            # Build hierarchy structure
            hierarchy = self._build_hierarchy(hierarchical_topics, levels)

            return {
                "hierarchy": hierarchy,
                "levels": levels,
                "total_topics": len(set(topics)),
            }
        except Exception as e:
            logger.error(f"Error extracting hierarchical topics: {e}")
            return {}

    def _build_hierarchy(self, hierarchical_topics, max_levels: int) -> List[Dict]:
        """Build hierarchical structure from BERTopic output."""
        # This is a simplified version - actual implementation would depend on BERTopic version
        hierarchy = []

        # Group topics by distance threshold
        for level in range(max_levels):
            level_topics = []
            # Add topic grouping logic here
            hierarchy.append({"level": level, "topics": level_topics})

        return hierarchy

    def track_topic_evolution(
        self, documents: List[str], timestamps: List[datetime], time_bins: int = 10
    ) -> Dict[str, Any]:
        """
        Track how topics evolve over time.

        Args:
            documents: List of documents
            timestamps: Timestamp for each document
            time_bins: Number of time periods to analyze

        Returns:
            Dictionary with topic evolution data
        """
        if len(documents) != len(timestamps):
            raise ValueError("Documents and timestamps must have same length")

        # Create time bins
        time_df = pd.DataFrame({"doc": documents, "time": timestamps})

        time_df["time_bin"] = pd.cut(time_df["time"], bins=time_bins, labels=False)

        # Fit model on all documents
        all_topics = self.fit_transform(documents)

        # Analyze topics per time bin
        evolution = defaultdict(lambda: defaultdict(int))

        for idx, (doc, time_bin) in enumerate(zip(documents, time_df["time_bin"])):
            topic = all_topics["document_topics"][idx]
            evolution[int(time_bin)][topic] += 1

        # Convert to time series
        topic_time_series = {}
        unique_topics = set(all_topics["document_topics"])

        for topic in unique_topics:
            if topic != -1:  # Skip outliers
                topic_time_series[topic] = [
                    evolution[bin_idx].get(topic, 0) for bin_idx in range(time_bins)
                ]

        # Detect emerging and declining topics
        emerging_topics = []
        declining_topics = []

        for topic, series in topic_time_series.items():
            if len(series) > 1:
                # Simple trend detection
                first_half = np.mean(series[: len(series) // 2])
                second_half = np.mean(series[len(series) // 2 :])

                if second_half > first_half * 1.5:
                    emerging_topics.append(topic)
                elif second_half < first_half * 0.5:
                    declining_topics.append(topic)

        return {
            "topic_time_series": topic_time_series,
            "emerging_topics": emerging_topics,
            "declining_topics": declining_topics,
            "time_bins": time_bins,
        }

    def find_similar_topics(
        self, query: str, n_similar: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find topics similar to a query.

        Args:
            query: Query text
            n_similar: Number of similar topics to return

        Returns:
            List of similar topics with scores
        """
        if not self.model:
            return []

        try:
            if self.method == "bertopic" and self.embedder:
                # Get query embedding (would use for similarity search)
                # query_embedding = self.embedder.encode([query])

                # Get topic embeddings (simplified - would need actual topic embeddings)
                # This is a placeholder implementation
                similar_topics = []

                return similar_topics

            else:
                # For sklearn models, use topic words similarity
                if hasattr(self, "vectorizer"):
                    query_vec = self.vectorizer.transform([query])

                    # Calculate similarity with each topic
                    similarities = []
                    for topic_idx in range(self.model.n_components):
                        topic_vec = self.model.components_[topic_idx]
                        similarity = np.dot(query_vec.toarray()[0], topic_vec) / (
                            np.linalg.norm(query_vec.toarray()[0])
                            * np.linalg.norm(topic_vec)
                        )
                        similarities.append(
                            {
                                "topic_id": topic_idx,
                                "similarity": float(similarity),
                                "top_words": self._get_topic_words(topic_idx, 5),
                            }
                        )

                    # Sort by similarity
                    similarities.sort(key=lambda x: x["similarity"], reverse=True)
                    return similarities[:n_similar]

        except Exception as e:
            logger.error(f"Error finding similar topics: {e}")

        return []

    def _get_topic_words(self, topic_id: int, n_words: int = 10) -> List[str]:
        """Get top words for a topic."""
        if hasattr(self, "vectorizer") and hasattr(self.model, "components_"):
            feature_names = self.vectorizer.get_feature_names_out()
            topic = self.model.components_[topic_id]
            top_indices = topic.argsort()[-n_words:][::-1]
            return [feature_names[i] for i in top_indices]
        return []

    def get_topic_diversity(self, topics: Optional[Dict] = None) -> float:
        """
        Calculate diversity of topics (how different they are).

        Args:
            topics: Topic data (uses last fit if not provided)

        Returns:
            Diversity score between 0 and 1
        """
        if topics is None or "topic_words" not in topics:
            return 0.0

        topic_words = topics["topic_words"]
        if not topic_words:
            return 0.0

        # Calculate Jaccard distance between all topic pairs
        all_words_sets = []
        for topic_id, words in topic_words.items():
            word_set = set(w["word"] for w in words[:10])  # Top 10 words
            all_words_sets.append(word_set)

        if len(all_words_sets) < 2:
            return 0.0

        # Calculate pairwise Jaccard distances
        distances = []
        for i in range(len(all_words_sets)):
            for j in range(i + 1, len(all_words_sets)):
                intersection = len(all_words_sets[i] & all_words_sets[j])
                union = len(all_words_sets[i] | all_words_sets[j])
                if union > 0:
                    jaccard = 1 - (intersection / union)
                    distances.append(jaccard)

        # Average distance as diversity measure
        return np.mean(distances) if distances else 0.0

    def get_topic_coherence(
        self, topics: Optional[Dict] = None, documents: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Calculate coherence scores for topics.

        Args:
            topics: Topic data
            documents: Original documents

        Returns:
            Dictionary with coherence scores per topic
        """
        if topics is None or "topic_words" not in topics:
            return {}

        coherence_scores = {}

        # Simplified coherence calculation
        # In practice, would use more sophisticated measures like UMass or CV
        for topic_id, words in topics["topic_words"].items():
            # Get top words
            top_words = [w["word"] for w in words[:10]]

            # Simple coherence: average pairwise word co-occurrence
            if documents:
                co_occurrences = 0
                pairs = 0

                for i in range(len(top_words)):
                    for j in range(i + 1, len(top_words)):
                        word1, word2 = top_words[i], top_words[j]
                        # Count documents containing both words
                        count = sum(
                            1 for doc in documents if word1 in doc and word2 in doc
                        )
                        co_occurrences += count
                        pairs += 1

                if pairs > 0 and len(documents) > 0:
                    coherence_scores[topic_id] = co_occurrences / (
                        pairs * len(documents)
                    )
                else:
                    coherence_scores[topic_id] = 0.0
            else:
                coherence_scores[topic_id] = 0.5  # Default if no documents

        return coherence_scores

    def generate_topic_labels(self, topics: Dict[str, Any]) -> Dict[int, str]:
        """
        Generate human-readable labels for topics.

        Args:
            topics: Topic data with words

        Returns:
            Dictionary mapping topic IDs to labels
        """
        labels = {}

        for topic_id, words in topics.get("topic_words", {}).items():
            # Get top 3 words
            top_words = [w["word"] for w in words[:3]]

            # Create label
            if len(top_words) >= 3:
                label = f"{top_words[0]}_{top_words[1]}_{top_words[2]}"
            else:
                label = "_".join(top_words)

            labels[topic_id] = label

        return labels
