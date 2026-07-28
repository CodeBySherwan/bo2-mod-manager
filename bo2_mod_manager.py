import os
import shutil
import sys
import configparser
import subprocess
from string import Template

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QFileDialog, QStatusBar, QFrame, QMessageBox, QGraphicsOpacityEffect,
    QToolTip, QStackedWidget, QTextBrowser, QButtonGroup, QMenu,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QTimer
from PyQt6.QtGui import QColor, QPixmap, QFont, QIcon, QImage


VERSION = "2.0"

ICON_B64 = """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
"""


THEMES = {
    "black_ops": {
        "label": "BLACK OPS II",
        "bg":            "#0a0a0a",
        "bg_panel":      "#0f0f0f",
        "bg_card":       "#141414",
        "accent":        "#e87a20",
        "accent_dim":    "#8a3a0a",
        "accent_bright": "#ff9a3a",
        "text":          "#b0a090",
        "text_dim":      "#6a5a4a",
        "text_faint":    "#3a3020",
        "border":        "#2a1a0a",
        "border_bright": "#e87a20",
        "success":       "#4a9a5a",
        "success_bright":"#6ad07a",
        "success_bg":    "#0d1a0a",
        "success_border":"#1a3a10",
        "danger":        "#cc3333",
        "danger_bright": "#ff5555",
        "danger_bg":     "#1a0a0a",
        "danger_border": "#3a1515",
    },
    "cold_war": {
        "label": "COLD WAR",
        "bg":            "#0a0a0c",
        "bg_panel":      "#0f0f12",
        "bg_card":       "#141416",
        "accent":        "#d4432a",
        "accent_dim":    "#7a2318",
        "accent_bright": "#ff5a3a",
        "text":          "#a8a0a0",
        "text_dim":      "#5c5458",
        "text_faint":    "#3a3438",
        "border":        "#3a1a1a",
        "border_bright": "#d4432a",
        "success":       "#3d8a6e",
        "success_bright":"#5dcc9e",
        "success_bg":    "#0d1f18",
        "success_border":"#1a4a38",
        "danger":        "#c9522a",
        "danger_bright": "#ff7844",
        "danger_bg":     "#1f120a",
        "danger_border": "#5a2a15",
    },
    "modern_warfare": {
        "label": "MODERN WARFARE",
        "bg":            "#0a0c08",
        "bg_panel":      "#10140e",
        "bg_card":       "#141814",
        "accent":        "#5a8a3a",
        "accent_dim":    "#2a4a1a",
        "accent_bright": "#78ba44",
        "text":          "#9aa08a",
        "text_dim":      "#5a6050",
        "text_faint":    "#3a4030",
        "border":        "#1a2218",
        "border_bright": "#5a8a3a",
        "success":       "#4a9a5a",
        "success_bright":"#6ac97a",
        "success_bg":    "#0d1f0a",
        "success_border":"#1a4a18",
        "danger":        "#c9522a",
        "danger_bright": "#e8703a",
        "danger_bg":     "#1f0f0a",
        "danger_border": "#5a2a15",
    },
    "classified": {
        "label": "CLASSIFIED",
        "bg":            "#000000",
        "bg_panel":      "#050008",
        "bg_card":       "#0a0010",
        "accent":        "#cc0000",
        "accent_dim":    "#550000",
        "accent_bright": "#ff2222",
        "text":          "#cc2222",
        "text_dim":      "#660011",
        "text_faint":    "#330008",
        "border":        "#1a0008",
        "border_bright": "#cc0000",
        "success":       "#cc2222",
        "success_bright":"#ff4444",
        "success_bg":    "#1a0000",
        "success_border":"#3a0000",
        "danger":        "#ff0000",
        "danger_bright": "#ff6666",
        "danger_bg":     "#1a0000",
        "danger_border": "#4a0000",
    },
    "light_ops": {
        "label": "LIGHT OPS",
        "bg":            "#e8e4dc",
        "bg_panel":      "#efebe3",
        "bg_card":       "#f4f0e8",
        "accent":        "#c47a20",
        "accent_dim":    "#9a6018",
        "accent_bright": "#e89030",
        "text":          "#1a1814",
        "text_dim":      "#5a5448",
        "text_faint":    "#8a8478",
        "border":        "#c8c0b4",
        "border_bright": "#c47a20",
        "success":       "#3a8a4a",
        "success_bright":"#5ab86a",
        "success_bg":    "#d8f0dc",
        "success_border":"#8ac894",
        "danger":        "#cc3333",
        "danger_bright": "#e86060",
        "danger_bg":     "#f0d8d8",
        "danger_border": "#d48a8a",
    },
}

THEME_ORDER = ["black_ops", "modern_warfare", "cold_war", "classified", "light_ops"]
DEFAULT_THEME = "black_ops"


TEMPLATE = """
QMainWindow, QWidget {
    background-color: $bg;
    color: $text;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QWidget#header {
    background-color: $bg_panel;
    border-bottom: 1px solid $border;
}

QLabel#titleMain {
    color: $accent_bright;
    font-size: 20px;
    font-weight: bold;
    font-family: 'Impact', 'Arial Black', sans-serif;
    letter-spacing: 2px;
}

QLabel#titleSub {
    color: $text_dim;
    font-size: 10px;
    letter-spacing: 3px;
    font-weight: bold;
}

QLabel#themeName {
    color: $accent;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
}

QLabel#sectionLabel {
    color: $text_dim;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 2px;
    background-color: $bg_panel;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 2px 6px;
}

QWidget#pathSection {
    background-color: $bg;
    border-bottom: 1px solid $border;
}

QPushButton#pathBtn {
    padding: 3px 10px;
    font-size: 10px;
    letter-spacing: 1px;
    min-height: 22px;
}

QLineEdit {
    background-color: $bg_card;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 3px 6px;
    color: $text_dim;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    selection-background-color: $accent_dim;
}
QLineEdit:focus {
    border: 1px solid $accent_dim;
}

QWidget#previewPanel {
    background-color: $bg_panel;
    border-left: 1px solid $border;
}

QLabel#previewLabel {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 4px;
}

QWidget#descPanel {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: 2px;
}

QTextBrowser {
    background-color: transparent;
    color: $text;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    border: none;
    padding: 6px;
}

QPushButton#tabBtn {
    background-color: $bg_panel;
    border: 1px solid $border;
    border-bottom: none;
    border-radius: 2px 2px 0 0;
    padding: 5px 16px;
    color: $text_dim;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
    min-height: 20px;
}
QPushButton#tabBtn:hover {
    background-color: $bg_card;
    color: $text;
}
QPushButton#tabBtn:checked {
    background-color: $bg;
    border-color: $accent_dim;
    color: $accent;
    border-bottom: 2px solid $accent;
}

QPushButton#favBtn {
    padding: 4px 10px;
    font-size: 11px;
    letter-spacing: 1px;
    min-height: 22px;
}
QPushButton#favBtn:checked {
    background-color: $accent_dim;
    border-color: $accent;
    color: $accent_bright;
}

QListWidget {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 2px;
    outline: none;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
    color: $text;
}
QListWidget::item {
    padding: 5px 8px;
    border-bottom: 1px solid $bg_panel;
    border-radius: 2px;
}
QListWidget::item:hover {
    background-color: $bg_card;
    color: $accent;
}
QListWidget::item:selected {
    background-color: $accent_dim;
    color: $accent_bright;
    border-left: 2px solid $accent;
}

QPushButton {
    background-color: $bg_card;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 5px 12px;
    color: $text;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
}
QPushButton:hover {
    background-color: $accent_dim;
    border-color: $accent;
    color: $accent_bright;
}
QPushButton:pressed {
    background-color: $bg;
}
QPushButton:disabled {
    color: $text_faint;
    border-color: $border;
    background-color: $bg_panel;
}

QPushButton#deployBtn {
    background-color: $success_bg;
    border: 1px solid $success_border;
    color: $success;
    font-size: 12px;
    letter-spacing: 2px;
    padding: 7px 14px;
}
QPushButton#deployBtn:hover {
    background-color: $success_border;
    border-color: $success_bright;
    color: $success_bright;
}
QPushButton#deployBtn:disabled {
    background-color: $bg_panel;
    border-color: $border;
    color: $text_faint;
}

QPushButton#resetBtn {
    background-color: $danger_bg;
    border: 1px solid $danger_border;
    color: $danger;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 7px 10px;
}
QPushButton#resetBtn:hover {
    background-color: $danger_border;
    border-color: $danger_bright;
    color: $danger_bright;
}
QPushButton#resetBtn:disabled {
    background-color: $bg_panel;
    border-color: $border;
    color: $text_faint;
}

QPushButton#launchBtn {
    background-color: $bg;
    border: 2px solid $accent_dim;
    color: $accent_bright;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 4px;
    padding: 8px 40px;
    border-radius: 2px;
    min-width: 280px;
}
QPushButton#launchBtn:hover {
    background-color: $accent_dim;
    border-color: $accent;
}
QPushButton#launchBtn:pressed {
    background-color: $bg;
    border-color: $accent_bright;
}
QPushButton#launchBtn:disabled {
    background-color: $bg_panel;
    border-color: $border;
    color: $text_faint;
}

QPushButton#swatchBtn {
    border-radius: 3px;
    padding: 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
    border: 2px solid transparent;
}
QPushButton#swatchBtn[active="true"] {
    border: 2px solid $text;
}

QFrame#divider {
    background-color: $border;
    max-height: 1px;
}
QFrame#vdivider {
    background-color: $border;
    max-width: 1px;
}

QWidget#launchSection {
    background-color: $bg_panel;
    border-top: 1px solid $border;
}

QStatusBar {
    background-color: $bg;
    color: $text_dim;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10px;
    border-top: 1px solid $border;
}

QScrollBar:vertical {
    background: $bg;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: $border;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: $accent_dim;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal { height: 0; }

QToolTip {
    background-color: $bg_card;
    color: $accent;
    border: 1px solid $accent_dim;
    padding: 4px 6px;
    font-size: 11px;
}
"""


def build_stylesheet(theme_id: str) -> str:
    tokens = THEMES.get(theme_id, THEMES[DEFAULT_THEME])
    return Template(TEMPLATE).substitute(tokens)


class BO2ModManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mymods_dir = ""
        self.t6_root = ""
        self.game_exe = ""
        self.active_mp = "NONE"
        self.active_zm = "NONE"
        self.theme_id = DEFAULT_THEME
        self.ignore_folders = {"raw", "zone", "main", "players", "scripts", "images"}
        if getattr(sys, "frozen", False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.app_dir, "bo2mm_config.ini")
        self.favorites = {"mp": set(), "zm": set()}
        self.show_favs_only = False
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

    def _build_ui(self):
        self.setWindowTitle("BO2 MOD MANAGER")
        self.setFixedSize(900, 780)

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

    def _build_path_section(self):
        section = QWidget()
        section.setObjectName("pathSection")
        section.setFixedHeight(68)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(14, 3, 14, 3)
        layout.setSpacing(4)

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
        self.exe_input.setPlaceholderText("Path...")
        self.exe_input.setReadOnly(True)
        btn4 = QPushButton("BROWSE")
        btn4.setObjectName("pathBtn")
        btn4.clicked.connect(self._browse_exe)
        row2.addWidget(lbl3)
        row2.addWidget(self.exe_input, 1)
        row2.addWidget(btn4)
        layout.addLayout(row2)

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
        layout.addStretch()

        self.launch_btn = QPushButton("\u25a0  LAUNCH  BLACK  OPS  II")
        self.launch_btn.setObjectName("launchBtn")
        self.launch_btn.clicked.connect(self._launch_game)
        self.launch_btn.setEnabled(False)
        layout.addWidget(self.launch_btn)
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
                self.launch_btn.setEnabled(True)
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
            "active_mp": self.active_mp,
            "active_zm": self.active_zm,
        }
        cfg["UI"] = {"theme": self.theme_id}
        cfg["Favorites"] = {
            "mp": ",".join(sorted(self.favorites["mp"])),
            "zm": ",".join(sorted(self.favorites["zm"])),
        }
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

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Game Executable", "C:/",
            "Executables (*.exe);;All Files (*)"
        )
        if path and os.path.isfile(path):
            self.game_exe = path
            self.exe_input.setText(path)
            self.launch_btn.setEnabled(True)
            self._save_config()
            self.status.showMessage(f"EXE SET  //  {os.path.basename(path)}", 4000)

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

    def _launch_game(self):
        if not self.game_exe or not os.path.isfile(self.game_exe):
            QMessageBox.warning(
                self, "EXE NOT FOUND",
                "Game executable path is invalid.\nBrowse and select it again.",
            )
            return
        try:
            exe_dir = os.path.dirname(self.game_exe)
            subprocess.Popen([self.game_exe], cwd=exe_dir)
            self.status.showMessage(
                f"LAUNCHING  //  {os.path.basename(self.game_exe)}  //  GOOD LUCK SOLDIER", 6000
            )
        except Exception as e:
            QMessageBox.critical(self, "LAUNCH FAILED", str(e))


if __name__ == "__main__":
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    app = QApplication(sys.argv)
    win = BO2ModManager()
    win.show()
    sys.exit(app.exec())
