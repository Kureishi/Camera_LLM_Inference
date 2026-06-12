"""
Screen 6 — Save Chat
Asks the user whether to save the session and, if so, lets them name it.
"""
from __future__ import annotations

from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSizePolicy, QMessageBox
)

import app.chat_store as chat_store
from app.chat_session import ChatSession
from app.styles       import (
    ACCENT_CYAN, BG_CARD, BG_PANEL, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_DIM, BORDER, ERROR_COLOR, SUCCESS
)


class Screen6_Save(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.mw       = main_window
        self._session: ChatSession | None = None
        self._setup_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setSpacing(28)
        outer.setContentsMargins(60, 60, 60, 60)

        icon = QLabel("💾")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 56px;")
        outer.addWidget(icon)

        heading = QLabel("Save this chat?")
        heading.setObjectName("title")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(heading)

        sub = QLabel(
            "Give your session a name to find it later,\nor skip to discard."
        )
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(sub)

        # Card
        card = QWidget()
        card.setStyleSheet(
            f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 14px;"
        )
        card.setMaximumWidth(500)
        card_v = QVBoxLayout(card)
        card_v.setContentsMargins(30, 24, 30, 24)
        card_v.setSpacing(14)

        name_lbl = QLabel("Chat name")
        name_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        card_v.addWidget(name_lbl)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g.  Lab Sample Analysis  June 4")
        self._name_edit.setFixedHeight(44)
        card_v.addWidget(self._name_edit)

        self._save_btn = QPushButton("💾  Save Chat")
        self._save_btn.setObjectName("primary")
        self._save_btn.setFixedHeight(46)
        self._save_btn.clicked.connect(self._save)
        card_v.addWidget(self._save_btn)

        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 12px;")
        card_v.addWidget(self._status_lbl)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        skip_btn = QPushButton("Skip  →")
        skip_btn.setFixedWidth(130)
        skip_btn.clicked.connect(self._skip)
        outer.addWidget(skip_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, session: ChatSession | None = None, **kwargs):
        self._session = session
        self._name_edit.clear()
        self._status_lbl.clear()
        if session:
            self._name_edit.setPlaceholderText(f"e.g.  {session.media_type.title()} Analysis")
            if hasattr(session, 'name') and session.name and session.name != "Untitled":
                self._name_edit.setText(session.name)
        self._name_edit.setFocus()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _save(self):
        if not self._session:
            self.mw.navigate_to(self.mw.DONE)
            return
        name = self._name_edit.text().strip()
        if not name:
            self._status_lbl.setStyleSheet(f"color: {ERROR_COLOR}; font-size: 12px;")
            self._status_lbl.setText("Please enter a name.")
            return
        self._session.name = name
        try:
            path = chat_store.save(self._session)
            self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 12px;")
            self._status_lbl.setText(f"✓  Saved!")
            # Slight delay then proceed
            from PySide6.QtCore import QTimer
            QTimer.singleShot(900, lambda: self.mw.navigate_to(self.mw.DONE))
        except Exception as exc:
            self._status_lbl.setStyleSheet(f"color: {ERROR_COLOR}; font-size: 12px;")
            self._status_lbl.setText(f"⚠  {exc}")

    def _skip(self):
        self.mw.navigate_to(self.mw.DONE)
