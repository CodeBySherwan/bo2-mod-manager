"""BO2ModManager: the main application window (scan, preview, deploy, launch)."""

import os
import shutil
import subprocess
import configparser

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QLineEdit, QFileDialog,
    QStatusBar, QFrame, QMessageBox, QGraphicsOpacityEffect,
    QStackedWidget, QTextBrowser, QButtonGroup, QMenu, QDialog,
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup,
)
from PyQt6.QtGui import QColor, QPixmap, QIcon

from .config import APP_DIR, CONFIG_FILE
from .constants import ICON_B64
from .debug import log_debug
from .fetch_dialog import FetchFromWebDialog
from .themes import THEMES, THEME_ORDER, DEFAULT_THEME, build_stylesheet


class BO2ModManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mymods_dir = ""
        self.t6_root = ""
        self.game_exe = ""
        self.bo2_game_dir = ""
        self.username = ""
        self.active_mp = "NONE"
        self.active_zm = "NONE"
        self.theme_id = DEFAULT_THEME
        self.ignore_folders = {"raw", "zone", "main", "players", "scripts", "images"}
        self.app_dir = APP_DIR
        self.config_file = CONFIG_FILE
        self.favorites = {"mp": set(), "zm": set()}
        self.show_favs_only = False
        self._fetch_dialog = None
        self._swatch_buttons = {}
        self._flash_anims = {}

        self._build_ui()
        self._set_window_icon()
        self._load_config()

    def _set_window_icon(self):
        try:
            import base64
            data = base64.b64decode(ICON_B64)
            pix = QPixmap()
            pix.loadFromData(data)
            self.setWindowIcon(QIcon(pix))
        except Exception:
            pass

    # ── UI BUILD ─────────────────────────────────────────────────────

    def _apply_window_geometry(self):
        """Size/position the window to fit within the visible screen area
        (i.e. never overlap the taskbar), while staying resizable so the
        user can shrink it further on smaller displays."""
        NATURAL_W, NATURAL_H = 900, 860
        MIN_W, MIN_H = 720, 620

        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None

        if avail:
            margin = 20
            width = min(NATURAL_W, avail.width() - margin)
            height = min(NATURAL_H, avail.height() - margin)
            width = max(width, MIN_W)
            height = max(height, MIN_H)
            self.setMinimumSize(min(MIN_W, width), min(MIN_H, height))
            self.resize(width, height)
            x = avail.x() + (avail.width() - width) // 2
            y = avail.y() + (avail.height() - height) // 2
            self.move(x, y)
        else:
            self.setMinimumSize(MIN_W, MIN_H)
            self.resize(NATURAL_W, NATURAL_H)

    def _build_ui(self):
        self.setWindowTitle("BO2 MOD MANAGER")
        self._apply_window_geometry()

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_header())
        main_layout.addWidget(self._build_path_section())

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(div)

        main_layout.addWidget(self._build_content(), 1)
        main_layout.addWidget(self._build_launch_bar())

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("SYSTEM READY  //  SELECT MYMODS DIRECTORY TO BEGIN")

        self._set_panels_enabled(False)

    def _build_header(self):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(50)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        t1 = QLabel("BLACK OPS II")
        t1.setObjectName("titleMain")
        t2 = QLabel("MOD MANAGER")
        t2.setObjectName("titleSub")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        hl.addLayout(title_col)
        hl.addStretch()

        for theme_id in THEME_ORDER:
            tokens = THEMES[theme_id]
            swatch = QPushButton()
            swatch.setObjectName("swatchBtn")
            swatch.setProperty("active", "false")
            swatch.setCursor(Qt.CursorShape.PointingHandCursor)
            swatch.setToolTip(tokens["label"])
            swatch_color = "#ffffff" if theme_id == "light_ops" else tokens["accent"]
            swatch.setStyleSheet(
                f"background-color: {swatch_color};"
                f"border-radius: 3px; border: 2px solid transparent;"
            )
            swatch.clicked.connect(lambda _, tid=theme_id: self._apply_theme(tid, True))
            self._swatch_buttons[theme_id] = swatch
            hl.addWidget(swatch)

        hl.addSpacing(8)
        self.theme_name_lbl = QLabel("")
        self.theme_name_lbl.setObjectName("themeName")
        hl.addWidget(self.theme_name_lbl)

        return header

    def _build_stacked_field(self, label_text, placeholder="", browse_handler=None,
                              readonly=True, editing_finished=None):
        """Label-above-input field block, e.g. 'Black Ops II folder' over an input+Browse row."""
        container = QVBoxLayout()
        container.setSpacing(3)

        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        container.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(6)
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setReadOnly(readonly)
        if editing_finished:
            field.editingFinished.connect(editing_finished)
        row.addWidget(field, 1)
        if browse_handler:
            btn = QPushButton("BROWSE")
            btn.setObjectName("pathBtn")
            btn.clicked.connect(browse_handler)
            row.addWidget(btn)
        container.addLayout(row)

        return container, field

    def _build_path_section(self):
        section = QWidget()
        section.setObjectName("pathSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(14, 6, 14, 8)
        layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        g1 = QHBoxLayout()
        g1.setSpacing(3)
        lbl1 = QLabel("MYMODS")
        lbl1.setObjectName("sectionLabel")
        self.mymods_input = QLineEdit()
        self.mymods_input.setPlaceholderText("Path...")
        self.mymods_input.setReadOnly(True)
        btn1 = QPushButton("BROWSE")
        btn1.setObjectName("pathBtn")
        btn1.clicked.connect(self._browse_mymods)
        g1.addWidget(lbl1)
        g1.addWidget(self.mymods_input, 1)
        g1.addWidget(btn1)
        row1.addLayout(g1, 1)

        g2 = QHBoxLayout()
        g2.setSpacing(3)
        lbl2 = QLabel("T6")
        lbl2.setObjectName("sectionLabel")
        self.t6_input = QLineEdit()
        self.t6_input.setPlaceholderText("Path...")
        self.t6_input.setReadOnly(True)
        btn2 = QPushButton("BROWSE")
        btn2.setObjectName("pathBtn")
        btn2.clicked.connect(self._browse_t6)
        btn3 = QPushButton("DET")
        btn3.setObjectName("pathBtn")
        btn3.setFixedWidth(40)
        btn3.setToolTip("Auto-detect Plutonium T6 installation")
        btn3.clicked.connect(self._auto_detect_t6)
        g2.addWidget(lbl2)
        g2.addWidget(self.t6_input, 1)
        g2.addWidget(btn2)
        g2.addWidget(btn3)
        row1.addLayout(g2, 1)

        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(3)
        lbl3 = QLabel("EXE")
        lbl3.setObjectName("sectionLabel")
        self.exe_input = QLineEdit()
        self.exe_input.setPlaceholderText("Plutonium's normal online launcher exe (plutonium-launcher-win32.exe)...")
        self.exe_input.setReadOnly(True)
        btn4 = QPushButton("BROWSE")
        btn4.setObjectName("pathBtn")
        btn4.clicked.connect(self._browse_exe)
        btn4b = QPushButton("DET")
        btn4b.setObjectName("pathBtn")
        btn4b.setFixedWidth(40)
        btn4b.setToolTip("Auto-detect Plutonium's online launcher exe")
        btn4b.clicked.connect(self._auto_detect_exe)
        row2.addWidget(lbl3)
        row2.addWidget(self.exe_input, 1)
        row2.addWidget(btn4)
        row2.addWidget(btn4b)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(14)

        bo2_stack, self.bo2dir_input = self._build_stacked_field(
            "Black Ops II folder",
            placeholder="Path to Black Ops II install (contains zone/all/base.ipak)...",
            browse_handler=self._browse_bo2dir,
        )
        row3.addLayout(bo2_stack, 2)

        user_stack, self.username_input = self._build_stacked_field(
            "Username",
            placeholder="In-game name...",
            readonly=False,
            editing_finished=self._on_username_changed,
        )
        row3.addLayout(user_stack, 1)

        layout.addLayout(row3)

        return section

    def _build_content(self):
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        mods = self._build_mods_panel()
        layout.addWidget(mods, 3)

        vdiv = QFrame()
        vdiv.setObjectName("vdivider")
        vdiv.setFrameShape(QFrame.Shape.VLine)
        layout.addWidget(vdiv)

        preview = self._build_preview_panel()
        layout.addWidget(preview, 2)

        return content

    def _build_preview_panel(self):
        panel = QWidget()
        panel.setObjectName("previewPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        preview_frame = QLabel()
        preview_frame.setObjectName("previewLabel")
        preview_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_frame.setText("NO MOD SELECTED")
        preview_frame.setMinimumHeight(100)
        self.preview_label = preview_frame
        layout.addWidget(self.preview_label, 3)

        fetch_row = QHBoxLayout()
        fetch_row.setContentsMargins(0, 0, 0, 0)
        fetch_row.setSpacing(6)
        fetch_row.addStretch()
        self.fetch_web_btn = QPushButton("\u2b07  FETCH FROM WEB")
        self.fetch_web_btn.setObjectName("fetchWebBtn")
        self.fetch_web_btn.setEnabled(False)
        self.fetch_web_btn.clicked.connect(self._open_fetch_dialog)
        fetch_row.addWidget(self.fetch_web_btn)
        layout.addLayout(fetch_row)

        desc_frame = QWidget()
        desc_frame.setObjectName("descPanel")
        desc_layout = QVBoxLayout(desc_frame)
        desc_layout.setContentsMargins(0, 0, 0, 0)

        desc_browser = QTextBrowser()
        desc_browser.setPlaceholderText("No description available")
        self.desc_browser = desc_browser
        desc_layout.addWidget(desc_browser)

        layout.addWidget(desc_frame, 2)

        return panel

    def _build_mods_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        tab_row = QHBoxLayout()
        tab_row.setSpacing(3)

        self.mp_tab_btn = QPushButton("  MP  ")
        self.mp_tab_btn.setObjectName("tabBtn")
        self.mp_tab_btn.setCheckable(True)
        self.mp_tab_btn.setChecked(True)

        self.zm_tab_btn = QPushButton("  ZM  ")
        self.zm_tab_btn.setObjectName("tabBtn")
        self.zm_tab_btn.setCheckable(True)

        self.tab_group = QButtonGroup()
        self.tab_group.addButton(self.mp_tab_btn, 0)
        self.tab_group.addButton(self.zm_tab_btn, 1)
        self.tab_group.setExclusive(True)
        self.tab_group.idToggled.connect(self._switch_tab)

        self.fav_toggle_btn = QPushButton("\u2605  FAVS")
        self.fav_toggle_btn.setObjectName("favBtn")
        self.fav_toggle_btn.setCheckable(True)
        self.fav_toggle_btn.toggled.connect(self._toggle_fav_view)

        tab_row.addWidget(self.mp_tab_btn)
        tab_row.addWidget(self.zm_tab_btn)
        tab_row.addStretch()
        tab_row.addWidget(self.fav_toggle_btn)

        layout.addLayout(tab_row)

        self.mod_stack = QStackedWidget()

        self.mp_list = QListWidget()
        self.mp_list.itemClicked.connect(lambda item: self._on_mod_selected(item, "mp"))

        self.zm_list = QListWidget()
        self.zm_list.itemClicked.connect(lambda item: self._on_mod_selected(item, "zm"))

        self.mod_stack.addWidget(self.mp_list)
        self.mod_stack.addWidget(self.zm_list)
        layout.addWidget(self.mod_stack, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.deploy_btn = QPushButton("\u25b6  DEPLOY MOD")
        self.deploy_btn.setObjectName("deployBtn")
        self.deploy_btn.clicked.connect(self._deploy_current)

        self.reset_btn = QPushButton("\u2715  RESET")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self._reset_current)

        btn_row.addWidget(self.deploy_btn, 1)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        self.mp_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.mp_list.customContextMenuRequested.connect(self._show_fav_context_menu)
        self.zm_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.zm_list.customContextMenuRequested.connect(self._show_fav_context_menu)

        return panel

    def _build_launch_bar(self):
        bar = QWidget()
        bar.setObjectName("launchSection")
        bar.setFixedHeight(54)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(14)
        layout.addStretch()

        self.mp_launch_btn = QPushButton("\u25a0  MULTIPLAYER")
        self.mp_launch_btn.setObjectName("launchBtn")
        self.mp_launch_btn.clicked.connect(lambda: self._launch_game("mp"))
        self.mp_launch_btn.setEnabled(False)
        layout.addWidget(self.mp_launch_btn)

        self.zm_launch_btn = QPushButton("\u25a0  ZOMBIES")
        self.zm_launch_btn.setObjectName("launchBtn")
        self.zm_launch_btn.clicked.connect(lambda: self._launch_game("zm"))
        self.zm_launch_btn.setEnabled(False)
        layout.addWidget(self.zm_launch_btn)

        layout.addStretch()

        return bar

    # ── THEME ─────────────────────────────────────────────────────────

    def _apply_theme(self, theme_id: str, user_action: bool = False):
        if theme_id not in THEMES:
            theme_id = DEFAULT_THEME
        self.theme_id = theme_id
        self.setStyleSheet(build_stylesheet(theme_id))

        for tid, btn in self._swatch_buttons.items():
            btn.setProperty("active", "true" if tid == theme_id else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.theme_name_lbl.setText(THEMES[theme_id]["label"])
        self._highlight_active()

        if user_action:
            self._save_config()
            self.status.showMessage(f"THEME SET  //  {THEMES[theme_id]['label']}", 3000)

    # ── STATE HELPERS ─────────────────────────────────────────────────

    def _set_panels_enabled(self, enabled: bool):
        self.deploy_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)

    def _flash_widget(self, widget):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(120)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.25)
        fade_out.setEasingCurve(QEasingCurve.Type.OutQuad)
        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(220)
        fade_in.setStartValue(0.25)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InQuad)
        group = QSequentialAnimationGroup(widget)
        group.addAnimation(fade_out)
        group.addAnimation(fade_in)
        self._flash_anims[id(widget)] = group
        group.start()

    def _current_mode(self) -> str:
        return "zm" if self.zm_tab_btn.isChecked() else "mp"

    def _current_list(self):
        return self.zm_list if self._current_mode() == "zm" else self.mp_list

    # ── CONFIG ────────────────────────────────────────────────────────

    def _load_config(self):
        cfg = configparser.ConfigParser()
        cfg.read(self.config_file)
        if "Paths" in cfg:
            mods_dir = cfg["Paths"].get("mymods_dir", "")
            t6_dir = cfg["Paths"].get("t6_root", "")
            exe_path = cfg["Paths"].get("game_exe", "")
            bo2dir_path = cfg["Paths"].get("bo2_game_dir", "")
            username = cfg["Paths"].get("username", "")
            self.active_mp = cfg["Paths"].get("active_mp", "NONE")
            self.active_zm = cfg["Paths"].get("active_zm", "NONE")
            if os.path.isdir(mods_dir):
                self.mymods_dir = mods_dir
                self.mymods_input.setText(mods_dir)
            if os.path.isdir(t6_dir):
                self.t6_root = t6_dir
                self.t6_input.setText(t6_dir)
            if os.path.isfile(exe_path):
                self.game_exe = exe_path
                self.exe_input.setText(exe_path)
            if os.path.isfile(os.path.join(bo2dir_path, "zone", "all", "base.ipak")):
                self.bo2_game_dir = bo2dir_path
                self.bo2dir_input.setText(bo2dir_path)
            if username:
                self.username = username
                self.username_input.setText(username)
            self._update_launch_enabled()
            if self.mymods_dir and self.t6_root:
                self._scan_mods()
                self._set_panels_enabled(True)

        if "Favorites" in cfg:
            mp_favs = cfg["Favorites"].get("mp", "")
            zm_favs = cfg["Favorites"].get("zm", "")
            self.favorites["mp"] = set(f.strip() for f in mp_favs.split(",") if f.strip())
            self.favorites["zm"] = set(f.strip() for f in zm_favs.split(",") if f.strip())

        theme_id = DEFAULT_THEME
        if "UI" in cfg:
            theme_id = cfg["UI"].get("theme", DEFAULT_THEME)
        self._apply_theme(theme_id)

    def _save_config(self):
        cfg = configparser.ConfigParser()
        cfg["Paths"] = {
            "mymods_dir": self.mymods_dir,
            "t6_root": self.t6_root,
            "game_exe": self.game_exe,
            "bo2_game_dir": self.bo2_game_dir,
            "username": self.username,
            "active_mp": self.active_mp,
            "active_zm": self.active_zm,
        }
        cfg["UI"] = {"theme": self.theme_id}
        cfg["Favorites"] = {
            "mp": ",".join(sorted(self.favorites["mp"])),
            "zm": ",".join(sorted(self.favorites["zm"])),
        }
        # Carry over a user-edited [WebEngine] section (Chromium flags)
        # so it survives our rewrite of the config file.
        try:
            old = configparser.ConfigParser()
            old.read(self.config_file)
            if "WebEngine" in old:
                cfg["WebEngine"] = dict(old["WebEngine"])
        except Exception:
            pass
        with open(self.config_file, "w") as f:
            cfg.write(f)

    # ── PATH ──────────────────────────────────────────────────────────

    def _browse_mymods(self):
        path = QFileDialog.getExistingDirectory(self, "Select Your Mymods Folder")
        if path:
            self.mymods_dir = path
            self.mymods_input.setText(path)
            self._try_enable()

    def _browse_t6(self):
        path = QFileDialog.getExistingDirectory(self, "Select Plutonium T6 Root")
        if path:
            self.t6_root = path
            self.t6_input.setText(path)
            self._try_enable()

    def _auto_detect_t6(self):
        users_dir = "C:/Users"
        if not os.path.exists(users_dir):
            self.status.showMessage("AUTO-DETECT  //  C:\\Users NOT FOUND")
            return
        for user in os.listdir(users_dir):
            candidate = os.path.join(users_dir, user, "AppData", "Local",
                                     "Plutonium", "storage", "t6")
            if os.path.isdir(candidate):
                self.t6_root = candidate
                self.t6_input.setText(candidate)
                self.status.showMessage(f"AUTO-DETECTED  //  {candidate}", 5000)
                self._try_enable()
                return
        self.status.showMessage("AUTO-DETECT FAILED  //  BROWSE MANUALLY")

    def _auto_detect_exe(self):
        users_dir = "C:/Users"
        if not os.path.exists(users_dir):
            self.status.showMessage("AUTO-DETECT  //  C:\\Users NOT FOUND")
            return
        for user in os.listdir(users_dir):
            candidate = os.path.join(users_dir, user, "AppData", "Local",
                                     "Plutonium", "bin", "plutonium-launcher-win32.exe")
            if os.path.isfile(candidate):
                self.game_exe = candidate
                self.exe_input.setText(candidate)
                self.status.showMessage(f"AUTO-DETECTED  //  {candidate}", 5000)
                self._save_config()
                self._update_launch_enabled()
                return
        self.status.showMessage("AUTO-DETECT FAILED  //  BROWSE MANUALLY")

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Game Executable", "C:/",
            "Executables (*.exe);;All Files (*)"
        )
        if path and os.path.isfile(path):
            self.game_exe = path
            self.exe_input.setText(path)
            self._save_config()
            self._update_launch_enabled()
            self.status.showMessage(f"EXE SET  //  {os.path.basename(path)}", 4000)

    def _browse_bo2dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Black Ops II Install Folder")
        if not path:
            return
        if not os.path.isfile(os.path.join(path, "zone", "all", "base.ipak")):
            QMessageBox.warning(
                self, "INVALID BO2 FOLDER",
                "That folder does not contain valid Black Ops II game data\n"
                "(missing zone/all/base.ipak).",
            )
            return
        self.bo2_game_dir = path
        self.bo2dir_input.setText(path)
        self._save_config()
        self._update_launch_enabled()
        self.status.showMessage(f"BO2 DIR SET  //  {path}", 4000)

    def _on_username_changed(self):
        self.username = self.username_input.text().strip()
        self._save_config()
        self._update_launch_enabled()

    def _update_launch_enabled(self):
        ready = bool(
            self.game_exe and os.path.isfile(self.game_exe)
            and self.bo2_game_dir and os.path.isfile(os.path.join(self.bo2_game_dir, "zone", "all", "base.ipak"))
            and self.username.strip()
        )
        self.mp_launch_btn.setEnabled(ready)
        self.zm_launch_btn.setEnabled(ready)

    def _try_enable(self):
        if self.mymods_dir and self.t6_root:
            self._scan_mods()
            self._set_panels_enabled(True)
            self._save_config()

    # ── TABS ──────────────────────────────────────────────────────────

    def _switch_tab(self, tab_id: int, checked: bool):
        if not checked:
            return
        self.mod_stack.setCurrentIndex(tab_id)
        self.fav_toggle_btn.setChecked(False)
        self.show_favs_only = False
        self._scan_mods()
        current_list = self._current_list()
        selected = current_list.selectedItems()
        if selected:
            self._update_preview(selected[0].data(Qt.ItemDataRole.UserRole))
        else:
            self._clear_preview()

    # ── FAVORITES ─────────────────────────────────────────────────────

    def _toggle_fav_view(self, checked: bool):
        self.show_favs_only = checked
        self._scan_mods()

    def _toggle_favorite(self, mode: str, mod_name: str):
        if mod_name in self.favorites[mode]:
            self.favorites[mode].discard(mod_name)
        else:
            self.favorites[mode].add(mod_name)
        self._save_config()
        self._scan_mods()

    def _show_fav_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)
        if not item:
            return
        mod_name = item.data(Qt.ItemDataRole.UserRole)
        mode = "zm" if list_widget is self.zm_list else "mp"

        menu = QMenu(self)
        if mod_name in self.favorites[mode]:
            action = menu.addAction("\u2606  Remove from Favorites")
        else:
            action = menu.addAction("\u2605  Add to Favorites")
        action.triggered.connect(lambda: self._toggle_favorite(mode, mod_name))
        menu.exec(list_widget.mapToGlobal(pos))

    # ── SCAN ──────────────────────────────────────────────────────────

    def _scan_mods(self):
        current_lst = self._current_list()
        selected = current_lst.selectedItems()
        last_selected = selected[0].data(Qt.ItemDataRole.UserRole) if selected else None

        self.mp_list.clear()
        self.zm_list.clear()

        if not os.path.isdir(self.mymods_dir):
            self._clear_preview()
            return

        mods_mp = []
        mods_zm = []

        for folder_name in sorted(os.listdir(self.mymods_dir)):
            full = os.path.join(self.mymods_dir, folder_name)
            if not os.path.isdir(full) or folder_name.lower() in self.ignore_folders:
                continue
            scripts = os.path.join(full, "scripts")
            has_mp = os.path.isdir(os.path.join(scripts, "mp"))
            has_zm = os.path.isdir(os.path.join(scripts, "zm"))

            if has_mp:
                mods_mp.append(folder_name)
            if has_zm:
                mods_zm.append(folder_name)

        self._populate_list(self.mp_list, mods_mp, "mp")
        self._populate_list(self.zm_list, mods_zm, "zm")

        self._highlight_active()

        if last_selected:
            for i in range(current_lst.count()):
                if current_lst.item(i).data(Qt.ItemDataRole.UserRole) == last_selected:
                    current_lst.setCurrentRow(i)
                    break

        self._update_preview_for_selection()
        self.status.showMessage(
            f"SCAN COMPLETE  //  {self.mp_list.count()} MP  |  "
            f"{self.zm_list.count()} ZM  MODS DETECTED"
        )

    def _populate_list(self, list_widget, mod_names: list, mode: str):
        favs = []
        others = []
        for name in mod_names:
            if self.show_favs_only and name not in self.favorites[mode]:
                continue
            if name in self.favorites[mode]:
                favs.append(name)
            else:
                others.append(name)

        favs.sort()
        others.sort()

        for name in favs + others:
            is_fav = name in self.favorites[mode]
            display = f"\u2605  {name}" if is_fav else f"   {name}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, name)
            list_widget.addItem(item)

    def _highlight_active(self):
        accent = QColor(THEMES[self.theme_id]["accent_bright"])
        normal = QColor(THEMES[self.theme_id]["text"])
        fav_color = QColor(THEMES[self.theme_id]["accent"])

        for lst, active in [(self.mp_list, self.active_mp), (self.zm_list, self.active_zm)]:
            for i in range(lst.count()):
                item = lst.item(i)
                name = item.data(Qt.ItemDataRole.UserRole)
                display = item.text()
                is_fav = display.startswith("\u2605")

                if name == active:
                    item.setText(f"\u25b6 {name}  [ACTIVE]")
                    item.setForeground(accent)
                elif is_fav:
                    item.setText(f"\u2605  {name}")
                    item.setForeground(fav_color)
                else:
                    item.setText(f"   {name}")
                    item.setForeground(normal)

    # ── PREVIEW / DESCRIPTION ──────────────────────────────────────────

    def _clear_preview(self):
        self.preview_label.setText("NO MOD SELECTED")
        self.preview_label.setPixmap(QPixmap())
        self.desc_browser.clear()
        self.fetch_web_btn.setEnabled(False)

    def _update_preview_for_selection(self):
        lst = self._current_list()
        sel = lst.selectedItems()
        if sel:
            self._update_preview(sel[0].data(Qt.ItemDataRole.UserRole))
        else:
            self._clear_preview()

    def _on_mod_selected(self, item, mode: str):
        mod_name = item.data(Qt.ItemDataRole.UserRole)
        self._update_preview(mod_name)

    def _update_preview(self, mod_name: str):
        if not mod_name or not self.mymods_dir:
            self._clear_preview()
            return

        mod_path = os.path.join(self.mymods_dir, mod_name)
        if not os.path.isdir(mod_path):
            self._clear_preview()
            return

        # A real mod folder is selected: the fetch-from-web button is usable.
        self.fetch_web_btn.setEnabled(True)

        preview_path = os.path.join(mod_path, "Preview.png")
        if os.path.isfile(preview_path):
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    max(self.preview_label.width() - 8, 1),
                    max(self.preview_label.height() - 8, 1),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
            else:
                self.preview_label.setText(f"  {mod_name}\n(Preview.png: invalid)")
        else:
            self.preview_label.setText(f"  {mod_name}\n(no Preview.png)")

        readme_path = os.path.join(mod_path, "readme.txt")
        if not os.path.isfile(readme_path):
            readme_path = os.path.join(mod_path, "README.txt")
        if os.path.isfile(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.desc_browser.setPlainText(content)
            except Exception:
                self.desc_browser.setPlainText("(Error reading readme.txt)")
        else:
            self.desc_browser.clear()

    # ── FETCH FROM WEB ───────────────────────────────────────────────

    def _open_fetch_dialog(self):
        lst = self._current_list()
        selected = lst.selectedItems()
        if not selected or not self.mymods_dir:
            self.status.showMessage("SELECT A MOD FIRST  //  THEN FETCH FROM WEB")
            return
        mod_name = selected[0].data(Qt.ItemDataRole.UserRole)
        mod_path = os.path.join(self.mymods_dir, mod_name)
        if not os.path.isdir(mod_path):
            self.status.showMessage("MOD FOLDER MISSING  //  CANNOT SAVE")
            return

        # IMPORTANT: open() not exec(). On some Windows machines, showing a
        # QWebEngineView inside a dialog running a *modal exec() loop makes
        # the loop die spuriously (exec() returns Rejected while the dialog
        # is still visible and usable), which leaves the dialog in a broken
        # state and hard-crashes the app during teardown. open() shows the
        # same window-modal dialog without running a nested event loop, and
        # the finished() signal reports the result instead.
        dialog = FetchFromWebDialog(mod_name, mod_path, self)
        self._fetch_dialog = dialog
        dialog.finished.connect(
            lambda r, d=dialog, n=mod_name: self._on_fetch_done(d, r, n))
        log_debug("open_fetch_dialog: open() start")
        dialog.open()
        log_debug("open_fetch_dialog: open() returned")

    def _on_fetch_done(self, dialog, result, mod_name):
        log_debug(f"fetch finished: {int(result)}")
        if self._fetch_dialog is dialog:
            self._fetch_dialog = None
        if result == QDialog.DialogCode.Accepted:
            # Refresh preview so the newly saved Preview.png + readme.txt show.
            self._update_preview(mod_name)
            self._flash_widget(self.preview_label)
            self.status.showMessage(
                f"FETCHED  //  {mod_name}  //  PREVIEW + DESCRIPTION SAVED",
                5000)

    # ── DEPLOY / RESET ───────────────────────────────────────────────

    def _deploy_current(self):
        mode = self._current_mode()
        lst = self._current_list()
        selected = lst.selectedItems()
        if not selected:
            self.status.showMessage(f"SELECT A {mode.upper()} MOD FIRST")
            return

        mod_name = selected[0].data(Qt.ItemDataRole.UserRole)
        mod_path = os.path.join(self.mymods_dir, mod_name)
        dest_scripts = os.path.join(self.t6_root, "scripts", mode)
        dest_images = os.path.join(self.t6_root, "images")
        src_scripts = os.path.join(mod_path, "scripts", mode)
        src_images = os.path.join(mod_path, "images")

        try:
            if os.path.isdir(dest_scripts):
                shutil.rmtree(dest_scripts)
            if os.path.isdir(src_scripts):
                shutil.copytree(src_scripts, dest_scripts)

            if os.path.isdir(src_images):
                os.makedirs(dest_images, exist_ok=True)
                for item in os.listdir(src_images):
                    s = os.path.join(src_images, item)
                    d = os.path.join(dest_images, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)

            if mode == "mp":
                self.active_mp = mod_name
            else:
                self.active_zm = mod_name

            self._save_config()
            self._highlight_active()
            self._flash_widget(self.deploy_btn)
            self.status.showMessage(f"DEPLOYED  //  {mode.upper()}  \u25b6  {mod_name}  //  READY TO LAUNCH")

        except Exception as e:
            QMessageBox.critical(self, "DEPLOY FAILED", str(e))
            self.status.showMessage(f"ERROR  //  {str(e)[:80]}")

    def _reset_current(self):
        mode = self._current_mode()
        reply = QMessageBox.question(
            self, "CONFIRM RESET",
            f"Remove all {mode.upper()} mod files from T6 root?\nThis restores stock/vanilla.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        dest_scripts = os.path.join(self.t6_root, "scripts", mode)
        try:
            if os.path.isdir(dest_scripts):
                shutil.rmtree(dest_scripts)

            if mode == "mp":
                self.active_mp = "NONE"
            else:
                self.active_zm = "NONE"

            self._save_config()
            self._highlight_active()
            self._flash_widget(self.reset_btn)
            self.status.showMessage(f"RESET COMPLETE  //  {mode.upper()}  RESTORED TO STOCK")

        except Exception as e:
            QMessageBox.critical(self, "RESET FAILED", str(e))

    # ── LAUNCH ────────────────────────────────────────────────────────

    def _launch_game(self, mode: str):
        if not self.game_exe or not os.path.isfile(self.game_exe):
            QMessageBox.warning(
                self, "EXE NOT FOUND",
                "Game executable path is invalid.\nBrowse and select it again.",
            )
            return
        if not self.bo2_game_dir or not os.path.isfile(os.path.join(self.bo2_game_dir, "zone", "all", "base.ipak")):
            QMessageBox.warning(
                self, "BO2 FOLDER NOT FOUND",
                "Black Ops II install folder is invalid.\nBrowse and select it again.",
            )
            return
        if not self.username.strip():
            QMessageBox.warning(self, "NAME REQUIRED", "Enter an in-game name before launching.")
            return

        plutonium_root = os.path.dirname(os.path.dirname(self.game_exe))
        bootstrapper = os.path.join(plutonium_root, "bin", "plutonium-bootstrapper-win32.exe")
        if not os.path.isfile(bootstrapper):
            QMessageBox.critical(
                self, "BOOTSTRAPPER NOT FOUND",
                f"Could not find:\n{bootstrapper}\n\nCheck your EXE path is inside a valid Plutonium install.",
            )
            return

        mode_id = "t6zm" if mode == "zm" else "t6mp"

        try:
            subprocess.Popen(
                [bootstrapper, mode_id, self.bo2_game_dir, "+name", self.username, "-lan"],
                cwd=plutonium_root,
            )
            self.status.showMessage(
                f"LAUNCHING OFFLINE  //  {mode_id.upper()}  //  {self.username}  //  GOOD LUCK SOLDIER", 6000
            )
        except Exception as e:
            QMessageBox.critical(self, "LAUNCH FAILED", str(e))

    def closeEvent(self, event):
        log_debug("main window closeEvent")
        super().closeEvent(event)
