"""
rag.py — the core RAG pipeline.

  retrieve → build prompt → call LLM → return answer
"""

import logging
from typing import Dict, Any

from app.services.retrieval import retrieve
from app.prompts.builder   import build_prompt
from app.services.llm      import call_llm
from app.services          import sessions

logger = logging.getLogger(__name__)


def answer(session_id: str, question: str) -> Dict[str, Any]:
    """
    Full RAG pipeline for a single user turn.
    Returns dict with reply, tokens_used, retrieved_chunks count, chunk details.
    """
    # 1. retrieve relevant chunks
    chunks = retrieve(question)

    # 2. if nothing retrieved, let LLM handle it as general chat
    if not chunks:
        logger.info("No chunks retrieved — falling back to general chat.")
        history = sessions.get_history(session_id)
        general_prompt = f"""You are a friendly support assistant. The user said something that isn't covered in the knowledge base — respond naturally and conversationally. If they greet you, greet them back. If they ask something outside your knowledge base, politely let them know you're best at answering questions about the platform.

Conversation History:
{chr(10).join([f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}" for m in history]) or 'No prior conversation.'}

User: {question}
Assistant:"""
        result = call_llm(general_prompt)
        sessions.add_turn(session_id, question, result["reply"])
        return {
            "reply":            result["reply"],
            "tokens_used":      result["tokens_used"],
            "retrieved_chunks": 0,
            "sources":          [],
        }

    # 3. get conversation history
    history = sessions.get_history(session_id)

    # 4. build prompt
    prompt = build_prompt(
        question=question,
        retrieved_chunks=chunks,
        history=history,
    )

    # 5. call LLM
    result = call_llm(prompt)
    reply  = result["reply"]

    # 6. save turn to session
    sessions.add_turn(session_id, question, reply)

    sources = [{"title": c["title"], "score": c["score"]} for c in chunks]

    logger.info(f"Session {session_id} — tokens used: {result['tokens_used']}, sources: {[s['title'] for s in sources]}")

    return {
        "reply":            reply,
        "tokens_used":      result["tokens_used"],
        "retrieved_chunks": len(chunks),
        "sources":          sources,
    }