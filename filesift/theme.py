"""Modern FileSift theme: Nordic Zen Minimalist (Arc/Cron Style) — UI/UX Pro Max."""
from __future__ import annotations

from dataclasses import dataclass

RADIUS_CARD = 18
RADIUS_CONTROL = 10
PILL_H = 38
PILL_RADIUS = 19
SIDEBAR_W = 210

FONT_STAT_PT = 26
FONT_STAT_WEIGHT = 600

FONT_FAMILIES = (
    "Plus Jakarta Sans",
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


# Nordic Zen Minimalist (Soft Warm Charcoal & Brushed Champagne Gold)
DARK = Palette(
    name="dark",
    bg="#141318",
    panel="#1B1A22",
    panel_border="#272632",
    card_top="#23222B",
    card_bottom="#191820",
    text="#F4F4F6",
    text_muted="#9E9DAA",
    card_text="#F4F4F6",
    accent="#E0A96D",
    on_accent="#141318",
    accent_glow="#E0A96D",
    input_border="#2B2A36",
    danger="#E06C75",
    shadow="#000000",
    nav_active="#E0A96D",
    nav_hover="#23222C",
    success="#98C379",
    warning="#E5C07B",
    copper="#D97706",
)

# Nordic Light Minimalist (Warm Alabaster Canvas & Brushed Amber Champagne)
LIGHT = Palette(
    name="light",
    bg="#F7F7FA",
    panel="#FFFFFF",
    panel_border="#E4E4EB",
    card_top="#FFFFFF",
    card_bottom="#F6F6F9",
    text="#18181B",
    text_muted="#6E6D7A",
    card_text="#18181B",
    accent="#D99543",
    on_accent="#18181B",
    accent_glow="#D99543",
    input_border="#DFDFE6",
    danger="#DC2626",
    shadow="#D0D0D8",
    nav_active="#D99543",
    nav_hover="#F0F0F5",
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
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
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
    QLabel[kind="bento-title"] {{
        color: {p.text};
        font-size: 13px;
        font-weight: 500;
    }}
    QLabel[kind="bento-stat"] {{
        color: {p.text};
        font-size: 20px;
        font-weight: 600;
        letter-spacing: -0.5px;
    }}
    QLabel[kind="bento-sub"] {{
        color: {p.text_muted};
        font-size: 11px;
    }}
    QLabel[kind="micro-badge"] {{
        color: {"#B45309" if p.name == "light" else "#E0A96D"};
        background: {"#FFF5E8" if p.name == "light" else "#28211A"};
        border: 1px solid {"#EEDCC5" if p.name == "light" else "#3F3429"};
        border-radius: 9px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel[kind="cleanable-badge"] {{
        color: {"#B45309" if p.name == "light" else "#E0A96D"};
        background: {"#FFF5E8" if p.name == "light" else "#28211A"};
        border: 1px solid {"#EEDCC5" if p.name == "light" else "#3F3429"};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 700;
    }}
    QLabel[kind="tag-badge"] {{
        color: {p.text_muted};
        background: {"#F0F0F5" if p.name == "light" else "#222129"};
        border: 1px solid {"#E4E4EB" if p.name == "light" else "#2D2B37"};
        border-radius: 6px;
        padding: 2px 7px;
        font-size: 11px;
        font-weight: 500;
    }}
    QFrame[kind="separator"] {{
        background: {p.panel_border};
        border: none;
        min-height: 1px;
        max-height: 1px;
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
    fonts_dir = Path(__file__).parent / "fonts"
    for font_name in ("PlusJakartaSans.ttf", "Inter.ttf"):
        font_file = fonts_dir / font_name
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
