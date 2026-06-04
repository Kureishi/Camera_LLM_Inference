"""
CameraThread — captures frames from OpenCV VideoCapture in a background QThread
and emits frame_ready(np.ndarray) signals to the GUI at ~30 fps.
"""
from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal


class CameraThread(QThread):
    """Background thread that continuously reads from a camera device."""

    frame_ready = Signal(np.ndarray)
    error       = Signal(str)

    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._running = False
        self._cap: cv2.VideoCapture | None = None

    # ── Public API ──────────────────────────────────────────────────────────

    def start_capture(self, camera_index: int | None = None) -> None:
        if camera_index is not None:
            self.camera_index = camera_index
        self._running = True
        self.start()

    def stop_capture(self) -> None:
        self._running = False
        self.wait(2000)  # give thread up to 2 s to finish

    # ── QThread lifecycle ────────────────────────────────────────────────────

    def run(self) -> None:
        self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            # Try without backend hint (Linux / macOS)
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            self.error.emit(f"Cannot open camera index {self.camera_index}")
            return

        # Prefer 720p for a good quality / performance balance
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._cap.set(cv2.CAP_PROP_FPS, 30)

        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                self.error.emit("Failed to read frame from camera")
                break
            # Convert BGR → RGB for Qt display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(frame_rgb)
            # ~30 fps → sleep ~33 ms
            self.msleep(33)

        if self._cap:
            self._cap.release()
            self._cap = None

    def __del__(self):
        self._running = False
        if self._cap:
            self._cap.release()
