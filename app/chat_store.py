"""
ChatStore — persists and loads ChatSession objects as JSON files
in the `chats/` directory next to the project root.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.chat_session import ChatSession

CHATS_DIR = Path(__file__).parent.parent / "chats"


def _ensure_dir() -> None:
    CHATS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Strip characters that are not safe for filenames."""
    safe = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return safe or "untitled"


def save(session: ChatSession) -> Path:
    """Write a ChatSession to a JSON file. Returns the file path."""
    _ensure_dir()
    filename = _safe_filename(session.name) + ".json"
    path     = CHATS_DIR / filename
    path.write_text(session.to_json(), encoding="utf-8")
    return path


def load_all() -> list[ChatSession]:
    """Load every saved ChatSession from the chats/ directory."""
    _ensure_dir()
    sessions: list[ChatSession] = []
    for fpath in sorted(CHATS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            session = ChatSession.from_json(fpath.read_text(encoding="utf-8"))
            from datetime import datetime
            session.saved_at = datetime.fromtimestamp(fpath.stat().st_mtime).isoformat()
            sessions.append(session)
        except Exception:
            pass  # skip malformed files
    return sessions


def delete(name: str) -> bool:
    """Delete a saved chat by its name. Returns True if deleted."""
    filename = _safe_filename(name) + ".json"
    path     = CHATS_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False
