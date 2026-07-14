"""
Configuration module for AI Legal Consultation Platform.
Manages application settings, API keys, and model configuration.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ─── Application Settings ───────────────────────────────────────────────────────

APP_NAME = "AI Legal Consultation Platform"
APP_VERSION = "1.0.0"
APP_ICON = "⚖️"
APP_DESCRIPTION = "AI-powered legal analysis, consultation, and document summarization"

# ─── Database Settings ──────────────────────────────────────────────────────────

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "legal_platform.db")
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "data")

# ─── LLM Settings ───────────────────────────────────────────────────────────────

DEFAULT_MODEL = "gpt-4o-mini"
AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

# ─── Embedding Settings ─────────────────────────────────────────────────────────

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ─── RAG Settings ────────────────────────────────────────────────────────────────

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.3

# ─── Risk Scoring ───────────────────────────────────────────────────────────────

RISK_THRESHOLDS = {
    "low": (0, 3),
    "medium": (4, 6),
    "high": (7, 10),
}

CONFIDENCE_THRESHOLD = 0.85  # 85% minimum for auto-approval

# ─── Supported Jurisdictions ────────────────────────────────────────────────────

JURISDICTIONS = [
    "India",
    "United States",
    "United Kingdom",
    "European Union",
    "Canada",
    "Australia",
    "General / International",
]

# ─── Contract Types ─────────────────────────────────────────────────────────────

CONTRACT_TYPES = [
    "Non-Disclosure Agreement (NDA)",
    "Employment Contract",
    "Lease Agreement",
    "Service Agreement",
    "Partnership Agreement",
    "Sales Contract",
    "Freelance/Consulting Agreement",
    "Other",
]

# ─── Supported File Types ───────────────────────────────────────────────────────

SUPPORTED_FILE_TYPES = ["pdf", "docx", "txt"]
MAX_FILE_SIZE_MB = 25

# ─── Session Config ─────────────────────────────────────────────────────────────

MAX_CHAT_HISTORY = 50


def get_openai_api_key():
    """Retrieve the OpenAI API key from environment, or secrets."""
    # 1. Check environment variable
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key

    # 2. Check Streamlit secrets
    try:
        return st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        return None


def get_selected_model():
    """Get the currently selected LLM model."""
    return st.session_state.get("selected_model", DEFAULT_MODEL)
