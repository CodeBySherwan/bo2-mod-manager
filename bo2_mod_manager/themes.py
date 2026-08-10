"""Theme token sets + the shared QSS template that renders them."""

from string import Template

THEMES = {
    "black_ops": {
        "label": "BLACK OPS II",
        "bg":            "#1c1a17",
        "bg_panel":      "#211f1b",
        "bg_card":       "#27241f",
        "accent":        "#d9822b",
        "accent_dim":    "#7a4a1e",
        "accent_bright": "#f0a050",
        "text":          "#c9beac",
        "text_dim":      "#8a8071",
        "text_faint":    "#5c574a",
        "border":        "#3a352c",
        "border_bright": "#d9822b",
        "success":       "#6b9d6e",
        "success_bright":"#8cc290",
        "success_bg":    "#1c2a1d",
        "success_border":"#33472f",
        "danger":        "#c05c4a",
        "danger_bright": "#e0806a",
        "danger_bg":     "#2a1c18",
        "danger_border": "#4a2e26",
    },
    "cold_war": {
        "label": "COLD WAR",
        "bg":            "#17181c",
        "bg_panel":      "#1b1d21",
        "bg_card":       "#212327",
        "accent":        "#c1584a",
        "accent_dim":    "#6e3229",
        "accent_bright": "#d97b6a",
        "text":          "#bcb8b4",
        "text_dim":      "#837f7a",
        "text_faint":    "#585550",
        "border":        "#33302e",
        "border_bright": "#c1584a",
        "success":       "#5a9178",
        "success_bright":"#7ab897",
        "success_bg":    "#1b2620",
        "success_border":"#2f4438",
        "danger":        "#c1704a",
        "danger_bright": "#dd9270",
        "danger_bg":     "#241a15",
        "danger_border": "#4a3226",
    },
    "modern_warfare": {
        "label": "MODERN WARFARE",
        "bg":            "#191a16",
        "bg_panel":      "#1e201a",
        "bg_card":       "#24261f",
        "accent":        "#7a9b5e",
        "accent_dim":    "#435530",
        "accent_bright": "#9bbb7d",
        "text":          "#bdbfae",
        "text_dim":      "#84876f",
        "text_faint":    "#585b4a",
        "border":        "#33362c",
        "border_bright": "#7a9b5e",
        "success":       "#6b9d6e",
        "success_bright":"#8cc290",
        "success_bg":    "#1c2a1d",
        "success_border":"#33472f",
        "danger":        "#c17a4a",
        "danger_bright": "#dd9c70",
        "danger_bg":     "#271c15",
        "danger_border": "#4a3626",
    },
    "classified": {
        "label": "CLASSIFIED",
        "bg":            "#141316",
        "bg_panel":      "#18171b",
        "bg_card":       "#1e1c21",
        "accent":        "#b1495a",
        "accent_dim":    "#5e2530",
        "accent_bright": "#cf6f7e",
        "text":          "#b7aeb0",
        "text_dim":      "#7e767a",
        "text_faint":    "#524b4e",
        "border":        "#2c272b",
        "border_bright": "#b1495a",
        "success":       "#6f9482",
        "success_bright":"#8fb89e",
        "success_bg":    "#1a231e",
        "success_border":"#304036",
        "danger":        "#b1495a",
        "danger_bright": "#d06e7e",
        "danger_bg":     "#22171a",
        "danger_border": "#452a30",
    },
    "light_ops": {
        "label": "LIGHT OPS",
        "bg":            "#ece7db",
        "bg_panel":      "#f1ece0",
        "bg_card":       "#f6f1e5",
        "accent":        "#b8752c",
        "accent_dim":    "#8f5a20",
        "accent_bright": "#d2924a",
        "text":          "#322e26",
        "text_dim":      "#6b6558",
        "text_faint":    "#9b9484",
        "border":        "#d5cdb9",
        "border_bright": "#b8752c",
        "success":       "#4f8a5c",
        "success_bright":"#6fac7c",
        "success_bg":    "#dcead9",
        "success_border":"#a8cbab",
        "danger":        "#b85a4a",
        "danger_bright": "#d67c6a",
        "danger_bg":     "#f0dcd6",
        "danger_border": "#d9aa9c",
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

QLabel#fieldLabel {
    color: $accent;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding-left: 1px;
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
    letter-spacing: 3px;
    padding: 8px 24px;
    border-radius: 2px;
    min-width: 220px;
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

QDialog {
    background-color: $bg;
}

QLineEdit#urlField {
    background-color: $bg_card;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 5px 8px;
    color: $text;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
}
QLineEdit#urlField:focus {
    border: 1px solid $accent_dim;
}

QPushButton#fetchBtn {
    background-color: $success_bg;
    border: 1px solid $success_border;
    color: $success_bright;
    padding: 5px 14px;
    letter-spacing: 1px;
}
QPushButton#fetchBtn:hover {
    background-color: $success_border;
    color: $success_bright;
}

QPushButton#fetchWebBtn {
    background-color: $accent_dim;
    border: 1px solid $accent;
    color: $accent_bright;
    padding: 4px 10px;
    font-size: 11px;
    letter-spacing: 1px;
}
QPushButton#fetchWebBtn:hover {
    background-color: $accent;
    color: $bg;
}

QPlainTextEdit#descEdit {
    background-color: $bg_card;
    border: 1px solid $border;
    border-radius: 2px;
    color: $text;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    padding: 6px;
}
QPlainTextEdit#descEdit:focus {
    border: 1px solid $accent_dim;
}

QListWidget#thumbBar {
    background-color: $bg_card;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 4px;
    color: $text_dim;
    font-size: 10px;
}
QListWidget#thumbBar::item {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: 2px;
    padding: 3px;
    color: $text_dim;
}
QListWidget#thumbBar::item:hover {
    border-color: $accent_dim;
}
QListWidget#thumbBar::item:selected {
    background-color: $bg_card;
    border: 1px solid $accent;
    color: $accent_bright;
}
QListWidget#thumbBar::item:selected:active {
    background-color: $bg_card;
    border: 1px solid $accent;
}
QListWidget#thumbBar QScrollBar:horizontal {
    background: $bg;
    height: 10px;
    margin: 0;
}
QListWidget#thumbBar QScrollBar::handle:horizontal {
    background: $border;
    min-width: 20px;
    border-radius: 5px;
}
QListWidget#thumbBar QScrollBar::add-line:horizontal,
QListWidget#thumbBar QScrollBar::sub-line:horizontal {
    width: 0px;
}

QLabel#dialogLabel {
    color: $accent;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}

QLabel#statusLabel {
    color: $text_dim;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10px;
}

QLabel#hintLabel {
    color: $danger_bright;
    font-size: 10px;
    font-style: italic;
}

QLabel#previewImg {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: 2px;
}
"""


def build_stylesheet(theme_id: str) -> str:
    tokens = THEMES.get(theme_id, THEMES[DEFAULT_THEME])
    return Template(TEMPLATE).substitute(tokens)
