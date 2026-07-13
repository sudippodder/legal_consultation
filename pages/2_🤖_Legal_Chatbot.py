"""
🤖 Legal Chatbot Page.
Interactive AI-powered legal Q&A with conversation memory and citations.
"""

import streamlit as st
import json
from datetime import datetime

from config import JURISDICTIONS
from database.db_manager import DatabaseManager
from agents.chatbot_agent import ChatbotAgent

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
        🤖 Legal Chatbot
    </h1>
    <p style="color: #94A3B8; font-size: 1rem;">
        Ask legal questions and get AI-powered answers with citations
    </p>
</div>
""", unsafe_allow_html=True)

db = DatabaseManager()
chatbot = ChatbotAgent()

# ─── Initialize Session State ────────────────────────────────────────────────────

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

# ─── Sidebar: Chat Sessions ─────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 💬 Conversations")

    jurisdiction = st.selectbox(
        "🌍 Jurisdiction",
        options=JURISDICTIONS,
        index=JURISDICTIONS.index(
            st.session_state.get("default_jurisdiction", "General / International")
        ) if st.session_state.get("default_jurisdiction") in JURISDICTIONS else len(JURISDICTIONS) - 1,
        key="chat_jurisdiction"
    )

    if st.button("➕ New Conversation", use_container_width=True):
        session_id = db.create_chat_session(
            user_id=st.session_state.user_id,
            jurisdiction=jurisdiction
        )
        st.session_state.current_session_id = session_id
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("---")

    # List existing sessions
    sessions = db.get_user_chat_sessions(st.session_state.user_id, limit=15)
    for session in sessions:
        s_id = session["id"]
        s_title = session.get("title", "New Conversation")
        s_count = session.get("message_count", 0)

        is_active = s_id == st.session_state.current_session_id
        btn_label = f"{'▸ ' if is_active else ''}{s_title[:35]}{'...' if len(s_title) > 35 else ''} ({s_count})"

        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(btn_label, key=f"session_{s_id}", use_container_width=True):
                st.session_state.current_session_id = s_id
                # Load messages
                messages = db.get_chat_messages(s_id)
                st.session_state.chat_messages = [
                    {"role": m["role"], "content": m["content"],
                     "sources": json.loads(m.get("sources_json", "[]")),
                     "confidence": m.get("confidence_score", 0)}
                    for m in messages
                ]
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_session_{s_id}"):
                db.delete_chat_session(s_id)
                if st.session_state.current_session_id == s_id:
                    st.session_state.current_session_id = None
                    st.session_state.chat_messages = []
                st.rerun()

# ─── Chat Interface ──────────────────────────────────────────────────────────────

# Disclaimer banner
st.markdown("""
<div style="background: rgba(212, 175, 55, 0.08); border: 1px solid rgba(212, 175, 55, 0.2);
     border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem; text-align: center;">
    <span style="color: #D4AF37; font-size: 0.85rem;">
        ⚖️ This is AI-generated legal information, NOT legal advice.
        Consult a qualified lawyer for your specific situation.
    </span>
</div>
""", unsafe_allow_html=True)

# Display chat messages
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_messages:
        # Welcome message
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #64748B;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
            <div style="font-size: 1.1rem; margin-bottom: 0.5rem;">
                Welcome to the Legal Chatbot
            </div>
            <div style="font-size: 0.9rem;">
                Ask any legal question. I can help with contract law, tenant rights,
                employment law, intellectual property, and more.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggested questions
        st.markdown("#### 💡 Try asking:")
        suggestions = [
            "Can my landlord enter my house without notice?",
            "What makes a contract legally binding?",
            "What are my rights if I'm terminated without cause?",
            "What is the difference between mediation and arbitration?",
        ]
        for suggestion in suggestions:
            if st.button(f"→ {suggestion}", key=f"suggest_{hash(suggestion)}"):
                st.session_state.pending_question = suggestion
                st.rerun()
    else:
        for i, msg in enumerate(st.session_state.chat_messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                # Show sources for assistant messages
                if msg["role"] == "assistant" and msg.get("sources"):
                    with st.expander("📚 Sources & Citations", expanded=False):
                        for src in msg["sources"]:
                            if isinstance(src, dict):
                                st.markdown(
                                    f"• **{src.get('title', 'Source')}** "
                                    f"({src.get('category', '')}) — "
                                    f"Relevance: {src.get('relevance', 0)}%"
                                )
                            else:
                                st.markdown(f"• {src}")

                # Show confidence for assistant messages
                if msg["role"] == "assistant" and msg.get("confidence", 0) > 0:
                    conf = msg["confidence"]
                    if conf >= 0.85:
                        st.caption(f"✅ Confidence: {conf:.0%}")
                    elif conf >= 0.5:
                        st.caption(f"⚠️ Confidence: {conf:.0%} — Consider professional advice")
                    else:
                        st.caption(f"🔴 Confidence: {conf:.0%} — Strongly recommend consulting a lawyer")

# ─── Chat Input ──────────────────────────────────────────────────────────────────

# Handle suggested question
pending = st.session_state.pop("pending_question", None)

user_input = st.chat_input("Ask a legal question...", key="chat_input")

# Use pending question if no direct input
if pending and not user_input:
    user_input = pending

if user_input:
    # Create session if none exists
    if not st.session_state.current_session_id:
        session_id = db.create_chat_session(
            user_id=st.session_state.user_id,
            title=chatbot.generate_session_title(user_input),
            jurisdiction=jurisdiction
        )
        st.session_state.current_session_id = session_id
    else:
        session_id = st.session_state.current_session_id

    # Add user message
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "sources": [],
        "confidence": 0
    })

    # Save to DB
    db.save_chat_message(session_id, "user", user_input)

    # Display user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)

    # Generate response
    with chat_container:
        with st.chat_message("assistant"):
            with st.spinner("🤔 Researching your question..."):
                # Build chat history for context
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_messages[-10:]
                ]

                result = chatbot.get_response(
                    user_message=user_input,
                    chat_history=history[:-1],  # Exclude current message
                    jurisdiction=jurisdiction
                )

                answer = result.get("answer", "I'm sorry, I couldn't process your question.")
                sources = result.get("sources", [])
                confidence = result.get("confidence_score", 0)
                follow_ups = result.get("follow_up_questions", [])

            st.markdown(answer)

            if sources:
                with st.expander("📚 Sources & Citations", expanded=False):
                    for src in sources:
                        st.markdown(
                            f"• **{src.get('title', 'Source')}** "
                            f"({src.get('category', '')}) — "
                            f"Relevance: {src.get('relevance', 0)}%"
                        )

            if confidence > 0:
                if confidence >= 0.85:
                    st.caption(f"✅ Confidence: {confidence:.0%}")
                elif confidence >= 0.5:
                    st.caption(f"⚠️ Confidence: {confidence:.0%} — Consider professional advice")
                else:
                    st.caption(f"🔴 Confidence: {confidence:.0%} — Strongly recommend consulting a lawyer")

    # Save assistant message
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "confidence": confidence
    })
    db.save_chat_message(
        session_id, "assistant", answer,
        sources_json=json.dumps(sources),
        confidence_score=confidence
    )

    # Update session title if first message
    if len(st.session_state.chat_messages) <= 2:
        db.update_chat_session_title(
            session_id,
            chatbot.generate_session_title(user_input)
        )

    # Show follow-up questions
    if follow_ups:
        st.markdown("#### 💡 Follow-up questions:")
        for fq in follow_ups:
            if st.button(f"→ {fq}", key=f"followup_{hash(fq)}"):
                st.session_state.pending_question = fq
                st.rerun()

    # Log action
    db.log_action(st.session_state.user_id, "chat",
                   f"Asked: {user_input[:100]}")
