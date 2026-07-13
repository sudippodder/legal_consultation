"""
Contract Analysis Agent.
Parses contracts, identifies clauses, classifies risk, and generates detailed reports.
"""

import json
from typing import Dict, List, Any, Optional
from agents.orchestrator import OrchestratorAgent


class ContractAnalysisAgent:
    """
    Specialist agent for contract analysis:
    1. Parse contract structure
    2. Identify and classify clauses
    3. Compare against standard templates
    4. Score risk for each clause
    5. Generate recommendations
    """

    SYSTEM_PROMPT = """You are an expert legal contract analyst. Your task is to analyze legal contracts/agreements and provide a comprehensive clause-by-clause breakdown.

For each contract you analyze, you must:
1. Identify all major clauses and provisions
2. Classify each clause type (payment, termination, liability, confidentiality, dispute resolution, indemnification, intellectual property, non-compete, force majeure, etc.)
3. Assess the risk level of each clause on a scale of 0-10:
   - 0-3: 🟢 Low Risk (standard, fair terms)
   - 4-6: 🟡 Medium Risk (needs attention, potentially unfavorable)
   - 7-10: 🔴 High Risk (dangerous, highly unfavorable, or potentially unenforceable)
4. Explain why each clause is risky or safe in plain English
5. Suggest improvements for risky clauses
6. Identify any MISSING important clauses that should be present

Consider the jurisdiction and contract type when assessing risk.

IMPORTANT: Always provide your analysis as a valid JSON response."""

    ANALYSIS_PROMPT = """Analyze the following {contract_type} contract under {jurisdiction} jurisdiction.

CONTRACT TEXT:
{contract_text}

{rag_context}

Provide your analysis as a JSON object with this EXACT structure:
{{
    "summary": "A 2-3 sentence plain-English summary of the entire contract",
    "overall_risk_score": <0.0-10.0>,
    "clauses": [
        {{
            "clause_number": 1,
            "clause_type": "Type of clause",
            "clause_text": "Key excerpt from the clause (first 200 chars)",
            "risk_score": <0.0-10.0>,
            "risk_level": "low|medium|high",
            "explanation": "Why this clause is risky/safe",
            "suggestion": "How to improve this clause (if risky)"
        }}
    ],
    "missing_clauses": [
        {{
            "clause_type": "Type of missing clause",
            "importance": "high|medium",
            "explanation": "Why this clause should be included",
            "suggestion": "Recommended language for this clause"
        }}
    ],
    "recommendations": [
        "Overall recommendation 1",
        "Overall recommendation 2"
    ],
    "confidence_score": <0.0-1.0>
}}"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()

    def analyze(self, contract_text: str, contract_type: str = "General Contract",
                jurisdiction: str = "General / International",
                rag_context: str = "") -> Dict[str, Any]:
        """
        Perform full contract analysis.

        Returns a structured analysis result dict.
        """
        # Build context section
        context_section = ""
        if rag_context:
            context_section = f"\nRELEVANT LEGAL CONTEXT:\n{rag_context}\n"

        # Truncate very long contracts to fit token limits
        max_chars = 12000
        if len(contract_text) > max_chars:
            contract_text = contract_text[:max_chars] + "\n\n[... document truncated for analysis ...]"

        prompt = self.ANALYSIS_PROMPT.format(
            contract_type=contract_type,
            jurisdiction=jurisdiction,
            contract_text=contract_text,
            rag_context=context_section
        )

        response = self.orchestrator.generate_response(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=3000
        )

        if not response:
            return self._empty_result("Failed to get AI response")

        return self._parse_response(response)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured result."""
        try:
            # Extract JSON from response
            text = response.strip()
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())

            # Validate and normalize
            result.setdefault("summary", "")
            result.setdefault("overall_risk_score", 5.0)
            result.setdefault("clauses", [])
            result.setdefault("missing_clauses", [])
            result.setdefault("recommendations", [])
            result.setdefault("confidence_score", 0.8)

            # Normalize clause risk levels
            for clause in result["clauses"]:
                score = clause.get("risk_score", 5)
                if score <= 3:
                    clause["risk_level"] = "low"
                elif score <= 6:
                    clause["risk_level"] = "medium"
                else:
                    clause["risk_level"] = "high"

            return result

        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract information from text
            return self._parse_text_response(response)

    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Fallback parser for non-JSON responses."""
        return {
            "summary": response[:500] if response else "Analysis could not be parsed.",
            "overall_risk_score": 5.0,
            "clauses": [],
            "missing_clauses": [],
            "recommendations": ["Please review the raw analysis output above."],
            "confidence_score": 0.5,
            "raw_response": response
        }

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return an empty result with error message."""
        return {
            "summary": error_msg,
            "overall_risk_score": 0.0,
            "clauses": [],
            "missing_clauses": [],
            "recommendations": [],
            "confidence_score": 0.0,
            "error": error_msg
        }
