"""
retrieval.py — takes a user query, embeds it, and retrieves relevant chunks.
"""

import logging
from typing import List, Dict, Any

from app.services.embeddings import embed_single
from app.vectorstore import store

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.40
TOP_K = 3


def retrieve(query: str, top_k: int = TOP_K, threshold: float = SIMILARITY_THRESHOLD) -> List[Dict[str, Any]]:
    """
    Embed query, search vector store, return ranked chunks.
    Each chunk dict has: text, title, chunk_id, score.
    """
    query_vec = embed_single(query)
    results   = store.search(query_vec, top_k=top_k, threshold=threshold)

    if results:
        scores = [r["score"] for r in results]
        logger.info(f"Retrieved {len(results)} chunks — scores: {scores}")
    else:
        logger.info("No chunks above threshold.")

    return results
