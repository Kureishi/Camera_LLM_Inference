"""
Screen 5 — Chat
Top half: thumbnail of the captured image (or video strip).
Bottom half: scrollable chat log with message bubbles + input box.
LLM calls run in a background QThread worker so the UI stays responsive.
"""
from __future__ import annotations

import base64
from typing import Generator

import numpy as np
from PySide6.QtCore    import Qt, QThread, Signal, Slot
from PySide6.QtGui     import QImage, QPixmap, QFont, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QSizePolicy, QFrame, QSplitter,
    QMessageBox, QApplication
)

from app.llm_client  import LMStudioClient
from app.chat_session import ChatSession
from app.styles       import (
    ACCENT_CYAN, ACCENT_AMBER, BG_CARD, BG_PANEL, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM, BORDER, ERROR_COLOR,
    USER_BUBBLE, BOT_BUBBLE
)


# ── LLM streaming worker ──────────────────────────────────────────────────────

class _LLMWorker(QThread):
    token_ready  = Signal(str)
    done         = Signal()
    error        = Signal(str)

    def __init__(self, client: LMStudioClient, messages: list, model: str):
        super().__init__()
        self._client   = client
        self._messages = messages
        self._model    = model

    def run(self):
        try:
            for token in self._client.chat(self._messages, self._model, stream=True):
                self.token_ready.emit(token)
            self.done.emit()
        except Exception as exc:
            self.error.emit(str(exc))


# ── Message bubble widget ─────────────────────────────────────────────────────

class _Bubble(QWidget):
    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self.role = role
        self._raw_text = ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFrameShape(QFrame.Shape.NoFrame)
        self._text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._text.document().contentsChanged.connect(self._adjust_height)

        if role == "user":
            bg    = USER_BUBBLE
            color = "#88ddff"
            align = Qt.AlignmentFlag.AlignRight
            layout.addStretch()
            layout.addWidget(self._text)
        else:
            bg    = BOT_BUBBLE
            color = TEXT_PRIMARY
            align = Qt.AlignmentFlag.AlignLeft
            layout.addWidget(self._text)
            layout.addStretch()

        self._text.setStyleSheet(
            f"QTextEdit {{ background: {bg}; color: {color}; border: 1px solid {BORDER};"
            f"border-radius: 10px; padding: 10px 14px; font-size: 13px; }}"
        )
        self._text.setMaximumWidth(620)

    def append_text(self, text: str):
        self._raw_text += text
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._text.setTextCursor(cursor)
        self._adjust_height()

    def set_text(self, text: str, as_markdown: bool = False):
        self._raw_text = text
        if as_markdown:
            self._text.setMarkdown(text)
        else:
            self._text.setPlainText(text)
        self._adjust_height()

    def render_markdown(self):
        self._text.setMarkdown(self._raw_text)
        self._adjust_height()

    def _adjust_height(self):
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, self._do_adjust_height)

    def _do_adjust_height(self):
        doc_h = int(self._text.document().size().height())
        self._text.setFixedHeight(max(40, doc_h + 24))


# ── Screen 5 ─────────────────────────────────────────────────────────────────

class Screen5_Chat(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.mw         = main_window
        self._client    = LMStudioClient(self.mw.lm_base_url)
        self._messages: list[dict] = []
        self._worker: _LLMWorker | None = None
        self._current_bot_bubble: _Bubble | None = None
        self._read_only = False
        self._session: ChatSession | None = None
        self._setup_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top bar
        top = QWidget()
        top.setStyleSheet(f"background: {BG_CARD}; border-bottom: 1px solid {BORDER};")
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(16, 12, 16, 12)

        self._finish_btn = QPushButton("✓  Finish")
        self._finish_btn.setObjectName("primary")
        self._finish_btn.setMinimumHeight(36)
        self._finish_btn.clicked.connect(self._finish)

        self._model_lbl = QLabel()
        self._model_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._model_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        self._mode_lbl = QLabel()
        self._mode_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._mode_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700;")

        top_l.addWidget(self._finish_btn)
        top_l.addWidget(self._model_lbl, stretch=1)
        top_l.addWidget(self._mode_lbl)
        outer.addWidget(top)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER}; }}")

        # ── Thumbnail panel (top half) ────────────────────────────────────────
        thumb_container = QWidget()
        thumb_container.setStyleSheet(f"background: #050709;")
        thumb_l = QVBoxLayout(thumb_container)
        thumb_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_l.setContentsMargins(12, 12, 12, 12)

        self._thumb_label = QLabel()
        self._thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_label.setStyleSheet(
            f"background: #080a10; border: 2px solid {BORDER}; border-radius: 10px;"
        )
        self._thumb_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        thumb_l.addWidget(self._thumb_label)

        # Video strip for multi-frame
        self._strip_widget = QWidget()
        self._strip_widget.hide()
        strip_l = QHBoxLayout(self._strip_widget)
        strip_l.setContentsMargins(0, 4, 0, 0)
        strip_l.setSpacing(4)
        strip_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._strip_labels: list[QLabel] = []
        thumb_l.addWidget(self._strip_widget)

        splitter.addWidget(thumb_container)

        # ── Chat panel (bottom half) ──────────────────────────────────────────
        chat_panel = QWidget()
        chat_panel.setStyleSheet(f"background: {BG_PANEL};")
        chat_v = QVBoxLayout(chat_panel)
        chat_v.setContentsMargins(0, 0, 0, 0)
        chat_v.setSpacing(0)

        # Scrollable chat log
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._chat_inner = QWidget()
        self._chat_inner.setStyleSheet(f"background: {BG_PANEL};")
        self._chat_layout = QVBoxLayout(self._chat_inner)
        self._chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._chat_layout.setSpacing(6)
        self._chat_layout.setContentsMargins(16, 12, 16, 12)
        self._chat_layout.addStretch()

        self._scroll.setWidget(self._chat_inner)
        chat_v.addWidget(self._scroll, stretch=1)

        # Input bar
        input_bar = QWidget()
        input_bar.setStyleSheet(
            f"background: {BG_CARD}; border-top: 1px solid {BORDER};"
        )
        input_l = QHBoxLayout(input_bar)
        input_l.setContentsMargins(16, 12, 16, 12)
        input_l.setSpacing(10)

        self._input = QTextEdit()
        self._input.setPlaceholderText("Ask something about this image/video…")
        self._input.setFixedHeight(50)
        self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._input.installEventFilter(self)

        self._send_btn = QPushButton("➤")
        self._send_btn.setObjectName("primary")
        self._send_btn.setMinimumSize(50, 50)
        self._send_btn.setToolTip("Send (or press Enter)")
        self._send_btn.clicked.connect(self._send)

        input_l.addWidget(self._input, stretch=1)
        input_l.addWidget(self._send_btn)
        chat_v.addWidget(input_bar)

        splitter.addWidget(chat_panel)
        splitter.setSizes([280, 420])

        outer.addWidget(splitter, stretch=1)

    # ── Qt event filter (Enter to send & Thumbnail clicks) ───────────────────

    def eventFilter(self, source, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui  import QKeyEvent
        
        # Click on thumbnail in the strip
        if event.type() == QEvent.Type.MouseButtonPress:
            if hasattr(self, "_strip_labels") and source in self._strip_labels:
                pix = getattr(source, "_full_pixmap", source.pixmap())
                if pix:
                    self._thumb_label.setPixmap(
                        pix.scaled(700, 280, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                    )
                return True

        # Enter key in input box
        if (source is self._input and
                event.type() == QEvent.Type.KeyPress):
            key = event.key()
            mod = event.modifiers()
            if (key == Qt.Key.Key_Return and
                    mod != Qt.KeyboardModifier.ShiftModifier):
                self._send()
                return True
        return super().eventFilter(source, event)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, session: ChatSession | None = None, read_only: bool = False, **kwargs):
        self._read_only = read_only
        self._clear_chat()

        if session is not None:
            # Replay a saved session (read-only)
            self._session  = session
            self._messages = list(session.messages)
            self._client.set_base_url(self.mw.lm_base_url)
            self._model_lbl.setText(f"📝 {session.name}  |  Model: {session.model}")
            self._mode_lbl.setText(
                f"<span style='color:{ACCENT_AMBER};'>{'🎬 VIDEO' if session.media_type == 'video' else '📷 IMAGE'}</span>"
            )
            
            if session.media_type == "video" and isinstance(session.media_data, list):
                self._load_thumbnails_for_video(session.media_data)
            else:
                self._load_thumbnail_from_url(session.get_thumbnail_data_url())
                
            for msg in session.messages:
                role    = msg.get("role", "")
                content = msg.get("content", "")
                
                # Helper to strip the hidden system prompt from the UI
                def _strip_prefix(t: str) -> str:
                    prefix = "The attached image is a grid of sequential frames from a video, read from left-to-right, top-to-bottom.\n\n"
                    if t.startswith(prefix):
                        return t[len(prefix):]
                    return t

                if isinstance(content, str):
                    self._add_bubble(role, _strip_prefix(content), as_markdown=True)
                elif isinstance(content, list):
                    for part in content:
                        if part.get("type") == "text":
                            self._add_bubble(role, _strip_prefix(part["text"]), as_markdown=True)
                            
            if self._read_only:
                self._input.setEnabled(False)
                self._send_btn.setEnabled(False)
                self._finish_btn.setText("← Close")
            else:
                self._input.setEnabled(True)
                self._send_btn.setEnabled(True)
                self._finish_btn.setText("✓  Finish")
        else:
            # Fresh session
            self._session   = None
            self._messages  = []
            self._client.set_base_url(self.mw.lm_base_url)
            model = self.mw.selected_model
            mode  = self.mw.capture_mode
            self._model_lbl.setText(f"Model: {model}")
            self._mode_lbl.setText(
                f"<span style='color:{ACCENT_AMBER if mode == 'video' else ACCENT_CYAN};'>"
                f"{'🎬 VIDEO' if mode == 'video' else '📷 IMAGE'}</span>"
            )
            self._load_thumbnail_from_mw()
            self._input.setEnabled(True)
            self._send_btn.setEnabled(True)
            self._finish_btn.setText("✓  Finish")

    def _load_thumbnail_from_url(self, data_url: str):
        self._strip_widget.hide()
        if not data_url:
            return
        try:
            header, b64 = data_url.split(",", 1)
            raw = base64.b64decode(b64)
            pix = QPixmap()
            pix.loadFromData(raw)
            self._thumb_label.setPixmap(
                pix.scaled(700, 280, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            )
        except Exception:
            pass

    def _load_thumbnails_for_video(self, urls: list[str]):
        if not urls:
            return
        # Show first frame as main thumb + strip of all frames
        self._load_thumbnail_from_url(urls[0])
        # Clear old strip
        for lbl in self._strip_labels:
            lbl.deleteLater()
        self._strip_labels.clear()
        # Rebuild strip
        strip_l = self._strip_widget.layout()
        while strip_l.count():
            strip_l.takeAt(0)
        for url in urls:
            lbl = QLabel()
            lbl.setFixedSize(80, 50)
            lbl.setStyleSheet(f"border: 1px solid {BORDER}; border-radius: 4px;")
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl.installEventFilter(self)
            try:
                _, b64 = url.split(",", 1)
                raw = base64.b64decode(b64)
                pix = QPixmap()
                pix.loadFromData(raw)
                lbl._full_pixmap = pix
                lbl.setPixmap(pix.scaled(80, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation))
            except Exception:
                pass
            strip_l.addWidget(lbl)
            self._strip_labels.append(lbl)
        self._strip_widget.show()

    def _load_thumbnail_from_mw(self):
        mode = self.mw.capture_mode
        if mode == "image":
            self._load_thumbnail_from_url(self.mw.media_data_url)
        else:
            self._load_thumbnails_for_video(self.mw.media_data_urls)

    # ── Chat logic ───────────────────────────────────────────────────────────

    def _send(self):
        if self._read_only:
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        self._input.setEnabled(False)
        self._send_btn.setEnabled(False)

        # Build message
        if not self._messages:
            # First message — include the image(s)
            mode = self.mw.capture_mode
            if mode == "image":
                msg = LMStudioClient.build_image_message(self.mw.media_data_url, text)
            else:
                grid_url = getattr(self.mw, "stitched_data_url", "") or self.mw.media_data_urls[0]
                prompt   = f"The attached image is a grid of sequential frames from a video, read from left-to-right, top-to-bottom.\n\n{text}"
                msg = LMStudioClient.build_image_message(grid_url, prompt)
        else:
            msg = {"role": "user", "content": text}

        self._messages.append(msg)
        self._add_bubble("user", text)

        # Kick off LLM worker
        self._current_bot_bubble = self._add_bubble("assistant", "")
        self._worker = _LLMWorker(self._client, list(self._messages), self.mw.selected_model)
        self._worker.token_ready.connect(self._on_token)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_llm_error)
        self._worker.start()

    @Slot(str)
    def _on_token(self, token: str):
        if self._current_bot_bubble:
            self._current_bot_bubble.append_text(token)
            self._scroll_to_bottom()

    @Slot()
    def _on_done(self):
        # Record the full assistant response
        if self._current_bot_bubble:
            full = self._current_bot_bubble._raw_text
            self._current_bot_bubble.render_markdown()
            self._messages.append({"role": "assistant", "content": full})
        self._current_bot_bubble = None
        self._input.setEnabled(not self._read_only)
        self._send_btn.setEnabled(not self._read_only)
        self._input.setFocus()

    @Slot(str)
    def _on_llm_error(self, err: str):
        if self._current_bot_bubble:
            self._current_bot_bubble.set_text(f"⚠  Error: {err}")
            self._current_bot_bubble._text.setStyleSheet(
                f"QTextEdit {{ background: #200010; color: {ERROR_COLOR}; border: 1px solid {ERROR_COLOR};"
                f"border-radius: 10px; padding: 10px 14px; }}"
            )
        self._current_bot_bubble = None
        self._input.setEnabled(True)
        self._send_btn.setEnabled(True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _add_bubble(self, role: str, text: str, as_markdown: bool = False) -> _Bubble:
        bubble = _Bubble(role)
        bubble.set_text(text, as_markdown=as_markdown)
        # Insert before the trailing stretch
        count = self._chat_layout.count()
        self._chat_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def _scroll_to_bottom(self):
        QApplication.processEvents()
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _clear_chat(self):
        # Remove all bubbles
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Finish ────────────────────────────────────────────────────────────────

    def _finish(self):
        if self._read_only:
            self.mw.go_home()
            return
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(1000)
            
        if self._session is not None:
            # Continuing an existing session
            self._session.messages = list(self._messages)
            self.mw.navigate_to(self.mw.SAVE, session=self._session)
            return

        # Package the new session
        mode = self.mw.capture_mode
        session = ChatSession(
            name       = "Untitled",
            media_type = mode,
            media_data = self.mw.media_data_url if mode == "image" else self.mw.media_data_urls,
            model      = self.mw.selected_model,
            messages   = list(self._messages),
        )
        self.mw.navigate_to(self.mw.SAVE, session=session)
