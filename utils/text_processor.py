"""
Text processing utilities for cleaning and analyzing legal text.
"""

import re
from typing import List, Dict


def clean_text(text: str) -> str:
    """Clean and normalize text from document parsing."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    # Remove common artifacts
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\x00", "", text)  # null bytes
    return text.strip()


def extract_sections(text: str) -> List[Dict[str, str]]:
    """Extract sections from a legal document."""
    section_patterns = [
        r"^(?:ARTICLE|Article|SECTION|Section|CLAUSE|Clause)\s+(\d+[\.\d]*)\s*[:\.\-]?\s*(.*)",
        r"^(\d+)\.\s+([A-Z][A-Z\s]+)",
        r"^(\d+\.\d+)\s+(.*)",
    ]

    sections = []
    current_section = {"number": "", "title": "", "content": ""}

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        matched = False
        for pattern in section_patterns:
            match = re.match(pattern, line)
            if match:
                if current_section["content"]:
                    sections.append(current_section.copy())
                current_section = {
                    "number": match.group(1),
                    "title": match.group(2).strip() if match.lastindex >= 2 else "",
                    "content": line
                }
                matched = True
                break

        if not matched:
            current_section["content"] += "\n" + line

    if current_section["content"]:
        sections.append(current_section)

    return sections


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split()) if text else 0


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def detect_contract_type(text: str) -> str:
    """Attempt to auto-detect the type of legal contract."""
    lower = text.lower()

    type_indicators = {
        "Non-Disclosure Agreement (NDA)": [
            "non-disclosure", "nda", "confidential information",
            "disclosing party", "receiving party"
        ],
        "Employment Contract": [
            "employment", "employee", "employer", "salary",
            "probation", "working hours", "termination of employment"
        ],
        "Lease Agreement": [
            "lease", "landlord", "tenant", "rent",
            "premises", "rental", "lessee", "lessor"
        ],
        "Service Agreement": [
            "service provider", "services rendered", "scope of services",
            "service level", "deliverables"
        ],
        "Partnership Agreement": [
            "partnership", "partner", "profit sharing",
            "joint venture", "partnership deed"
        ],
        "Sales Contract": [
            "sale of goods", "buyer", "seller", "purchase price",
            "delivery of goods", "sale agreement"
        ],
        "Freelance/Consulting Agreement": [
            "consultant", "consulting", "freelance", "independent contractor",
            "statement of work"
        ],
    }

    scores = {}
    for contract_type, keywords in type_indicators.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[contract_type] = score

    if scores:
        return max(scores, key=scores.get)
    return "Other"
