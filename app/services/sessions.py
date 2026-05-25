"""
sessions.py — in-memory session store for conversation history.

Each session keeps the last MAX_TURNS message pairs (user + assistant).
"""

from typing import List, Dict
from collections import defaultdict

MAX_TURNS = 4   # keep last N user-assistant pairs

# { session_id: [{"role": "user"|"assistant", "content": str}, ...] }
_sessions: Dict[str, List[Dict]] = defaultdict(list)


def get_history(session_id: str) -> List[Dict]:
    return list(_sessions[session_id])


def add_turn(session_id: str, user_msg: str, assistant_msg: str):
    history = _sessions[session_id]
    history.append({"role": "user",      "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})

    # Trim to last MAX_TURNS pairs (each pair = 2 messages)
    max_msgs = MAX_TURNS * 2
    if len(history) > max_msgs:
        _sessions[session_id] = history[-max_msgs:]


def clear_session(session_id: str):
    _sessions.pop(session_id, None)
