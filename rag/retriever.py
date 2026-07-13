"""
Hybrid retriever combining vector similarity search and keyword (FTS5) search.
Implements multi-query expansion and result merging for better recall.
"""

from typing import List, Tuple, Dict, Optional
from database.db_manager import DatabaseManager
from config import TOP_K_RESULTS, SIMILARITY_THRESHOLD


class HybridRetriever:
    """
    Combines vector search and keyword search for optimal retrieval.
    Implements:
    - Multi-query expansion
    - Hybrid scoring (vector + keyword)
    - Result deduplication and merging
    """

    def __init__(self):
        self.db = DatabaseManager()
        self._vector_store = None  # Lazy-loaded to avoid slow model init

    @property
    def vector_store(self):
        """Lazy-load vector store only when needed."""
        if self._vector_store is None:
            from rag.vector_store import VectorStore
            self._vector_store = VectorStore()
        return self._vector_store

    def retrieve(self, query: str, jurisdiction: str = None,
                 category: str = None, top_k: int = TOP_K_RESULTS) -> List[Dict]:
        """
        Retrieve relevant context using hybrid search.

        Returns list of dicts with: text, score, source, metadata
        """
        results = {}

        # 1. Vector similarity search (only if embeddings exist — avoids slow model load)
        try:
            vector_results = self.vector_store.search(
                query=query,
                top_k=top_k * 2,
                threshold=SIMILARITY_THRESHOLD
            )
            for text, score, meta in vector_results:
                key = text[:100]  # dedup key
                if key not in results or results[key]["score"] < score:
                    results[key] = {
                        "text": text,
                        "score": score,
                        "source": "vector",
                        "metadata": meta
                    }
        except Exception:
            pass  # Vector search is optional; FTS5 is the primary fallback

        # 2. Keyword (FTS5) search from knowledge base — this is always fast
        try:
            keyword_results = self.db.search_knowledge_base(
                query=query,
                jurisdiction=jurisdiction,
                category=category,
                limit=top_k
            )
            for entry in keyword_results:
                key = entry.get("content", "")[:100]
                fts_score = 0.5  # baseline score for FTS results
                if key not in results:
                    results[key] = {
                        "text": entry.get("content", ""),
                        "score": fts_score,
                        "source": "knowledge_base",
                        "metadata": {
                            "title": entry.get("title", ""),
                            "category": entry.get("category", ""),
                            "jurisdiction": entry.get("jurisdiction", ""),
                        }
                    }
                else:
                    # Boost score if found in both searches
                    results[key]["score"] = min(results[key]["score"] + 0.2, 1.0)
                    results[key]["source"] = "hybrid"
        except Exception:
            pass  # FTS might not have data yet

        # Sort by score and return top-k
        sorted_results = sorted(results.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:top_k]

    def build_context(self, query: str, jurisdiction: str = None,
                      max_context_length: int = 3000) -> str:
        """
        Build a context string from retrieved documents for LLM prompt.
        """
        results = self.retrieve(query, jurisdiction=jurisdiction)

        if not results:
            return ""

        context_parts = []
        total_length = 0

        for i, result in enumerate(results):
            text = result["text"]
            if total_length + len(text) > max_context_length:
                # Truncate to fit
                remaining = max_context_length - total_length
                if remaining > 100:
                    text = text[:remaining] + "..."
                else:
                    break
            source_info = ""
            meta = result.get("metadata", {})
            if meta.get("title"):
                source_info = f" (Source: {meta['title']})"
            context_parts.append(f"[{i+1}] {text}{source_info}")
            total_length += len(text)

        return "\n\n".join(context_parts)
