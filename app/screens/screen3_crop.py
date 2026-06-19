"""
Screen 3 — Crop / Review
Displays the captured image (or first video frame) and lets the user
draw a rubber-band rectangle to crop it before sending to the LLM.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtCore    import Qt, QRect, QPoint, QSize
from PySide6.QtGui     import QImage, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFrame
)

from app.llm_client import LMStudioClient
from app.styles     import (
    ACCENT_CYAN, ACCENT_AMBER, BG_CARD, BG_PANEL, TEXT_PRIMARY,
    TEXT_SECONDARY, BORDER
)


class _CropLabel(QLabel):
    """QLabel subclass that supports rubber-band crop selection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._origin: QPoint | None = None
        self._rect:   QRect         = QRect()
        self._active: bool          = False
        self.setCursor(Qt.CursorShape.CrossCursor)

    def reset(self):
        self._origin = None
        self._rect   = QRect()
        self._active = False
        self.update()

    @property
    def selection_rect(self) -> QRect:
        return self._rect.normalized()

    # ── Mouse events ─────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._rect   = QRect(self._origin, QSize())
            self._active = True

    def mouseMoveEvent(self, event):
        if self._active and self._origin:
            self._rect = QRect(self._origin, event.position().toPoint())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = False
            self.update()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        rect = self._rect.normalized()
        if rect.isNull() or rect.width() < 4 or rect.height() < 4:
            return
        
        from PySide6.QtGui import QRegion
        painter = QPainter(self)
        
        # Dim overlay outside selection
        dim_region = QRegion(self.rect()) - QRegion(rect)
        painter.setClipRegion(dim_region)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        painter.setClipping(False)
        
        # Draw selection border
        pen = QPen(QColor("#00d4ff"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(rect)
        painter.end()


class Screen3_Crop(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.mw            = main_window
        self._source_frame: np.ndarray | None = None   # image or first video frame
        self._pixmap_offset = QPoint(0, 0)
        self._pixmap_scale  = 1.0
        self._setup_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top bar
        top = QWidget()
        top.setStyleSheet(f"background: {BG_CARD}; border-bottom: 1px solid {BORDER};")
        top.setFixedHeight(56)
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(16, 8, 16, 8)

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self._go_back)
        back_btn.setFixedWidth(90)
        top_l.addWidget(back_btn)

        self._title = QLabel()
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ACCENT_CYAN};")
        top_l.addWidget(self._title, stretch=1)

        hint = QLabel("Drag to select a region")
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        top_l.addWidget(hint)
        outer.addWidget(top)

        # Image / crop area
        self._crop_label = _CropLabel()
        self._crop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._crop_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._crop_label.setStyleSheet("background: #050709;")
        outer.addWidget(self._crop_label, stretch=1)

        # Bottom controls
        ctrl = QWidget()
        ctrl.setStyleSheet(f"background: {BG_PANEL}; border-top: 1px solid {BORDER};")
        ctrl.setFixedHeight(80)
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(30, 10, 30, 10)
        ctrl_l.setSpacing(16)
        ctrl_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        reset_btn = QPushButton("↺  Reset Selection")
        reset_btn.clicked.connect(self._reset_selection)

        full_btn = QPushButton("⬜  Use Full Frame")
        full_btn.clicked.connect(self._use_full)

        crop_btn = QPushButton("✂  Apply Crop  →")
        crop_btn.setObjectName("primary")
        crop_btn.setFixedHeight(44)
        crop_btn.clicked.connect(self._apply_crop)

        ctrl_l.addWidget(reset_btn)
        ctrl_l.addStretch()
        ctrl_l.addWidget(full_btn)
        ctrl_l.addWidget(crop_btn)
        outer.addWidget(ctrl)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        mode = self.mw.capture_mode
        self._crop_label.reset()

        if mode == "image":
            self._source_frame = self.mw.captured_frame
            self._title.setText("Review & Crop — Image")
        else:
            frames = self.mw.captured_frames
            self._source_frame = frames[0] if frames else None
            self._title.setText(
                f"Review & Crop — Video  ({len(frames)} frames  "
                f"≈ {len(frames) // 30}s)"
            )

        if self._source_frame is not None:
            self._show_frame(self._source_frame)

    def _go_back(self):
        self.mw.navigate_to(self.mw.CAPTURE)

    # ── Display ───────────────────────────────────────────────────────────────

    def _show_frame(self, frame: np.ndarray):
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self._crop_label.setPixmap(
            pix.scaled(
                self._crop_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._source_pixmap = pix

    # ── Actions ───────────────────────────────────────────────────────────────

    def _reset_selection(self):
        self._crop_label.reset()

    def _use_full(self):
        """Skip cropping — use the entire frame(s)."""
        self._encode_and_proceed(crop_rect=None)

    def _apply_crop(self):
        sel = self._crop_label.selection_rect
        if sel.isNull() or sel.width() < 4 or sel.height() < 4:
            # Nothing selected — treat as full frame
            self._encode_and_proceed(crop_rect=None)
            return
        self._encode_and_proceed(crop_rect=sel)

    def _encode_and_proceed(self, crop_rect: QRect | None):
        """Encode the (possibly cropped) frame(s) to base64 data-URLs."""
        mode = self.mw.capture_mode

        if mode == "image":
            frame = self._source_frame
            if crop_rect is not None:
                frame = self._crop_frame(frame, crop_rect)
            self.mw.media_data_url  = LMStudioClient.encode_frame(frame)
            self.mw.media_data_urls = []
        else:
            frames = self.mw.captured_frames
            if crop_rect is not None:
                frames = [self._crop_frame(f, crop_rect) for f in frames]
            self.mw.media_data_urls = LMStudioClient.encode_video_frames(frames)
            self.mw.media_data_url  = self.mw.media_data_urls[0] if self.mw.media_data_urls else ""
            self.mw.stitched_data_url = LMStudioClient.encode_video_as_grid(frames)

        self.mw.navigate_to(self.mw.MODEL_SELECT)

    # ── Crop helper ───────────────────────────────────────────────────────────

    def _crop_frame(self, frame: np.ndarray, label_rect: QRect) -> np.ndarray:
        """
        Convert the label-space rectangle to frame-space and slice the array.
        """
        lw = self._crop_label.width()
        lh = self._crop_label.height()
        fh, fw = frame.shape[:2]

        # Compute displayed pixmap size (letterboxed)
        scale  = min(lw / fw, lh / fh)
        disp_w = fw * scale
        disp_h = fh * scale
        off_x  = (lw - disp_w) / 2
        off_y  = (lh - disp_h) / 2

        # Map label rect → frame coords
        x1 = int((label_rect.left()   - off_x) / scale)
        y1 = int((label_rect.top()    - off_y) / scale)
        x2 = int((label_rect.right()  - off_x) / scale)
        y2 = int((label_rect.bottom() - off_y) / scale)

        # Clamp
        x1, x2 = max(0, x1), min(fw, x2)
        y1, y2 = max(0, y1), min(fh, y2)
        if x2 <= x1 or y2 <= y1:
            return frame  # invalid crop → return full frame

        return frame[y1:y2, x1:x2].copy()
