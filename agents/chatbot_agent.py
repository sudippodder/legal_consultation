"""
Legal Chatbot Agent.
Conversational AI for legal Q&A with RAG-powered answers,
jurisdiction awareness, and citation support.
"""

import json
from typing import Dict, List, Any, Optional
from agents.orchestrator import OrchestratorAgent
from rag.retriever import HybridRetriever


class ChatbotAgent:
    """
    Legal chatbot with:
    - Conversation memory
    - RAG-powered legal knowledge
    - Jurisdiction-specific guidance
    - Source citation
    - Confidence scoring
    """

    SYSTEM_PROMPT = """You are an AI Legal Assistant providing legal information and guidance. You are knowledgeable about laws across multiple jurisdictions, with particular depth in Indian law.

IMPORTANT RULES:
1. Always provide accurate, well-researched legal information
2. Cite specific laws, sections, or case precedents when possible
3. Consider the user's jurisdiction when answering
4. Use plain, understandable English — avoid unnecessary legal jargon
5. If you're not confident about an answer, say so clearly
6. ALWAYS include a disclaimer that this is AI-generated legal information, NOT legal advice
7. Suggest consulting a qualified lawyer for specific situations
8. If context from the knowledge base is provided, prioritize that information

Format your response with:
- A clear, direct answer
- Relevant legal references (if applicable)
- Practical implications
- A brief disclaimer at the end

When providing a confidence level, consider:
- 0.9-1.0: Well-established law, clear precedent
- 0.7-0.9: Generally clear but may have exceptions
- 0.5-0.7: Complex area, varies by circumstances
- Below 0.5: Uncertain, strongly recommend professional advice"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.retriever = HybridRetriever()

    def get_response(self, user_message: str,
                     chat_history: List[Dict[str, str]] = None,
                     jurisdiction: str = "General / International") -> Dict[str, Any]:
        """
        Generate a response to a legal question.

        Returns dict with: answer, sources, confidence_score, follow_up_questions
        """
        # Build RAG context (fast FTS5 search; falls back gracefully)
        rag_context = ""
        try:
            rag_context = self.retriever.build_context(
                query=user_message,
                jurisdiction=jurisdiction
            )
        except Exception:
            rag_context = ""

        # Build conversation messages
        messages = []

        # Add conversation history (last 10 messages for context)
        if chat_history:
            for msg in chat_history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # Build the current user message with RAG context
        enhanced_message = user_message
        if rag_context:
            enhanced_message = f"""User Question: {user_message}

Jurisdiction: {jurisdiction}

Relevant Legal Context from Knowledge Base:
{rag_context}

Please answer the user's question using the above context where relevant. Include citations."""
        else:
            enhanced_message = f"""User Question: {user_message}

Jurisdiction: {jurisdiction}

Please answer this legal question. Include relevant legal references and citations."""

        messages.append({"role": "user", "content": enhanced_message})

        # Add system prompt for jurisdiction context
        system = self.SYSTEM_PROMPT + f"\n\nThe user's selected jurisdiction is: {jurisdiction}"

        # Generate response
        response = self.orchestrator.generate_chat_response(
            messages=messages,
            system_prompt=system,
            temperature=0.3,
            max_tokens=1500
        )

        if not response:
            return {
                "answer": "I apologize, but I'm unable to process your question right now. Please check your API key in Settings.",
                "sources": [],
                "confidence_score": 0.0,
                "follow_up_questions": []
            }

        # Extract sources from RAG results
        sources = []
        if rag_context:
            rag_results = self.retriever.retrieve(user_message, jurisdiction=jurisdiction)
            for r in rag_results[:3]:
                meta = r.get("metadata", {})
                sources.append({
                    "title": meta.get("title", "Knowledge Base"),
                    "category": meta.get("category", ""),
                    "relevance": round(r.get("score", 0) * 100, 1)
                })

        # Estimate confidence based on RAG results and response quality
        confidence = self._estimate_confidence(response, sources)

        return {
            "answer": response,
            "sources": sources,
            "confidence_score": confidence,
            "follow_up_questions": self._generate_follow_ups(user_message, jurisdiction)
        }

    def _estimate_confidence(self, response: str, sources: list) -> float:
        """Estimate confidence based on response quality indicators."""
        confidence = 0.6  # Base confidence

        # Boost if we have RAG sources
        if sources:
            confidence += min(len(sources) * 0.05, 0.15)

        # Boost if response contains legal references
        legal_indicators = ["section", "act", "article", "clause",
                           "regulation", "statute", "court", "judgment",
                           "precedent", "ruling", "§"]
        for indicator in legal_indicators:
            if indicator.lower() in response.lower():
                confidence += 0.02

        # Cap at 0.95
        return min(round(confidence, 2), 0.95)

    def _generate_follow_ups(self, question: str, jurisdiction: str) -> List[str]:
        """Generate suggested follow-up questions."""
        # Simple rule-based follow-ups
        follow_ups = []
        lower = question.lower()

        if "landlord" in lower or "tenant" in lower or "rent" in lower:
            follow_ups = [
                "What are my rights as a tenant regarding security deposits?",
                "Can a landlord increase rent without notice?",
                "What is the eviction process?"
            ]
        elif "employee" in lower or "employer" in lower or "work" in lower:
            follow_ups = [
                "What are the legal working hours?",
                "What are my rights regarding overtime pay?",
                "What constitutes wrongful termination?"
            ]
        elif "divorce" in lower or "marriage" in lower:
            follow_ups = [
                "What are the grounds for divorce?",
                "How is property divided in divorce?",
                "What about child custody rights?"
            ]
        elif "contract" in lower or "agreement" in lower:
            follow_ups = [
                "What makes a contract legally binding?",
                "Can I cancel a signed contract?",
                "What if the other party breaches the contract?"
            ]
        else:
            follow_ups = [
                f"What are my specific rights in {jurisdiction}?",
                "Should I consult a lawyer for my situation?",
                "What documents do I need to prepare?"
            ]

        return follow_ups[:3]

    def generate_session_title(self, first_message: str) -> str:
        """Generate a concise title for a chat session."""
        # Truncate and clean
        title = first_message[:60].strip()
        if len(first_message) > 60:
            title += "..."
        return title
