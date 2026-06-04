"""
Global stylesheet and design tokens for the Camera LLM Inference App.
Deep-space dark theme with electric cyan and amber accents.
"""

# ── Colour palette ──────────────────────────────────────────────
BG_DEEP       = "#0d0f14"
BG_PANEL      = "#13161e"
BG_CARD       = "#1a1e2a"
BG_INPUT      = "#1f2333"
ACCENT_CYAN   = "#00d4ff"
ACCENT_CYAN2  = "#0099bb"
ACCENT_AMBER  = "#ffb347"
ACCENT_AMBER2 = "#cc8a2a"
TEXT_PRIMARY  = "#e8eaf0"
TEXT_SECONDARY= "#7a8299"
TEXT_DIM      = "#424860"
BORDER        = "#262b3d"
BORDER_ACTIVE = "#00d4ff"
SUCCESS       = "#4cff91"
ERROR_COLOR   = "#ff4f6b"
USER_BUBBLE   = "#0a3340"
BOT_BUBBLE    = "#1a1e2a"

MAIN_STYLESHEET = f"""
/* ── Application root ─────────────────────────────────────── */
QWidget {{
    background-color: {BG_DEEP};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    font-size: 14px;
}}

QMainWindow {{
    background-color: {BG_DEEP};
}}

/* ── Scroll areas ──────────────────────────────────────────── */
QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {TEXT_DIM};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_CYAN};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {BG_PANEL};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {TEXT_DIM};
    border-radius: 3px;
}}

/* ── Buttons ───────────────────────────────────────────────── */
QPushButton {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #222840;
    border: 1px solid {ACCENT_CYAN};
    color: {ACCENT_CYAN};
}}
QPushButton:pressed {{
    background-color: #0a1520;
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
    border-color: {TEXT_DIM};
}}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #005577, stop:1 #007799);
    border: 1px solid {ACCENT_CYAN};
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #006688, stop:1 #0099bb);
    border: 1px solid #55eeff;
    color: #55eeff;
}}

QPushButton#danger {{
    background: #2a0a0f;
    border: 1px solid {ERROR_COLOR};
    color: {ERROR_COLOR};
}}
QPushButton#danger:hover {{
    background: #3a0a14;
    color: #ff7f8f;
    border-color: #ff7f8f;
}}

QPushButton#amber {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #553300, stop:1 #7a4a00);
    border: 1px solid {ACCENT_AMBER};
    color: {ACCENT_AMBER};
    font-size: 15px;
    font-weight: 700;
}}
QPushButton#amber:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #664400, stop:1 #995500);
    border: 1px solid #ffd080;
    color: #ffd080;
}}

QPushButton#record {{
    background: #3a0a0a;
    border: 2px solid {ERROR_COLOR};
    color: {ERROR_COLOR};
    border-radius: 24px;
    min-width: 48px; min-height: 48px;
    max-width: 48px; max-height: 48px;
    font-size: 18px;
}}
QPushButton#record:hover {{
    background: #500f0f;
}}

/* ── Labels ────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {TEXT_PRIMARY};
}}
QLabel#title {{
    font-size: 28px;
    font-weight: 700;
    color: {ACCENT_CYAN};
    letter-spacing: 1px;
}}
QLabel#subtitle {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
}}
QLabel#section {{
    font-size: 16px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}
QLabel#camera_feed {{
    background: #050709;
    border: 2px solid {BORDER};
    border-radius: 12px;
}}
QLabel#tag {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 2px 8px;
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}

/* ── Text inputs ───────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    selection-background-color: {ACCENT_CYAN2};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {ACCENT_CYAN};
    background-color: #1a2233;
}}

/* ── ComboBox ─────────────────────────────────────────────── */
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 14px;
    min-width: 200px;
}}
QComboBox:focus, QComboBox:on {{
    border: 1px solid {ACCENT_CYAN};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {ACCENT_CYAN};
    width: 0; height: 0;
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_ACTIVE};
    selection-background-color: {ACCENT_CYAN2};
    color: {TEXT_PRIMARY};
    border-radius: 6px;
    outline: none;
}}

/* ── Frame / Group dividers ───────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {BORDER};
}}

/* ── Splitter ─────────────────────────────────────────────── */
QSplitter::handle {{
    background: {BORDER};
}}

/* ── Side panel list ──────────────────────────────────────── */
QListWidget {{
    background: {BG_PANEL};
    border: none;
    border-right: 1px solid {BORDER};
    outline: none;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-radius: 6px;
    color: {TEXT_SECONDARY};
    margin: 2px 4px;
}}
QListWidget::item:hover {{
    background: {BG_CARD};
    color: {TEXT_PRIMARY};
}}
QListWidget::item:selected {{
    background: #0a2030;
    color: {ACCENT_CYAN};
    border-left: 3px solid {ACCENT_CYAN};
}}

/* ── Slider (recording timer) ─────────────────────────────── */
QProgressBar {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_CYAN}, stop:1 {ACCENT_CYAN2});
    border-radius: 4px;
}}

/* ── Tool tips ────────────────────────────────────────────── */
QToolTip {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_ACTIVE};
    border-radius: 6px;
    padding: 6px 10px;
}}
"""

# Big hero button style for Screen 1
def hero_button_style(accent: str, glow: str) -> str:
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a1e2a, stop:1 #13161e);
            border: 2px solid {accent};
            border-radius: 20px;
            color: {accent};
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 1px;
            min-width: 220px;
            min-height: 130px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #202840, stop:1 #151820);
            border: 2px solid {glow};
            color: {glow};
        }}
        QPushButton:pressed {{
            background: #0a0d14;
        }}
    """
"""
"""
