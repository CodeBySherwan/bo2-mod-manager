"""Browser subprocess that hosts the pywebview window for the fetch dialog.

pywebview insists on running its GUI loop from a process's *main* thread
(``webview.start()`` raises "pywebview must be run on a main thread." otherwise),
but this app's main thread is already spoken for by Qt's ``app.exec()`` -- the
two GUI loops cannot share it. The clean split is:

  * The Qt app runs the main window in this process.
  * This module runs in a *separate* Python process whose main thread is free,
    so ``webview.start()`` works there. The browser window lives its whole
    session in that process.

The parent talks to it over stdin/stdout using newline-delimited JSON:

  -> {"id": 1, "cmd": "load_url",    "url": "https://..."}
  -> {"id": 2, "cmd": "evaluate_js", "script": "document.title"}
  -> {"id": 3, "cmd": "show"}
  -> {"id": 4, "cmd": "hide"}
  -> {"id": 5, "cmd": "quit"}

  <- {"event": "ready"}
  <- {"id": 1, "ok": true}
  <- {"id": 2, "ok": true, "result": "..."}
  <- {"id": 2, "ok": false, "error": "..."}
  <- {"event": "loaded"}      # a page load/reload finished (fires per nav)
  <- {"event": "start_failed", "error": "..."}
  <- {"event": "exited"}

Commands are handled on a background thread; pywebview's Window methods are
thread-safe and marshal onto the GUI thread internally. The single window is
created hidden once and reused for every fetch (mirroring the old "one shared
QWebEngineView" approach).
"""

import json
import sys
import threading

_CMDS = ("load_url", "evaluate_js", "show", "hide", "quit")
_EVAL_TIMEOUT_S = 10


def server_main():
    try:
        import webview
    except Exception as e:
        sys.stdout.write(json.dumps({
            "event": "start_failed",
            "error": f"webview not importable: {e}",
        }) + "\n")
        sys.stdout.flush()
        return

    window = webview.create_window(
        "BO2MM fetch", "about:blank", hidden=True,
        width=1000, height=760,
    )

    # The 'loaded' event fires on every top-level page load/reload (the
    # edgechromium backend injects the pywebview bridge on each
    # NavigationCompleted, which sets window.events.loaded). It is what lets
    # the parent detect Cloudflare's post-challenge reload instead of polling
    # page JS while a navigation is still in flight.
    def _on_loaded():
        _send({"event": "loaded"})

    try:
        window.events.loaded += _on_loaded
    except Exception:
        pass

    # stdout is now written from two places (the command loop thread and the
    # loaded-event handler's thread), so serialise the writes.
    _send_lock = threading.Lock()

    def _send(obj):
        try:
            with _send_lock:
                sys.stdout.write(json.dumps(obj) + "\n")
                sys.stdout.flush()
        except Exception:
            pass

    def _cmd_loop():
        try:
            for raw in sys.stdin:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                cid = msg.get("id")
                cmd = msg.get("cmd")
                if cmd == "quit":
                    try:
                        window.destroy()
                    except Exception:
                        pass
                    _send({"id": cid, "ok": True})
                    break
                if cmd not in _CMDS:
                    _send({"id": cid, "ok": False,
                           "error": f"unknown command: {cmd}"})
                    continue
                try:
                    if cmd == "load_url":
                        window.load_url(msg.get("url") or "about:blank")
                    elif cmd == "evaluate_js":
                        # WebView2's ExecuteScriptAsync can HANG without ever
                        # calling back when a navigation starts while the call
                        # is in flight (exactly what happens when Cloudflare
                        # reloads after the challenge clears). Run it on a
                        # daemon thread and give up after _EVAL_TIMEOUT_S so a
                        # stuck call cannot freeze this command loop (and with
                        # it every later fetch command).
                        script = msg.get("script") or ""
                        box = {}

                        def _run_eval():
                            try:
                                box["result"] = window.evaluate_js(script)
                                box["ok"] = True
                            except Exception as e:
                                box["error"] = str(e)

                        t = threading.Thread(target=_run_eval, daemon=True)
                        t.start()
                        t.join(_EVAL_TIMEOUT_S)
                        if t.is_alive():
                            _send({"id": cid, "ok": False,
                                   "error": "evaluate_js timed out after "
                                            f"{_EVAL_TIMEOUT_S}s"})
                        elif box.get("ok"):
                            _send({"id": cid, "ok": True,
                                   "result": box.get("result")})
                        else:
                            _send({"id": cid, "ok": False,
                                   "error": box.get("error",
                                                   "evaluate_js failed")})
                        continue
                    elif cmd == "show":
                        window.show()
                    elif cmd == "hide":
                        window.hide()
                    _send({"id": cid, "ok": True})
                except Exception as e:
                    _send({"id": cid, "ok": False, "error": str(e)})
        finally:
            # stdin hit EOF (parent died/closed): tear the window down so
            # webview.start() returns and this process exits on its own.
            try:
                window.destroy()
            except Exception:
                pass

    def _on_gui_started():
        # webview.start()'s `func` argument is invoked (on its own thread)
        # only once the GUI loop has actually initialized the native window
        # / WebView2 backend for `window`. That -- not the moment right
        # after create_window() -- is the earliest point it's safe to tell
        # the parent we're ready and start dispatching load_url/evaluate_js
        # against `window`.
        #
        # Previously "ready" was sent (and this loop started) immediately
        # after create_window(), before webview.start() below had run at
        # all. create_window() only *registers* a window; nothing backing
        # it exists until start() creates it. On a cold session the parent
        # would see "ready" and fire load_url() right away, landing on a
        # backend that didn't exist yet -- that first navigation was
        # silently lost, so the Cloudflare-clear poll never saw a real
        # page and timed out with "browser didn't clear the page in time"
        # even though the window itself visibly opened. Pressing Fetch
        # again worked because by then start() had finished initializing
        # the backend from the first (lost) attempt.
        _send({"event": "ready"})
        _cmd_loop()

    try:
        webview.start(_on_gui_started, gui="edgechromium", debug=False)
    except Exception as e:
        _send({"event": "start_failed", "error": str(e)})
        return
    _send({"event": "exited"})


if __name__ == "__main__":
    server_main()
