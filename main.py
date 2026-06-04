"""
Camera → LLM Inference App
Entry point — creates the QApplication, applies the dark theme, and shows the MainWindow.

Usage:
    python main.py
"""
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui     import QFont, QIcon
from PySide6.QtCore    import Qt

from app.main_window import MainWindow


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Camera LLM Inference")
    app.setOrganizationName("CameraLLM")

    # Set default font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    # Apply dark theme via pyqtdarktheme as a base, then layer our custom stylesheet
    try:
        import qdarktheme
        base_sheet = qdarktheme.load_stylesheet("dark")
        app.setStyleSheet(base_sheet)
    except (ImportError, Exception):
        pass  # Our MAIN_STYLESHEET in styles.py covers everything standalone

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
