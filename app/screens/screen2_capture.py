"""
Screen 2 — Camera Capture
Live camera feed via CameraThread.
Image mode : "Capture" button freezes the frame, goes to Screen 3.
Video mode : "Record/Stop" toggles in-memory recording, goes to Screen 3.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtCore    import Qt, QTimer, Signal, Slot
from PySide6.QtGui     import QImage, QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QFrame, QSizePolicy, QMessageBox
)

from app.camera_thread import CameraThread
from app.styles        import (
    ACCENT_CYAN, ACCENT_AMBER, BG_CARD, BG_PANEL, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_DIM, BORDER, ERROR_COLOR
)


class Screen2_Capture(QWidget):

    MAX_VIDEO_SECONDS = 60

    def __init__(self, main_window):
        super().__init__()
        self.mw            = main_window
        self._thread       = CameraThread()
        self._recording    = False
        self._recorded_frames: list[np.ndarray] = []
        self._latest_frame: np.ndarray | None   = None
        self._elapsed_sec  = 0
        self._timer        = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick_timer)

        self._thread.frame_ready.connect(self._on_frame)
        self._thread.error.connect(self._on_camera_error)

        self._setup_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = QWidget()
        top.setStyleSheet(f"background: {BG_CARD}; border-bottom: 1px solid {BORDER};")
        top.setFixedHeight(52)
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(16, 0, 16, 0)

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self._go_back)
        back_btn.setFixedWidth(90)
        top_l.addWidget(back_btn)

        self._mode_label = QLabel()
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_label.setStyleSheet(f"font-size: 16px; font-weight: 700;")
        top_l.addWidget(self._mode_label, stretch=1)

        # Camera index selector
        cam_lbl = QLabel("Camera:")
        cam_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self._cam_input = QLineEdit("0")
        self._cam_input.setFixedWidth(200)
        self._cam_input.setToolTip("Camera index (0, 1) or IP Camera URL (http://...)")
        self._cam_input.returnPressed.connect(self._switch_camera)
        top_l.addWidget(cam_lbl)
        top_l.addWidget(self._cam_input)
        outer.addWidget(top)

        # ── Camera feed ──────────────────────────────────────────────────────
        feed_area = QWidget()
        feed_area.setStyleSheet("background: #050709;")
        feed_layout = QVBoxLayout(feed_area)
        feed_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        feed_layout.setContentsMargins(20, 20, 20, 8)

        self._feed_label = QLabel("Initialising camera…")
        self._feed_label.setObjectName("camera_feed")
        self._feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feed_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._feed_label.setMinimumSize(480, 320)
        self._feed_label.setStyleSheet(
            f"background: #050709; border: 2px solid {BORDER}; border-radius: 12px;"
            f"color: {TEXT_DIM}; font-size: 16px;"
        )
        feed_layout.addWidget(self._feed_label)

        # Recording progress bar (video only)
        self._rec_bar = QProgressBar()
        self._rec_bar.setRange(0, self.MAX_VIDEO_SECONDS)
        self._rec_bar.setValue(0)
        self._rec_bar.setFixedHeight(6)
        self._rec_bar.setTextVisible(False)
        self._rec_bar.hide()
        feed_layout.addWidget(self._rec_bar)

        outer.addWidget(feed_area, stretch=1)

        # ── Bottom controls ──────────────────────────────────────────────────
        ctrl = QWidget()
        ctrl.setStyleSheet(f"background: {BG_PANEL}; border-top: 1px solid {BORDER};")
        ctrl.setFixedHeight(90)
        ctrl_l = QHBoxLayout(ctrl)
        ctrl_l.setContentsMargins(30, 0, 30, 0)
        ctrl_l.setSpacing(20)
        ctrl_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Image capture button
        self._capture_btn = QPushButton("📷  Capture")
        self._capture_btn.setObjectName("primary")
        self._capture_btn.setFixedHeight(48)
        self._capture_btn.clicked.connect(self._capture_image)
        ctrl_l.addWidget(self._capture_btn)

        # Record / Stop buttons (video mode)
        self._record_btn = QPushButton("⏺")
        self._record_btn.setObjectName("record")
        self._record_btn.setToolTip("Start recording")
        self._record_btn.clicked.connect(self._start_recording)

        self._stop_btn = QPushButton("⏹  Stop & Proceed")
        self._stop_btn.setObjectName("amber")
        self._stop_btn.setFixedHeight(48)
        self._stop_btn.clicked.connect(self._stop_recording)

        self._timer_label = QLabel("00:00")
        self._timer_label.setStyleSheet(
            f"color: {ERROR_COLOR}; font-size: 22px; font-weight: 700; min-width: 70px;"
        )

        ctrl_l.addWidget(self._record_btn)
        ctrl_l.addWidget(self._timer_label)
        ctrl_l.addWidget(self._stop_btn)

        outer.addWidget(ctrl)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        mode = self.mw.capture_mode
        is_video = (mode == "video")

        # Toggle visible controls
        self._capture_btn.setVisible(not is_video)
        self._record_btn.setVisible(is_video)
        self._stop_btn.setVisible(is_video)
        self._timer_label.setVisible(is_video)
        self._rec_bar.setVisible(is_video)

        accent = ACCENT_AMBER if is_video else ACCENT_CYAN
        self._mode_label.setText(
            f"<span style='color:{accent};'>{'🎬  VIDEO' if is_video else '📷  IMAGE'}</span>  —  Live Preview"
        )

        # Reset recording state
        self._recording  = False
        self._recorded_frames.clear()
        self._latest_frame = None
        self._elapsed_sec  = 0
        self._timer_label.setText("00:00")
        self._rec_bar.setValue(0)
        self._feed_label.setText("Initialising camera…")

        # Start camera thread
        if self._thread.isRunning():
            self._thread.stop_capture()
        
        text = self._cam_input.text().strip()
        source = int(text) if text.isdigit() else text
        self._thread.start_capture(source)

    def _go_back(self):
        if self._thread.isRunning():
            self._thread.stop_capture()
        if self._timer.isActive():
            self._timer.stop()
        self.mw.go_home()

    # ── Frame handling ───────────────────────────────────────────────────────

    @Slot(np.ndarray)
    def _on_frame(self, frame: np.ndarray):
        self._latest_frame = frame
        if self._recording:
            self._recorded_frames.append(frame.copy())
            # Auto-stop at max length
            if len(self._recorded_frames) >= self.MAX_VIDEO_SECONDS * 30:
                self._stop_recording()
        self._display_frame(frame)

    def _display_frame(self, frame: np.ndarray):
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self._feed_label.setPixmap(
            pix.scaled(
                self._feed_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    @Slot(str)
    def _on_camera_error(self, msg: str):
        self._feed_label.setText(f"⚠  {msg}")
        self._feed_label.setStyleSheet(
            f"background: #1a0005; border: 2px solid {ERROR_COLOR}; border-radius: 12px;"
            f"color: {ERROR_COLOR}; font-size: 14px; padding: 20px;"
        )

    # ── Camera switch ────────────────────────────────────────────────────────

    def _switch_camera(self):
        if self._thread.isRunning():
            self._thread.stop_capture()
        
        text = self._cam_input.text().strip()
        if not text:
            return
        source = int(text) if text.isdigit() else text
        self._thread.start_capture(source)

    # ── Image capture ────────────────────────────────────────────────────────

    def _capture_image(self):
        if self._latest_frame is None:
            return
        self._thread.stop_capture()
        self.mw.captured_frame = self._latest_frame.copy()
        self.mw.navigate_to(self.mw.CROP)

    # ── Video recording ──────────────────────────────────────────────────────

    def _start_recording(self):
        if self._recording:
            return
        self._recording = True
        self._recorded_frames.clear()
        self._elapsed_sec = 0
        self._rec_bar.setValue(0)
        self._timer.start()
        self._record_btn.setStyleSheet(
            "QPushButton { background: #600; border: 2px solid #ff0000;"
            "border-radius: 24px; min-width:48px; min-height:48px;"
            "max-width:48px; max-height:48px; font-size: 18px; color: #ff0000;}"
        )
        self._timer_label.setStyleSheet(
            f"color: #ff3333; font-size: 22px; font-weight: 700; min-width: 70px;"
        )

    def _stop_recording(self):
        if not self._recording:
            return
        self._recording = False
        self._timer.stop()
        self._thread.stop_capture()
        if not self._recorded_frames:
            QMessageBox.warning(self, "No frames", "No frames were captured. Please try again.")
            
            text = self._cam_input.text().strip()
            source = int(text) if text.isdigit() else text
            self._thread.start_capture(source)
            return
        self.mw.captured_frames = list(self._recorded_frames)
        self.mw.navigate_to(self.mw.CROP)

    def _tick_timer(self):
        self._elapsed_sec += 1
        m, s = divmod(self._elapsed_sec, 60)
        self._timer_label.setText(f"{m:02d}:{s:02d}")
        self._rec_bar.setValue(min(self._elapsed_sec, self.MAX_VIDEO_SECONDS))
        if self._elapsed_sec >= self.MAX_VIDEO_SECONDS:
            self._stop_recording()
