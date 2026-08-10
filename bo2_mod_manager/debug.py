"""Crash diagnostics: step logging, faulthandler and uncaught-exception dump.

Everything lands in bo2mm_debug.log next to the app. If the app hard-crashes,
the last logged step tells us exactly where it stopped."""

import os
import sys

from .config import APP_DIR

DEBUG_FILE = None


def log_debug(msg):
    if DEBUG_FILE is None:
        return
    try:
        import time
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def setup_diagnostics():
    """Reset the debug log and arm faulthandler + an excepthook that writes
    tracebacks into the same file. Safe to call once from main()."""
    global DEBUG_FILE
    DEBUG_FILE = os.path.join(APP_DIR, "bo2mm_debug.log")
    try:
        open(DEBUG_FILE, "w").close()
    except Exception:
        DEBUG_FILE = None
        return

    try:
        import faulthandler
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            faulthandler.enable(file=f)

        def _excepthook(etype, evalue, tb):
            import traceback
            with open(DEBUG_FILE, "a", encoding="utf-8") as f:
                f.write("=== UNCAUGHT EXCEPTION ===\n")
                traceback.print_exception(etype, evalue, tb, file=f)
            sys.__excepthook__(etype, evalue, tb)

        sys.excepthook = _excepthook
    except Exception:
        pass
