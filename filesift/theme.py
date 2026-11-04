"""Modern FileSift theme: palettes, stylesheet, fonts, glow."""
from __future__ import annotations

from dataclasses import dataclass

RADIUS_CARD = 22
RADIUS_CONTROL = 12
PILL_H = 36
PILL_RADIUS = 18
SIDEBAR_W = 80

FONT_STAT_PT = 34
FONT_STAT_WEIGHT = 300

FONT_FAMILIES = ("Segoe UI Variable Text", "Segoe UI")


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    panel: str
    panel_border: str
    card_top: str
    card_bottom: str
    text: str
    text_muted: str
    card_text: str
    accent: str
    on_accent: str
    accent_glow: str
    input_border: str
    danger: str
    shadow: str
    nav_active: str
    nav_hover: str


DARK = Palette(
    name="dark",
    bg="#2A2E48",
    panel="#33374F",
    panel_border="#3E4263",
    card_top="#E8E5FA",
    card_bottom="#D9D5F0",
    text="#1A1C2E",
    text_muted="#5A5E78",
    card_text="#1A1C2E",
    accent="#3DB8F5",
    on_accent="#0A2A3A",
    accent_glow="#3DB8F5",
    input_border="#44486A",
    danger="#FF5C7A",
    shadow="#000000",
    nav_active="#3DB8F5",
    nav_hover="#3A3F5E",
)

LIGHT = Palette(
    name="light",
    bg="#F0F2FA",
    panel="#FFFFFF",
    panel_border="#DDE1EE",
    card_top="#EAE8FF",
    card_bottom="#D6D2F5",
    text="#1A1C2E",
    text_muted="#6B7088",
    card_text="#1A1C2E",
    accent="#1A8FD4",
    on_accent="#FFFFFF",
    accent_glow="#1A8FD4",
    input_border="#C8CEE0",
    danger="#E03A5B",
    shadow="#3A3F5E",
    nav_active="#1A8FD4",
    nav_hover="#E7ECF7",
)

_current: Palette = DARK


def normalize(name: str) -> str:
    name = (name or "").strip().lower()
    return "dark" if name.startswith("d") else "light"


def current() -> Palette:
    return _current


def build_stylesheet(p: Palette) -> str:
    return f"""
    QWidget {{
        background: {p.bg};
        color: {p.text};
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background: {p.bg};
    }}
    QLabel {{
        background: transparent;
        color: {p.text};
    }}
    QLabel[kind="muted"] {{
        color: {p.text_muted};
    }}
    QLabel[kind="card-text"] {{
        color: {p.card_text};
    }}
    QFrame[kind="panel"], QFrame[kind="content"] {{
        background: transparent;
        border: none;
    }}
    QPushButton {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.panel_border};
        border-radius: {RADIUS_CONTROL}px;
        padding: 6px 14px;
    }}
    QPushButton:hover {{
        border: 1px solid {p.accent};
    }}
    QPushButton:disabled {{
        color: {p.text_muted};
        border: 1px solid {p.panel_border};
    }}
    QToolButton {{
        background: transparent;
        border: none;
        color: {p.text_muted};
        border-radius: {RADIUS_CONTROL}px;
    }}
    QToolButton:hover {{
        background: {p.nav_hover};
    }}
    QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL}px;
        padding: 6px 8px;
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}
    QPlainTextEdit, QTextEdit {{
        border: 1px solid {p.input_border};
    }}
    QComboBox QAbstractItemView {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.input_border};
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QSlider::groove:horizontal {{
        background: {p.input_border};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {p.accent};
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    QSlider::sub-page:horizontal {{
        background: {p.accent};
        border-radius: 3px;
    }}
    QProgressBar {{
        background: {p.panel};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL}px;
        text-align: center;
        color: {p.text};
        height: 18px;
    }}
    QProgressBar::chunk {{
        background: {p.accent};
        border-radius: {RADIUS_CONTROL - 1}px;
    }}
    QListWidget {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL}px;
        outline: 0;
    }}
    QListWidget::item {{
        border-radius: {RADIUS_CONTROL - 2}px;
        padding: 4px 6px;
    }}
    QListWidget::item:selected {{
        background: {p.accent};
        color: {p.on_accent};
    }}
    QHeaderView::section {{
        background: {p.panel};
        color: {p.text_muted};
        border: none;
        padding: 4px;
    }}
    QListView, QTreeView, QTableView {{
        background: {p.bg};
        color: {p.text};
        border: none;
        outline: 0;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.input_border};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.accent};
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.input_border};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        height: 0;
        width: 0;
    }}
    QToolTip {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL - 2}px;
        padding: 4px 8px;
    }}
    """


def pick_font(app) -> None:
    from PySide6.QtGui import QFont, QFontDatabase
    available = set(QFontDatabase.families())
    for fam in FONT_FAMILIES:
        if fam in available:
            app.setFont(QFont(fam))
            return
    app.setFont(QFont(FONT_FAMILIES[-1]))


def apply_theme(app, name: str) -> Palette:
    global _current
    p = DARK if normalize(name) == "dark" else LIGHT
    app.setStyleSheet(build_stylesheet(p))
    _current = p
    return p


def add_glow(widget) -> None:
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    p = current()
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(28)
    eff.setOffset(0, 4)
    c = QColor(p.accent_glow)
    c.setAlpha(140)
    eff.setColor(c)
    widget.setGraphicsEffect(eff)
