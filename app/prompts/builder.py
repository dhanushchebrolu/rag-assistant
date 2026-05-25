"""
builder.py — constructs the RAG prompt from context, history, and question.
"""

from typing import List, Dict


SYSTEM_INSTRUCTIONS = """You are a helpful support assistant. Answer the user's question using ONLY the information provided in the context below. If the context does not contain enough information to answer, say so clearly — do not make up an answer or use outside knowledge.

Keep answers concise and friendly. Use plain language."""


def build_prompt(
    question: str,
    retrieved_chunks: List[Dict],
    history: List[Dict],
) -> str:
    """
    Assemble the full prompt string.

    history entries look like: {"role": "user"|"assistant", "content": str}
    """

    # --- context block ---
    if retrieved_chunks:
        context_parts = []
        for chunk in retrieved_chunks:
            context_parts.append(f"[{chunk['title']}]\n{chunk['text']}")
        context_block = "\n\n".join(context_parts)
    else:
        context_block = "No relevant information found in the knowledge base."

    # --- history block ---
    if history:
        history_lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_lines.append(f"{role}: {msg['content']}")
        history_block = "\n".join(history_lines)
    else:
        history_block = "No prior conversation."

    prompt = f"""{SYSTEM_INSTRUCTIONS}

---
CONTEXT:
{context_block}

---
CONVERSATION HISTORY:
{history_block}

---
USER QUESTION:
{question}

ANSWER:"""

    return prompt
