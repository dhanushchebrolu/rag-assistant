"""
llm.py — thin wrapper around multiple LLM providers.

Supported:  claude | openai | gemini | mistral | openrouter | groq
Set LLM_PROVIDER in .env.
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def call_llm(prompt: str) -> Dict:
    """
    Send prompt to configured LLM.
    Returns { "reply": str, "tokens_used": int }
    """
    provider = os.getenv("LLM_PROVIDER", "claude").lower()

    try:
        if provider == "claude":
            return _call_claude(prompt)
        if provider == "openai":
            return _call_openai(prompt)
        if provider == "gemini":
            return _call_gemini(prompt)
        if provider == "mistral":
            return _call_mistral(prompt)
        if provider == "openrouter":
            return _call_openrouter(prompt)
        if provider == "groq":
            return _call_groq(prompt)
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    except Exception as exc:
        err = str(exc)
        if "api_key" in err.lower() or "authentication" in err.lower() or "401" in err:
            raise RuntimeError("Invalid or missing API key. Check your .env file.")
        if "timeout" in err.lower() or "timed out" in err.lower():
            raise RuntimeError("Request to LLM timed out. Please try again.")
        if "rate" in err.lower() or "429" in err:
            raise RuntimeError("LLM rate limit exceeded. Please wait a moment.")
        raise RuntimeError(f"LLM error: {err}")


# ── Anthropic Claude ──────────────────────────────────────────────────────────

def _call_claude(prompt: str) -> Dict:
    import httpx, json

    api_key = os.getenv("CLAUDE_API_KEY", "")
    if not api_key:
        raise RuntimeError("CLAUDE_API_KEY is not set.")

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    reply  = data["content"][0]["text"].strip()
    tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
    return {"reply": reply, "tokens_used": tokens}


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _call_openai(prompt: str) -> Dict:
    import openai

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )
    reply  = resp.choices[0].message.content.strip()
    tokens = resp.usage.total_tokens if resp.usage else 0
    return {"reply": reply, "tokens_used": tokens}


# ── Google Gemini ─────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> Dict:
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return {"reply": response.text.strip(), "tokens_used": 0}


# ── Mistral ───────────────────────────────────────────────────────────────────

def _call_mistral(prompt: str) -> Dict:
    import httpx

    api_key = os.getenv("MISTRAL_API_KEY", "")
    resp = httpx.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
        json={
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data   = resp.json()
    reply  = data["choices"][0]["message"]["content"].strip()
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return {"reply": reply, "tokens_used": tokens}


# ── OpenRouter ────────────────────────────────────────────────────────────────

def _call_openrouter(prompt: str) -> Dict:
    import httpx

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data   = resp.json()
    reply  = data["choices"][0]["message"]["content"].strip()
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return {"reply": reply, "tokens_used": tokens}


# ── Groq ──────────────────────────────────────────────────────────────────────

def _call_groq(prompt: str) -> Dict:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )
    reply  = resp.choices[0].message.content.strip()
    tokens = resp.usage.total_tokens if resp.usage else 0
    return {"reply": reply, "tokens_used": tokens}