"""
Topic modeling system for Reddit content analysis.

This module provides topic modeling capabilities using both traditional
approaches (LDA) and modern transformer-based methods (BERT) for
comprehensive topic discovery and analysis.
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime
import pickle

# Core libraries
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Gensim for traditional topic modeling (currently disabled)
GENSIM_AVAILABLE = False
# Gensim imports removed as they're not currently used
# Uncomment below if gensim functionality is implemented:
# try:
#     import gensim
#     GENSIM_AVAILABLE = True
# except ImportError:
#     GENSIM_AVAILABLE = False

# Transformer libraries for BERT-based topic modeling
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    from umap import UMAP

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning(
        "Transformers/UMAP not available. BERT-based topic modeling disabled."
    )

logger = logging.getLogger(__name__)


class TopicModeler:
    """
    Comprehensive topic modeling system supporting multiple approaches.

    Provides both traditional statistical methods (LDA) and modern
    transformer-based approaches for topic discovery and analysis.
    """

    def __init__(
        self,
        n_topics: int = 10,
        method: str = "lda",
        min_df: int = 5,
        max_df: float = 0.8,
        max_features: int = 1000,
        random_state: int = 42,
    ):
        """
        Initialize the topic modeler.

        Args:
            n_topics: Number of topics to discover
            method: Topic modeling method ('lda', 'bert', 'combined')
            min_df: Minimum document frequency for features
            max_df: Maximum document frequency for features
            max_features: Maximum number of features
            random_state: Random state for reproducibility
        """
        self.n_topics = n_topics
        self.method = method
        self.min_df = min_df
        self.max_df = max_df
        self.max_features = max_features
        self.random_state = random_state

        # Initialize components
        self.vectorizer = None
        self.lda_model = None
        self.bert_model = None
        self.bert_tokenizer = None
        self.topic_labels = {}
        self.is_fitted = False

        # Initialize models based on method
        self._initialize_models()

    def _initialize_models(self):
        """Initialize the required models based on the selected method."""
        if self.method in ["lda", "combined"]:
            self.vectorizer = CountVectorizer(
                min_df=self.min_df,
                max_df=self.max_df,
                max_features=self.max_features,
                stop_words="english",
                ngram_range=(1, 2),
            )
            logger.info("Initialized LDA vectorizer")

        if self.method in ["bert", "combined"] and TRANSFORMERS_AVAILABLE:
            try:
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
                self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.bert_model = AutoModel.from_pretrained(model_name)
                logger.info(f"Initialized BERT model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize BERT model: {e}")
                if self.method == "bert":
                    self.method = "lda"  # Fallback to LDA

    def preprocess_texts(self, texts: List[str]) -> List[str]:
        """
        Preprocess texts for topic modeling.

        Args:
            texts: List of text documents

        Returns:
            List of preprocessed texts
        """
        processed_texts = []

        for text in texts:
            if not text or not isinstance(text, str):
                processed_texts.append("")
                continue

            # Basic preprocessing
            text = text.lower().strip()

            # Remove very short texts
            if len(text.split()) < 3:
                processed_texts.append("")
                continue

            processed_texts.append(text)

        return processed_texts

    def fit_lda_model(self, texts: List[str]) -> Dict[str, Any]:
        """
        Fit LDA topic model on texts.

        Args:
            texts: List of text documents

        Returns:
            Dictionary with LDA model results
        """
        if not texts:
            return {}

        try:
            # Vectorize texts
            doc_term_matrix = self.vectorizer.fit_transform(texts)

            # Fit LDA model
            self.lda_model = LatentDirichletAllocation(
                n_components=self.n_topics,
                max_iter=20,
                learning_method="online",
                learning_offset=50.0,
                random_state=self.random_state,
            )

            self.lda_model.fit(doc_term_matrix)

            # Extract topics
            feature_names = self.vectorizer.get_feature_names_out()
            topics = self._extract_lda_topics(feature_names)

            # Calculate perplexity and log-likelihood
            perplexity = self.lda_model.perplexity(doc_term_matrix)
            log_likelihood = self.lda_model.score(doc_term_matrix)

            logger.info(f"LDA model fitted with {self.n_topics} topics")

            return {
                "topics": topics,
                "perplexity": perplexity,
                "log_likelihood": log_likelihood,
                "n_documents": len(texts),
                "vocabulary_size": len(feature_names),
            }

        except Exception as e:
            logger.error(f"LDA model fitting failed: {e}")
            return {}

    def _extract_lda_topics(
        self, feature_names: np.ndarray, n_top_words: int = 10
    ) -> List[Dict[str, Any]]:
        """Extract topic information from fitted LDA model."""
        topics = []

        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_words_idx = topic.argsort()[-n_top_words:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            top_weights = [topic[i] for i in top_words_idx]

            topic_info = {
                "topic_id": topic_idx,
                "words": top_words,
                "weights": top_weights,
                "total_weight": float(topic.sum()),
            }

            topics.append(topic_info)

        return topics

    def fit_bert_model(self, texts: List[str]) -> Dict[str, Any]:
        """
        Fit BERT-based topic model using clustering on embeddings.

        Args:
            texts: List of text documents

        Returns:
            Dictionary with BERT model results
        """
        if not texts or not TRANSFORMERS_AVAILABLE:
            return {}

        try:
            # Generate embeddings
            embeddings = self._generate_bert_embeddings(texts)

            if embeddings is None or len(embeddings) == 0:
                return {}

            # Reduce dimensionality
            if len(embeddings[0]) > 50:
                reducer = UMAP(
                    n_components=min(50, len(texts)), random_state=self.random_state
                )
                reduced_embeddings = reducer.fit_transform(embeddings)
            else:
                reduced_embeddings = embeddings

            # Cluster embeddings
            kmeans = KMeans(
                n_clusters=self.n_topics, random_state=self.random_state, n_init=10
            )
            cluster_labels = kmeans.fit_predict(reduced_embeddings)

            # Calculate silhouette score
            silhouette = silhouette_score(reduced_embeddings, cluster_labels)

            # Extract topic information
            topics = self._extract_bert_topics(texts, cluster_labels)

            # Store model components
            self.bert_cluster_model = kmeans
            self.bert_embeddings = embeddings
            self.bert_cluster_labels = cluster_labels

            logger.info(f"BERT model fitted with {self.n_topics} topics")

            return {
                "topics": topics,
                "silhouette_score": silhouette,
                "n_documents": len(texts),
                "embedding_dim": len(embeddings[0]) if embeddings else 0,
            }

        except Exception as e:
            logger.error(f"BERT model fitting failed: {e}")
            return {}

    def _generate_bert_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate BERT embeddings for texts."""
        if not self.bert_model or not self.bert_tokenizer:
            return None

        embeddings = []
        batch_size = 32

        try:
            self.bert_model.eval()

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]

                # Tokenize batch
                inputs = self.bert_tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )

                # Generate embeddings
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    # Use CLS token embedding
                    batch_embeddings = outputs.last_hidden_state[:, 0, :].numpy()
                    embeddings.extend(batch_embeddings)

            return np.array(embeddings)

        except Exception as e:
            logger.warning(f"BERT embedding generation failed: {e}")
            return None

    def _extract_bert_topics(
        self, texts: List[str], cluster_labels: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Extract topic information from BERT clustering results."""
        topics = []

        # Group texts by cluster
        for topic_id in range(self.n_topics):
            topic_texts = [
                texts[i] for i, label in enumerate(cluster_labels) if label == topic_id
            ]

            if not topic_texts:
                topics.append(
                    {
                        "topic_id": topic_id,
                        "words": [],
                        "representative_texts": [],
                        "document_count": 0,
                    }
                )
                continue

            # Extract keywords using TF-IDF on cluster texts
            try:
                tfidf = TfidfVectorizer(
                    max_features=20, stop_words="english", ngram_range=(1, 2)
                )

                tfidf_matrix = tfidf.fit_transform(topic_texts)
                feature_names = tfidf.get_feature_names_out()

                # Get average TF-IDF scores
                mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
                top_indices = mean_scores.argsort()[-10:][::-1]

                top_words = [feature_names[i] for i in top_indices]
                top_scores = [mean_scores[i] for i in top_indices]

                # Select representative texts (shortest ones for readability)
                representative_texts = sorted(topic_texts, key=len)[:3]

                topic_info = {
                    "topic_id": topic_id,
                    "words": top_words,
                    "word_scores": top_scores,
                    "representative_texts": representative_texts,
                    "document_count": len(topic_texts),
                }

                topics.append(topic_info)

            except Exception as e:
                logger.warning(f"Failed to extract topic {topic_id}: {e}")
                topics.append(
                    {
                        "topic_id": topic_id,
                        "words": [],
                        "representative_texts": topic_texts[:3],
                        "document_count": len(topic_texts),
                    }
                )

        return topics

    def fit(self, texts: List[str]) -> Dict[str, Any]:
        """
        Fit topic model(s) on texts.

        Args:
            texts: List of text documents

        Returns:
            Dictionary with fitting results
        """
        if not texts:
            logger.warning("No texts provided for topic modeling")
            return {}

        # Preprocess texts
        processed_texts = self.preprocess_texts(texts)
        valid_texts = [text for text in processed_texts if text]

        if len(valid_texts) < self.n_topics:
            logger.warning(
                f"Not enough valid texts ({len(valid_texts)}) for {self.n_topics} topics"
            )
            return {}

        results = {
            "method": self.method,
            "n_topics": self.n_topics,
            "n_documents": len(valid_texts),
            "fit_timestamp": datetime.now().isoformat(),
        }

        # Fit models based on method
        if self.method in ["lda", "combined"]:
            lda_results = self.fit_lda_model(valid_texts)
            results["lda"] = lda_results

        if self.method in ["bert", "combined"]:
            bert_results = self.fit_bert_model(valid_texts)
            results["bert"] = bert_results

        self.is_fitted = True
        logger.info(f"Topic modeling completed using {self.method} method")

        return results

    def predict_topics(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Predict topics for new texts.

        Args:
            texts: List of text documents to predict topics for

        Returns:
            List of topic predictions for each text
        """
        if not self.is_fitted:
            logger.warning("Model not fitted. Call fit() first.")
            return []

        predictions = []
        processed_texts = self.preprocess_texts(texts)

        for i, text in enumerate(processed_texts):
            if not text:
                predictions.append(self._empty_prediction())
                continue

            prediction = {"text_index": i, "text": texts[i]}

            # LDA predictions
            if self.method in ["lda", "combined"] and self.lda_model:
                lda_pred = self._predict_lda_topic(text)
                prediction["lda"] = lda_pred

            # BERT predictions
            if self.method in ["bert", "combined"] and hasattr(
                self, "bert_cluster_model"
            ):
                bert_pred = self._predict_bert_topic(text)
                prediction["bert"] = bert_pred

            predictions.append(prediction)

        return predictions

    def _predict_lda_topic(self, text: str) -> Dict[str, Any]:
        """Predict LDA topic for a single text."""
        try:
            doc_vector = self.vectorizer.transform([text])
            topic_probs = self.lda_model.transform(doc_vector)[0]

            # Get top topic
            top_topic = np.argmax(topic_probs)
            top_prob = topic_probs[top_topic]

            return {
                "top_topic": int(top_topic),
                "probability": float(top_prob),
                "all_probabilities": topic_probs.tolist(),
            }
        except Exception as e:
            logger.warning(f"LDA prediction failed: {e}")
            return {"top_topic": -1, "probability": 0.0, "all_probabilities": []}

    def _predict_bert_topic(self, text: str) -> Dict[str, Any]:
        """Predict BERT topic for a single text."""
        try:
            # Generate embedding
            embedding = self._generate_bert_embeddings([text])
            if embedding is None or len(embedding) == 0:
                return {"top_topic": -1, "distance": float("inf")}

            # Predict cluster
            cluster = self.bert_cluster_model.predict(embedding[0].reshape(1, -1))[0]

            # Calculate distance to cluster center
            distance = np.linalg.norm(
                embedding[0] - self.bert_cluster_model.cluster_centers_[cluster]
            )

            return {"top_topic": int(cluster), "distance": float(distance)}
        except Exception as e:
            logger.warning(f"BERT prediction failed: {e}")
            return {"top_topic": -1, "distance": float("inf")}

    def get_topic_distribution(self, text: str) -> Dict[str, float]:
        """
        Get topic distribution for a single text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping topic IDs to probabilities
        """
        if not self.is_fitted or not self.lda_model:
            return {}

        try:
            processed_text = self.preprocess_texts([text])[0]
            if not processed_text:
                return {}

            doc_vector = self.vectorizer.transform([processed_text])
            topic_probs = self.lda_model.transform(doc_vector)[0]

            return {f"topic_{i}": float(prob) for i, prob in enumerate(topic_probs)}
        except Exception as e:
            logger.warning(f"Topic distribution calculation failed: {e}")
            return {}

    def get_topic_words(
        self, topic_id: int, n_words: int = 10
    ) -> List[Dict[str, float]]:
        """
        Get top words for a specific topic.

        Args:
            topic_id: ID of the topic
            n_words: Number of top words to return

        Returns:
            List of word-weight dictionaries
        """
        if not self.is_fitted or not self.lda_model:
            return []

        if topic_id >= self.n_topics or topic_id < 0:
            return []

        try:
            feature_names = self.vectorizer.get_feature_names_out()
            topic = self.lda_model.components_[topic_id]

            top_words_idx = topic.argsort()[-n_words:][::-1]

            words = []
            for idx in top_words_idx:
                words.append({"word": feature_names[idx], "weight": float(topic[idx])})

            return words
        except Exception as e:
            logger.warning(f"Failed to get topic words: {e}")
            return []

    def calculate_topic_coherence(self, texts: List[str]) -> float:
        """
        Calculate topic coherence score.

        Args:
            texts: Texts used for training

        Returns:
            Coherence score
        """
        if not GENSIM_AVAILABLE or not self.is_fitted or not self.lda_model:
            return 0.0

        try:
            # Prepare data for potential gensim operations
            # Note: actual gensim operations removed as they're not currently used

            # Convert sklearn LDA to gensim format (simplified)
            # This is a simplified version - full conversion would be more complex

            # For now, return a placeholder coherence score
            # In practice, you might want to fit a gensim LDA model for coherence
            return 0.5  # Placeholder

        except Exception as e:
            logger.warning(f"Coherence calculation failed: {e}")
            return 0.0

    def save_model(self, filepath: str):
        """Save the fitted model to file."""
        if not self.is_fitted:
            logger.warning("No fitted model to save")
            return

        try:
            model_data = {
                "method": self.method,
                "n_topics": self.n_topics,
                "vectorizer": self.vectorizer,
                "lda_model": self.lda_model,
                "topic_labels": self.topic_labels,
                "parameters": {
                    "min_df": self.min_df,
                    "max_df": self.max_df,
                    "max_features": self.max_features,
                    "random_state": self.random_state,
                },
            }

            with open(filepath, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def load_model(self, filepath: str):
        """Load a fitted model from file."""
        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)

            self.method = model_data["method"]
            self.n_topics = model_data["n_topics"]
            self.vectorizer = model_data["vectorizer"]
            self.lda_model = model_data["lda_model"]
            self.topic_labels = model_data["topic_labels"]

            # Restore parameters
            params = model_data.get("parameters", {})
            self.min_df = params.get("min_df", self.min_df)
            self.max_df = params.get("max_df", self.max_df)
            self.max_features = params.get("max_features", self.max_features)
            self.random_state = params.get("random_state", self.random_state)

            self.is_fitted = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def _empty_prediction(self) -> Dict[str, Any]:
        """Return empty prediction result."""
        return {
            "text_index": -1,
            "text": "",
            "lda": {"top_topic": -1, "probability": 0.0, "all_probabilities": []},
            "bert": {"top_topic": -1, "distance": float("inf")},
        }
