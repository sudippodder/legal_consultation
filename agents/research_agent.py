"""
Research Agent.
Queries the RAG knowledge base for relevant laws, cases, and precedents.
"""

from typing import Dict, List, Any
from rag.retriever import HybridRetriever


class ResearchAgent:
    """
    Research agent that:
    - Queries the RAG knowledge base
    - Performs multi-query expansion
    - Filters by jurisdiction
    - Formats legal citations
    """

    def __init__(self):
        self.retriever = HybridRetriever()

    def research(self, query: str, jurisdiction: str = None,
                 category: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Research a legal topic and return relevant information.
        """
        results = self.retriever.retrieve(
            query=query,
            jurisdiction=jurisdiction,
            category=category,
            top_k=top_k
        )

        formatted_results = []
        for r in results:
            formatted_results.append({
                "text": r.get("text", ""),
                "score": round(r.get("score", 0), 3),
                "source": r.get("source", ""),
                "title": r.get("metadata", {}).get("title", ""),
                "category": r.get("metadata", {}).get("category", ""),
                "jurisdiction": r.get("metadata", {}).get("jurisdiction", ""),
            })

        context = self.retriever.build_context(query, jurisdiction=jurisdiction)

        return {
            "results": formatted_results,
            "context": context,
            "total_found": len(formatted_results),
            "query": query,
            "jurisdiction": jurisdiction
        }

    def get_context_for_analysis(self, document_text: str,
                                  contract_type: str = "",
                                  jurisdiction: str = None) -> str:
        """
        Get relevant context for contract analysis.
        Builds a targeted query from the document and contract type.
        """
        # Build a focused query from contract type and key terms
        query_parts = []
        if contract_type:
            query_parts.append(f"{contract_type} legal requirements")
        if jurisdiction:
            query_parts.append(f"{jurisdiction} contract law")

        # Extract some key terms from the document
        key_legal_terms = [
            "indemnification", "termination", "liability",
            "confidentiality", "non-compete", "dispute resolution",
            "force majeure", "intellectual property", "warranty"
        ]
        doc_lower = document_text.lower()
        found_terms = [t for t in key_legal_terms if t in doc_lower]
        if found_terms:
            query_parts.append(" ".join(found_terms[:3]))

        query = " ".join(query_parts) if query_parts else "contract analysis legal review"

        return self.retriever.build_context(query, jurisdiction=jurisdiction)
