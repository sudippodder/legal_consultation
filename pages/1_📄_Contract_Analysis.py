"""
📄 Contract Analysis Page.
Upload legal contracts for AI-powered risk analysis and clause breakdown.
"""

import streamlit as st
import json
from datetime import datetime

from config import CONTRACT_TYPES, JURISDICTIONS, SUPPORTED_FILE_TYPES
from database.db_manager import DatabaseManager
from agents.contract_agent import ContractAnalysisAgent
from agents.risk_agent import RiskAgent
from agents.research_agent import ResearchAgent
from agents.validation_agent import ValidationAgent
from utils.document_parser import parse_document, get_file_type
from utils.text_processor import clean_text, detect_contract_type, count_words
from utils.report_generator import generate_contract_analysis_pdf

# ─── Auth Guard ──────────────────────────────────────────────────────────────────

if not st.session_state.get("authenticated"):
    st.warning("🔒 Please log in to access this page.")
    st.stop()

# ─── Page Config ─────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align: center; padding: 1.5rem 0;">
    <h1 style="background: linear-gradient(135deg, #D4AF37, #F5E6A3);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.2rem; margin-bottom: 0.3rem;">
        📄 Contract Analysis
    </h1>
    <p style="color: #94A3B8; font-size: 1rem;">
        Upload your contract for AI-powered risk identification and clause-by-clause breakdown
    </p>
</div>
""", unsafe_allow_html=True)

db = DatabaseManager()
contract_agent = ContractAnalysisAgent()
risk_agent = RiskAgent()
research_agent = ResearchAgent()
validation_agent = ValidationAgent()

# ─── Upload Section ──────────────────────────────────────────────────────────────

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload Contract Document",
        type=SUPPORTED_FILE_TYPES,
        help="Supported formats: PDF, DOCX, TXT (max 25MB)",
        key="contract_upload"
    )

with col2:
    contract_type = st.selectbox(
        "Contract Type",
        options=["Auto-Detect"] + CONTRACT_TYPES,
        key="contract_type"
    )

    jurisdiction = st.selectbox(
        "Jurisdiction",
        options=JURISDICTIONS,
        index=JURISDICTIONS.index(
            st.session_state.get("default_jurisdiction", "General / International")
        ) if st.session_state.get("default_jurisdiction") in JURISDICTIONS else len(JURISDICTIONS) - 1,
        key="contract_jurisdiction"
    )

# ─── Analysis ────────────────────────────────────────────────────────────────────

if uploaded_file:
    # Parse document
    with st.spinner("📖 Parsing document..."):
        content = parse_document(uploaded_file)
        content = clean_text(content)

    if not content or content.startswith("Error"):
        st.error(f"❌ Failed to parse document: {content}")
        st.stop()

    # Auto-detect contract type
    if contract_type == "Auto-Detect":
        detected = detect_contract_type(content)
        st.info(f"🔍 Auto-detected contract type: **{detected}**")
        contract_type = detected

    # Show document preview
    with st.expander("📋 Document Preview", expanded=False):
        st.text_area("Extracted Text", content[:3000] + ("..." if len(content) > 3000 else ""),
                      height=200, disabled=True)
        st.caption(f"📊 {count_words(content)} words | {len(content)} characters")

    # Analyze button
    if st.button("🔍 Analyze Contract", use_container_width=True, type="primary"):
        # Save document to DB
        file_type = get_file_type(uploaded_file.name)
        doc_id = db.save_document(
            user_id=st.session_state.user_id,
            filename=uploaded_file.name,
            file_type=file_type,
            file_size=uploaded_file.size,
            content_text=content,
            document_type=contract_type
        )
        db.update_document_status(doc_id, "processing")

        # Progress tracking
        progress = st.progress(0, text="Starting analysis...")

        # Step 1: Research (fast — uses FTS5 keyword search; skips if unavailable)
        progress.progress(15, text="🔍 Searching legal knowledge base...")
        rag_context = ""
        try:
            rag_context = research_agent.get_context_for_analysis(
                content, contract_type, jurisdiction
            )
        except Exception:
            rag_context = ""  # Analysis works fine without RAG context

        # Step 2: Contract Analysis
        progress.progress(40, text="📄 Analyzing contract clauses...")
        analysis_result = contract_agent.analyze(
            contract_text=content,
            contract_type=contract_type,
            jurisdiction=jurisdiction,
            rag_context=rag_context
        )

        # Step 3: Validation
        progress.progress(80, text="✅ Validating results...")
        validation = validation_agent.validate(
            {"confidence_score": analysis_result.get("confidence_score", 0),
             "summary": analysis_result.get("summary", "")},
            source_context=rag_context
        )

        # Save results
        clauses = analysis_result.get("clauses", [])
        high_risk = sum(1 for c in clauses if c.get("risk_level") == "high")
        med_risk = sum(1 for c in clauses if c.get("risk_level") == "medium")
        low_risk = sum(1 for c in clauses if c.get("risk_level") == "low")

        analysis_id = db.save_contract_analysis(
            document_id=doc_id,
            user_id=st.session_state.user_id,
            contract_type=contract_type,
            jurisdiction=jurisdiction,
            overall_risk_score=analysis_result.get("overall_risk_score", 0),
            total_clauses=len(clauses),
            high_risk=high_risk,
            medium_risk=med_risk,
            low_risk=low_risk,
            clauses_json=json.dumps(clauses),
            recommendations_json=json.dumps(analysis_result.get("recommendations", [])),
            summary=analysis_result.get("summary", ""),
            confidence_score=analysis_result.get("confidence_score", 0)
        )

        db.update_document_status(doc_id, "analyzed")
        db.log_action(st.session_state.user_id, "analyze",
                       f"Analyzed contract: {uploaded_file.name}")

        progress.progress(100, text="✅ Analysis complete!")
        st.session_state.last_analysis = analysis_result
        st.session_state.last_analysis_meta = {
            "filename": uploaded_file.name,
            "contract_type": contract_type,
            "jurisdiction": jurisdiction,
            "validation": validation,
            "analysis_id": analysis_id,
            "doc_id": doc_id,
        }

# ─── Results Display ────────────────────────────────────────────────────────────

if "last_analysis" in st.session_state:
    analysis = st.session_state.last_analysis
    meta = st.session_state.get("last_analysis_meta", {})

    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    # Risk Score Header
    risk_score = analysis.get("overall_risk_score", 0)
    risk_color = risk_agent.get_risk_color(risk_score)
    risk_emoji = risk_agent.get_risk_emoji(risk_score)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Risk Score", f"{risk_score}/10")
    with col2:
        clauses = analysis.get("clauses", [])
        st.metric("Total Clauses", len(clauses))
    with col3:
        high = sum(1 for c in clauses if c.get("risk_level") == "high")
        st.metric("🔴 High Risk", high)
    with col4:
        confidence = analysis.get("confidence_score", 0)
        st.metric("Confidence", f"{confidence:.0%}")

    # Risk level indicator
    if risk_score <= 3:
        st.success(f"{risk_emoji} **LOW RISK** — This contract appears to have standard, fair terms.")
    elif risk_score <= 6:
        st.warning(f"{risk_emoji} **MEDIUM RISK** — Some clauses need attention and may require negotiation.")
    else:
        st.error(f"{risk_emoji} **HIGH RISK** — This contract contains potentially dangerous or unfair terms.")

    # Validation status
    validation = meta.get("validation", {})
    if validation:
        st.caption(validation.get("recommendation", ""))

    # Summary
    st.markdown("### 📝 Executive Summary")
    st.markdown(analysis.get("summary", "No summary available."))

    # Clause Analysis
    if clauses:
        st.markdown("### 📋 Clause-by-Clause Analysis")

        for i, clause in enumerate(clauses):
            c_score = clause.get("risk_score", 0)
            c_level = clause.get("risk_level", "low")
            c_emoji = risk_agent.get_risk_emoji(c_score)
            c_color = risk_agent.get_risk_color(c_score)
            c_type = clause.get("clause_type", "Unknown")

            with st.expander(f"{c_emoji} Clause {i+1}: {c_type} — Risk: {c_score}/10"):
                st.markdown(f"**Risk Level:** :{c_level.replace('high', 'red').replace('medium', 'orange').replace('low', 'green')}[{c_level.upper()}]")
                if clause.get("clause_text"):
                    st.markdown(f"**Excerpt:** {clause['clause_text'][:300]}")
                if clause.get("explanation"):
                    st.markdown(f"**Analysis:** {clause['explanation']}")
                if clause.get("suggestion"):
                    st.info(f"💡 **Suggestion:** {clause['suggestion']}")

    # Missing clauses
    missing = analysis.get("missing_clauses", [])
    if missing:
        st.markdown("### ⚠️ Missing Important Clauses")
        for m in missing:
            if isinstance(m, dict):
                with st.expander(f"❌ Missing: {m.get('clause_type', 'Unknown')}"):
                    st.markdown(f"**Importance:** {m.get('importance', 'N/A')}")
                    st.markdown(f"**Why needed:** {m.get('explanation', '')}")
                    if m.get("suggestion"):
                        st.info(f"💡 **Suggested text:** {m['suggestion']}")

    # Recommendations
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        st.markdown("### 💡 Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")

    # Export
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        pdf_data = generate_contract_analysis_pdf(
            {**analysis, "contract_type": meta.get("contract_type", ""),
             "jurisdiction": meta.get("jurisdiction", "")},
            filename=meta.get("filename", "")
        )
        st.download_button(
            "📥 Download PDF Report",
            data=pdf_data,
            file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col2:
        st.download_button(
            "📥 Download JSON Data",
            data=json.dumps(analysis, indent=2),
            file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

# ─── Past Analyses ──────────────────────────────────────────────────────────────

st.markdown("---")
with st.expander("📜 Past Analyses", expanded=False):
    past = db.get_user_analyses(st.session_state.user_id, limit=10)
    if past:
        for a in past:
            r_emoji = risk_agent.get_risk_emoji(a.get("overall_risk_score", 0))
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"{r_emoji} **{a.get('filename', 'Unknown')}** — "
                    f"Risk: {a.get('overall_risk_score', 0)}/10 | "
                    f"Type: {a.get('contract_type', 'N/A')} | "
                    f"{a.get('created_at', '')}"
                )
            with col2:
                if st.button("View Details", key=f"view_past_{a.get('id', 0)}"):
                    st.session_state.last_analysis = {
                        "overall_risk_score": a.get("overall_risk_score", 0),
                        "clauses": json.loads(a.get("clauses_json", "[]")),
                        "recommendations": json.loads(a.get("recommendations_json", "[]")),
                        "summary": a.get("summary", ""),
                        "confidence_score": a.get("confidence_score", 0),
                    }
                    st.session_state.last_analysis_meta = {
                        "filename": a.get("filename", "Unknown"),
                        "contract_type": a.get("contract_type", "N/A"),
                        "jurisdiction": a.get("jurisdiction", ""),
                        "validation": {},
                        "analysis_id": a.get("id", 0),
                        "doc_id": a.get("document_id", 0),
                    }
                    st.rerun()
    else:
        st.caption("No past analyses yet. Upload a contract to get started!")
