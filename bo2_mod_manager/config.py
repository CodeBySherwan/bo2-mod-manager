"""App paths configuration.

The config file and the debug log always live next to the app so a portable
build stays self-contained: beside the .exe when frozen by PyInstaller, or in
the repo root when running from source (this package's parent directory).

Note: this used to also hold apply_webengine_flags(), which set Chromium
command-line flags (QTWEBENGINE_CHROMIUM_FLAGS) for the old QtWebEngine-based
fetch dialog. That's gone now that the fetch dialog runs on pywebview/WebView2
(see webengine.py) -- WebView2 is a shared OS component with its own update
and configuration story, not a bundled Chromium this app controls flags for.
"""

import os
import sys

# Where the app lives (used for the config + debug log).
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(APP_DIR, "bo2mm_config.ini")
