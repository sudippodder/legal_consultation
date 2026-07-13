"""
Orchestrator Agent — Master Controller.
Routes user requests to the appropriate specialist agents,
collects results, and assembles final reports.
"""

import json
from typing import Dict, Any, Optional
from openai import OpenAI

from config import get_openai_api_key, get_selected_model


class OrchestratorAgent:
    """
    Master controller that:
    1. Receives user request
    2. Classifies intent
    3. Routes to specialist agents
    4. Aggregates results
    5. Delivers final output
    """

    INTENT_PROMPT = """You are an AI legal platform orchestrator. Classify the user's intent into exactly one of these categories:

1. "contract_analysis" — User wants to analyze a legal contract/agreement for risks and clauses
2. "legal_question" — User has a legal question or needs legal information/guidance
3. "document_summary" — User wants to summarize a legal document
4. "general_chat" — General conversation, greetings, or non-legal questions

Respond with ONLY a JSON object:
{
    "intent": "<one of the categories above>",
    "confidence": <0.0 to 1.0>,
    "sub_tasks": ["<list of sub-tasks needed>"],
    "requires_document": <true/false>
}

User Input: """

    def __init__(self):
        self.client = None

    def _get_client(self) -> Optional[OpenAI]:
        """Get or create OpenAI client."""
        api_key = get_openai_api_key()
        if not api_key:
            return None
        if self.client is None:
            self.client = OpenAI(api_key=api_key)
        return self.client

    def classify_intent(self, user_input: str, has_document: bool = False) -> Dict[str, Any]:
        """Classify user intent and plan sub-tasks."""
        client = self._get_client()
        if not client:
            return {
                "intent": "general_chat",
                "confidence": 0.0,
                "sub_tasks": [],
                "requires_document": False,
                "error": "No API key configured"
            }

        # If document is uploaded, adjust the classification
        context = user_input
        if has_document:
            context = f"[User has uploaded a document] {user_input}"

        try:
            response = client.chat.completions.create(
                model=get_selected_model(),
                messages=[
                    {"role": "system", "content": self.INTENT_PROMPT},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=200
            )
            result_text = response.choices[0].message.content.strip()
            # Parse JSON from response
            result_text = result_text.strip("`").strip()
            if result_text.startswith("json"):
                result_text = result_text[4:].strip()
            return json.loads(result_text)
        except Exception as e:
            # Fallback classification based on keywords
            return self._fallback_classify(user_input, has_document)

    def _fallback_classify(self, user_input: str, has_document: bool) -> Dict[str, Any]:
        """Keyword-based fallback classification."""
        lower = user_input.lower()

        if has_document:
            if any(w in lower for w in ["analyze", "contract", "review", "risk", "clause"]):
                return {
                    "intent": "contract_analysis",
                    "confidence": 0.7,
                    "sub_tasks": ["parse_document", "analyze_clauses", "assess_risk"],
                    "requires_document": True
                }
            else:
                return {
                    "intent": "document_summary",
                    "confidence": 0.7,
                    "sub_tasks": ["parse_document", "summarize", "extract_key_points"],
                    "requires_document": True
                }

        if any(w in lower for w in ["summarize", "summary", "key points", "brief"]):
            return {
                "intent": "document_summary",
                "confidence": 0.6,
                "sub_tasks": ["summarize"],
                "requires_document": True
            }

        if any(w in lower for w in ["law", "legal", "right", "court", "case",
                                     "sue", "contract", "jurisdiction",
                                     "tenant", "landlord", "employee", "divorce"]):
            return {
                "intent": "legal_question",
                "confidence": 0.7,
                "sub_tasks": ["research", "answer", "cite"],
                "requires_document": False
            }

        return {
            "intent": "general_chat",
            "confidence": 0.5,
            "sub_tasks": [],
            "requires_document": False
        }

    def generate_response(self, prompt: str, system_prompt: str = "",
                          temperature: float = 0.3,
                          max_tokens: int = 2000) -> Optional[str]:
        """Generate a response from the LLM."""
        client = self._get_client()
        if not client:
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=get_selected_model(),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_chat_response(self, messages: list,
                               system_prompt: str = "",
                               temperature: float = 0.3,
                               max_tokens: int = 2000) -> Optional[str]:
        """Generate a chat response with full conversation history."""
        client = self._get_client()
        if not client:
            return None

        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)

        try:
            response = client.chat.completions.create(
                model=get_selected_model(),
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
