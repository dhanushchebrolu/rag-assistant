"""
embeddings.py — generates vector embeddings for text chunks.

Supports two backends:
  - local   : sentence-transformers (all-MiniLM-L6-v2), no API needed
  - openai  : OpenAI text-embedding-3-small
  - gemini  : Google generativeai embeddings
"""

import os
import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

_local_model = None   # lazy-loaded once on first call


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model (first time — may take a moment)…")
        _local_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded.")
    return _local_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of text strings.
    Returns a list of float vectors (one per input text).
    """
    backend = os.getenv("EMBEDDING_BACKEND", "local").lower()

    if backend == "local":
        model = _get_local_model()
        vectors = model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]

    if backend == "openai":
        return _embed_openai(texts)

    if backend == "gemini":
        return _embed_gemini(texts)

    raise ValueError(f"Unknown EMBEDDING_BACKEND: {backend}")


def embed_single(text: str) -> List[float]:
    return embed_texts([text])[0]


# ── provider helpers ──────────────────────────────────────────────────────────

def _embed_openai(texts: List[str]) -> List[List[float]]:
    import openai
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [item.embedding for item in resp.data]


def _embed_gemini(texts: List[str]) -> List[List[float]]:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    results = []
    for t in texts:
        r = genai.embed_content(model="models/embedding-001", content=t)
        results.append(r["embedding"])
    return results
