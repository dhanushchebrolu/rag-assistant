<<<<<<< HEAD
# RAG Chat Assistant

A production-style GenAI chat assistant that answers questions from a custom knowledge base using Retrieval-Augmented Generation (RAG).

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                        Browser                           │
│          HTML / CSS / Vanilla JS (frontend/)             │
└──────────────────────┬───────────────────────────────────┘
                       │  POST /api/chat
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI  (main.py)                    │
│                                                          │
│   ┌──────────┐   ┌───────────┐   ┌────────────────────┐ │
│   │ /api/chat│──▶│  rag.py   │──▶│  sessions.py       │ │
│   └──────────┘   │ pipeline  │   │  conversation hist │ │
│                  └─────┬─────┘   └────────────────────┘ │
│            ┌───────────┼──────────────┐                  │
│            ▼           ▼              ▼                  │
│     retrieval.py   builder.py      llm.py                │
│     (embed query   (RAG prompt)    (LLM API call)        │
│      + search)                                           │
│            │                          │                  │
│            ▼                          ▼                  │
│      embeddings.py            OpenAI / Claude /          │
│      (all-MiniLM-L6)          Gemini / Mistral           │
│            │                                             │
│            ▼                                             │
│      store.py  (in-memory cosine similarity search)      │
│            ▲                                             │
│            │ (indexed at startup)                        │
│      indexer.py ──▶ chunker.py ──▶ docs.json            │
└──────────────────────────────────────────────────────────┘
```

---

## RAG Workflow Explanation

### Indexing (at startup)
1. Load all documents from `docs.json`
2. Split each document into overlapping text chunks (~120 words, 20-word overlap)
3. Generate a semantic embedding vector for each chunk using `all-MiniLM-L6-v2`
4. Store `{ text, embedding, title, chunk_id }` in the in-memory vector store

### Querying (per user message)
1. Embed the user's question using the same embedding model
2. Compute cosine similarity between the query vector and every stored chunk vector
3. Filter chunks below the similarity threshold (0.40)
4. Select the top-3 highest-scoring chunks
5. If no chunks pass the threshold → return a safe fallback message
6. Build the prompt: system instructions + retrieved context + conversation history + question
7. Send prompt to the configured LLM at temperature 0.2
8. Store the turn in session memory (last 4 pairs kept)
9. Return the reply + source titles + token count

---

## Embedding Strategy

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (local, no API key required)
- **Dimension**: 384
- **Why this model**: Small, fast, well-generalised for English semantic similarity tasks. Runs on CPU with ~50ms per batch encode.
- **Alternative backends**: set `EMBEDDING_BACKEND=openai` or `EMBEDDING_BACKEND=gemini` in `.env`

---

## Similarity Search Logic

Cosine similarity between query vector **q** and document vector **d**:

```
similarity = (q · d) / (|q| × |d|)
```

- Range: 0 (unrelated) → 1 (identical meaning)
- Threshold: **0.40** — tuned to avoid returning irrelevant chunks while staying permissive enough for paraphrased questions
- Top-K: **3** chunks injected into the prompt

The threshold can be adjusted in `app/services/retrieval.py`.

---

## Prompt Design Reasoning

```
{SYSTEM INSTRUCTIONS}
---
CONTEXT:
[retrieved chunk 1 — title]
...chunk text...

[retrieved chunk 2 — title]
...chunk text...
---
CONVERSATION HISTORY:
User: ...
Assistant: ...
---
USER QUESTION:
...
ANSWER:
```

- **System instructions first** — LLMs attend to early tokens more strongly
- **Context before history** — grounds the model in facts before it sees prior turns
- **Explicit constraint** ("Use ONLY the provided context") — reduces hallucination
- **Low temperature (0.2)** — produces consistent, factual answers

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- pip

### 1. Clone or unzip the project

```bash
cd rag-assistant
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The first run will download the `all-MiniLM-L6-v2` model (~90 MB) automatically.

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your LLM provider + API key:

```
LLM_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-...
EMBEDDING_BACKEND=local
```

Supported providers: `claude` | `openai` | `gemini` | `mistral`

### 5. Run the server

```bash
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

---

## API Reference

### `POST /api/chat`
Send a message and get a grounded reply.

**Request**
```json
{
  "sessionId": "s_abc123",
  "message": "How do I reset my password?"
}
```

**Response**
```json
{
  "reply": "You can reset your password from Settings > Security...",
  "tokens_used": 312,
  "retrieved_chunks": 2,
  "sources": [
    { "title": "Reset Password", "score": 0.8234 }
  ]
}
```

### `POST /api/session/clear`
Clear conversation history for a session.

**Request**
```json
{ "sessionId": "s_abc123" }
```

### `GET /health`
Returns `{ "status": "healthy" }` when the server is running.

---

## Project Structure

```
rag-assistant/
├── main.py                    # FastAPI app, startup, routing
├── docs.json                  # Knowledge base (10 documents)
├── requirements.txt
├── .env.example
├── README.md
│
├── app/
│   ├── routes/
│   │   └── chat.py            # /api/chat and /api/session/clear
│   │
│   ├── services/
│   │   ├── rag.py             # Core pipeline orchestrator
│   │   ├── retrieval.py       # Query embedding + vector search
│   │   ├── embeddings.py      # Embedding backends (local/openai/gemini)
│   │   ├── indexer.py         # Startup indexing: load → chunk → embed → store
│   │   ├── llm.py             # LLM provider wrappers
│   │   └── sessions.py        # Conversation history per session
│   │
│   ├── vectorstore/
│   │   └── store.py           # In-memory store + cosine search
│   │
│   ├── prompts/
│   │   └── builder.py         # RAG prompt constructor
│   │
│   └── utils/
│       └── chunker.py         # Overlapping word-window chunker
│
└── frontend/
    ├── index.html
    ├── styles.css
    └── app.js
```

---

## Customising the Knowledge Base

Edit `docs.json` and add/remove documents in this format:

```json
[
  {
    "title": "Your Topic",
    "content": "Full text content here..."
  }
]
```

Restart the server — documents are re-indexed on every startup.

---

## Deployment

The app is a standard ASGI app. Deploy with:

**Render / Railway:**
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set environment variables in the dashboard

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
=======
# rag-assistant
>>>>>>> c800785955bcde52bff4a612239dc613f686f457
