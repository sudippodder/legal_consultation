"""
📑 Document Summary Page.
Upload legal documents for AI-powered plain-language summarization.
"""

import streamlit as st
import json
from datetime import datetime

from config import SUPPORTED_FILE_TYPES
from database.db_manager import DatabaseManager
from agents.summary_agent import SummaryAgent
from utils.document_parser import parse_document, get_file_type
from utils.text_processor import clean_text, count_words
from utils.report_generator import generate_summary_pdf

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
        📑 Document Summary
    </h1>
    <p style="color: #94A3B8; font-size: 1rem;">
        Convert lengthy legal documents into plain-language summaries with key points
    </p>
</div>
""", unsafe_allow_html=True)

db = DatabaseManager()
summary_agent = SummaryAgent()

# ─── Upload Section ──────────────────────────────────────────────────────────────

st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload Legal Document",
        type=SUPPORTED_FILE_TYPES,
        help="Supported formats: PDF, DOCX, TXT",
        key="summary_upload"
    )

with col2:
    summary_type = st.selectbox(
        "Summary Length",
        options=["brief", "standard", "detailed"],
        index=1,
        format_func=lambda x: {
            "brief": "📝 Brief (~100 words)",
            "standard": "📄 Standard (~300 words)",
            "detailed": "📚 Detailed (~500+ words)"
        }.get(x, x),
        key="summary_type"
    )

# ─── Processing ─────────────────────────────────────────────────────────────────

if uploaded_file:
    # Parse document
    with st.spinner("📖 Parsing document..."):
        content = parse_document(uploaded_file)
        content = clean_text(content)

    if not content or content.startswith("Error"):
        st.error(f"❌ Failed to parse document: {content}")
        st.stop()

    # Document preview
    with st.expander("📋 Document Preview", expanded=False):
        st.text_area("Extracted Text", content[:3000] + ("..." if len(content) > 3000 else ""),
                      height=200, disabled=True)
        st.caption(f"📊 {count_words(content)} words | {len(content)} characters")

    # Summarize button
    if st.button("📑 Generate Summary", use_container_width=True, type="primary"):
        # Save document
        file_type = get_file_type(uploaded_file.name)
        doc_id = db.save_document(
            user_id=st.session_state.user_id,
            filename=uploaded_file.name,
            file_type=file_type,
            file_size=uploaded_file.size,
            content_text=content,
            document_type="summary_request"
        )

        # Progress
        progress = st.progress(0, text="Starting summarization...")

        progress.progress(20, text="📖 Reading and chunking document...")
        progress.progress(50, text="🤖 Generating summary with AI...")

        # Summarize
        result = summary_agent.summarize(content, summary_type)

        progress.progress(80, text="📝 Formatting results...")

        # Save to DB
        db.save_document_summary(
            document_id=doc_id,
            user_id=st.session_state.user_id,
            summary_type=summary_type,
            executive_summary=result.get("executive_summary", ""),
            key_points_json=json.dumps(result.get("key_points", [])),
            action_items_json=json.dumps(result.get("action_items", [])),
            parties_json=json.dumps(result.get("parties_involved", [])),
            dates_json=json.dumps(result.get("important_dates", [])),
            obligations_json=json.dumps(result.get("obligations", [])),
            confidence_score=result.get("confidence_score", 0)
        )

        db.update_document_status(doc_id, "analyzed")
        db.log_action(st.session_state.user_id, "summarize",
                       f"Summarized: {uploaded_file.name}")

        progress.progress(100, text="✅ Summary complete!")

        st.session_state.last_summary = result
        st.session_state.last_summary_filename = uploaded_file.name

# ─── Results Display ────────────────────────────────────────────────────────────

if "last_summary" in st.session_state:
    result = st.session_state.last_summary
    filename = st.session_state.get("last_summary_filename", "")

    st.markdown("---")
    st.markdown("## 📊 Summary Results")

    # Executive Summary
    st.markdown("### 📝 Executive Summary")
    st.markdown(result.get("executive_summary", "No summary available."))

    # Confidence
    confidence = result.get("confidence_score", 0)
    if confidence >= 0.85:
        st.success(f"✅ Confidence: {confidence:.0%}")
    elif confidence >= 0.5:
        st.warning(f"⚠️ Confidence: {confidence:.0%}")
    else:
        st.error(f"🔴 Confidence: {confidence:.0%}")

    # Key Points
    key_points = result.get("key_points", [])
    if key_points:
        st.markdown("### 🔑 Key Points")
        for i, point in enumerate(key_points, 1):
            st.markdown(f"**{i}.** {point}")

    # Layout: parties and dates side by side
    col1, col2 = st.columns(2)

    with col1:
        # Parties Involved
        parties = result.get("parties_involved", [])
        if parties:
            st.markdown("### 👥 Parties Involved")
            for party in parties:
                if isinstance(party, dict):
                    st.markdown(f"• **{party.get('name', 'Unknown')}** — {party.get('role', '')}")
                else:
                    st.markdown(f"• {party}")

    with col2:
        # Important Dates
        dates = result.get("important_dates", [])
        if dates:
            st.markdown("### 📅 Important Dates")
            for d in dates:
                if isinstance(d, dict):
                    st.markdown(f"• **{d.get('date', 'N/A')}** — {d.get('description', '')}")
                else:
                    st.markdown(f"• {d}")

    # Obligations
    obligations = result.get("obligations", [])
    if obligations:
        st.markdown("### ⚖️ Obligations")
        for ob in obligations:
            if isinstance(ob, dict):
                st.markdown(
                    f"• **{ob.get('party', 'Unknown')}**: {ob.get('obligation', '')} "
                    f"{'(Due: ' + ob.get('deadline', '') + ')' if ob.get('deadline') else ''}"
                )
            else:
                st.markdown(f"• {ob}")

    # Action Items
    action_items = result.get("action_items", [])
    if action_items:
        st.markdown("### ✅ Action Items")
        for item in action_items:
            if isinstance(item, dict):
                priority = item.get("priority", "medium").upper()
                emoji = "🔴" if priority == "HIGH" else ("🟡" if priority == "MEDIUM" else "🟢")
                st.markdown(
                    f"{emoji} **[{priority}]** {item.get('action', '')} "
                    f"{'— Due: ' + item.get('deadline', '') if item.get('deadline') else ''}"
                )
            else:
                st.markdown(f"• {item}")

    # Export
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        pdf_data = generate_summary_pdf(result, filename=filename)
        st.download_button(
            "📥 Download PDF Report",
            data=pdf_data,
            file_name=f"document_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col2:
        st.download_button(
            "📥 Download JSON Data",
            data=json.dumps(result, indent=2, default=str),
            file_name=f"document_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

# ─── Past Summaries ────────────────────────────────────────────────────────────

st.markdown("---")
with st.expander("📜 Past Summaries", expanded=False):
    past = db.get_user_summaries(st.session_state.user_id, limit=10)
    if past:
        for s in past:
            st.markdown(
                f"📑 **{s.get('filename', 'Unknown')}** — "
                f"Type: {s.get('summary_type', 'standard')} | "
                f"Confidence: {s.get('confidence_score', 0):.0%} | "
                f"{s.get('created_at', '')}"
            )
    else:
        st.caption("No past summaries yet. Upload a document to get started!")
