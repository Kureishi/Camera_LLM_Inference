"""
LMStudioClient — wraps the openai Python client pointed at a local LM Studio server.
All image/video encoding is done fully in-memory (no files written to disk).
"""
from __future__ import annotations

import base64
from typing import Generator

import cv2
import numpy as np
from openai import OpenAI, OpenAIError


class LMStudioClient:
    """Interface to LM Studio's OpenAI-compatible local API."""

    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url
        self._client  = self._make_client(base_url)

    # ── Connection ───────────────────────────────────────────────────────────

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url
        self._client  = self._make_client(base_url)

    def _make_client(self, base_url: str) -> OpenAI:
        return OpenAI(base_url=base_url, api_key="lm-studio")

    # ── Model discovery ──────────────────────────────────────────────────────

    def list_models(self) -> list[str]:
        """Return model IDs available on the local server."""
        try:
            models = self._client.models.list()
            return [m.id for m in models.data]
        except OpenAIError as exc:
            raise ConnectionError(
                f"Cannot reach LM Studio at {self.base_url}.\n"
                f"Make sure LM Studio is running and the server is started.\n\nDetail: {exc}"
            ) from exc

    # ── Encoding helpers (fully in-memory) ───────────────────────────────────

    @staticmethod
    def encode_frame(frame: np.ndarray, quality: int = 85) -> str:
        """
        Encode a numpy RGB frame to a base64 JPEG data-URL string.
        No file is written to disk.
        """
        # Convert RGB → BGR for cv2 (cv2 works in BGR)
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        success, buffer = cv2.imencode(".jpg", bgr, encode_params)
        if not success:
            raise RuntimeError("cv2.imencode failed")
        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    @staticmethod
    def sample_video_frames(
        frames: list[np.ndarray], max_frames: int = 8
    ) -> list[np.ndarray]:
        """
        Down-sample a list of video frames to at most max_frames evenly spaced frames.
        """
        if not frames:
            return []
        if len(frames) <= max_frames:
            return frames
        step  = len(frames) / max_frames
        idxs  = [int(i * step) for i in range(max_frames)]
        return [frames[i] for i in idxs]

    @staticmethod
    def encode_video_frames(
        frames: list[np.ndarray], max_frames: int = 8
    ) -> list[str]:
        """Return a list of base64 data-URL strings for sampled video frames."""
        sampled = LMStudioClient.sample_video_frames(frames, max_frames)
        return [LMStudioClient.encode_frame(f) for f in sampled]

    @staticmethod
    def encode_video_as_grid(
        frames: list[np.ndarray], max_frames: int = 8, cols: int = 4
    ) -> str:
        """Stitch sampled frames into a single image grid (robust for local VLMs)."""
        sampled = LMStudioClient.sample_video_frames(frames, max_frames)
        if not sampled:
            return ""
        
        # Resize to keep the grid reasonable
        target_w, target_h = 320, 180
        resized = [cv2.resize(f, (target_w, target_h)) for f in sampled]
        
        # Pad with black frames if needed
        while len(resized) % cols != 0:
            resized.append(np.zeros((target_h, target_w, 3), dtype=np.uint8))
            
        rows = []
        for i in range(0, len(resized), cols):
            row = np.hstack(resized[i:i+cols])
            rows.append(row)
            
        grid = np.vstack(rows)
        return LMStudioClient.encode_frame(grid)

    # ── Chat ─────────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: list[dict],
        model: str,
        stream: bool = True,
    ) -> Generator[str, None, None]:
        """
        Send a messages list to the model and yield token chunks.
        Supports streaming for responsive chat UI.
        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                temperature=0.7,
                max_tokens=2048,
            )
            if stream:
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
            else:
                yield response.choices[0].message.content or ""
        except OpenAIError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

    # ── Build initial vision message ─────────────────────────────────────────

    @staticmethod
    def build_image_message(data_url: str, user_text: str) -> dict:
        """Construct the first user message containing a still image."""
        return {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
                {"type": "text", "text": user_text},
            ],
        }

    @staticmethod
    def build_video_message(data_urls: list[str], user_text: str) -> dict:
        """Construct the first user message with multiple video frames."""
        content = []
        for i, url in enumerate(data_urls):
            content.append({
                "type": "image_url",
                "image_url": {"url": url},
            })
        content.append({"type": "text", "text": user_text})
        return {"role": "user", "content": content}
