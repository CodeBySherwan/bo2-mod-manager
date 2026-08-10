"""Embedded-browser plumbing for the Cloudflare-challenge fetch, backed by
pywebview running in a dedicated subprocess.

Why the switch: QtWebEngine bundles a private copy of Chromium into the app
(~190MB on Windows, since it ships the whole browser engine as part of the
build). pywebview's Windows backend ("edgechromium") instead drives the Edge
WebView2 runtime, which already ships with Windows 10/11 as a shared OS
component -- the app itself goes back to a normal-sized PyQt6 build, nothing
extra bundled.

Threading model (this is the part that actually matters here):
  - pywebview's webview.start() MUST run on a process's *main* thread; calling
    it from a background thread raises "pywebview must be run on a main
    thread." Qt already owns this process's main thread (app.exec()), so the
    two GUI loops cannot share it. Instead a separate *browser subprocess*
    (see webview_server.py) runs webview.start() on its own main thread; this
    process talks to it with newline-delimited JSON over stdin/stdout.
  - A single pywebview window is created once (hidden) in the subprocess and
    reused for every fetch, mirroring the old "one shared QWebEngineView for
    the app's lifetime" approach.
  - Each fetch runs on a short-lived QThread worker. Its window calls
    (load_url / evaluate_js / show / hide) are synchronous blocking round-trips
    over the pipe, so they must never run on the Qt GUI thread (would freeze
    the UI while polling). Results cross back into Qt via signals, which PyQt
    marshals onto the GUI thread automatically.
"""

import json
import queue
import subprocess
import sys
import threading
import time

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from .debug import log_debug

try:
    import webview
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

_CF_TITLE_MARKERS = ("Just a moment", "Attention Required")
_POLL_INTERVAL_S = 2.0
# 4 minutes: the Cloudflare check can sit pending for a while (user must spot
# and click the checkbox / wait for an auto-check), and the first fetch of a
# session is slow (cold WebView2 + no cookies yet). The live countdown lets
# the user close early; a too-short window is what produced "page was loaded
# but the app gave up" failures.
_POLL_TIMEOUT_S = 240.0
# The child bounds evaluate_js at _EVAL_TIMEOUT_S; these are the parent-side
# ceilings for its state/extraction reads (slightly larger, since the child
# times out first and replies with an error).
_STATE_READ_TIMEOUT_S = 12.0
_EXTRACT_READ_TIMEOUT_S = 12.0
# One round-trip per poll: title, document ready state and current URL so the
# CF loop can tell "mid-navigation" (empty/None, rs=loading) from a genuinely
# cleared page instead of relying on title alone.
_STATE_JS = ("JSON.stringify({t: document.title, rs: document.readyState, "
             "u: location.href})")
_CMD_TIMEOUT_S = 120.0
_START_TIMEOUT_S = 20.0
_EXTRACT_ATTEMPTS = 8
_EXTRACT_RETRY_DELAY_S = 0.5


def _child_args():
    """Command line for the browser subprocess. When frozen with PyInstaller
    the only interpreter available is the exe itself, so it is re-launched
    with a flag that routes it into webview_server.main (see app.py)."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--webview-server"]
    return [sys.executable, "-m", "bo2_mod_manager.webview_server"]


class _WindowProxy:
    """Thread-safe stand-in for a pywebview Window that talks to the browser
    subprocess. Exactly one command is in flight at a time (guarded by a
    write lock); replies are matched back by id from the reader thread."""

    def __init__(self):
        self._proc = None
        self._stdin = None
        self._stdout = None
        self._write_lock = threading.Lock()
        self._pending = {}
        self._pending_lock = threading.Lock()
        self._next_id = 0
        self._ready = threading.Event()
        self._start_error = None
        self._loaded_q = queue.Queue()

    def start(self):
        try:
            self._proc = subprocess.Popen(
                _child_args(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            raise RuntimeError(f"could not start browser subprocess: {e}")
        self._stdin = self._proc.stdin
        self._stdout = self._proc.stdout
        threading.Thread(target=self._reader_loop,
                         args=(self._proc.stdout,), daemon=True).start()
        if not self._ready.wait(timeout=_START_TIMEOUT_S):
            raise RuntimeError(self._start_error or
                               "browser subprocess did not start in time")

    def _reader_loop(self, stdout):
        for raw in stdout:
            raw = raw.strip()
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if "id" in msg:
                with self._pending_lock:
                    evt = self._pending.pop(msg["id"], None)
                if evt is not None:
                    evt["msg"] = msg
                    evt["done"].set()
            elif msg.get("event") == "ready":
                self._ready.set()
            elif msg.get("event") == "start_failed":
                self._start_error = msg.get("error", "browser failed to start")
                self._ready.set()
            elif msg.get("event") == "loaded":
                # A top-level page load/reload finished in the child (fires on
                # every navigation, including Cloudflare's post-challenge
                # reload). Lets the CF loop react to completed loads instead
                # of polling blind while a navigation is still in flight.
                self._loaded_q.put(msg)
        # EOF: the subprocess is gone. Fail anything still in flight.
        with self._pending_lock:
            for evt in self._pending.values():
                evt["msg"] = {"id": evt["id"], "ok": False,
                              "error": "browser subprocess closed"}
                evt["done"].set()
            self._pending.clear()

    def _request(self, cmd, timeout=None, **kwargs):
        if self._proc is None or self._proc.poll() is not None:
            raise RuntimeError("browser subprocess is not running")
        with self._write_lock:
            self._next_id += 1
            cid = self._next_id
            payload = {"id": cid, "cmd": cmd}
            payload.update(kwargs)
            try:
                self._stdin.write((json.dumps(payload) + "\n").encode("utf-8"))
                self._stdin.flush()
            except Exception as e:
                raise RuntimeError(f"could not send command to browser: {e}")
            evt = {"id": cid, "msg": None, "done": threading.Event()}
            with self._pending_lock:
                self._pending[cid] = evt
            if not evt["done"].wait(timeout=timeout or _CMD_TIMEOUT_S):
                with self._pending_lock:
                    self._pending.pop(cid, None)
                raise RuntimeError(f"browser command timed out ({cmd})")
            msg = evt["msg"]
            if not msg.get("ok"):
                raise RuntimeError(msg.get("error", "browser command failed"))
            return msg.get("result")

    # -- window API (mirrors the pywebview calls the old worker made) --

    def load_url(self, url):
        self._request("load_url", url=url)

    def evaluate_js(self, script, timeout=None):
        return self._request("evaluate_js", timeout=timeout, script=script)

    def clear_loaded(self):
        """Drop any stale 'loaded' events left over from a previous fetch so
        the next CF loop only reacts to loads of the page it is fetching."""
        while True:
            try:
                self._loaded_q.get_nowait()
            except queue.Empty:
                return

    def wait_loaded(self, timeout):
        """Block up to `timeout` seconds for the browser to finish loading a
        page. Returns the 'loaded' event dict, or None on timeout."""
        try:
            return self._loaded_q.get(timeout=timeout)
        except queue.Empty:
            return None

    def show(self):
        self._request("show")

    def hide(self):
        self._request("hide")

    def close(self):
        """Best-effort shutdown: nudge the child to quit, then hard-kill if
        it doesn't. Never waits on the write lock (a fetch may still be in
        flight); the child tears itself down on stdin EOF anyway."""
        try:
            if self._proc is not None and self._proc.poll() is None:
                self._stdin.write(b'{"cmd": "quit"}\n')
                self._stdin.flush()
        except Exception:
            pass
        try:
            if self._proc is not None:
                self._proc.wait(timeout=3)
        except Exception:
            pass
        try:
            if self._proc is not None and self._proc.poll() is None:
                self._proc.terminate()
        except Exception:
            pass
        self._proc = None


class _FetchWorker(QThread):
    """One-shot worker for a single fetch: navigates the shared window,
    polls document.title until Cloudflare clears (or times out), then runs
    the extraction script and emits the raw JSON result."""

    status = pyqtSignal(str)
    finished_ok = pyqtSignal(str)   # raw JSON string from EXTRACT_JS
    failed = pyqtSignal(str)        # human-readable failure reason

    def __init__(self, window, url, extract_js, parent=None):
        super().__init__(parent)
        self._window = window
        self._url = url
        self._extract_js = extract_js

    def run(self):
        try:
            self.status.emit(
                "LOADING PAGE  //  WAIT FOR THE CLOUDFLARE CHECK IF IT "
                "APPEARS...")
            self._window.clear_loaded()
            self._window.load_url(self._url)
            self._window.show()

            def read_state():
                # One round-trip that captures everything we need to diagnose
                # (and react to) the CF flow. Bounded by _STATE_READ_TIMEOUT_S
                # so a pathological hang can't stall the loop. Returns a dict,
                # or None if the read failed.
                try:
                    raw = self._window.evaluate_js(
                        _STATE_JS, timeout=_STATE_READ_TIMEOUT_S)
                except Exception as e:
                    log_debug(f"evaluate_js(state) failed: {e}")
                    return None
                if not isinstance(raw, str) or not raw.strip():
                    return None
                try:
                    return json.loads(raw)
                except Exception:
                    return None

            deadline = time.time() + _POLL_TIMEOUT_S
            cleared = False
            last_state = None
            # Two detection paths so one can't silently fail:
            #   1. The child's 'loaded' event fires when a page finishes
            #      loading, so a Cloudflare reload is caught the moment it
            #      completes (wait_loaded returns at once instead of sleeping).
            #   2. A periodic bounded state read on every loop iteration
            #      catches a clear even if a 'loaded' event is ever missed
            #      (pywebview's bridge-injection run_js can hang on a heavy
            #      page, which delays events.loaded.set()). The read is safe
            #      mid-navigation: the child aborts a hung evaluate_js after
            #      _EVAL_TIMEOUT_S and replies "timed out".
            while time.time() < deadline:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._window.wait_loaded(
                    timeout=min(_POLL_INTERVAL_S, remaining))
                state = read_state()
                if state:
                    last_state = state
                    log_debug("cf state: "
                              f"t={state.get('t')!r} rs={state.get('rs')!r} "
                              f"u={state.get('u')!r}")
                    title = state.get("t") or ""
                    if title and not any(m in title
                                         for m in _CF_TITLE_MARKERS):
                        cleared = True
                        break
                remaining = max(int(deadline - time.time()), 0)
                self.status.emit(
                    "CLOUDFLARE CHECK OPEN  //  CLICK THE VERIFY CHECKBOX "
                    f"IN THE BROWSER IF SHOWN  //  AUTO-CLOSE IN {remaining}s")
            log_debug(f"cf loop done: cleared={cleared} "
                      f"last_state={last_state!r}")

            if not cleared:
                self.failed.emit(
                    "CLOUDFLARE CHECK DID NOT COMPLETE IN TIME  //  PRESS "
                    "FETCH AGAIN OR USE MANUAL MODE")
                return

            self.status.emit("EXTRACTING MOD INFO...")
            # We do NOT wait for the whole page to finish loading: NodeBB
            # server-renders the first post, so the description + image URLs
            # exist well before document.readyState hits "complete". EXTRACT_JS
            # reports ready=true as soon as that content is in the DOM; retry
            # only while it isn't (covers the Cloudflare reload window).
            # Break early once we have actual content; otherwise keep the last
            # ready snapshot so a page with genuinely no images/description
            # still yields something instead of failing.
            result = ""
            for attempt in range(_EXTRACT_ATTEMPTS):
                try:
                    raw = self._window.evaluate_js(
                        self._extract_js, timeout=_EXTRACT_READ_TIMEOUT_S)
                except Exception as e:
                    log_debug(f"evaluate_js(extract) failed: {e}")
                    raw = ""
                if isinstance(raw, str) and raw.strip():
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, dict) and parsed.get("ready"):
                        result = raw
                        if parsed.get("description") or parsed.get("images"):
                            break
                    else:
                        log_debug(f"extraction attempt {attempt + 1}: "
                                  "page content not ready")
                time.sleep(_EXTRACT_RETRY_DELAY_S)
            if not result:
                self.failed.emit(
                    "EXTRACTION FAILED  //  RETRY OR USE MANUAL MODE")
                return
            self.finished_ok.emit(result)
        except Exception as e:
            log_debug(f"fetch worker error: {e}")
            self.failed.emit(f"FETCH FAILED  //  {e}")
        finally:
            # Always put the shared browser window away, no matter which path
            # we took (success, failure or exception).
            try:
                self._window.hide()
            except Exception:
                pass


class FetchEngine(QObject):
    """Owns the single persistent browser subprocess (and its window) for the
    app session and runs fetches against it. Mirrors the old ensure_engine()/
    shared-view pattern so callers' lifecycle assumptions (create once, reuse,
    never destroy mid-session) still hold."""

    status = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._window = None
        self._started = False
        self._worker = None

    def _start_browser(self):
        if self._started:
            return True
        try:
            self._window = _WindowProxy()
            self._window.start()
            self._started = True
            log_debug("browser subprocess ready")
            return True
        except Exception as e:
            log_debug(f"browser subprocess failed to start: {e}")
            self._window = None
            return False

    def fetch(self, url, extract_js):
        if not WEBENGINE_AVAILABLE:
            self.failed.emit("pywebview not installed")
            return
        if not self._start_browser():
            self.failed.emit("Browser engine failed to start")
            return
        # One fetch at a time; a fresh worker per fetch is cheap since the
        # window itself (not the thread) is what's persistent/shared.
        self._worker = _FetchWorker(self._window, url, extract_js, self)
        self._worker.status.connect(self.status)
        self._worker.finished_ok.connect(self.finished_ok)
        self._worker.failed.connect(self.failed)
        self._worker.start()

    def show_window(self):
        window = self._window
        if window is not None:
            try:
                window.show()
            except Exception:
                pass

    def hide(self):
        window = self._window
        if window is not None:
            try:
                window.hide()
            except Exception:
                pass

    def shutdown(self):
        if self._window is not None:
            try:
                self._window.close()
            except Exception:
                pass
            self._window = None
        self._started = False


_ENGINE = None


def ensure_engine():
    """Return the shared FetchEngine, creating it once. None if pywebview
    is missing."""
    global _ENGINE
    if not WEBENGINE_AVAILABLE:
        return None
    if _ENGINE is None:
        _ENGINE = FetchEngine()
        log_debug("pywebview engine created")
    return _ENGINE


def shutdown_engine():
    """Tear the shared engine (and its browser subprocess) down. Called from
    app shutdown so the child process doesn't outlive the parent."""
    global _ENGINE
    if _ENGINE is not None:
        try:
            _ENGINE.shutdown()
        except Exception:
            pass
        _ENGINE = None
