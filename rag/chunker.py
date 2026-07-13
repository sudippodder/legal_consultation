"""
Semantic document chunking for the RAG engine.
Splits legal documents by meaning and structure, not fixed character count.
"""

import re
from typing import List

from config import CHUNK_SIZE, CHUNK_OVERLAP


class DocumentChunker:
    """Chunks legal documents using semantic and structural boundaries."""

    # Common legal section markers
    SECTION_PATTERNS = [
        r"^(?:ARTICLE|Article|SECTION|Section|CLAUSE|Clause)\s+\d+",
        r"^\d+\.\s+[A-Z]",              # Numbered sections: "1. DEFINITIONS"
        r"^\d+\.\d+\s+",                # Sub-sections: "1.1 "
        r"^(?:WHEREAS|NOW THEREFORE|IN WITNESS WHEREOF)",
        r"^(?:SCHEDULE|ANNEXURE|APPENDIX|EXHIBIT)\s+",
        r"^(?:PART|CHAPTER)\s+(?:\d+|[IVX]+)",
    ]

    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._section_regex = re.compile(
            "|".join(self.SECTION_PATTERNS), re.MULTILINE
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text using a hybrid approach:
        1. First try structural splitting (legal sections)
        2. Then split large sections by sentences
        3. Apply overlap for context continuity
        """
        if not text or not text.strip():
            return []

        # Clean the text
        text = self._clean_text(text)

        # Step 1: Split by structural boundaries
        sections = self._split_by_structure(text)

        # Step 2: Split large sections into sentence-based chunks
        chunks = []
        for section in sections:
            if len(section.split()) <= self.chunk_size:
                if section.strip():
                    chunks.append(section.strip())
            else:
                sub_chunks = self._split_by_sentences(section)
                chunks.extend(sub_chunks)

        # Step 3: Apply overlap
        if self.overlap > 0 and len(chunks) > 1:
            chunks = self._apply_overlap(chunks)

        return [c for c in chunks if c.strip() and len(c.split()) >= 5]

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        # Remove page numbers/headers
        text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)
        return text.strip()

    def _split_by_structure(self, text: str) -> List[str]:
        """Split text by legal document structure."""
        positions = [0]
        for match in self._section_regex.finditer(text):
            positions.append(match.start())
        positions.append(len(text))

        sections = []
        for i in range(len(positions) - 1):
            section = text[positions[i]:positions[i + 1]].strip()
            if section:
                sections.append(section)

        # If no structural splits found, return as single section
        if len(sections) <= 1:
            return [text]

        return sections

    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text into chunks by sentence boundaries."""
        # Split on sentence-ending punctuation
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            word_count = len(sentence.split())
            if current_word_count + word_count > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_word_count = 0
            current_chunk.append(sentence)
            current_word_count += word_count

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlapping context between chunks."""
        if not chunks:
            return chunks

        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_words = chunks[i - 1].split()
            overlap_words = prev_words[-self.overlap:] if len(prev_words) > self.overlap else prev_words
            overlap_text = " ".join(overlap_words)
            overlapped.append(overlap_text + " " + chunks[i])

        return overlapped
