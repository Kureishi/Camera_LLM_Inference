"""
MainWindow — hosts a QStackedWidget for all 7 screens plus the slide-in side panel.

Navigation contract:
    Each screen receives a reference to MainWindow and calls
    self.main_window.navigate_to(SCREEN_ID, **kwargs) to move forward,
    or self.main_window.go_home() to return to Screen 1.

Screen indices:
    0  Screen1_Home
    1  Screen2_Capture
    2  Screen3_Crop
    3  Screen4_ModelSelect
    4  Screen5_Chat
    5  Screen6_Save
    6  Screen7_Done
"""
from __future__ import annotations

from PySide6.QtCore    import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QSizePolicy
)

from camera_llm.styles import MAIN_STYLESHEET


class MainWindow(QMainWindow):

    # ── Screen indices ───────────────────────────────────────────────────────
    HOME           = 0
    CAPTURE        = 1
    CROP           = 2
    MODEL_SELECT   = 3
    CHAT           = 4
    SAVE           = 5
    DONE           = 6

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera → LLM Inference")
        self.resize(1100, 780)
        self.setMinimumSize(900, 640)
        self.setStyleSheet(MAIN_STYLESHEET)

        # ── Shared state (passed between screens via navigate_to) ────────────
        self.capture_mode: str          = "image"   # "image" | "video"
        self.captured_frame             = None       # np.ndarray  (image still)
        self.captured_frames: list      = []         # list[np.ndarray] (video)
        self.media_data_url             = None       # str  (image data-URL)
        self.media_data_urls: list      = []         # list[str] (video data-URLs)
        self.stitched_data_url: str     = ""         # str (video grid data-URL)
        self.selected_model: str        = ""
        self.lm_base_url: str           = "http://localhost:1234/v1"

        # ── Build UI ─────────────────────────────────────────────────────────
        self._root   = QWidget()
        self._layout = QHBoxLayout(self._root)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setCentralWidget(self._root)

        # Lazy import screens to avoid circular dependency at module level
        from camera_llm.screens.screen1_home         import Screen1_Home
        from camera_llm.screens.screen2_capture      import Screen2_Capture
        from camera_llm.screens.screen3_crop         import Screen3_Crop
        from camera_llm.screens.screen4_model_select import Screen4_ModelSelect
        from camera_llm.screens.screen5_chat         import Screen5_Chat
        from camera_llm.screens.screen6_save         import Screen6_Save
        from camera_llm.screens.screen7_done         import Screen7_Done

        self.screen1 = Screen1_Home(self)
        self.screen2 = Screen2_Capture(self)
        self.screen3 = Screen3_Crop(self)
        self.screen4 = Screen4_ModelSelect(self)
        self.screen5 = Screen5_Chat(self)
        self.screen6 = Screen6_Save(self)
        self.screen7 = Screen7_Done(self)

        self._stack = QStackedWidget()
        for screen in [
            self.screen1, self.screen2, self.screen3, self.screen4,
            self.screen5, self.screen6, self.screen7,
        ]:
            self._stack.addWidget(screen)

        self._layout.addWidget(self._stack)
        self.navigate_to(self.HOME)

    # ── Navigation ───────────────────────────────────────────────────────────

    def navigate_to(self, screen_index: int, **kwargs) -> None:
        """Switch to the given screen and call its on_enter(**kwargs) hook."""
        self._stack.setCurrentIndex(screen_index)
        screen = self._stack.currentWidget()
        if hasattr(screen, "on_enter"):
            screen.on_enter(**kwargs)

    def go_home(self) -> None:
        """Return to Screen 1 and refresh the saved-chats side panel."""
        self.screen1.refresh_side_panel()
        self._stack.setCurrentIndex(self.HOME)
