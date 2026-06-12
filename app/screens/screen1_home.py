"""
Screen 1 — Home
Two hero buttons (Image / Video) + collapsible side panel listing saved chats.
"""
from __future__ import annotations

from PySide6.QtCore    import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui     import QFont, QIcon, QPixmap, QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSizePolicy, QFrame, QScrollArea,
    QGraphicsDropShadowEffect
)

import app.chat_store as chat_store
from app.chat_session import ChatSession
from app.styles       import (
    BG_PANEL, BG_CARD, ACCENT_CYAN, ACCENT_AMBER, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_DIM, BORDER, hero_button_style
)


class Screen1_Home(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._panel_open    = False
        self._panel_anim: QPropertyAnimation | None = None
        self._setup_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Side panel (saved chats) ─────────────────────────────────────────
        self._side_panel = self._build_side_panel()
        self._side_panel.setFixedWidth(0)   # collapsed initially
        root.addWidget(self._side_panel)

        # ── Separator ────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {BORDER};")
        root.addWidget(sep)

        # ── Main hero area ───────────────────────────────────────────────────
        root.addWidget(self._build_hero(), stretch=1)

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {BG_PANEL};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f"background: {BG_CARD}; border-bottom: 1px solid {BORDER};")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(14, 12, 14, 12)
        title_lbl = QLabel("💬  Saved Chats")
        title_lbl.setStyleSheet(
            f"color: {ACCENT_CYAN}; font-size: 13px; font-weight: 700;"
        )
        hdr_l.addWidget(title_lbl)
        layout.addWidget(hdr)

        # Chat list
        self._chat_list = QListWidget()
        self._chat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._chat_list.itemDoubleClicked.connect(self._open_saved_chat)
        self._chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._chat_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._chat_list, stretch=1)

        # Footer hint
        hint = QLabel("Double-click to reopen")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; padding: 8px;")
        layout.addWidget(hint)
        return panel

    def _build_hero(self) -> QWidget:
        hero = QWidget()
        v    = QVBoxLayout(hero)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(32)

        # ── Menu toggle ──────────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        self._menu_btn = QPushButton("☰  Saved Chats")
        self._menu_btn.setFixedHeight(36)
        self._menu_btn.setStyleSheet(
            f"QPushButton {{ background: {BG_CARD}; border: 1px solid {BORDER};"
            f"border-radius: 8px; color: {TEXT_SECONDARY}; font-size: 13px; padding: 0 16px; }}"
            f"QPushButton:hover {{ color: {ACCENT_CYAN}; border-color: {ACCENT_CYAN}; }}"
        )
        self._menu_btn.clicked.connect(self._toggle_panel)
        top_bar.addWidget(self._menu_btn)
        top_bar.addStretch()
        v.addLayout(top_bar)

        v.addStretch()

        # ── App logo / title ─────────────────────────────────────────────────
        logo_lbl = QLabel("🔬  Camera LLM")
        logo_lbl.setObjectName("title")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet(
            f"font-size: 36px; font-weight: 800; color: {ACCENT_CYAN};"
            f"letter-spacing: 2px;"
        )
        v.addWidget(logo_lbl)

        sub_lbl = QLabel("Capture · Crop · Analyse with any local LLM")
        sub_lbl.setObjectName("subtitle")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 15px; margin-bottom: 24px;")
        v.addWidget(sub_lbl)

        # ── Hero buttons ─────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(40)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._img_btn = QPushButton("📷\n\nImage")
        self._img_btn.setStyleSheet(hero_button_style(ACCENT_CYAN, "#55eeff"))
        self._img_btn.setToolTip("Capture a still image and send to an LLM")
        self._img_btn.clicked.connect(self._go_image)

        self._vid_btn = QPushButton("🎬\n\nVideo")
        self._vid_btn.setStyleSheet(hero_button_style(ACCENT_AMBER, "#ffd080"))
        self._vid_btn.setToolTip("Record a video clip and send frames to an LLM")
        self._vid_btn.clicked.connect(self._go_video)

        btn_row.addWidget(self._img_btn)
        btn_row.addWidget(self._vid_btn)
        v.addLayout(btn_row)

        v.addStretch()

        # Footer
        footer = QLabel("Powered by LM Studio  •  OpenCV  •  PySide6")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; padding-bottom: 16px;")
        v.addWidget(footer)

        return hero

    # ── Slot handlers ────────────────────────────────────────────────────────

    def _go_image(self):
        self.mw.capture_mode = "image"
        self.mw.navigate_to(self.mw.CAPTURE)

    def _go_video(self):
        self.mw.capture_mode = "video"
        self.mw.navigate_to(self.mw.CAPTURE)

    def _toggle_panel(self):
        self._panel_open = not self._panel_open
        target_w = 300 if self._panel_open else 0

        if self._panel_anim:
            self._panel_anim.stop()

        self._panel_anim = QPropertyAnimation(self._side_panel, b"minimumWidth")
        self._panel_anim.setDuration(200)
        self._panel_anim.setEndValue(target_w)
        self._panel_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._panel_anim.start()

        # Also animate max width
        anim2 = QPropertyAnimation(self._side_panel, b"maximumWidth")
        anim2.setDuration(200)
        anim2.setEndValue(target_w)
        anim2.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim2.start()
        self._anim2 = anim2  # keep reference

    def _open_saved_chat(self, item: QListWidgetItem):
        session: ChatSession = item.data(Qt.ItemDataRole.UserRole)
        if session:
            self.mw.navigate_to(self.mw.CHAT, session=session, read_only=False)

    def _show_context_menu(self, pos):
        item = self._chat_list.itemAt(pos)
        if not item:
            return
        from PySide6.QtWidgets import QMenu, QMessageBox, QInputDialog
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; }}")
        
        rename_action = menu.addAction("Rename Chat")
        delete_action = menu.addAction("Delete Chat")
        
        action = menu.exec(self._chat_list.mapToGlobal(pos))
        
        if action == rename_action:
            session: ChatSession = item.data(Qt.ItemDataRole.UserRole)
            if session:
                # Add simple styling for the input dialog
                self.setStyleSheet(f"QInputDialog {{ background: {BG_CARD}; }}")
                new_name, ok = QInputDialog.getText(
                    self, "Rename Chat", "Enter new name for this chat:", text=session.name
                )
                if ok and new_name and new_name.strip() != session.name:
                    old_name = session.name
                    session.name = new_name.strip()
                    chat_store.save(session)
                    chat_store.delete(old_name)
                    self.refresh_side_panel()
                    
        elif action == delete_action:
            session: ChatSession = item.data(Qt.ItemDataRole.UserRole)
            if session:
                reply = QMessageBox.question(
                    self, "Delete Chat", f"Are you sure you want to delete '{session.name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    chat_store.delete(session.name)
                    self.refresh_side_panel()

    # ── Public API (called by MainWindow) ────────────────────────────────────

    def refresh_side_panel(self):
        self._chat_list.clear()
        sessions = chat_store.load_all()
        for session in sessions:
            item = QListWidgetItem()
            item.setText(f"  {session.name}\n  Saved: {session.display_saved_at}")
            item.setData(Qt.ItemDataRole.UserRole, session)
            item.setSizeHint(QSize(280, 66))
            self._chat_list.addItem(item)

    def on_enter(self, **kwargs):
        self.refresh_side_panel()
