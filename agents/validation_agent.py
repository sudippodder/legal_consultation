"""
Validation Agent.
Checks AI outputs for confidence, hallucination, and quality.
"""

from typing import Dict, Any
from config import CONFIDENCE_THRESHOLD


class ValidationAgent:
    """
    Validates AI-generated outputs:
    - Confidence threshold checking (>85% auto-approve)
    - Basic hallucination detection
    - Output quality scoring
    - Flag for human review
    """

    def validate(self, output: Dict[str, Any],
                 source_context: str = "") -> Dict[str, Any]:
        """
        Validate an AI output.

        Returns:
            dict with: is_valid, confidence, issues, recommendation
        """
        issues = []
        confidence = output.get("confidence_score", 0.0)

        # Check confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            issues.append(f"Confidence ({confidence:.0%}) below threshold ({CONFIDENCE_THRESHOLD:.0%})")

        # Check for empty or very short outputs
        summary = output.get("summary", output.get("executive_summary",
                                                      output.get("answer", "")))
        if not summary or len(summary) < 20:
            issues.append("Output is too short or empty")
            confidence = min(confidence, 0.3)

        # Check for hallucination indicators
        hallucination_phrases = [
            "I don't have enough information",
            "I cannot determine",
            "this is purely speculative",
            "I'm making this up",
            "I'm not sure about this",
        ]
        if summary:
            for phrase in hallucination_phrases:
                if phrase.lower() in summary.lower():
                    issues.append(f"Potential uncertainty detected: '{phrase}'")
                    confidence = min(confidence, 0.6)

        # Check for disclaimer presence (required for legal content)
        has_disclaimer = False
        if summary:
            disclaimer_keywords = ["not legal advice", "consult a lawyer",
                                   "professional advice", "qualified attorney",
                                   "legal professional"]
            for kw in disclaimer_keywords:
                if kw.lower() in summary.lower():
                    has_disclaimer = True
                    break

        if not has_disclaimer and len(summary) > 100:
            issues.append("Missing legal disclaimer")

        # Determine recommendation
        is_valid = len(issues) == 0 and confidence >= CONFIDENCE_THRESHOLD
        if is_valid:
            recommendation = "✅ Approved — Output meets quality standards"
        elif confidence >= 0.5:
            recommendation = "⚠️ Review Recommended — Some concerns detected"
        else:
            recommendation = "🔴 Human Review Required — Low confidence or quality issues"

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues": issues,
            "recommendation": recommendation,
            "has_disclaimer": has_disclaimer
        }
