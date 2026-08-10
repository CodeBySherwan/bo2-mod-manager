"""Application entry point: builds the QApplication and runs the main window."""

import os
import sys

from .debug import setup_diagnostics, log_debug
from .webengine import WEBENGINE_AVAILABLE


def main():
    # The browser subprocess re-launches the frozen exe with this flag (see
    # webengine._child_args) so the child's *main* thread is free for
    # pywebview.start(). Must be checked before anything Qt/UI related.
    if "--webview-server" in sys.argv:
        from .webview_server import server_main
        server_main()
        return

    # Crash diagnostics: every lifecycle step + any fatal traceback lands in
    # bo2mm_debug.log next to the app. Handy even after the console is gone.
    setup_diagnostics()
    log_debug(f"webengine available: {WEBENGINE_AVAILABLE}")

    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.FreeConsole()

    from PyQt6.QtWidgets import QApplication
    from .main_window import BO2ModManager

    app = QApplication(sys.argv)
    win = BO2ModManager()
    win.show()
    log_debug("app started")
    try:
        rc = app.exec()
    finally:
        log_debug("app.exec returned, QApplication shutting down")
        from .webengine import shutdown_engine
        shutdown_engine()
    sys.exit(rc)
