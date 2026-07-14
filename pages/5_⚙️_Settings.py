"""
⚙️ Settings Page.
Manage API keys, preferences, and knowledge base.
"""

import streamlit as st
import json
import os
from datetime import datetime

from config import AVAILABLE_MODELS, DEFAULT_MODEL, JURISDICTIONS, APP_VERSION
from database.db_manager import DatabaseManager

# ─── Auth Guard ──────────────────────────────────────────────────────────────────

if not st.session_state.get("authenticated"):
    st.warning("🔒 Please log in to access this page.")
    st.stop()

# ─── Page Header ─────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <h1 style="background: linear-gradient(135deg, #D4AF37, #F5E6A3);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.2rem; margin-bottom: 0.3rem;">
        ⚙️ Settings
    </h1>
    <p style="color: #94A3B8; font-size: 1rem;">
        Configure your API keys, preferences, and manage the knowledge base
    </p>
</div>
""", unsafe_allow_html=True)

db = DatabaseManager()

# ─── API Configuration ──────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 🔑 API Configuration")

with st.form("api_settings"):
    model = st.selectbox(
        "AI Model",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(
            st.session_state.get("selected_model", DEFAULT_MODEL)
        ) if st.session_state.get("selected_model") in AVAILABLE_MODELS else 1,
        help="Select the OpenAI model to use. GPT-4o-mini is recommended for balance of quality and cost."
    )

    if st.form_submit_button("💾 Save API Settings", use_container_width=True):
        st.session_state.selected_model = model
        db.log_action(st.session_state.user_id, "settings", "Updated API settings")
        st.success("✅ API settings saved!")

# ─── User Preferences ──────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 👤 User Preferences")

user = db.get_user_by_id(st.session_state.user_id)

with st.form("user_preferences"):
    full_name = st.text_input(
        "Full Name",
        value=user.get("full_name", "") if user else "",
    )

    email = st.text_input(
        "Email",
        value=user.get("email", "") if user else "",
    )

    default_jur = st.selectbox(
        "Default Jurisdiction",
        options=JURISDICTIONS,
        index=JURISDICTIONS.index(
            user.get("default_jurisdiction", "General / International")
        ) if user and user.get("default_jurisdiction") in JURISDICTIONS else len(JURISDICTIONS) - 1,
    )

    if st.form_submit_button("💾 Save Preferences", use_container_width=True):
        db.update_user_settings(
            st.session_state.user_id,
            full_name=full_name,
            email=email,
            default_jurisdiction=default_jur
        )
        st.session_state.user_full_name = full_name
        st.session_state.default_jurisdiction = default_jur
        db.log_action(st.session_state.user_id, "settings", "Updated user preferences")
        st.success("✅ Preferences saved!")

# ─── Knowledge Base Management ──────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 📚 Knowledge Base")

kb_count = db.get_knowledge_entry_count()
st.info(f"📊 Knowledge base contains **{kb_count}** entries.")

with st.expander("➕ Add Knowledge Entry"):
    with st.form("add_knowledge"):
        kb_title = st.text_input("Title", placeholder="e.g., Indian Contract Act, 1872 - Section 27")
        kb_content = st.text_area("Content", placeholder="Enter the legal content...", height=150)
        col1, col2 = st.columns(2)
        with col1:
            kb_category = st.selectbox(
                "Category",
                options=["statute", "case_law", "template", "glossary", "rule"]
            )
        with col2:
            kb_jurisdiction = st.selectbox(
                "Jurisdiction",
                options=JURISDICTIONS,
                key="kb_jurisdiction"
            )
        kb_source = st.text_input("Source", placeholder="e.g., Bar Council of India")

        if st.form_submit_button("Add Entry", use_container_width=True):
            if kb_title and kb_content:
                db.add_knowledge_entry(
                    title=kb_title,
                    content=kb_content,
                    category=kb_category,
                    jurisdiction=kb_jurisdiction,
                    source=kb_source
                )
                db.log_action(st.session_state.user_id, "settings",
                               f"Added knowledge entry: {kb_title}")
                st.success(f"✅ Added: {kb_title}")
                st.rerun()
            else:
                st.warning("Please provide both title and content.")

# ─── Search Knowledge Base ──────────────────────────────────────────────────────

with st.expander("🔍 Search Knowledge Base"):
    search_query = st.text_input("Search", placeholder="Search legal knowledge...",
                                  key="kb_search")
    if search_query:
        results = db.search_knowledge_base(search_query, limit=10)
        if results:
            for r in results:
                st.markdown(
                    f"• **{r.get('title', 'Untitled')}** "
                    f"({r.get('category', '')}, {r.get('jurisdiction', '')}) — "
                    f"{r.get('content', '')[:200]}..."
                )
        else:
            st.caption("No results found.")

# ─── Data Management ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 🗄️ Data Management")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Export All Data (JSON)", use_container_width=True):
        data = {
            "user": db.get_user_by_id(st.session_state.user_id),
            "documents": db.get_user_documents(st.session_state.user_id),
            "analyses": db.get_user_analyses(st.session_state.user_id),
            "summaries": db.get_user_summaries(st.session_state.user_id),
            "chat_sessions": db.get_user_chat_sessions(st.session_state.user_id),
            "exported_at": datetime.now().isoformat()
        }
        # Remove sensitive data
        if data["user"]:
            data["user"].pop("password_hash", None)
        json_data = json.dumps(data, indent=2, default=str)
        st.download_button(
            "📥 Download Export",
            data=json_data,
            file_name=f"legal_platform_export_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

with col2:
    st.caption(f"📍 Database: SQLite (local)")
    st.caption(f"📦 App Version: {APP_VERSION}")
    st.caption(f"🤖 Model: {st.session_state.get('selected_model', DEFAULT_MODEL)}")

# ─── About ──────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### ℹ️ About")

st.markdown(f"""
**AI Legal Consultation Platform** v{APP_VERSION}

An AI-powered platform for legal contract analysis, consultation, and document summarization.

**Features:**
- 📄 Automated contract risk analysis
- 🤖 AI legal chatbot with RAG knowledge base
- 📑 Document summarization with key point extraction
- 📊 Analytics dashboard
- 🔐 Multi-user authentication

**Tech Stack:** Python, Streamlit, SQLite, OpenAI, sentence-transformers

⚖️ *This platform provides AI-generated legal information, NOT legal advice.*
""")
