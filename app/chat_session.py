"""
ChatSession — dataclass for a single chat session (image or video + messages).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class ChatSession:
    name:       str
    media_type: Literal["image", "video"]
    # For image: single data-URL string.
    # For video: list of frame data-URL strings.
    media_data: str | list[str]
    model:      str
    messages:   list[dict] = field(default_factory=list)
    timestamp:  str        = field(default_factory=lambda: datetime.now().isoformat())

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "media_type": self.media_type,
            "media_data": self.media_data,
            "model":      self.model,
            "messages":   self.messages,
            "timestamp":  self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        return cls(
            name       = data["name"],
            media_type = data["media_type"],
            media_data = data["media_data"],
            model      = data["model"],
            messages   = data.get("messages", []),
            timestamp  = data.get("timestamp", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ChatSession":
        return cls.from_dict(json.loads(json_str))

    # ── Helpers ──────────────────────────────────────────────────────────────

    @property
    def display_timestamp(self) -> str:
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%b %d, %Y  %H:%M")
        except ValueError:
            return self.timestamp

    def get_thumbnail_data_url(self) -> str:
        """Return the first (or only) frame data-URL for thumbnail display."""
        if self.media_type == "image":
            return self.media_data  # type: ignore[return-value]
        frames = self.media_data  # type: ignore[assignment]
        return frames[0] if frames else ""
