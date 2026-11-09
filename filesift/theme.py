"""Modern FileSift theme: Nordic Zen Minimalist (Arc/Cron Style) — UI/UX Pro Max."""
from __future__ import annotations

from dataclasses import dataclass

RADIUS_CARD = 14
RADIUS_CONTROL = 8
PILL_H = 38
PILL_RADIUS = 19
SIDEBAR_W = 210

FONT_STAT_PT = 26
FONT_STAT_WEIGHT = 600

FONT_FAMILIES = (
    "Inter",
    "Segoe UI Variable Text",
    "Segoe UI",
    "SF Pro Display",
    "Helvetica Neue",
    "Arial",
)


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
    success: str = "#98C379"
    warning: str = "#E5C07B"
    copper: str = "#D97706"


# Nordic Zen Minimalist (Warm Charcoal & Brushed Champagne Gold)
DARK = Palette(
    name="dark",
    bg="#131316",
    panel="#1B1B20",
    panel_border="#282830",
    card_top="#212128",
    card_bottom="#16161A",
    text="#F4F4F5",
    text_muted="#A1A1AA",
    card_text="#F4F4F5",
    accent="#E2B170",
    on_accent="#131316",
    accent_glow="#E2B170",
    input_border="#2B2B33",
    danger="#E06C75",
    shadow="#000000",
    nav_active="#E2B170",
    nav_hover="#222228",
    success="#98C379",
    warning="#E5C07B",
    copper="#D97706",
)

# Nordic Light Minimalist (Clean Warm Canvas & Brushed Copper)
LIGHT = Palette(
    name="light",
    bg="#F5F5F7",
    panel="#FFFFFF",
    panel_border="#E4E4E7",
    card_top="#FFFFFF",
    card_bottom="#F4F4F6",
    text="#18181B",
    text_muted="#71717A",
    card_text="#18181B",
    accent="#C99755",
    on_accent="#FFFFFF",
    accent_glow="#C99755",
    input_border="#D4D4D8",
    danger="#DC2626",
    shadow="#A1A1AA",
    nav_active="#C99755",
    nav_hover="#ECECEF",
    success="#16A34A",
    warning="#D97706",
    copper="#B45309",
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
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
        font-size: 12px;
    }}
    QLabel[kind="heading"] {{
        color: {p.text};
        font-size: 16px;
        font-weight: 600;
    }}
    QLabel[kind="card-text"] {{
        color: {p.card_text};
    }}
    QLabel[kind="micro-badge"] {{
        color: {p.accent};
        background: {p.card_bottom};
        border: 1px solid {p.panel_border};
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.5px;
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
        padding: 7px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: {p.nav_hover};
        border: 1px solid {p.accent};
        color: {p.text};
    }}
    QPushButton:pressed {{
        background: {p.panel_border};
    }}
    QPushButton:disabled {{
        color: {p.text_muted};
        border: 1px solid {p.panel_border};
        background: {p.bg};
        opacity: 0.5;
    }}
    QToolButton {{
        background: transparent;
        border: none;
        color: {p.text_muted};
        border-radius: {RADIUS_CONTROL}px;
    }}
    QToolButton:hover {{
        background: {p.nav_hover};
        color: {p.text};
    }}
    QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL}px;
        padding: 6px 10px;
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1px solid {p.accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.panel_border};
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
        border-radius: 6px;
        padding: 4px;
    }}
    QSlider::groove:horizontal {{
        background: {p.input_border};
        height: 5px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {p.accent};
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    QSlider::sub-page:horizontal {{
        background: {p.accent};
        border-radius: 2px;
    }}
    QProgressBar {{
        background: {p.panel};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL}px;
        text-align: center;
        color: {p.text};
        font-weight: 600;
        font-size: 11px;
        height: 20px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p.accent}, stop:1 {p.copper});
        border-radius: {RADIUS_CONTROL - 1}px;
    }}
    QListWidget {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.input_border};
        border-radius: {RADIUS_CONTROL}px;
        padding: 4px;
        outline: 0;
    }}
    QListWidget::item {{
        border-radius: 6px;
        padding: 6px 10px;
        margin: 2px 0;
        color: {p.text};
    }}
    QListWidget::item:hover {{
        background: {p.nav_hover};
    }}
    QListWidget::item:selected {{
        background: {p.accent};
        color: {p.on_accent};
        font-weight: 600;
    }}
    QHeaderView::section {{
        background: {p.panel};
        color: {p.text_muted};
        border: none;
        padding: 6px;
        font-weight: 600;
    }}
    QListView, QTreeView, QTableView {{
        background: {p.bg};
        color: {p.text};
        border: none;
        outline: 0;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.input_border};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.accent};
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.input_border};
        border-radius: 3px;
        min-width: 24px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        height: 0;
        width: 0;
    }}
    QToolTip {{
        background: {p.panel};
        color: {p.text};
        border: 1px solid {p.panel_border};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    """


def pick_font(app) -> None:
    from pathlib import Path
    from PySide6.QtGui import QFont, QFontDatabase
    font_file = Path(__file__).parent / "fonts" / "Inter.ttf"
    if font_file.exists():
        QFontDatabase.addApplicationFont(str(font_file))
    available = set(QFontDatabase.families())
    for fam in FONT_FAMILIES:
        if fam in available:
            f = QFont(fam, 10)
            f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            app.setFont(f)
            return
    app.setFont(QFont("Segoe UI", 10))


def apply_theme(app, name: str) -> Palette:
    global _current
    p = DARK if normalize(name) == "dark" else LIGHT
    app.setStyleSheet(build_stylesheet(p))
    _current = p
    return p


def toggle_theme(app) -> Palette:
    global _current
    new_mode = "light" if _current.name == "dark" else "dark"
    return apply_theme(app, new_mode)


def add_glow(widget) -> None:
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    p = current()
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(20)
    eff.setOffset(0, 3)
    c = QColor(p.accent_glow)
    c.setAlpha(80)
    eff.setColor(c)
    widget.setGraphicsEffect(eff)
