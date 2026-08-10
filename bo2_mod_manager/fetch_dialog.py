"""FetchFromWebDialog: dialog that scrapes a mod's preview image +
description from a (Cloudflare-protected) forum page, via a pywebview
browser window."""

import os

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QWidget, QPlainTextEdit, QSizePolicy,
    QMessageBox, QListWidget, QListWidgetItem, QListView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QUrl, QByteArray, QSize
from PyQt6.QtGui import QPixmap, QIcon, QClipboard
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from .constants import EXTRACT_JS
from .debug import log_debug
from .webengine import WEBENGINE_AVAILABLE, ensure_engine


class FetchFromWebDialog(QDialog):
    """Fetch a mod's preview image + description from its forum page,
    let the user edit both, then save them to the mod folder as
    Preview.png + readme.txt.

    The forum sits behind Cloudflare's interactive challenge, which only
    a *visible* real-browser session can clear (a hidden/offscreen engine
    stays stuck on "Just a moment..."). Clearing it now happens in a
    separate native pywebview window (backed by the shared OS WebView2
    runtime on Windows, not a bundled Chromium) that pops up alongside this
    dialog -- if a Turnstile checkbox appears there, the user clicks it.
    Extraction runs automatically once the page clears; results flow back
    into this dialog via Qt signals. If pywebview is missing or the user
    prefers, manual entry is always available."""

    def __init__(self, mod_name, mod_path, parent=None):
        super().__init__(parent)
        self.mod_name = mod_name
        self.mod_path = mod_path
        self.setWindowTitle("FETCH MOD INFO")
        self.resize(900, 680)
        self.setMinimumSize(720, 560)

        # State
        self.image_urls = []          # ordered list of discovered image URLs
        self.image_index = -1         # currently shown image
        self.image_bytes = {}         # url -> downloaded QByteArray
        self._extracted = False       # has the page yielded usable data?
        self._manual_mode = not WEBENGINE_AVAILABLE
        self._engine = None           # shared FetchEngine, connected while fetching
        self._fetching = False

        self.nam = QNetworkAccessManager(self)
        self._replies = []            # keep refs to in-flight image replies

        self._build_ui()
        if not WEBENGINE_AVAILABLE:
            self._enable_manual_mode(
                "pywebview not installed \u2014 paste the image URL and "
                "description manually.")

    # ── UI ──────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # URL row
        url_row = QHBoxLayout()
        url_row.setSpacing(6)
        url_lbl = QLabel("FORUM URL")
        url_lbl.setObjectName("dialogLabel")
        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlField")
        self.url_input.setPlaceholderText(
            "https://forum.plutonium.pw/topic/... ")
        self.url_input.returnPressed.connect(self._do_fetch)
        self.fetch_btn = QPushButton("FETCH")
        self.fetch_btn.setObjectName("fetchBtn")
        self.fetch_btn.clicked.connect(self._do_fetch)
        self.manual_btn = QPushButton("MANUAL MODE")
        self.manual_btn.clicked.connect(
            lambda: self._enable_manual_mode(""))
        url_row.addWidget(url_lbl)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.fetch_btn)
        url_row.addWidget(self.manual_btn)
        layout.addLayout(url_row)

        # Clipboard pre-fill (most users copy the URL first)
        cb = QApplication.clipboard()
        clip = cb.text(QClipboard.Mode.Clipboard).strip() if cb else ""
        if clip.startswith("http"):
            self.url_input.setText(clip)

        # Status + hint
        self.status_lbl = QLabel("READY  //  PASTE A FORUM URL OR USE CLIPBOARD")
        self.status_lbl.setObjectName("statusLabel")
        layout.addWidget(self.status_lbl)
        self.hint_lbl = QLabel("")
        self.hint_lbl.setObjectName("hintLabel")
        self.hint_lbl.setWordWrap(True)
        self.hint_lbl.hide()
        layout.addWidget(self.hint_lbl)

        # Stacked widget: page 0 = browser, page 1 = edit view.
        self.stack = QStackedWidget()

        # ── Page 0: "browser is open in its own window" status pane ──
        # pywebview owns a real native OS window (WebView2 on Windows), it
        # can't be embedded inside this dialog's layout the way the old
        # QWebEngineView was. A separate window pops up alongside this
        # dialog instead; this page just explains that and lets the user
        # bring it back to front if it gets buried.
        self.browser_page = QWidget()
        bpl = QVBoxLayout(self.browser_page)
        bpl.setContentsMargins(0, 0, 0, 0)
        bpl.setSpacing(4)
        cf_hint = QLabel(
            "A separate browser window has opened. If a Cloudflare "
            "\u201cVerify you are human\u201d box appears there, click it. "
            "Extraction continues automatically once the page loads.")
        cf_hint.setObjectName("hintLabel")
        cf_hint.setWordWrap(True)
        bpl.addWidget(cf_hint)
        self.browser_container = QWidget()
        self.browser_container.setStyleSheet(
            "background-color: #000; border: 1px solid #444;")
        bcl = QVBoxLayout(self.browser_container)
        bcl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bring_front_btn = QPushButton("BRING BROWSER WINDOW TO FRONT")
        self.bring_front_btn.clicked.connect(self._bring_browser_to_front)
        bcl.addWidget(self.bring_front_btn)
        self.browser_container.setMinimumHeight(420)
        bpl.addWidget(self.browser_container, 1)
        self.stack.addWidget(self.browser_page)

        # ── Page 1: edit view (image + description) ──
        self.edit_page = QWidget()
        epl = QVBoxLayout(self.edit_page)
        epl.setContentsMargins(0, 0, 0, 0)
        epl.setSpacing(8)

        columns = QHBoxLayout()
        columns.setSpacing(8)

        # Left: preview image
        img_col = QVBoxLayout()
        img_col.setSpacing(4)
        img_head = QLabel("PREVIEW IMAGE")
        img_head.setObjectName("dialogLabel")
        img_col.addWidget(img_head)
        self.img_label = QLabel("(no image yet)")
        self.img_label.setObjectName("previewImg")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setMinimumSize(300, 220)
        self.img_label.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Expanding)
        img_col.addWidget(self.img_label, 1)
        columns.addLayout(img_col, 3)

        # Right: description editor
        desc_col = QVBoxLayout()
        desc_col.setSpacing(4)
        desc_head = QLabel("DESCRIPTION  (editable)")
        desc_head.setObjectName("dialogLabel")
        desc_col.addWidget(desc_head)
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setObjectName("descEdit")
        self.desc_edit.setPlaceholderText("Mod description will appear here. "
                                          "Edit freely before saving.")
        desc_col.addWidget(self.desc_edit, 1)
        columns.addLayout(desc_col, 4)

        epl.addLayout(columns, 1)

        # Thumbnail bar: every downloaded image becomes a clickable
        # thumbnail; clicking one previews it on the left.
        thumb_row = QHBoxLayout()
        thumb_row.setSpacing(6)
        thumb_lbl = QLabel("IMAGES  (click a thumbnail to preview)")
        thumb_lbl.setObjectName("dialogLabel")
        self.img_pos_lbl = QLabel("0 of 0")
        self.img_pos_lbl.setObjectName("statusLabel")
        thumb_row.addWidget(thumb_lbl)
        thumb_row.addStretch()
        thumb_row.addWidget(self.img_pos_lbl)
        epl.addLayout(thumb_row)

        self.thumb_list = QListWidget()
        self.thumb_list.setObjectName("thumbBar")
        self.thumb_list.setFlow(QListView.Flow.LeftToRight)
        self.thumb_list.setWrapping(False)
        self.thumb_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.thumb_list.setMovement(QListView.Movement.Static)
        self.thumb_list.setIconSize(QSize(96, 64))
        self.thumb_list.setSpacing(6)
        self.thumb_list.setFixedHeight(92)
        self.thumb_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.thumb_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumb_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.thumb_list.currentRowChanged.connect(self._on_thumb_selected)
        epl.addWidget(self.thumb_list)

        # Manual image-URL row (hidden until manual mode)
        self.manual_row = QWidget()
        mrl = QHBoxLayout(self.manual_row)
        mrl.setContentsMargins(0, 0, 0, 0)
        mrl.setSpacing(6)
        mrl_lbl = QLabel("IMAGE URL:")
        mrl_lbl.setObjectName("dialogLabel")
        self.manual_url = QLineEdit()
        self.manual_url.setObjectName("urlField")
        self.manual_url.setPlaceholderText("Paste a direct image URL "
                                           "(ending in .png/.jpg)...")
        self.manual_url.editingFinished.connect(self._load_manual_image)
        mrl.addWidget(mrl_lbl)
        mrl.addWidget(self.manual_url, 1)
        self.manual_row.hide()
        epl.addWidget(self.manual_row)

        self.stack.addWidget(self.edit_page)
        layout.addWidget(self.stack, 1)

        # Buttons
        btn_row = QHBoxLayout()
        self.back_btn = QPushButton("\u25c0  BACK TO BROWSER")
        self.back_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.browser_page))
        btn_row.addWidget(self.back_btn)
        btn_row.addStretch()
        self.save_btn = QPushButton("\u25b6  SAVE TO MOD")
        self.save_btn.setObjectName("deployBtn")
        self.save_btn.clicked.connect(self._save_to_mod)
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        # Start on the edit page; switch to browser when fetching.
        self.stack.setCurrentWidget(self.edit_page)

    # ── FETCH ORCHESTRATION ─────────────────────────────────────────

    def _do_fetch(self):
        url = self.url_input.text().strip()
        if not url or not url.startswith("http"):
            self._set_status("ENTER A VALID URL STARTING WITH http(s)://")
            return
        self._extracted = False
        self._fetching = True
        self.desc_edit.clear()
        self.image_urls = []
        self.image_bytes = {}
        self.image_index = -1
        self.thumb_list.blockSignals(True)
        self.thumb_list.clear()
        self.thumb_list.blockSignals(False)
        self.img_pos_lbl.setText("0 of 0")
        self.hint_lbl.hide()

        if not WEBENGINE_AVAILABLE:
            self._enable_manual_mode("pywebview not installed \u2014 paste "
                                     "the image URL and description manually.")
            self._set_status("MANUAL MODE  //  OPEN THE URL IN YOUR BROWSER "
                             "AND PASTE THE CONTENTS")
            return

        self._set_status("LOADING PAGE  //  CLEAR CLOUDFLARE IF PROMPTED...")
        self.fetch_btn.setEnabled(False)
        self.stack.setCurrentWidget(self.browser_page)
        self._auto_fetch(url)

    def _auto_fetch(self, url):
        # Disconnect any wiring left over from a previous fetch in this
        # dialog; the shared engine (and its browser window) stays alive.
        log_debug(f"auto_fetch start: {url}")
        self._teardown_view()

        engine = ensure_engine()
        if engine is None:
            self._enable_manual_mode(
                "pywebview not installed \u2014 paste the image URL and "
                "description manually.")
            self._set_status("MANUAL MODE  //  OPEN THE URL IN YOUR BROWSER "
                             "AND PASTE THE CONTENTS")
            return

        self._engine = engine
        engine.status.connect(self._set_status)
        engine.finished_ok.connect(self._on_extracted)
        engine.failed.connect(self._on_fetch_failed)
        engine.fetch(url, EXTRACT_JS)
        log_debug("auto_fetch: engine.fetch() dispatched")

    def _bring_browser_to_front(self):
        if self._engine is not None:
            self._engine.show_window()

    def _on_fetch_failed(self, reason):
        if self._extracted:
            return
        self._extracted = True
        self.fetch_btn.setEnabled(True)
        self._set_status(reason)
        self._enable_manual_mode(
            "The browser window did not clear the page in time (or "
            "pywebview hit an error). Open the URL in your own browser, "
            "copy the image URL and description, and paste them here.")

    def _on_extracted(self, data):
        # EXTRACT_JS returns JSON.stringify(...), so this arrives as a
        # *string*, not an object. Accept either form defensively.
        if isinstance(data, str):
            import json as _json
            try:
                data = _json.loads(data)
            except Exception:
                data = None
        if not data or not isinstance(data, dict):
            self._set_status("EXTRACTION FAILED  //  RETRY OR USE MANUAL MODE")
            # Stop retrying on a hard parse failure so we don't loop.
            self._extracted = True
            self.fetch_btn.setEnabled(True)
            return

        self._extracted = True
        self._fetching = False
        self.fetch_btn.setEnabled(True)

        desc = (data.get("description") or "").strip()
        if desc:
            self.desc_edit.setPlainText(desc)
        images = data.get("images") or []

        if images:
            self._set_status(f"GOT {len(images)} IMAGE(S)  //  EDIT IF NEEDED, "
                             f"THEN SAVE")
            self._set_images(images)
        else:
            self._set_status("NO IMAGES FOUND  //  ENTER AN IMAGE URL "
                             "MANUALLY IF NEEDED")
            self._enable_manual_mode("")

        # Switch to the edit view; the browser window itself stays alive
        # (just hidden by the engine) so a re-fetch reuses the cleared
        # session instead of tripping Cloudflare again.
        self.stack.setCurrentWidget(self.edit_page)

    def _teardown_view(self):
        log_debug("teardown_view start")
        engine = self._engine
        self._engine = None  # clear reference first; prevent re-entry
        if engine is None:
            log_debug("teardown_view no engine")
            return
        try:
            engine.status.disconnect(self._set_status)
        except Exception:
            pass
        try:
            engine.finished_ok.disconnect(self._on_extracted)
        except Exception:
            pass
        try:
            engine.failed.disconnect(self._on_fetch_failed)
        except Exception:
            pass
        # Do NOT tear down the pywebview window itself: it's shared and
        # reused for the whole app session (recreating/destroying it mid
        # session is unnecessary churn and was exactly the kind of thing
        # that used to crash the old QWebEngineView). Just hide it.
        engine.hide()
        log_debug("teardown_view done")

    # ── MANUAL MODE ─────────────────────────────────────────────────

    def _enable_manual_mode(self, hint):
        self._manual_mode = True
        self.manual_row.show()
        self.stack.setCurrentWidget(self.edit_page)
        if hint:
            self.hint_lbl.setText(hint)
            self.hint_lbl.show()
        self.fetch_btn.setEnabled(True)
        self._set_status("MANUAL MODE  //  PASTE IMAGE URL + DESCRIPTION")

    def _load_manual_image(self):
        url = self.manual_url.text().strip()
        if not url:
            return
        # Manual mode: treat this single URL as the only image so the
        # standard display/save path works.
        self.image_urls = [url]
        self.image_bytes = {}
        self.image_index = -1
        self.thumb_list.blockSignals(True)
        self.thumb_list.clear()
        item = QListWidgetItem(QIcon(), (url.rsplit("/", 1)[-1] or url)[:40])
        item.setData(Qt.ItemDataRole.UserRole, url)
        item.setToolTip(url)
        self.thumb_list.addItem(item)
        self.thumb_list.blockSignals(False)
        self.img_pos_lbl.setText("0 of 1")
        self._set_status(f"DOWNLOADING IMAGE  //  {url[:60]}")
        self._download_image(url)

    # ── IMAGE DOWNLOAD / DISPLAY ────────────────────────────────────

    def _set_images(self, urls):
        self.image_urls = list(urls)
        self.image_bytes = {}
        self.image_index = -1
        self.thumb_list.blockSignals(True)
        self.thumb_list.clear()
        for u in self.image_urls:
            item = QListWidgetItem(QIcon(), (u.rsplit("/", 1)[-1] or u)[:40])
            item.setData(Qt.ItemDataRole.UserRole, u)
            item.setToolTip(u)
            self.thumb_list.addItem(item)
        self.thumb_list.blockSignals(False)
        self.img_pos_lbl.setText(f"0 of {len(self.image_urls)}")
        # Queue them all; first to arrive becomes the preview.
        for u in self.image_urls:
            self._download_image(u)

    def _download_image(self, url):
        req = QNetworkRequest(QUrl(url))
        req.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader,
                      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "PyQt6-BO2ModManager")
        reply = self.nam.get(req)
        reply.setProperty("url", url)
        self._replies.append(reply)
        reply.finished.connect(lambda r=reply: self._on_image_downloaded(r))

    def _on_image_downloaded(self, reply):
        url = reply.property("url")
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                if data.size() > 0:
                    self.image_bytes[url] = data
                    self._update_thumb(url, data)
                    # If no preview shown yet, show this one.
                    if self.image_index < 0:
                        idx = self.image_urls.index(url) \
                              if url in self.image_urls else 0
                        self._show_image(idx)
                    self._refresh_state()
                    self._set_status(
                        f"IMAGE READY  //  {len(self.image_bytes)} OF "
                        f"{max(len(self.image_urls), len(self.image_bytes))} "
                        f"DOWNLOADED")
        except Exception:
            pass
        finally:
            if reply in self._replies:
                self._replies.remove(reply)
            reply.deleteLater()

    def _update_thumb(self, url, data):
        pix = QPixmap()
        pix.loadFromData(QByteArray(data))
        if pix.isNull():
            return
        icon = QIcon(pix.scaled(
            self.thumb_list.iconSize().width(),
            self.thumb_list.iconSize().height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        self.thumb_list.blockSignals(True)
        for i in range(self.thumb_list.count()):
            item = self.thumb_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == url:
                item.setIcon(icon)
                break
        self.thumb_list.blockSignals(False)

    def _show_image(self, index):
        if index < 0 or index >= len(self.image_urls):
            return
        url = self.image_urls[index]
        data = self.image_bytes.get(url)
        if not data:
            self.img_label.setText("(downloading image...)")
            self.img_label.setPixmap(QPixmap())
            return
        pix = QPixmap()
        pix.loadFromData(QByteArray(data))
        if pix.isNull():
            self.img_label.setText("(invalid image data)")
            self.img_label.setPixmap(QPixmap())
            return
        scaled = pix.scaled(
            max(self.img_label.width() - 12, 1),
            max(self.img_label.height() - 12, 1),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.img_label.setPixmap(scaled)
        self.image_index = index
        self._refresh_state()

    def _on_thumb_selected(self, row):
        if row < 0:
            return
        if row < len(self.image_urls):
            self._show_image(row)

    def _refresh_state(self):
        n = max(len(self.image_urls), len(self.image_bytes))
        cur = self.image_index + 1 if self.image_index >= 0 else 0
        self.img_pos_lbl.setText(f"{cur} of {n}")
        if 0 <= self.image_index < self.thumb_list.count():
            self.thumb_list.blockSignals(True)
            self.thumb_list.setCurrentRow(self.image_index)
            self.thumb_list.blockSignals(False)

    def _set_status(self, msg):
        self.status_lbl.setText(msg)

    # ── RESIZE KEEPS PREVIEW SCALED ─────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_index >= 0:
            self._show_image(self.image_index)

    # ── SAVE ────────────────────────────────────────────────────────

    def _current_image_bytes(self):
        if self.image_index >= 0 and self.image_index < len(self.image_urls):
            url = self.image_urls[self.image_index]
            return self.image_bytes.get(url)
        # Manual mode may have produced a single image.
        if len(self.image_bytes) == 1:
            return next(iter(self.image_bytes.values()))
        return None

    def _save_to_mod(self):
        data = self._current_image_bytes()
        if not data:
            QMessageBox.warning(
                self, "NO IMAGE",
                "No image has been downloaded yet.\n"
                "Fetch a URL or paste an image URL first.")
            return

        pix = QPixmap()
        pix.loadFromData(QByteArray(data))
        if pix.isNull():
            QMessageBox.warning(self, "INVALID IMAGE",
                                "The selected image data could not be read.")
            return

        preview_path = os.path.join(self.mod_path, "Preview.png")
        readme_path = os.path.join(self.mod_path, "readme.txt")

        # Always save as PNG so the preview panel reads it reliably.
        try:
            if not pix.save(preview_path, "PNG"):
                QMessageBox.critical(self, "SAVE FAILED",
                                     f"Could not write:\n{preview_path}")
                return
        except Exception as e:
            QMessageBox.critical(self, "SAVE FAILED", str(e))
            return

        # Save the (possibly edited) description.
        try:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(self.desc_edit.toPlainText())
        except Exception as e:
            QMessageBox.warning(
                self, "README NOT SAVED",
                f"Preview image saved, but the description could not be "
                f"written:\n{e}")
            # Still accept: the image is the important part.

        self._set_status(f"SAVED  //  {preview_path}")
        log_debug("save_to_mod done")
        self.accept()

    # ── CLEANUP ─────────────────────────────────────────────────────

    def done(self, result):
        # All close paths go through done(): SAVE (accept), CANCEL
        # (reject), the X button and ESC. accept()/reject() only hide the
        # dialog, so closeEvent never runs for them \u2014 if the view is
        # still parented here it gets destroyed with the dialog and the
        # WebEngine teardown crashes the app. Detach it before that.
        log_debug(f"done({result}) start")
        self._teardown_view()
        super().done(result)
        log_debug(f"done({result}) end")

    def closeEvent(self, event):
        log_debug("dialog closeEvent")
        self._teardown_view()
        super().closeEvent(event)
