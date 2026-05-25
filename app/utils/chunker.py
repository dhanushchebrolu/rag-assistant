"""
chunker.py — splits document content into overlapping token-ish chunks.

We approximate token count as words (good enough for 300-500 target).
Overlap of ~50 words keeps context across chunk boundaries.
"""

from typing import List

CHUNK_SIZE = 120      # ~words per chunk  (≈ 150-180 tokens)
OVERLAP    = 20       # words of overlap between consecutive chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    """
    Split a piece of text into overlapping word-window chunks.
    Returns a list of chunk strings.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap   # slide forward with overlap

    return chunks
