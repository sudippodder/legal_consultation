-- ============================================================================
-- AI Legal Consultation Platform - Database Schema
-- SQLite with WAL mode and FTS5 full-text search
-- ============================================================================

-- Enable WAL mode for better concurrent performance
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─── Users Table ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT DEFAULT '',
    role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
    default_jurisdiction TEXT DEFAULT 'General / International',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- ─── Documents Table ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    content_text TEXT DEFAULT '',
    document_type TEXT DEFAULT '',
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'uploaded' CHECK(status IN ('uploaded', 'processing', 'analyzed', 'error')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Contract Analyses Table ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS contract_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    contract_type TEXT DEFAULT '',
    jurisdiction TEXT DEFAULT '',
    overall_risk_score REAL DEFAULT 0.0,
    total_clauses INTEGER DEFAULT 0,
    high_risk_count INTEGER DEFAULT 0,
    medium_risk_count INTEGER DEFAULT 0,
    low_risk_count INTEGER DEFAULT 0,
    clauses_json TEXT DEFAULT '[]',
    recommendations_json TEXT DEFAULT '[]',
    summary TEXT DEFAULT '',
    confidence_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Chat Sessions Table ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT DEFAULT 'New Conversation',
    jurisdiction TEXT DEFAULT 'General / International',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Chat Messages Table ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    sources_json TEXT DEFAULT '[]',
    confidence_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- ─── Document Summaries Table ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS document_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    summary_type TEXT DEFAULT 'standard' CHECK(summary_type IN ('brief', 'standard', 'detailed')),
    executive_summary TEXT DEFAULT '',
    key_points_json TEXT DEFAULT '[]',
    action_items_json TEXT DEFAULT '[]',
    parties_involved_json TEXT DEFAULT '[]',
    important_dates_json TEXT DEFAULT '[]',
    obligations_json TEXT DEFAULT '[]',
    confidence_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Knowledge Base Table ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT '' CHECK(category IN ('statute', 'case_law', 'template', 'glossary', 'rule', '')),
    jurisdiction TEXT DEFAULT 'General / International',
    source TEXT DEFAULT '',
    year INTEGER,
    embedding_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE SET NULL
);

-- ─── Embeddings Table (Vector Store) ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL,
    content_text TEXT NOT NULL,
    embedding_blob BLOB,
    source_type TEXT DEFAULT '',
    source_id INTEGER,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Audit Log Table ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT DEFAULT '',
    ip_address TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ─── Indexes ────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_contract_analyses_user_id ON contract_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_contract_analyses_document_id ON contract_analyses(document_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_document_summaries_user_id ON document_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_jurisdiction ON knowledge_base(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_hash ON embeddings(content_hash);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- ─── Full-Text Search (FTS5) ────────────────────────────────────────────────────

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_base_fts USING fts5(
    title, content, category, jurisdiction,
    content='knowledge_base',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS knowledge_base_ai AFTER INSERT ON knowledge_base BEGIN
    INSERT INTO knowledge_base_fts(rowid, title, content, category, jurisdiction)
    VALUES (new.id, new.title, new.content, new.category, new.jurisdiction);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_base_ad AFTER DELETE ON knowledge_base BEGIN
    INSERT INTO knowledge_base_fts(knowledge_base_fts, rowid, title, content, category, jurisdiction)
    VALUES ('delete', old.id, old.title, old.content, old.category, old.jurisdiction);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_base_au AFTER UPDATE ON knowledge_base BEGIN
    INSERT INTO knowledge_base_fts(knowledge_base_fts, rowid, title, content, category, jurisdiction)
    VALUES ('delete', old.id, old.title, old.content, old.category, old.jurisdiction);
    INSERT INTO knowledge_base_fts(rowid, title, content, category, jurisdiction)
    VALUES (new.id, new.title, new.content, new.category, new.jurisdiction);
END;
