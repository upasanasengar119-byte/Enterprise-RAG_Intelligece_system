"""
Simplified embedding model using TF-IDF style approach with numpy.
No external dependencies beyond numpy.
"""
import os
import re
import math
import numpy as np
from typing import List, Dict, Set
from collections import Counter

# Disable HuggingFace downloads
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


class EmbeddingModel:
    """
    Lightweight TF-IDF based embedding model.
    Produces deterministic, semantic-ish embeddings using word frequencies.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name=None):
        if not hasattr(self, 'vocabulary'):
            self.vocabulary = {}
            self.idf = {}
            self.embedding_dim = 256
            self.fitted = False
            self.documents_for_fitting = []

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words."""
        text = text.lower()
        # Remove punctuation and split
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        tokens = text.split()
        # Remove very short tokens and common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                        'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was',
                        'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
                        'did', 'will', 'would', 'should', 'could', 'may', 'might',
                        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
                        'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when',
                        'where', 'why', 'how'}
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    def fit(self, documents: List[str]):
        """Build vocabulary and IDF from a corpus."""
        if self.fitted:
            return

        self.documents_for_fitting = documents
        doc_count = len(documents)

        # Build vocabulary
        doc_freq = Counter()
        all_tokens = Counter()

        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                doc_freq[token] += 1
            for token in self._tokenize(doc):
                all_tokens[token] += 1

        # Keep top N words
        most_common = all_tokens.most_common(self.embedding_dim)
        self.vocabulary = {word: idx for idx, (word, _) in enumerate(most_common)}

        # Compute IDF
        self.idf = {}
        for word, idx in self.vocabulary.items():
            df = doc_freq.get(word, 1)
            self.idf[word] = math.log((doc_count + 1) / (df + 1)) + 1

        self.fitted = True

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self.fitted:
            # Return zero embedding if not fitted yet
            return [0.0] * self.embedding_dim

        tokens = self._tokenize(text)
        token_counts = Counter(tokens)

        # Build TF-IDF vector
        vector = np.zeros(self.embedding_dim)
        for token, count in token_counts.items():
            if token in self.vocabulary:
                idx = self.vocabulary[token]
                tf = 1 + math.log(count)  # Log normalization
                idf = self.idf[token]
                vector[idx] = tf * idf

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        return [self.embed_text(text) for text in texts]

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        emb1 = np.array(self.embed_text(text1))
        emb2 = np.array(self.embed_text(text2))

        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(v1, v2) / (norm1 * norm2))


# Global instance
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create the global embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
