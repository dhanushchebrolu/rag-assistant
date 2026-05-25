"""
chat.py — /api/chat and /api/session routes.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional

from app.services.rag      import answer
from app.services.sessions import clear_session

router = APIRouter()


# ── request / response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    sessionId: str
    message: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message field must not be empty")
        return v

    @field_validator("sessionId")
    @classmethod
    def session_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("sessionId field must not be empty")
        return v


class ClearRequest(BaseModel):
    sessionId: str


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = answer(session_id=req.sessionId, question=req.message)
        return result
    except RuntimeError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": f"Unexpected error: {str(exc)}"})


@router.post("/session/clear")
async def session_clear(req: ClearRequest):
    clear_session(req.sessionId)
    return {"status": "ok", "sessionId": req.sessionId}
