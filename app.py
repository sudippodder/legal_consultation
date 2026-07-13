"""
AI Legal Consultation Platform — Main Application Entry Point.
Streamlit multi-page app with authentication, navigation, and premium UI.
"""

import streamlit as st
import bcrypt
import os
import json
from datetime import datetime

from config import APP_NAME, APP_ICON, APP_VERSION, JURISDICTIONS
from database.db_manager import DatabaseManager

# ─── Page Configuration ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Global Styles ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hide Streamlit Defaults ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Animated Gradient Background ── */
    .stApp {
        background: linear-gradient(135deg, #0A0F1C 0%, #111827 50%, #0F172A 100%);
    }

    /* ── Hero Section ── */
    .hero-container {
        text-align: center;
        padding: 3rem 1rem 2rem;
        animation: fadeInUp 0.8s ease-out;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #D4AF37, #F5E6A3, #D4AF37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 1.2rem;
        color: #94A3B8;
        font-weight: 300;
        margin-bottom: 2rem;
    }

    /* ── Feature Cards ── */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        padding: 1rem 0;
    }

    .feature-card {
        background: linear-gradient(135deg, rgba(20, 27, 45, 0.9), rgba(30, 41, 59, 0.7));
        border: 1px solid rgba(212, 175, 55, 0.15);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.05), transparent);
        transition: left 0.5s;
    }

    .feature-card:hover::before {
        left: 100%;
    }

    .feature-card:hover {
        border-color: rgba(212, 175, 55, 0.4);
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(212, 175, 55, 0.15);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }

    .feature-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #E8E8E8;
        margin-bottom: 0.5rem;
    }

    .feature-desc {
        font-size: 0.9rem;
        color: #94A3B8;
        line-height: 1.6;
    }

    /* ── Stats Bar ── */
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 3rem;
        padding: 2rem 0;
        margin: 2rem 0;
        border-top: 1px solid rgba(212, 175, 55, 0.1);
        border-bottom: 1px solid rgba(212, 175, 55, 0.1);
    }

    .stat-item {
        text-align: center;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: #D4AF37;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ── Auth Forms ── */
    .auth-container {
        max-width: 450px;
        margin: 2rem auto;
        padding: 2.5rem;
        background: linear-gradient(135deg, rgba(20, 27, 45, 0.95), rgba(30, 41, 59, 0.8));
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .auth-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #D4AF37;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* ── Sidebar Styling ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1321 0%, #141B2D 100%);
        border-right: 1px solid rgba(212, 175, 55, 0.1);
    }

    /* ── Button Overrides ── */
    .stButton > button {
        background: linear-gradient(135deg, #D4AF37, #B8941F);
        color: #0A0F1C;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #F5E6A3, #D4AF37);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
        transform: translateY(-1px);
    }

    /* ── Input Fields ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(212, 175, 55, 0.2) !important;
        border-radius: 10px !important;
        color: #E8E8E8 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        color: #D4AF37;
    }

    /* ── Disclaimer ── */
    .disclaimer {
        text-align: center;
        padding: 1.5rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(212, 175, 55, 0.1);
        color: #64748B;
        font-size: 0.8rem;
        font-style: italic;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .feature-grid { grid-template-columns: 1fr; }
        .hero-title { font-size: 2rem; }
        .stats-bar { flex-direction: column; gap: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# ─── Initialize Database ────────────────────────────────────────────────────────

db = DatabaseManager()


# ─── Authentication Functions ────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def login_user(username: str, password: str) -> bool:
    """Attempt to log in a user."""
    user = db.get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        st.session_state.authenticated = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.user_role = user["role"]
        st.session_state.user_full_name = user.get("full_name", username)
        st.session_state.default_jurisdiction = user.get("default_jurisdiction", "General / International")
        db.update_last_login(user["id"])
        db.log_action(user["id"], "login", f"User {username} logged in")
        return True
    return False


def register_user(username: str, email: str, password: str, full_name: str) -> tuple:
    """Register a new user. Returns (success, message)."""
    # Validation
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email:
        return False, "Please enter a valid email address."

    # Check if user exists
    if db.get_user_by_username(username):
        return False, "Username already exists."
    if db.get_user_by_email(email):
        return False, "Email already registered."

    # Create user
    try:
        pw_hash = hash_password(password)
        user_id = db.create_user(username, email, pw_hash, full_name)
        db.log_action(user_id, "register", f"New user registered: {username}")
        return True, "Account created successfully! Please log in."
    except Exception as e:
        return False, f"Registration failed: {str(e)}"


def logout_user():
    """Log out the current user."""
    for key in ["authenticated", "user_id", "username", "user_role",
                "user_full_name", "default_jurisdiction"]:
        st.session_state.pop(key, None)


# ─── Seed Knowledge Base ────────────────────────────────────────────────────────

def seed_knowledge_base():
    """Load initial knowledge base data from JSON files."""
    if st.session_state.get("kb_seeded"):
        return

    kb_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")

    # Load glossary
    glossary_path = os.path.join(kb_dir, "legal_glossary.json")
    if os.path.exists(glossary_path):
        with open(glossary_path, "r", encoding="utf-8") as f:
            glossary = json.load(f)
        for term_data in glossary.get("terms", []):
            try:
                db.add_knowledge_entry(
                    title=term_data["term"],
                    content=term_data["definition"],
                    category="glossary",
                    source="Legal Glossary"
                )
            except Exception:
                pass  # Skip duplicates

    # Load jurisdiction rules
    rules_path = os.path.join(kb_dir, "jurisdiction_rules.json")
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = json.load(f)
        for jur in rules.get("jurisdictions", []):
            # Add key laws as knowledge entries
            for law in jur.get("key_contract_laws", []):
                try:
                    db.add_knowledge_entry(
                        title=law,
                        content=f"{law} — applicable in {jur['name']}. Legal system: {jur['legal_system']}.",
                        category="statute",
                        jurisdiction=jur["name"],
                        source="Jurisdiction Rules"
                    )
                except Exception:
                    pass

            # Add non-compete info
            nc = jur.get("non_compete_enforceability", "")
            if nc:
                try:
                    db.add_knowledge_entry(
                        title=f"Non-Compete Enforceability in {jur['name']}",
                        content=nc,
                        category="rule",
                        jurisdiction=jur["name"],
                        source="Jurisdiction Rules"
                    )
                except Exception:
                    pass

    st.session_state.kb_seeded = True


# ─── Auth Page ───────────────────────────────────────────────────────────────────

def show_auth_page():
    """Show login/registration page."""
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">⚖️ AI Legal Consultation</div>
        <div class="hero-subtitle">
            Intelligent contract analysis, legal guidance, and document summarization
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Auth tabs
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        with st.form("login_form"):
            st.markdown("#### Welcome Back")
            username = st.text_input("Username", key="login_username",
                                     placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password",
                                     placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if username and password:
                    if login_user(username, password):
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password.")
                else:
                    st.warning("Please fill in all fields.")

    with tab2:
        with st.form("register_form"):
            st.markdown("#### Create Account")
            reg_fullname = st.text_input("Full Name", key="reg_fullname",
                                         placeholder="Your full name")
            reg_username = st.text_input("Username", key="reg_username",
                                         placeholder="Choose a username (min 3 chars)")
            reg_email = st.text_input("Email", key="reg_email",
                                      placeholder="your@email.com")
            reg_password = st.text_input("Password", type="password", key="reg_password",
                                         placeholder="Min 6 characters")
            reg_password2 = st.text_input("Confirm Password", type="password",
                                          key="reg_password2",
                                          placeholder="Repeat your password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if reg_password != reg_password2:
                    st.error("❌ Passwords do not match.")
                elif all([reg_fullname, reg_username, reg_email, reg_password]):
                    success, message = register_user(
                        reg_username, reg_email, reg_password, reg_fullname
                    )
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("Please fill in all fields.")

    # Footer
    st.markdown("""
    <div class="disclaimer">
        ⚖️ This platform provides AI-generated legal information, NOT legal advice.<br>
        Always consult a qualified lawyer for your specific situation.
    </div>
    """, unsafe_allow_html=True)


# ─── Main Dashboard (Logged In) ─────────────────────────────────────────────────

def show_main_page():
    """Show the main landing page for authenticated users."""
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2rem;">⚖️</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #D4AF37; margin-top: 0.5rem;">
                {APP_NAME}
            </div>
            <div style="font-size: 0.75rem; color: #64748B;">v{APP_VERSION}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown(f"""
        <div style="padding: 0.5rem; background: rgba(212, 175, 55, 0.05);
             border-radius: 10px; border: 1px solid rgba(212, 175, 55, 0.1); margin-bottom: 1rem;">
            <div style="font-size: 0.85rem; color: #94A3B8;">Logged in as</div>
            <div style="font-size: 1rem; font-weight: 600; color: #E8E8E8;">
                👤 {st.session_state.get('user_full_name', st.session_state.get('username', ''))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

    # Hero section
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">⚖️ AI Legal Consultation</div>
        <div class="hero-subtitle">
            Welcome back, {st.session_state.get('user_full_name', 'User')}!
            Choose a service below to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <span class="feature-icon">📄</span>
            <div class="feature-title">Contract Analysis</div>
            <div class="feature-desc">
                Upload contracts for automated risk identification,
                clause-by-clause breakdown, and detailed recommendations.
            </div>
        </div>
        <div class="feature-card">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">Legal Chatbot</div>
            <div class="feature-desc">
                Ask legal questions and get AI-powered answers with
                jurisdiction-specific guidance and legal citations.
            </div>
        </div>
        <div class="feature-card">
            <span class="feature-icon">📑</span>
            <div class="feature-title">Document Summary</div>
            <div class="feature-desc">
                Convert lengthy legal documents into plain-language summaries
                with key points, action items, and deadlines.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats bar
    try:
        stats = db.get_user_stats(st.session_state.user_id)
    except Exception:
        stats = {"total_documents": 0, "total_analyses": 0, "total_chats": 0, "total_summaries": 0}

    st.markdown(f"""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-value">{stats.get('total_documents', 0)}</div>
            <div class="stat-label">Documents</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{stats.get('total_analyses', 0)}</div>
            <div class="stat-label">Analyses</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{stats.get('total_chats', 0)}</div>
            <div class="stat-label">Conversations</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{stats.get('total_summaries', 0)}</div>
            <div class="stat-label">Summaries</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick start instructions
    st.markdown("---")
    st.markdown("### 🚀 Quick Start")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📄 **Contract Analysis**\n\nGo to the sidebar → `📄 Contract Analysis` to upload and analyze contracts.")
    with col2:
        st.info("🤖 **Legal Chatbot**\n\nGo to the sidebar → `🤖 Legal Chatbot` to ask legal questions.")
    with col3:
        st.info("📑 **Document Summary**\n\nGo to the sidebar → `📑 Document Summary` to summarize legal documents.")

    # API key notice
    if not st.session_state.get("openai_api_key"):
        st.warning(
            "⚠️ **OpenAI API Key not configured.** "
            "Go to **⚙️ Settings** in the sidebar to add your API key for AI features to work."
        )

    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        ⚖️ This platform provides AI-generated legal information, NOT legal advice.
        Always consult a qualified lawyer for your specific situation.<br>
        Powered by OpenAI • Built with Streamlit • Data stored locally in SQLite
    </div>
    """, unsafe_allow_html=True)


# ─── Main App Flow ───────────────────────────────────────────────────────────────

def main():
    """Main application entry point."""
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Seed knowledge base
    seed_knowledge_base()

    # Route based on auth state
    if st.session_state.authenticated:
        show_main_page()
    else:
        show_auth_page()


if __name__ == "__main__":
    main()
