"""
Screen 7 — Done
Brief confirmation, then auto-returns to Screen 1.
"""
from __future__ import annotations

from PySide6.QtCore    import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)

from app.styles import ACCENT_CYAN, TEXT_SECONDARY, TEXT_DIM


class Screen7_Done(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.mw     = main_window
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._go_home)
        self._setup_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(20)

        icon = QLabel("✅")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 72px;")
        v.addWidget(icon)

        heading = QLabel("All done!")
        heading.setObjectName("title")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(heading)

        self._sub = QLabel("Returning to home in 3 s…")
        self._sub.setObjectName("subtitle")
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self._sub)

        back_btn = QPushButton("↩  Go Home Now")
        back_btn.setObjectName("primary")
        back_btn.setFixedHeight(44)
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(self._go_home_now)
        v.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Countdown label
        self._countdown_lbl = QLabel()
        self._countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
        v.addWidget(self._countdown_lbl)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self._remaining = 3

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        self._remaining = 3
        self._sub.setText("Returning to home in 3 s…")
        self._countdown_timer.start()
        self._timer.start(3000)

    def _tick_countdown(self):
        self._remaining -= 1
        if self._remaining > 0:
            self._sub.setText(f"Returning to home in {self._remaining} s…")
        else:
            self._countdown_timer.stop()

    def _go_home(self):
        self._countdown_timer.stop()
        self._timer.stop()
        self.mw.go_home()

    def _go_home_now(self):
        self._countdown_timer.stop()
        self._timer.stop()
        self.mw.go_home()
