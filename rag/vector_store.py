"""
SQLite-backed vector store for RAG.
Stores embeddings as BLOBs and computes cosine similarity in Python.
"""

import numpy as np
from typing import List, Tuple, Optional
from database.db_manager import DatabaseManager
from rag.embeddings import EmbeddingEngine


class VectorStore:
    """SQLite-backed vector similarity search."""

    def __init__(self):
        self.db = DatabaseManager()
        self.engine = EmbeddingEngine()

    def add_text(self, text: str, source_type: str = "",
                 source_id: int = None, metadata: dict = None) -> int:
        """Embed and store a text chunk."""
        import json
        embedding = self.engine.embed_text(text)
        embedding_bytes = self.engine.embedding_to_bytes(embedding)
        metadata_json = json.dumps(metadata or {})

        return self.db.save_embedding(
            content_text=text,
            embedding_blob=embedding_bytes,
            source_type=source_type,
            source_id=source_id,
            metadata_json=metadata_json,
        )

    def add_texts(self, texts: List[str], source_type: str = "",
                  source_id: int = None, metadata_list: List[dict] = None) -> List[int]:
        """Embed and store multiple text chunks."""
        import json
        embeddings = self.engine.embed_batch(texts)
        ids = []
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            meta = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
            emb_bytes = self.engine.embedding_to_bytes(emb)
            eid = self.db.save_embedding(
                content_text=text,
                embedding_blob=emb_bytes,
                source_type=source_type,
                source_id=source_id,
                metadata_json=json.dumps(meta),
            )
            ids.append(eid)
        return ids

    def search(self, query: str, top_k: int = 5,
               source_type: str = None,
               threshold: float = 0.3) -> List[Tuple[str, float, dict]]:
        """
        Search for similar texts using cosine similarity.

        Returns list of (text, score, metadata) tuples sorted by relevance.
        """
        import json

        # IMPORTANT: Check if any embeddings exist BEFORE loading the heavy model
        records = self.db.get_all_embeddings(source_type=source_type)

        if not records:
            return []

        query_embedding = self.engine.embed_text(query)

        results = []
        for record in records:
            if not record.get("embedding_blob"):
                continue
            stored_emb = self.engine.bytes_to_embedding(record["embedding_blob"])
            score = float(np.dot(query_embedding, stored_emb))  # cosine sim (normalized)

            if score >= threshold:
                meta = json.loads(record.get("metadata_json", "{}"))
                results.append((record["content_text"], score, meta))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_store_size(self) -> int:
        """Get the number of stored embeddings."""
        records = self.db.get_all_embeddings()
        return len(records)
