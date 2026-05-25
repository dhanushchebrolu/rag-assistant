"""
indexer.py — loads docs.json, chunks every document, generates embeddings,
and populates the vector store.

Called once at application startup.
"""

import json
import logging
import os
from typing import List, Dict, Any

from app.utils.chunker import chunk_text
from app.services.embeddings import embed_texts
from app.vectorstore import store

logger = logging.getLogger(__name__)


def index_documents(docs_path: str = None):
    if docs_path is None:
        docs_path = os.getenv("DOCS_PATH", "docs.json")

    with open(docs_path, "r", encoding="utf-8") as f:
        documents: List[Dict[str, Any]] = json.load(f)

    logger.info(f"Indexing {len(documents)} documents from {docs_path} …")

    all_chunks: List[str] = []
    chunk_meta: List[Dict[str, Any]] = []

    for doc in documents:
        title   = doc.get("title", "Untitled")
        content = doc.get("content", "")
        chunks  = chunk_text(content)

        for idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_meta.append({"title": title, "chunk_id": idx})

    # Batch-embed all chunks in one call (faster for local model)
    logger.info(f"Generating embeddings for {len(all_chunks)} chunks …")
    embeddings = embed_texts(all_chunks)

    for text, embedding, meta in zip(all_chunks, embeddings, chunk_meta):
        store.add(
            text=text,
            embedding=embedding,
            title=meta["title"],
            chunk_id=meta["chunk_id"],
        )

    logger.info(f"Vector store ready — {store.size()} chunks indexed.")
