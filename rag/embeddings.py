"""
Embedding generation for the RAG engine.
Uses sentence-transformers for local, free embedding computation.
"""

import numpy as np
import hashlib
import streamlit as st
from typing import List, Optional


@st.cache_resource(show_spinner=False)
def load_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load and cache the sentence-transformer model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


class EmbeddingEngine:
    """Generates embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = load_embedding_model(self.model_name)
        return self._model

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text string."""
        if not text or not text.strip():
            return np.zeros(384)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return np.array(embedding, dtype=np.float32)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        # Filter empty texts but keep index mapping
        valid_texts = []
        valid_indices = []
        for i, t in enumerate(texts):
            if t and t.strip():
                valid_texts.append(t)
                valid_indices.append(i)

        if not valid_texts:
            return [np.zeros(384) for _ in texts]

        embeddings = self.model.encode(
            valid_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        # Map back to original indices
        result = [np.zeros(384, dtype=np.float32) for _ in texts]
        for idx, emb in zip(valid_indices, embeddings):
            result[idx] = np.array(emb, dtype=np.float32)

        return result

    def embedding_to_bytes(self, embedding: np.ndarray) -> bytes:
        """Convert embedding to bytes for SQLite storage."""
        return embedding.astype(np.float32).tobytes()

    def bytes_to_embedding(self, data: bytes) -> np.ndarray:
        """Convert bytes back to embedding array."""
        return np.frombuffer(data, dtype=np.float32)

    @staticmethod
    def content_hash(text: str) -> str:
        """Generate a SHA-256 hash for content deduplication."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
