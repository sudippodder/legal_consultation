"""
📊 Dashboard Page.
Analytics and activity overview for the user.
"""

import streamlit as st
import json
from datetime import datetime

from database.db_manager import DatabaseManager
from agents.risk_agent import RiskAgent

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
        📊 Dashboard
    </h1>
    <p style="color: #94A3B8; font-size: 1rem;">
        Your analytics and activity overview
    </p>
</div>
""", unsafe_allow_html=True)

db = DatabaseManager()
risk_agent = RiskAgent()

# ─── Stats Overview ─────────────────────────────────────────────────────────────

stats = db.get_user_stats(st.session_state.user_id)

st.markdown("---")
st.markdown("### 📈 Overview")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📄 Documents", stats.get("total_documents", 0))
with col2:
    st.metric("🔍 Analyses", stats.get("total_analyses", 0))
with col3:
    st.metric("💬 Conversations", stats.get("total_chats", 0))
with col4:
    st.metric("📑 Summaries", stats.get("total_summaries", 0))

col1, col2 = st.columns(2)
with col1:
    st.metric("💬 Total Messages", stats.get("total_messages", 0))
with col2:
    st.metric("⚠️ Avg Risk Score", f"{stats.get('avg_risk_score', 0)}/10")

# ─── Risk Distribution Chart ────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### ⚖️ Risk Distribution")

risk_dist = stats.get("risk_distribution", {"high": 0, "medium": 0, "low": 0})

if any(v > 0 for v in risk_dist.values()):
    try:
        import plotly.graph_objects as go

        fig = go.Figure(data=[go.Pie(
            labels=["🟢 Low Risk", "🟡 Medium Risk", "🔴 High Risk"],
            values=[risk_dist.get("low", 0), risk_dist.get("medium", 0), risk_dist.get("high", 0)],
            hole=0.5,
            marker=dict(colors=["#22C55E", "#EAB308", "#EF4444"]),
            textinfo="label+value",
            textfont=dict(size=14, color="white"),
        )])
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E8E8E8"),
            showlegend=False,
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Fallback if plotly not installed
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🟢 Low Risk", risk_dist.get("low", 0))
        with col2:
            st.metric("🟡 Medium Risk", risk_dist.get("medium", 0))
        with col3:
            st.metric("🔴 High Risk", risk_dist.get("high", 0))
else:
    st.info("📊 No analysis data yet. Analyze some contracts to see risk distribution!")

# ─── Recent Analyses ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 📋 Recent Contract Analyses")

analyses = db.get_user_analyses(st.session_state.user_id, limit=5)
if analyses:
    for a in analyses:
        risk_score = a.get("overall_risk_score", 0)
        emoji = risk_agent.get_risk_emoji(risk_score)
        color = risk_agent.get_risk_color(risk_score)

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{a.get('filename', 'Unknown')}**")
                st.caption(f"{a.get('contract_type', 'N/A')} | {a.get('jurisdiction', 'N/A')}")
            with col2:
                st.markdown(f"{emoji} **{risk_score}/10**")
            with col3:
                st.markdown(f"📋 {a.get('total_clauses', 0)} clauses")
            with col4:
                st.caption(a.get("created_at", ""))
            st.markdown("---")
else:
    st.info("📄 No analyses yet. Go to Contract Analysis to get started!")

# ─── Recent Summaries ──────────────────────────────────────────────────────────

st.markdown("### 📑 Recent Document Summaries")

summaries = db.get_user_summaries(st.session_state.user_id, limit=5)
if summaries:
    for s in summaries:
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{s.get('filename', 'Unknown')}**")
            with col2:
                st.markdown(f"📊 {s.get('confidence_score', 0):.0%}")
            with col3:
                st.caption(s.get("created_at", ""))
else:
    st.info("📑 No summaries yet. Go to Document Summary to get started!")

# ─── Recent Activity ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 🕐 Recent Activity")

activity = db.get_recent_activity(st.session_state.user_id, limit=10)
if activity:
    for log in activity:
        action = log.get("action", "")
        emoji_map = {
            "login": "🔑",
            "register": "📝",
            "upload": "📤",
            "analyze": "🔍",
            "chat": "💬",
            "summarize": "📑",
            "export": "📥",
            "settings": "⚙️",
        }
        emoji = emoji_map.get(action, "📌")
        st.caption(f"{emoji} **{action.title()}** — {log.get('details', '')[:80]} | {log.get('created_at', '')}")
else:
    st.caption("No activity recorded yet.")
