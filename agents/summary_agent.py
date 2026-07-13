"""
Document Summarization Agent.
Converts lengthy legal documents into plain-language summaries
with key points, action items, and deadline extraction.
"""

import json
from typing import Dict, List, Any
from agents.orchestrator import OrchestratorAgent
from rag.chunker import DocumentChunker


class SummaryAgent:
    """
    Summarization agent that:
    1. Chunks the document
    2. Summarizes each chunk
    3. Extracts key points, dates, parties, obligations
    4. Generates executive summary
    """

    SYSTEM_PROMPT = """You are a legal document summarization expert. Your task is to create clear, accurate, plain-language summaries of legal documents.

You must:
1. Convert complex legal language into simple, understandable English
2. Preserve all critical legal meaning and nuances
3. Identify and highlight key information
4. Never add information not present in the document
5. Maintain factual accuracy"""

    SUMMARY_PROMPT = """Summarize the following legal document. Provide your response as a JSON object.

DOCUMENT TEXT:
{document_text}

SUMMARY TYPE: {summary_type}
- "brief": 3-5 bullet points, ~100 words
- "standard": Comprehensive summary, ~300 words
- "detailed": Thorough analysis, ~500+ words

Respond with this EXACT JSON structure:
{{
    "executive_summary": "A clear, plain-English summary of the entire document",
    "key_points": [
        "Key point 1",
        "Key point 2",
        "Key point 3"
    ],
    "parties_involved": [
        {{
            "name": "Party name or role",
            "role": "Their role in the document (e.g., Employer, Landlord, Disclosing Party)"
        }}
    ],
    "important_dates": [
        {{
            "date": "The date or time period",
            "description": "What this date relates to"
        }}
    ],
    "obligations": [
        {{
            "party": "Who has this obligation",
            "obligation": "What they must do",
            "deadline": "When (if specified)"
        }}
    ],
    "action_items": [
        {{
            "action": "What needs to be done",
            "priority": "high|medium|low",
            "deadline": "When (if applicable)"
        }}
    ],
    "confidence_score": <0.0-1.0>
}}"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.chunker = DocumentChunker()

    def summarize(self, document_text: str,
                  summary_type: str = "standard") -> Dict[str, Any]:
        """
        Generate a comprehensive document summary.
        """
        if not document_text or not document_text.strip():
            return self._empty_result("No document text provided.")

        # For very long documents, chunk and summarize incrementally
        if len(document_text) > 10000:
            return self._summarize_long_document(document_text, summary_type)

        # Direct summarization for shorter documents
        return self._summarize_text(document_text, summary_type)

    def _summarize_text(self, text: str, summary_type: str) -> Dict[str, Any]:
        """Summarize a single text block."""
        # Truncate if still too long for single prompt
        max_chars = 12000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n[... document truncated ...]"

        prompt = self.SUMMARY_PROMPT.format(
            document_text=text,
            summary_type=summary_type
        )

        response = self.orchestrator.generate_response(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2000
        )

        if not response:
            return self._empty_result("Failed to generate summary.")

        return self._parse_response(response)

    def _summarize_long_document(self, text: str,
                                  summary_type: str) -> Dict[str, Any]:
        """Handle long documents by chunking and merging summaries."""
        chunks = self.chunker.chunk_text(text)

        if not chunks:
            return self._empty_result("Could not chunk the document.")

        # Summarize each chunk briefly
        chunk_summaries = []
        all_key_points = []
        all_parties = []
        all_dates = []
        all_obligations = []
        all_actions = []

        for i, chunk in enumerate(chunks[:10]):  # Limit to 10 chunks
            chunk_result = self._summarize_text(chunk, "brief")

            if chunk_result.get("executive_summary"):
                chunk_summaries.append(chunk_result["executive_summary"])
            all_key_points.extend(chunk_result.get("key_points", []))
            all_parties.extend(chunk_result.get("parties_involved", []))
            all_dates.extend(chunk_result.get("important_dates", []))
            all_obligations.extend(chunk_result.get("obligations", []))
            all_actions.extend(chunk_result.get("action_items", []))

        # Merge chunk summaries into a final executive summary
        merged_text = "\n\n".join(chunk_summaries)
        if merged_text:
            final_prompt = f"""Combine these section summaries into one coherent executive summary ({summary_type} length):

{merged_text}

Provide ONLY the merged summary text, no JSON."""

            executive_summary = self.orchestrator.generate_response(
                prompt=final_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=800
            ) or merged_text
        else:
            executive_summary = "Unable to generate summary."

        # Deduplicate parties
        seen_parties = set()
        unique_parties = []
        for p in all_parties:
            name = p.get("name", "") if isinstance(p, dict) else str(p)
            if name not in seen_parties:
                seen_parties.add(name)
                unique_parties.append(p)

        return {
            "executive_summary": executive_summary,
            "key_points": all_key_points[:10],  # Top 10
            "parties_involved": unique_parties,
            "important_dates": all_dates,
            "obligations": all_obligations,
            "action_items": all_actions,
            "confidence_score": 0.75
        }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured result."""
        try:
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())
            result.setdefault("executive_summary", "")
            result.setdefault("key_points", [])
            result.setdefault("parties_involved", [])
            result.setdefault("important_dates", [])
            result.setdefault("obligations", [])
            result.setdefault("action_items", [])
            result.setdefault("confidence_score", 0.7)
            return result

        except json.JSONDecodeError:
            return {
                "executive_summary": response[:1000] if response else "",
                "key_points": [],
                "parties_involved": [],
                "important_dates": [],
                "obligations": [],
                "action_items": [],
                "confidence_score": 0.5
            }

    def _empty_result(self, msg: str) -> Dict[str, Any]:
        return {
            "executive_summary": msg,
            "key_points": [],
            "parties_involved": [],
            "important_dates": [],
            "obligations": [],
            "action_items": [],
            "confidence_score": 0.0,
            "error": msg
        }
