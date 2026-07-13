"""
Risk Detection Agent.
Scores clauses and contracts for legal risk on a 0-10 scale.
"""

import json
from typing import Dict, List, Any
from agents.orchestrator import OrchestratorAgent


class RiskAgent:
    """
    Risk assessment agent that:
    - Scores individual clauses (0-10)
    - Checks enforceability by jurisdiction
    - Categorizes risk levels (🟢🟡🔴)
    - Provides overall document risk score
    """

    SYSTEM_PROMPT = """You are a legal risk assessment specialist. Evaluate legal clauses and contracts for potential risks.

Risk Scoring Guide:
- 0-3 (🟢 Low Risk): Standard industry terms, fair and balanced, commonly accepted
- 4-6 (🟡 Medium Risk): Slightly one-sided, may need negotiation, potential issues
- 7-10 (🔴 High Risk): Highly unfavorable, potentially unenforceable, unusual terms, legal traps

Consider:
- Enforceability in the specified jurisdiction
- Industry standards and common practices
- Potential financial/legal exposure
- Clarity and specificity of language
- Balance of obligations between parties"""

    RISK_PROMPT = """Assess the risk of the following contract clauses under {jurisdiction} jurisdiction.

CONTRACT TYPE: {contract_type}

CLAUSES TO EVALUATE:
{clauses_text}

For each clause, provide a JSON array:
[
    {{
        "clause_index": 0,
        "risk_score": <0-10>,
        "risk_level": "low|medium|high",
        "risk_factors": ["List of specific risk factors"],
        "enforceability": "enforceable|partially_enforceable|likely_unenforceable",
        "explanation": "Why this risk level was assigned",
        "mitigation": "How to reduce the risk"
    }}
]

Also provide an overall assessment:
{{
    "clauses": [<array above>],
    "overall_risk_score": <0.0-10.0>,
    "overall_assessment": "Brief overall risk summary",
    "top_concerns": ["Most important concern 1", "Concern 2"]
}}"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()

    def assess_risk(self, clauses: List[Dict], contract_type: str = "",
                    jurisdiction: str = "General / International") -> Dict[str, Any]:
        """Assess risk for a list of clauses."""
        if not clauses:
            return {"overall_risk_score": 0, "clauses": [], "top_concerns": []}

        # Format clauses for the prompt
        clauses_text = ""
        for i, clause in enumerate(clauses):
            text = clause.get("clause_text", clause.get("text", ""))
            ctype = clause.get("clause_type", clause.get("type", "Unknown"))
            clauses_text += f"\nClause {i+1} ({ctype}):\n{text}\n"

        prompt = self.RISK_PROMPT.format(
            jurisdiction=jurisdiction,
            contract_type=contract_type,
            clauses_text=clauses_text
        )

        response = self.orchestrator.generate_response(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2000
        )

        if not response:
            return self._fallback_assessment(clauses)

        return self._parse_response(response, clauses)

    def calculate_overall_score(self, clause_scores: List[float]) -> float:
        """Calculate weighted overall risk score."""
        if not clause_scores:
            return 0.0
        # Weight high-risk clauses more heavily
        weighted = []
        for score in clause_scores:
            weight = 1.5 if score >= 7 else (1.2 if score >= 4 else 1.0)
            weighted.append(score * weight)
        return round(sum(weighted) / sum(
            1.5 if s >= 7 else (1.2 if s >= 4 else 1.0) for s in clause_scores
        ), 1)

    def get_risk_emoji(self, score: float) -> str:
        """Get risk emoji for a score."""
        if score <= 3:
            return "🟢"
        elif score <= 6:
            return "🟡"
        return "🔴"

    def get_risk_color(self, score: float) -> str:
        """Get risk color for UI display."""
        if score <= 3:
            return "#22C55E"  # green
        elif score <= 6:
            return "#EAB308"  # yellow
        return "#EF4444"  # red

    def _parse_response(self, response: str,
                        original_clauses: List[Dict]) -> Dict[str, Any]:
        """Parse LLM risk assessment response."""
        try:
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())
            result.setdefault("overall_risk_score", 5.0)
            result.setdefault("clauses", [])
            result.setdefault("top_concerns", [])
            return result

        except json.JSONDecodeError:
            return self._fallback_assessment(original_clauses)

    def _fallback_assessment(self, clauses: List[Dict]) -> Dict[str, Any]:
        """Simple keyword-based risk assessment fallback."""
        high_risk_keywords = [
            "indemnify", "unlimited liability", "sole discretion",
            "without notice", "irrevocable", "waive", "forfeit",
            "non-compete", "perpetual", "exclusive"
        ]
        medium_risk_keywords = [
            "terminate", "penalty", "damages", "limitation",
            "confidential", "restricted", "binding"
        ]

        assessed_clauses = []
        scores = []

        for i, clause in enumerate(clauses):
            text = clause.get("clause_text", clause.get("text", "")).lower()
            score = 2.0  # base low risk

            for kw in high_risk_keywords:
                if kw in text:
                    score += 2.0
            for kw in medium_risk_keywords:
                if kw in text:
                    score += 1.0

            score = min(score, 10.0)
            scores.append(score)

            assessed_clauses.append({
                "clause_index": i,
                "risk_score": score,
                "risk_level": "high" if score > 6 else ("medium" if score > 3 else "low"),
                "explanation": "Keyword-based risk assessment (AI unavailable)",
            })

        return {
            "overall_risk_score": self.calculate_overall_score(scores),
            "clauses": assessed_clauses,
            "top_concerns": ["AI-based assessment unavailable; using keyword analysis"],
        }
