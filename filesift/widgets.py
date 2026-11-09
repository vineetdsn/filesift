"""Reusable Nordic Zen widgets: architectural cards, champagne gold buttons, Swiss sidebar — UI/UX Pro Max."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QIcon, QImageReader, QLinearGradient,
                           QPainter, QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QFrame, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QSizePolicy,
                               QToolButton, QVBoxLayout, QWidget)

from . import icons, presenters, theme
from .models import FileInfo


def _load_thumb(path: str, box: int = 360) -> QPixmap:
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and size.width() > 0:
        size.scale(QSize(box, box), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)
    img = reader.read()
    return QPixmap.fromImage(img) if not img.isNull() else QPixmap()


class Card(QFrame):
    """Architectural rounded panel with whisper-thin border and matte depth."""

    def __init__(self, kind: str = "panel", parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setProperty("kind", kind)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        r = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(pal.panel_border), 1))
        if self._kind == "panel":
            p.setBrush(QColor(pal.panel))
        else:  # content / elevated
            grad = QLinearGradient(0, 0, 0, max(1, r.height()))
            grad.setColorAt(0.0, QColor(pal.card_top))
            grad.setColorAt(1.0, QColor(pal.card_bottom))
            p.setBrush(grad)
        p.drawRoundedRect(r, theme.RADIUS_CARD, theme.RADIUS_CARD)


class StatCard(Card):
    """Minimalist Scandinavian bento metric card with brushed champagne gold numbers."""

    def __init__(self, label: str, parent=None):
        super().__init__("content", parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        self._cap = QLabel(label.upper())
        self._cap.setProperty("kind", "muted")
        cap_f = self._cap.font()
        cap_f.setPointSize(9)
        cap_f.setBold(True)
        cap_f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        self._cap.setFont(cap_f)

        self._value = QLabel(presenters.EM_DASH)
        f = self._value.font()
        f.setPointSize(theme.FONT_STAT_PT)
        f.setWeight(QFont.Weight.Bold)
        self._value.setFont(f)
        self._value.setProperty("kind", "card-text")

        # Color highlight: brushed champagne gold & warm copper
        if "reclaim" in label.lower() or "safe" in label.lower():
            self._value.setStyleSheet("color: #E2B170; font-weight: bold;")
        elif "duplicate" in label.lower():
            self._value.setStyleSheet("color: #D97706; font-weight: bold;")
        else:
            self._value.setStyleSheet("color: #F4F4F5; font-weight: bold;")

        lay.addWidget(self._cap)
        lay.addWidget(self._value)

    def set_value(self, text: str) -> None:
        self._value.setText(text)


class PillButton(QPushButton):
    """Brushed Champagne Gold & architectural matte button with subtle satin depth."""

    def __init__(self, text: str = "", primary: bool = False, danger: bool = False, parent=None):
        super().__init__(text, parent)
        self._primary = primary
        self._danger = danger
        self.setProperty("primary", primary)
        self.setFixedHeight(theme.PILL_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        f = self.font()
        f.setBold(primary or danger)
        self.setFont(f)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        r = self.rect().adjusted(1, 1, -1, -1)
        rad = 12 if self._primary or self._danger else theme.RADIUS_CONTROL

        if self._primary:
            grad = QLinearGradient(0, 0, r.width(), 0)
            if self.underMouse() and self.isEnabled():
                grad.setColorAt(0.0, QColor("#EAC188"))
                grad.setColorAt(1.0, QColor("#D8A665"))
            else:
                grad.setColorAt(0.0, QColor(pal.accent))
                grad.setColorAt(1.0, QColor(pal.copper))
            p.setBrush(grad)
            p.setPen(QPen(QColor(pal.accent), 1))
            fg = QColor(pal.on_accent)
        elif self._danger:
            bg = QColor(pal.danger)
            if self.underMouse() and self.isEnabled():
                bg = bg.lighter(110)
            p.setBrush(bg)
            p.setPen(QPen(QColor(pal.danger), 1))
            fg = QColor("#FFFFFF")
        else:
            bg = QColor(pal.panel)
            border = QColor(pal.panel_border)
            if self.underMouse() and self.isEnabled():
                bg = QColor(pal.nav_hover)
                border = QColor(pal.accent)
            p.setBrush(bg)
            p.setPen(QPen(border, 1))
            fg = QColor(pal.text)

        if not self.isEnabled():
            p.setBrush(QColor(pal.panel).lighter(105))
            p.setPen(QPen(QColor(pal.panel_border), 1))
            fg = QColor(pal.text_muted)
        elif self.isDown() or self.isChecked():
            p.setBrush(QColor(pal.panel_border))

        p.drawRoundedRect(r, rad, rad)
        p.setPen(fg)
        p.setFont(self.font())
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())


class ToggleSwitch(QAbstractButton):
    """Accessible toggle switch with warm copper/champagne gold track."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 26)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(self.update)

    def hitButton(self, pos):  # noqa: N802
        return self.contentsRect().contains(pos)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        on = self.isChecked()

        track = QColor(pal.accent) if on else QColor(pal.input_border)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, 48, 26, 13, 13)

        kx = 25 if on else 3
        knob_color = QColor(pal.on_accent) if on else QColor("#FFFFFF")
        p.setBrush(knob_color)
        p.drawEllipse(kx, 3, 20, 20)


class ListRow(QFrame):
    """Clean architectural option row with whisper-thin border and generous spacing."""

    def __init__(self, icon_name: str | None = None, title: str = "",
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("kind", "row")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(62)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        self._icon = QLabel()
        self._icon.setFixedSize(26, 26)
        if icon_name:
            self._icon.setPixmap(icons.icon(icon_name, "#E2B170").pixmap(QSize(24, 24)))

        self._title = QLabel(title)
        f = self._title.font()
        f.setBold(True)
        f.setPointSize(13)
        self._title.setFont(f)

        self._sub = QLabel(subtitle)
        self._sub.setProperty("kind", "muted")
        self._sub.setWordWrap(True)

        col = QVBoxLayout()
        col.setContentsMargins(0, 2, 0, 2)
        col.setSpacing(3)
        col.addWidget(self._title)
        col.addWidget(self._sub)

        lay.addWidget(self._icon)
        lay.addLayout(col, 1)
        self._trail: QWidget | None = None

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        p.setPen(QPen(QColor(pal.panel_border), 1))
        p.setBrush(QColor(pal.panel))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1),
                          theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

    def set_title(self, t: str) -> None:
        self._title.setText(t)

    def set_subtitle(self, t: str) -> None:
        self._sub.setText(t)

    def set_trailing(self, w: QWidget) -> None:
        if self._trail is not None:
            self._trail.setParent(None)
        self._trail = w
        self.layout().addWidget(w)

    def trailing(self) -> QWidget | None:
        return self._trail


class NavButton(QToolButton):
    """Nordic Zen squircle navigation item with warm champagne indicator and micro-badge."""
    requested = Signal(str)

    def __init__(self, page_id: str, icon_name: str, label: str = "", parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self._label = label or page_id.capitalize()
        self._icon_name = icon_name
        self._badge: int | None = None
        self._active = False
        self.setText(self._label)
        self.setIcon(icons.icon(icon_name))
        self.setIconSize(QSize(20, 20))
        self.setFixedSize(190, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: self.requested.emit(self._page_id))

    def set_active(self, on: bool) -> None:
        self._active = on
        self.update()

    def set_badge(self, n: int | None) -> None:
        self._badge = n
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        w = self.width()
        h = self.height()
        btn_rect = self.rect().adjusted(4, 2, -4, -2)

        if self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.nav_hover))
            p.drawRoundedRect(btn_rect, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)
            # Left champagne gold indicator pill
            p.setBrush(QColor(pal.accent))
            p.drawRoundedRect(QRect(4, 9, 3, h - 18), 1.5, 1.5)
        elif self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.nav_hover))
            p.drawRoundedRect(btn_rect, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        # Icon
        icon_color = pal.accent if self._active else pal.text_muted
        pm = icons.icon(self._icon_name, icon_color).pixmap(QSize(20, 20))
        p.drawPixmap(14, (h - pm.height()) // 2, pm)

        # Label Text
        f = self.font()
        f.setPointSize(11)
        f.setBold(self._active)
        p.setFont(f)
        text_color = QColor(pal.text) if self._active else QColor(pal.text_muted)
        p.setPen(text_color)
        text_rect = QRect(44, 0, w - 50, h)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self._label)

        # Champagne micro-badge
        text = presenters.format_badge(self._badge) if self._badge else None
        if text:
            bf = self.font()
            bf.setPointSize(8)
            bf.setBold(True)
            p.setFont(bf)
            fm = p.fontMetrics()
            tw = max(fm.horizontalAdvance(text), 14)
            bw = tw + 10
            bh = 18
            bx = w - bw - 10
            by = (h - bh) // 2

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.accent))
            p.drawRoundedRect(QRect(bx, by, bw, bh), 9, 9)

            p.setPen(QColor(pal.on_accent))
            p.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, text)


class Sidebar(QFrame):
    """Full Scandinavian minimalist sidebar with brand header and theme switcher."""
    page_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(theme.SIDEBAR_W)
        self.setProperty("kind", "sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 20, 10, 16)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # App Brand Header
        brand_box = QWidget()
        brand_box.setFixedWidth(190)
        brand_lay = QHBoxLayout(brand_box)
        brand_lay.setContentsMargins(4, 0, 4, 16)
        brand_lay.setSpacing(10)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(icons.icon("scan", "#E2B170").pixmap(QSize(26, 26)))

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_lbl = QLabel("FileSift")
        tf = title_lbl.font()
        tf.setPointSize(15)
        tf.setBold(True)
        title_lbl.setFont(tf)

        sub_lbl = QLabel("Storage Sifter")
        sub_lbl.setProperty("kind", "muted")
        sf = sub_lbl.font()
        sf.setPointSize(9)
        sub_lbl.setFont(sf)

        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        brand_lay.addWidget(logo_lbl)
        brand_lay.addLayout(title_box)
        lay.addWidget(brand_box)

        # Navigation Buttons
        self._scan = NavButton("scan", "scan", "Scan & Folders")
        self._dup = NavButton("duplicates", "duplicates", "Duplicates")
        self._clean = NavButton("cleanup", "cleanup", "Clean Up")

        for b in (self._scan, self._dup, self._clean):
            b.requested.connect(self.page_requested)
            lay.addWidget(b)

        lay.addStretch(1)

        # Quick Theme Toggle Pill
        self._theme_btn = QPushButton("🌙 Dark Mode")
        self._theme_btn.setFixedSize(190, 36)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.clicked.connect(self._toggle_theme)
        lay.addWidget(self._theme_btn)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        pal = theme.current()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(pal.panel))
        p.drawRect(self.rect())
        p.setPen(QPen(QColor(pal.panel_border), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

    def _toggle_theme(self) -> None:
        app = QApplication.instance()
        if app:
            new_pal = theme.toggle_theme(app)
            if new_pal.name == "dark":
                self._theme_btn.setText("🌙 Dark Mode")
            else:
                self._theme_btn.setText("☀️ Light Mode")
            for widget in app.topLevelWidgets():
                widget.update()

    def set_active(self, page_id: str) -> None:
        self._scan.set_active(page_id == "scan")
        self._dup.set_active(page_id == "duplicates")
        self._clean.set_active(page_id == "cleanup")

    def set_badges(self, dups: int, safe: int) -> None:
        self._dup.set_badge(dups)
        self._clean.set_badge(safe)


class PreviewPanel(Card):
    """Architectural file preview card with formatted details and thumbnail."""

    def __init__(self, parent=None):
        super().__init__("content", parent)
        self.setMinimumWidth(320)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        head = QLabel("FILE PREVIEW")
        head.setProperty("kind", "muted")
        hf = head.font()
        hf.setPointSize(9)
        hf.setBold(True)
        head.setFont(hf)
        lay.addWidget(head)

        self._image = QLabel("Select a file to preview")
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setMinimumHeight(260)
        pal = theme.current()
        self._image.setStyleSheet(
            f"background: {pal.bg}; color: {pal.text_muted}; border: 1px dashed {pal.panel_border}; border-radius: 12px; font-size: 13px;"
        )

        self._details = QPlainTextEdit()
        self._details.setReadOnly(True)
        self._details.setMaximumHeight(200)
        self._details.setPlaceholderText("File metadata and details will appear here...")

        lay.addWidget(self._image, 1)
        lay.addWidget(self._details)

    def show_file(self, fi: FileInfo | None) -> None:
        if fi is None:
            self._image.setPixmap(QPixmap())
            self._image.setText("Select a file to preview")
            self._details.setPlainText("")
            return
        pm = _load_thumb(fi.path, 360) if fi.is_image else QPixmap()
        if pm.isNull():
            self._image.setPixmap(QPixmap())
            self._image.setText(presenters.placeholder_label(fi))
        else:
            self._image.setPixmap(pm)
        self._details.setPlainText(presenters.preview_details(fi))
