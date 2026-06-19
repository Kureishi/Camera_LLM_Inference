"""
Screen 4 — Model Selection
Fetches available models from LM Studio and lets the user pick one.
Also exposes the LM Studio base URL for configuration.
"""
from __future__ import annotations

from PySide6.QtCore    import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QSizePolicy, QMessageBox
)

from app.llm_client import LMStudioClient
from app.styles     import (
    ACCENT_CYAN, BG_CARD, BG_PANEL, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_DIM, BORDER, ERROR_COLOR, SUCCESS
)


class _FetchModelsThread(QThread):
    models_ready = Signal(list)
    error        = Signal(str)

    def __init__(self, client: LMStudioClient):
        super().__init__()
        self._client = client

    def run(self):
        try:
            models = self._client.list_models()
            self.models_ready.emit(models)
        except Exception as exc:
            self.error.emit(str(exc))


class Screen4_ModelSelect(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.mw      = main_window
        self._client = LMStudioClient(self.mw.lm_base_url)
        self._fetch_thread: _FetchModelsThread | None = None
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
        title = QLabel("Select LLM Model")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ACCENT_CYAN};")
        top_l.addWidget(title, stretch=1)
        outer.addWidget(top)

        # Content
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        v = QVBoxLayout(content)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(28)
        v.setContentsMargins(60, 40, 60, 40)

        # Server URL group
        url_frame = self._card()
        url_v = QVBoxLayout(url_frame)
        url_v.setSpacing(10)
        url_lbl = QLabel("LM Studio Server URL")
        url_lbl.setObjectName("section")
        url_sub = QLabel("Make sure LM Studio is open and the local server is running.")
        url_sub.setObjectName("subtitle")
        self._url_edit = QLineEdit(self.mw.lm_base_url)
        self._url_edit.setPlaceholderText("http://localhost:1234/v1")
        self._url_edit.returnPressed.connect(self._refresh_models)
        refresh_btn = QPushButton("⟳  Refresh Models")
        refresh_btn.setObjectName("primary")
        refresh_btn.setFixedHeight(40)
        refresh_btn.clicked.connect(self._refresh_models)
        url_v.addWidget(url_lbl)
        url_v.addWidget(url_sub)
        url_v.addWidget(self._url_edit)
        url_v.addWidget(refresh_btn)
        v.addWidget(url_frame)

        # Model selection group
        model_frame = self._card()
        model_v = QVBoxLayout(model_frame)
        model_v.setSpacing(10)
        model_lbl = QLabel("Available Models")
        model_lbl.setObjectName("section")
        self._status_lbl = QLabel("Press Refresh to load models")
        self._status_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(400)
        model_v.addWidget(model_lbl)
        model_v.addWidget(self._status_lbl)
        model_v.addWidget(self._model_combo)
        v.addWidget(model_frame)

        # Proceed button
        self._proceed_btn = QPushButton("Analyse  →")
        self._proceed_btn.setObjectName("primary")
        self._proceed_btn.setFixedHeight(52)
        self._proceed_btn.setFixedWidth(220)
        self._proceed_btn.clicked.connect(self._proceed)
        v.addWidget(self._proceed_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(content, stretch=1)

    def _card(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(
            f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px;"
        )
        w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return w

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        self._url_edit.setText(self.mw.lm_base_url)
        self._refresh_models()

    def _go_back(self):
        self.mw.navigate_to(self.mw.CROP)

    # ── Model loading ────────────────────────────────────────────────────────

    def _refresh_models(self):
        url = self._url_edit.text().strip() or "http://localhost:1234/v1"
        self.mw.lm_base_url = url
        self._client.set_base_url(url)
        self._status_lbl.setText("Connecting…")
        self._status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self._model_combo.clear()
        self._proceed_btn.setEnabled(False)

        if self._fetch_thread and self._fetch_thread.isRunning():
            self._fetch_thread.quit()
            self._fetch_thread.wait(500)

        self._fetch_thread = _FetchModelsThread(self._client)
        self._fetch_thread.models_ready.connect(self._on_models_ready)
        self._fetch_thread.error.connect(self._on_fetch_error)
        self._fetch_thread.start()

    def _on_models_ready(self, models: list):
        self._model_combo.clear()
        if not models:
            self._status_lbl.setText("No models found. Load a model in LM Studio first.")
            self._status_lbl.setStyleSheet(f"color: {ACCENT_AMBER if hasattr(self,'ACCENT_AMBER') else '#ffb347'}; font-size:12px;")
            return
        for m in models:
            self._model_combo.addItem(m)
        self._status_lbl.setText(f"✓  {len(models)} model(s) found")
        self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 12px;")
        self._proceed_btn.setEnabled(True)

    def _on_fetch_error(self, err: str):
        self._status_lbl.setText(f"⚠  {err}")
        self._status_lbl.setStyleSheet(f"color: {ERROR_COLOR}; font-size: 12px;")

    # ── Proceed ──────────────────────────────────────────────────────────────

    def _proceed(self):
        model = self._model_combo.currentText().strip()
        if not model:
            QMessageBox.warning(self, "No Model", "Please select a model first.")
            return
        self.mw.selected_model = model
        self.mw.navigate_to(self.mw.CHAT)
