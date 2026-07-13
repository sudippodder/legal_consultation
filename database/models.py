"""
Data models for the AI Legal Consultation Platform.
Uses Python dataclasses for type safety and serialization.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = "user"  # user, admin
    default_jurisdiction: str = "General / International"
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    is_active: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class Document:
    id: Optional[int] = None
    user_id: int = 0
    filename: str = ""
    file_type: str = ""
    file_size: int = 0
    content_text: str = ""
    document_type: str = ""  # NDA, employment, lease, etc.
    upload_date: Optional[str] = None
    status: str = "uploaded"  # uploaded, processing, analyzed, error

    def to_dict(self):
        return asdict(self)


@dataclass
class ContractAnalysis:
    id: Optional[int] = None
    document_id: int = 0
    user_id: int = 0
    contract_type: str = ""
    jurisdiction: str = ""
    overall_risk_score: float = 0.0
    total_clauses: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    clauses_json: str = "[]"  # JSON array of clause analyses
    recommendations_json: str = "[]"  # JSON array of recommendations
    summary: str = ""
    confidence_score: float = 0.0
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @property
    def clauses(self) -> list:
        return json.loads(self.clauses_json)

    @property
    def recommendations(self) -> list:
        return json.loads(self.recommendations_json)


@dataclass
class ClauseAnalysis:
    """Individual clause analysis result."""
    clause_number: int = 0
    clause_type: str = ""
    clause_text: str = ""
    risk_score: float = 0.0
    risk_level: str = "low"  # low, medium, high
    explanation: str = ""
    suggestion: str = ""
    is_missing: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class ChatSession:
    id: Optional[int] = None
    user_id: int = 0
    title: str = "New Conversation"
    jurisdiction: str = "General / International"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True
    message_count: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class ChatMessage:
    id: Optional[int] = None
    session_id: int = 0
    role: str = "user"  # user, assistant, system
    content: str = ""
    sources_json: str = "[]"  # JSON array of source citations
    confidence_score: float = 0.0
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @property
    def sources(self) -> list:
        return json.loads(self.sources_json)


@dataclass
class DocumentSummary:
    id: Optional[int] = None
    document_id: int = 0
    user_id: int = 0
    summary_type: str = "standard"  # brief, standard, detailed
    executive_summary: str = ""
    key_points_json: str = "[]"
    action_items_json: str = "[]"
    parties_involved_json: str = "[]"
    important_dates_json: str = "[]"
    obligations_json: str = "[]"
    confidence_score: float = 0.0
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @property
    def key_points(self) -> list:
        return json.loads(self.key_points_json)

    @property
    def action_items(self) -> list:
        return json.loads(self.action_items_json)

    @property
    def parties_involved(self) -> list:
        return json.loads(self.parties_involved_json)

    @property
    def important_dates(self) -> list:
        return json.loads(self.important_dates_json)

    @property
    def obligations(self) -> list:
        return json.loads(self.obligations_json)


@dataclass
class KnowledgeEntry:
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    category: str = ""  # statute, case_law, template, glossary, rule
    jurisdiction: str = "General / International"
    source: str = ""
    year: Optional[int] = None
    embedding_id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class EmbeddingRecord:
    id: Optional[int] = None
    content_hash: str = ""
    content_text: str = ""
    embedding_blob: Optional[bytes] = None
    source_type: str = ""  # document, knowledge_base, chat
    source_id: Optional[int] = None
    metadata_json: str = "{}"
    created_at: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        # Don't serialize binary blob to dict
        d.pop("embedding_blob", None)
        return d


@dataclass
class AuditLog:
    id: Optional[int] = None
    user_id: int = 0
    action: str = ""  # login, upload, analyze, chat, summarize, export
    details: str = ""
    ip_address: str = ""
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)
