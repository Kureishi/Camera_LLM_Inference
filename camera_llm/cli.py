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

from camera_llm.main_window import MainWindow

# def get_resource_path(relative_path):
#     """Get path to resource, works for both dev and PyInstaller bundle."""
#     if hasattr(sys, '_MEIPASS'):
#         # PyInstaller extracts files to a temp folder (_MEIPASS) at runtime
#         return os.path.join(sys._MEIPASS, relative_path)
#     return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def run_app():
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

    # Set app-wide icon (affects taskbar, window title bar, etc.)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

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

def cli():
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # Remove 'run' so QApplication doesn't try to parse it
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        run_app()
    else:
        print("Usage: camera-llm run")
        sys.exit(1)

if __name__ == "__main__":
    run_app()
