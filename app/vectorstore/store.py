"""
vectorstore.py — in-memory vector store with cosine similarity search.

Chunks are loaded once at startup.  The store holds:
  { "text": str, "embedding": List[float], "title": str, "chunk_id": int }
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

_store: List[Dict[str, Any]] = []


def add(text: str, embedding: List[float], title: str, chunk_id: int):
    _store.append({
        "text": text,
        "embedding": embedding,
        "title": title,
        "chunk_id": chunk_id,
    })


def size() -> int:
    return len(_store)


def search(query_embedding: List[float], top_k: int = 3, threshold: float = 0.40) -> List[Dict[str, Any]]:
    """
    Cosine-similarity search.
    Returns up to top_k chunks whose similarity score >= threshold,
    sorted by score descending.
    """
    if not _store:
        return []

    q = np.array(query_embedding, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        return []

    results: List[Tuple[float, Dict]] = []

    for entry in _store:
        d = np.array(entry["embedding"], dtype=np.float32)
        d_norm = np.linalg.norm(d)
        if d_norm == 0:
            continue
        score = float(np.dot(q, d) / (q_norm * d_norm))
        if score >= threshold:
            results.append((score, entry))

    results.sort(key=lambda x: x[0], reverse=True)
    top = results[:top_k]

    return [
        {
            "text": entry["text"],
            "title": entry["title"],
            "chunk_id": entry["chunk_id"],
            "score": round(score, 4),
        }
        for score, entry in top
    ]
