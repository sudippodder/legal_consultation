"""
Database Manager for AI Legal Consultation Platform.
Handles SQLite connections, schema initialization, and CRUD operations.
"""

import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple, Any

from config import DATABASE_PATH, DATABASE_DIR


class DatabaseManager:
    """Manages all database operations with SQLite."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self.db_path = DATABASE_PATH
        self.initialize()
        self._initialized = True

    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection with WAL mode."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self):
        """Initialize the database with schema."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn = self.get_connection()
            try:
                conn.executescript(schema_sql)
                conn.commit()
            finally:
                conn.close()

    # ─── User Operations ────────────────────────────────────────────────────

    def create_user(self, username: str, email: str, password_hash: str,
                    full_name: str = "", role: str = "user",
                    default_jurisdiction: str = "General / International") -> int:
        """Create a new user and return the user ID."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role, default_jurisdiction)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, email, password_hash, full_name, role, default_jurisdiction)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_last_login(self, user_id: int):
        """Update last login timestamp."""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def update_user_settings(self, user_id: int, **kwargs):
        """Update user settings dynamically."""
        allowed = {"full_name", "default_jurisdiction", "email"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        conn = self.get_connection()
        try:
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()
        finally:
            conn.close()

    # ─── Document Operations ────────────────────────────────────────────────

    def save_document(self, user_id: int, filename: str, file_type: str,
                      file_size: int, content_text: str,
                      document_type: str = "") -> int:
        """Save a document and return its ID."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO documents (user_id, filename, file_type, file_size,
                   content_text, document_type) VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, filename, file_type, file_size, content_text, document_type)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_user_documents(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get all documents for a user."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                """SELECT * FROM documents WHERE user_id = ?
                   ORDER BY upload_date DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_document_status(self, doc_id: int, status: str):
        """Update document processing status."""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE documents SET status = ? WHERE id = ?", (status, doc_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_document_by_id(self, doc_id: int) -> Optional[dict]:
        """Get a single document by ID."""
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ─── Contract Analysis Operations ───────────────────────────────────────

    def save_contract_analysis(self, document_id: int, user_id: int,
                               contract_type: str, jurisdiction: str,
                               overall_risk_score: float, total_clauses: int,
                               high_risk: int, medium_risk: int, low_risk: int,
                               clauses_json: str, recommendations_json: str,
                               summary: str, confidence_score: float) -> int:
        """Save a contract analysis result."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO contract_analyses
                   (document_id, user_id, contract_type, jurisdiction,
                    overall_risk_score, total_clauses, high_risk_count,
                    medium_risk_count, low_risk_count, clauses_json,
                    recommendations_json, summary, confidence_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (document_id, user_id, contract_type, jurisdiction,
                 overall_risk_score, total_clauses, high_risk, medium_risk,
                 low_risk, clauses_json, recommendations_json, summary,
                 confidence_score)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_user_analyses(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get all contract analyses for a user."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                """SELECT ca.*, d.filename FROM contract_analyses ca
                   JOIN documents d ON ca.document_id = d.id
                   WHERE ca.user_id = ? ORDER BY ca.created_at DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_analysis_by_id(self, analysis_id: int) -> Optional[dict]:
        """Get a single contract analysis by ID."""
        conn = self.get_connection()
        try:
            row = conn.execute(
                """SELECT ca.*, d.filename FROM contract_analyses ca
                   JOIN documents d ON ca.document_id = d.id
                   WHERE ca.id = ?""",
                (analysis_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ─── Chat Session Operations ────────────────────────────────────────────

    def create_chat_session(self, user_id: int, title: str = "New Conversation",
                            jurisdiction: str = "General / International") -> int:
        """Create a new chat session."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO chat_sessions (user_id, title, jurisdiction)
                   VALUES (?, ?, ?)""",
                (user_id, title, jurisdiction)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_user_chat_sessions(self, user_id: int, limit: int = 30) -> List[dict]:
        """Get all chat sessions for a user."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                """SELECT * FROM chat_sessions WHERE user_id = ? AND is_active = 1
                   ORDER BY updated_at DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_chat_session_title(self, session_id: int, title: str):
        """Update chat session title."""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, session_id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete_chat_session(self, session_id: int):
        """Soft-delete a chat session."""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE chat_sessions SET is_active = 0 WHERE id = ?",
                (session_id,)
            )
            conn.commit()
        finally:
            conn.close()

    # ─── Chat Message Operations ────────────────────────────────────────────

    def save_chat_message(self, session_id: int, role: str, content: str,
                          sources_json: str = "[]",
                          confidence_score: float = 0.0) -> int:
        """Save a chat message."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO chat_messages (session_id, role, content, sources_json, confidence_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, role, content, sources_json, confidence_score)
            )
            # Update session metadata
            conn.execute(
                """UPDATE chat_sessions
                   SET message_count = message_count + 1,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (session_id,)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_chat_messages(self, session_id: int, limit: int = 100) -> List[dict]:
        """Get all messages in a chat session."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                """SELECT * FROM chat_messages WHERE session_id = ?
                   ORDER BY created_at ASC LIMIT ?""",
                (session_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ─── Document Summary Operations ────────────────────────────────────────

    def save_document_summary(self, document_id: int, user_id: int,
                              summary_type: str, executive_summary: str,
                              key_points_json: str, action_items_json: str,
                              parties_json: str, dates_json: str,
                              obligations_json: str,
                              confidence_score: float) -> int:
        """Save a document summary."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO document_summaries
                   (document_id, user_id, summary_type, executive_summary,
                    key_points_json, action_items_json, parties_involved_json,
                    important_dates_json, obligations_json, confidence_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (document_id, user_id, summary_type, executive_summary,
                 key_points_json, action_items_json, parties_json, dates_json,
                 obligations_json, confidence_score)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_user_summaries(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get all document summaries for a user."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                """SELECT ds.*, d.filename FROM document_summaries ds
                   JOIN documents d ON ds.document_id = d.id
                   WHERE ds.user_id = ? ORDER BY ds.created_at DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ─── Knowledge Base Operations ──────────────────────────────────────────

    def add_knowledge_entry(self, title: str, content: str, category: str,
                            jurisdiction: str = "General / International",
                            source: str = "", year: int = None,
                            embedding_id: int = None) -> int:
        """Add a knowledge base entry."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO knowledge_base
                   (title, content, category, jurisdiction, source, year, embedding_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (title, content, category, jurisdiction, source, year, embedding_id)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def search_knowledge_base(self, query: str, jurisdiction: str = None,
                              category: str = None, limit: int = 10) -> List[dict]:
        """Full-text search the knowledge base using FTS5."""
        conn = self.get_connection()
        try:
            # Build FTS5 query
            fts_query = query.replace('"', '""')
            where_clauses = []
            params = []

            base_sql = """
                SELECT kb.*, rank
                FROM knowledge_base_fts fts
                JOIN knowledge_base kb ON fts.rowid = kb.id
                WHERE knowledge_base_fts MATCH ?
            """
            params.append(fts_query)

            if jurisdiction and jurisdiction != "General / International":
                where_clauses.append("kb.jurisdiction IN (?, 'General / International')")
                params.append(jurisdiction)

            if category:
                where_clauses.append("kb.category = ?")
                params.append(category)

            if where_clauses:
                base_sql += " AND " + " AND ".join(where_clauses)

            base_sql += " ORDER BY rank LIMIT ?"
            params.append(limit)

            rows = conn.execute(base_sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_knowledge_entry_count(self) -> int:
        """Get total number of knowledge base entries."""
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM knowledge_base").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    # ─── Embedding Operations ───────────────────────────────────────────────

    def save_embedding(self, content_text: str, embedding_blob: bytes,
                       source_type: str = "", source_id: int = None,
                       metadata_json: str = "{}") -> int:
        """Save an embedding vector."""
        content_hash = hashlib.sha256(content_text.encode()).hexdigest()
        conn = self.get_connection()
        try:
            # Check if already exists
            existing = conn.execute(
                "SELECT id FROM embeddings WHERE content_hash = ?", (content_hash,)
            ).fetchone()
            if existing:
                return existing["id"]

            cursor = conn.execute(
                """INSERT INTO embeddings
                   (content_hash, content_text, embedding_blob, source_type,
                    source_id, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (content_hash, content_text, embedding_blob, source_type,
                 source_id, metadata_json)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_all_embeddings(self, source_type: str = None) -> List[dict]:
        """Get all embeddings, optionally filtered by source type."""
        conn = self.get_connection()
        try:
            if source_type:
                rows = conn.execute(
                    "SELECT * FROM embeddings WHERE source_type = ?", (source_type,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM embeddings").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ─── Audit Log Operations ───────────────────────────────────────────────

    def log_action(self, user_id: int, action: str, details: str = "",
                   ip_address: str = ""):
        """Log a user action."""
        conn = self.get_connection()
        try:
            conn.execute(
                """INSERT INTO audit_log (user_id, action, details, ip_address)
                   VALUES (?, ?, ?, ?)""",
                (user_id, action, details, ip_address)
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_activity(self, user_id: int, limit: int = 20) -> List[dict]:
        """Get recent activity for a user."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                """SELECT * FROM audit_log WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ─── Dashboard Stats ────────────────────────────────────────────────────

    def get_user_stats(self, user_id: int) -> dict:
        """Get statistics for the dashboard."""
        conn = self.get_connection()
        try:
            stats = {}

            # Document count
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE user_id = ?", (user_id,)
            ).fetchone()
            stats["total_documents"] = row["cnt"] if row else 0

            # Analysis count
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM contract_analyses WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            stats["total_analyses"] = row["cnt"] if row else 0

            # Chat session count
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM chat_sessions WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
            stats["total_chats"] = row["cnt"] if row else 0

            # Summary count
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM document_summaries WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            stats["total_summaries"] = row["cnt"] if row else 0

            # Average risk score
            row = conn.execute(
                """SELECT AVG(overall_risk_score) as avg_risk
                   FROM contract_analyses WHERE user_id = ?""",
                (user_id,)
            ).fetchone()
            stats["avg_risk_score"] = round(row["avg_risk"], 1) if row and row["avg_risk"] else 0.0

            # Total messages
            row = conn.execute(
                """SELECT COUNT(*) as cnt FROM chat_messages cm
                   JOIN chat_sessions cs ON cm.session_id = cs.id
                   WHERE cs.user_id = ?""",
                (user_id,)
            ).fetchone()
            stats["total_messages"] = row["cnt"] if row else 0

            # Risk distribution
            rows = conn.execute(
                """SELECT
                     SUM(high_risk_count) as high,
                     SUM(medium_risk_count) as medium,
                     SUM(low_risk_count) as low
                   FROM contract_analyses WHERE user_id = ?""",
                (user_id,)
            ).fetchone()
            stats["risk_distribution"] = {
                "high": rows["high"] or 0 if rows else 0,
                "medium": rows["medium"] or 0 if rows else 0,
                "low": rows["low"] or 0 if rows else 0,
            }

            return stats
        finally:
            conn.close()
